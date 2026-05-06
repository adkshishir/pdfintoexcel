#!/usr/bin/env python3
"""Compare two .xlsx files and report accuracy metrics.

Use case:
    1. Convert your fixture PDF with our pipeline → ours.xlsx
    2. Convert the same PDF with iLovePDF (or Camelot, or whatever) → theirs.xlsx
    3. python -m scripts.benchmark theirs.xlsx ours.xlsx

The "reference" workbook is the *first* argument; "candidate" is the second.
The script reports per-sheet metrics and an overall accuracy score.

Metrics:
    headers_match     — whether candidate sheet has same header names (set-equal)
    row_count_ratio   — candidate_rows / reference_rows (1.0 = same)
    cell_recall       — how many reference cells were found in candidate (after norm)
    type_preservation — % of numeric/date cells that came back as the right type
    overall           — geometric mean of the above (single comparable number)

This is *advisory*. Two competing converters can both be "right" with
different layouts; the test is "did we get the same DATA out". We normalize
case, whitespace, and currency formatting before comparing values.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

_WS = re.compile(r"\s+")
_NUM_PUNCT = re.compile(r"[,\s£\$€¥%]")


def normalize(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        # Strip trailing zeros so 10.0 == "10" == "10.00".
        return ("%g" % float(value))
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    s = str(value).strip().lower()
    s = _WS.sub(" ", s)
    # If it looks numeric after stripping currency/punct, normalize that form.
    cleaned = _NUM_PUNCT.sub("", s)
    try:
        return "%g" % float(cleaned)
    except ValueError:
        return s


def is_numeric_cell(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_date_cell(value) -> bool:
    return isinstance(value, (date, datetime))


def sheet_to_grid(ws) -> tuple[list[str], list[list]]:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    body = [list(r) for r in rows[1:]]
    return headers, body


def compare_workbook(reference: Path, candidate: Path) -> dict:
    ref_wb = load_workbook(reference, data_only=True)
    cand_wb = load_workbook(candidate, data_only=True)

    ref_sheets  = [n for n in ref_wb.sheetnames  if not n.startswith("_conf_")]
    cand_sheets = [n for n in cand_wb.sheetnames if not n.startswith("_conf_")]

    print(f"reference: {reference}  ({len(ref_sheets)} data sheet(s))")
    print(f"candidate: {candidate}  ({len(cand_sheets)} data sheet(s))")
    print()

    # Match sheets by name first; fall back to positional matching.
    matched: list[tuple[str, str]] = []
    used_cand: set[str] = set()
    for r in ref_sheets:
        if r in cand_sheets:
            matched.append((r, r))
            used_cand.add(r)
    leftover_ref  = [r for r in ref_sheets  if r not in {a for (a, _) in matched}]
    leftover_cand = [c for c in cand_sheets if c not in used_cand]
    for r, c in zip(leftover_ref, leftover_cand):
        matched.append((r, c))

    overall_metrics: dict[str, list[float]] = defaultdict(list)
    for ref_name, cand_name in matched:
        m = compare_sheet(ref_wb[ref_name], cand_wb[cand_name])
        print(f"--- '{ref_name}' vs '{cand_name}' ---")
        for k, v in m.items():
            print(f"  {k:20s} {v:.3f}" if isinstance(v, float) else f"  {k:20s} {v}")
        for k, v in m.items():
            if isinstance(v, float):
                overall_metrics[k].append(v)
        print()

    if not matched:
        print("no sheet matches found — nothing to compare.")
        return {"overall": 0.0}

    # Overall = geometric mean of per-sheet scores, averaged across metric types.
    summary: dict[str, float] = {}
    for k, vs in overall_metrics.items():
        if not vs:
            continue
        summary[k] = sum(vs) / len(vs)

    floats = [v for v in summary.values() if isinstance(v, float) and v > 0]
    overall = math.exp(sum(math.log(v) for v in floats) / len(floats)) if floats else 0.0
    summary["overall"] = overall

    print("=== summary ===")
    for k, v in summary.items():
        print(f"  {k:20s} {v:.3f}")
    return summary


def compare_sheet(ref_ws, cand_ws) -> dict:
    ref_headers,  ref_body  = sheet_to_grid(ref_ws)
    cand_headers, cand_body = sheet_to_grid(cand_ws)

    # Headers — unordered set-equality on normalized strings.
    rh = {normalize(h) for h in ref_headers if h}
    ch = {normalize(h) for h in cand_headers if h}
    headers_match = 1.0 if rh and rh == ch else (
        len(rh & ch) / len(rh | ch) if (rh or ch) else 0.0
    )

    # Row count ratio.
    row_count_ratio = (
        min(len(cand_body), len(ref_body)) / max(len(cand_body), len(ref_body))
        if max(len(cand_body), len(ref_body)) else 0.0
    )

    # Cell recall — for each non-empty reference cell, was the same value
    # found *anywhere* in the candidate workbook's cells (column-aligned).
    # Column matching by normalized header.
    ref_col_by_name  = {normalize(h): i for i, h in enumerate(ref_headers)  if h}
    cand_col_by_name = {normalize(h): i for i, h in enumerate(cand_headers) if h}

    matches = 0
    misses = 0
    type_correct = 0
    type_total = 0
    for ref_row in ref_body:
        for ref_col_idx, ref_val in enumerate(ref_row):
            if ref_col_idx >= len(ref_headers):
                continue
            ref_header_norm = normalize(ref_headers[ref_col_idx])
            if not ref_header_norm or ref_val in (None, ""):
                continue
            if ref_header_norm not in cand_col_by_name:
                misses += 1
                continue
            cand_col_idx = cand_col_by_name[ref_header_norm]
            ref_norm = normalize(ref_val)
            # Look for this ref value in the candidate column.
            cand_values = [
                normalize(r[cand_col_idx])
                for r in cand_body
                if cand_col_idx < len(r)
            ]
            if ref_norm in cand_values:
                matches += 1
                # Type preservation
                if is_numeric_cell(ref_val) or is_date_cell(ref_val):
                    type_total += 1
                    matching_cand = next(
                        (r[cand_col_idx] for r in cand_body
                         if cand_col_idx < len(r) and normalize(r[cand_col_idx]) == ref_norm),
                        None,
                    )
                    if (is_numeric_cell(ref_val) and is_numeric_cell(matching_cand)) or \
                       (is_date_cell(ref_val) and is_date_cell(matching_cand)):
                        type_correct += 1
            else:
                misses += 1

    cell_recall = matches / (matches + misses) if (matches + misses) else 0.0
    type_preservation = type_correct / type_total if type_total else 1.0

    return {
        "headers_match":     headers_match,
        "row_count_ratio":   row_count_ratio,
        "cell_recall":       cell_recall,
        "type_preservation": type_preservation,
        "ref_rows":          len(ref_body),
        "cand_rows":         len(cand_body),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("reference", type=Path, help="The 'truth' workbook to compare against.")
    p.add_argument("candidate", type=Path, help="The workbook produced by our pipeline.")
    args = p.parse_args(argv)

    if not args.reference.exists() or not args.candidate.exists():
        print("both files must exist", file=sys.stderr)
        return 2

    summary = compare_workbook(args.reference, args.candidate)
    return 0 if summary.get("overall", 0.0) >= 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
