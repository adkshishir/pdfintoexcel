"""Stage 4 — clean RawTable[] → CleanTable[].

Pipeline of independent transformations:
  1. raw_to_clean        — RawCells → grid → CleanTable. Carries `row_gaps`
                           (Y-distance from previous row) for downstream
                           geometry-aware logic.
  2. drop_non_tables     — kill noise tables (cover-page layout artifacts).
  3. merge_consecutive   — fold consecutive same-header tables into one
                           sheet. Inserts +inf gap at the page boundary so
                           cross-page rows never fold.
  4. merge_continuations — fold "row with empty anchor" into the previous
                           row only when the gap is smaller than the
                           median row gap × tolerance. This is what makes
                           it safe to enable by default in `accurate` mode.
  5. infer_column_types  — text/number/date per column.
"""

from __future__ import annotations

import math
import re
from statistics import median
from typing import Iterable

from app.pipeline.types import CleanTable, ColumnType, OutputLayout, RawTable

_WS = re.compile(r"\s+")

# --- table-quality filter ---
MIN_TABLE_ROWS = 3
MIN_TABLE_COLS = 2
MAX_HEADER_LEN = 40
CONSISTENT_FILL_HIGH = 0.70
CONSISTENT_FILL_LOW = 0.10

# --- continuation merging ---
# A row is a continuation if its gap from the previous row is ≤ this
# multiple of the median within-table row gap. Tuned so wraps within a
# transaction (~1× median) fold but breaks between transactions (~2× median)
# don't.
CONTINUATION_GAP_FACTOR = 1.5
CONTINUATION_ANCHOR_THRESHOLD = 0.5

# --- type inference ---
# Month names (abbreviated + full, case-insensitive).
_MON = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_DATE_PATTERNS: list[re.Pattern] = [
    # 01/05/2024  01-05-2024  01.05.2024  (numeric separators)
    re.compile(r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$"),
    # 2024-01-05  2024/01/05  (ISO-ish)
    re.compile(r"^\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}$"),
    # 01 Jan 2024  01-Jan-24  01/Jan/2024
    re.compile(rf"^\d{{1,2}}[\s\-/\.]{_MON}[\s\-/\.]\d{{2,4}}$", re.I),
    # January 1, 2024  Jan 1 2024
    re.compile(rf"^{_MON}[\s\-/\.]{{1,2}}\d{{1,2}},?\s*\d{{4}}$", re.I),
    # 01-Jan-24 (already covered above, but explicit for clarity)
    re.compile(rf"^\d{{1,2}}{_MON}\d{{2,4}}$", re.I),
]
_NUM_RE = re.compile(r"^[\-\+]?[\d,]+(?:\.\d+)?$")
_CURRENCY_PREFIX = re.compile(r"^[\$£€¥]")
TYPE_MIN_CONFIDENCE = 0.7


# =====================================================================
def clean_tables(
    raw: list[RawTable],
    *,
    merge_continuations: bool = False,
    output_layout: OutputLayout = "merged",
) -> list[CleanTable]:
    """Reconstructed → clean.

    `merge_continuations` (mode-controlled): fold within-table wrap rows into
    the previous row using a geometric Y-gap signal.

    `output_layout`:
      - "merged" (default) — fold consecutive same-header tables into one sheet.
      - "split"            — keep each detected table on its own sheet.
    """
    used_names: set[str] = set()
    basic = []
    for table in raw:
        ct = _raw_to_clean(table, used_names)
        if ct is not None:
            basic.append(ct)

    filtered = [ct for ct in basic if _looks_like_table(ct)]
    if output_layout == "merged":
        sheets = _merge_consecutive(filtered)
    else:
        sheets = filtered

    out: list[CleanTable] = []
    for ct in sheets:
        if merge_continuations:
            ct = _merge_continuations(ct)
        ct.column_types = _infer_column_types(ct)
        out.append(ct)
    return _renumber_sheets(out)


# =====================================================================
# 1. raw → clean
# =====================================================================
def _raw_to_clean(t: RawTable, used: set[str]) -> CleanTable | None:
    if not t.cells or t.n_rows < 2:
        return None

    grid: dict[tuple[int, int], tuple[str, float]] = {}
    for c in t.cells:
        text = _WS.sub(" ", c.text).strip()
        if not text:
            continue
        grid[(c.row, c.col)] = (text, c.confidence)

    max_row = max((r for (r, _) in grid), default=-1)
    max_col = max((c for (_, c) in grid), default=-1)
    if max_row < 1 or max_col < 0:
        return None

    headers = [grid.get((0, c), ("", 1.0))[0] for c in range(max_col + 1)]
    headers = [h or f"col_{i+1}" for i, h in enumerate(headers)]

    rows: list[list[str]] = []
    confs: list[list[float]] = []
    body_y_centers: list[float] = []
    for r in range(1, max_row + 1):
        row = [grid.get((r, c), ("", 1.0))[0] for c in range(max_col + 1)]
        if not any(cell.strip() for cell in row):
            continue
        rows.append(row)
        confs.append([grid.get((r, c), ("", 1.0))[1] for c in range(max_col + 1)])
        if r < len(t.row_y_centers):
            body_y_centers.append(t.row_y_centers[r])
        else:
            body_y_centers.append(float(r))  # fallback when geometry absent

    if not rows:
        return None

    name = _make_sheet_name(t.page, used)
    used.add(name)

    # Initial gap series for this single page.
    gaps = _gaps_from_y_centers(body_y_centers)

    return CleanTable(
        sheet_name=name, headers=headers, rows=rows, confidence=confs,
        row_gaps=gaps,
        source_page=t.page,
        source_y=t.bbox[1],
    )


def _gaps_from_y_centers(ys: list[float]) -> list[float]:
    if not ys:
        return []
    gaps = [math.inf]  # first row has no predecessor
    for i in range(1, len(ys)):
        gaps.append(ys[i] - ys[i - 1])
    return gaps


def _make_sheet_name(page: int, used: set[str]) -> str:
    base = f"Page {page + 1}"
    if base not in used:
        return base
    i = 2
    while f"{base} ({i})" in used:
        i += 1
    return f"{base} ({i})"


# =====================================================================
# 2. drop non-tables
# =====================================================================
def _looks_like_table(ct: CleanTable) -> bool:
    if len(ct.rows) < MIN_TABLE_ROWS or len(ct.headers) < MIN_TABLE_COLS:
        return False
    if any(len(h) > MAX_HEADER_LEN for h in ct.headers):
        return False

    # Headers should look like labels (terse), not prose. Tolerate one
    # non-label header in tables with ≥3 columns; require all labels for
    # 2-column tables (where prose headers are a strong "this isn't a
    # table" signal).
    K = len(ct.headers)
    non_labels = sum(1 for h in ct.headers if not _looks_label(h))
    if non_labels > (1 if K >= 3 else 0):
        return False

    # Body shape: at least one column should be *consistently* filled or
    # empty. Layout coincidences sit in the middling 30–70% band everywhere.
    n = len(ct.rows)
    for col in range(K):
        fill_rate = sum(1 for r in ct.rows if r[col].strip()) / n
        if fill_rate >= CONSISTENT_FILL_HIGH or fill_rate <= CONSISTENT_FILL_LOW:
            return True
    return False


def _looks_label(h: str) -> bool:
    """A label is short. Two-word labels like '(GBP) Amount' qualify;
    three-word phrases like 'Elaine Rowena Gregory' don't."""
    return len(h.split()) <= 2 or len(h) <= 8


# =====================================================================
# 3. merge consecutive same-header tables
# =====================================================================
def _merge_consecutive(tables: list[CleanTable]) -> list[CleanTable]:
    if not tables:
        return []
    out: list[CleanTable] = [_clone_for_merge(tables[0])]
    for t in tables[1:]:
        prev = out[-1]
        if _headers_equivalent(prev.headers, t.headers):
            prev.rows.extend(t.rows)
            prev.confidence.extend(t.confidence)
            # +inf gap at the page boundary so cross-page rows never fold.
            prev.row_gaps.append(math.inf)
            # First row of the appended table already has a gap value (inf
            # in its own series) — replace it with our boundary marker, then
            # append the rest.
            prev.row_gaps.extend(t.row_gaps[1:])
            prev.sheet_name = f"{prev.sheet_name.split(' (')[0]} (merged)"
        else:
            out.append(_clone_for_merge(t))
    return out


def _clone_for_merge(t: CleanTable) -> CleanTable:
    return CleanTable(
        sheet_name=t.sheet_name,
        headers=list(t.headers),
        rows=[list(r) for r in t.rows],
        confidence=[list(c) for c in t.confidence],
        column_types=list(t.column_types),
        row_gaps=list(t.row_gaps),
        source_page=t.source_page,
        source_y=t.source_y,
    )


def _headers_equivalent(a: list[str], b: list[str]) -> bool:
    if len(a) != len(b):
        return False
    return all(_norm_header(x) == _norm_header(y) for x, y in zip(a, b))


def _norm_header(h: str) -> str:
    return _WS.sub(" ", h).strip().lower()


# =====================================================================
# 4. continuation merging — geometry-aware
# =====================================================================
def _merge_continuations(ct: CleanTable) -> CleanTable:
    """Fold wrap rows into their logical anchor row.

    Three cases:

    1. Backward merge (existing): anchor-empty or sparse row *after* an anchor
       row with a small Y-gap → append into previous output row.

    2. Forward merge (new): anchor-empty rows that appear *before* the first
       anchor row (or after a cross-page boundary), followed by an anchor row
       within threshold gap → prepend buffered content into the anchor row.
       Handles PDFs where description text starts above the date/amount
       because those cells are vertically centred inside the row height.

    3. Mid-table preamble (new): when an anchor-empty row sits between two
       anchor rows, look ahead — if the *next* anchor row is at least as
       close as the *previous* one, treat the empty row as a preamble for
       the next row rather than a tail of the previous one.

    Cross-page boundaries (gap=inf) always prevent merging.
    """
    if len(ct.rows) < 2:
        return ct

    K = len(ct.headers)
    n = len(ct.rows)

    anchor_col = None
    for col in range(K):
        fill = sum(1 for r in ct.rows if r[col].strip()) / n
        if fill >= CONTINUATION_ANCHOR_THRESHOLD:
            anchor_col = col
            break

    finite_gaps = [g for g in ct.row_gaps if math.isfinite(g) and g > 0]
    if not finite_gaps:
        return ct
    threshold = median(finite_gaps) * CONTINUATION_GAP_FACTOR
    avg_fill_cells = sum(sum(1 for c in r if c.strip()) for r in ct.rows) / n

    new_rows: list[list[str]] = []
    new_confs: list[list[float]] = []
    new_gaps: list[float] = []

    # Preamble buffer: anchor-empty rows with no prior anchor row to merge
    # into, accumulated as a single pre-merged row pending the next anchor.
    pre_row: list[str] | None = None
    pre_conf: list[float] | None = None
    pre_entry_gap: float = math.inf

    def _flush_pre() -> None:
        nonlocal pre_row, pre_conf, pre_entry_gap
        if pre_row is not None:
            new_rows.append(pre_row)
            new_confs.append(pre_conf)
            new_gaps.append(pre_entry_gap)
            pre_row = None
            pre_conf = None
            pre_entry_gap = math.inf

    def _accum_pre(row: list[str], conf: list[float], entry_gap: float) -> None:
        nonlocal pre_row, pre_conf, pre_entry_gap
        if pre_row is None:
            pre_row = list(row)
            pre_conf = list(conf)
            pre_entry_gap = entry_gap
        else:
            for c in range(K):
                cell = row[c].strip()
                if not cell:
                    continue
                if pre_row[c].strip():
                    pre_row[c] = (pre_row[c] + " " + cell).strip()
                    pre_conf[c] = min(pre_conf[c], conf[c])
                else:
                    pre_row[c] = cell
                    pre_conf[c] = conf[c]

    for i, row in enumerate(ct.rows):
        gap = ct.row_gaps[i] if i < len(ct.row_gaps) else math.inf
        row_fill_cells = sum(1 for c in row if c.strip())

        anchor_empty = anchor_col is not None and not row[anchor_col].strip()
        sparse = row_fill_cells < max(1, avg_fill_cells * 0.5)
        is_small_gap = math.isfinite(gap) and gap <= threshold

        if anchor_empty or sparse:
            # Decide between backward merge, forward preamble, and plain emit.

            # Look ahead: is the next row an anchor row and at least as close
            # as the current gap?  If so, this row is a preamble for the next
            # row, not a tail of the previous one.
            next_gap = ct.row_gaps[i + 1] if i + 1 < len(ct.row_gaps) else math.inf
            next_has_anchor = (
                anchor_col is not None
                and i + 1 < len(ct.rows)
                and ct.rows[i + 1][anchor_col].strip()
            )
            # Forward preamble only applies when backward merge is impossible:
            # either no previous anchor row exists, or the gap to that row is
            # too large (e.g. cross-page boundary).  When backward merge IS
            # possible, prefer it to avoid misrouting wrap rows.
            is_preamble_for_next = (
                (not new_rows or not is_small_gap)
                and next_has_anchor
                and math.isfinite(next_gap)
                and next_gap <= threshold
            )

            if is_small_gap and new_rows and not is_preamble_for_next:
                # Case 1: backward merge into previous output row.
                for c in range(K):
                    cell = row[c].strip()
                    if not cell:
                        continue
                    if new_rows[-1][c].strip():
                        new_rows[-1][c] = (new_rows[-1][c] + " " + cell).strip()
                    else:
                        new_rows[-1][c] = cell
                    new_confs[-1][c] = min(new_confs[-1][c], ct.confidence[i][c])
            else:
                # Case 2 / 3: park as preamble for a forward merge.
                # If the gap is large (cross-page), flush any existing preamble first.
                if not is_small_gap and pre_row is not None:
                    _flush_pre()
                _accum_pre(list(row), list(ct.confidence[i]), gap)

        else:
            # Anchor-filled row.
            if pre_row is not None and is_small_gap:
                # Case 2/3 forward merge: prepend preamble content into this row.
                merged = list(row)
                merged_conf = list(ct.confidence[i])
                for c in range(K):
                    cell = pre_row[c].strip()
                    if not cell:
                        continue
                    if merged[c].strip():
                        # Preamble text precedes anchor text in reading order.
                        merged[c] = (cell + " " + merged[c]).strip()
                        merged_conf[c] = min(pre_conf[c], merged_conf[c])
                    else:
                        merged[c] = cell
                        merged_conf[c] = pre_conf[c]
                new_rows.append(merged)
                new_confs.append(merged_conf)
                new_gaps.append(pre_entry_gap)
                pre_row = None
                pre_conf = None
                pre_entry_gap = math.inf
            else:
                _flush_pre()
                new_rows.append(list(row))
                new_confs.append(list(ct.confidence[i]))
                new_gaps.append(gap)

    _flush_pre()

    return CleanTable(
        sheet_name=ct.sheet_name,
        headers=ct.headers,
        rows=new_rows,
        confidence=new_confs,
        column_types=ct.column_types,
        row_gaps=new_gaps,
    )


# =====================================================================
# 5. column type inference
# =====================================================================
def _infer_column_types(ct: CleanTable) -> list[ColumnType]:
    K = len(ct.headers)
    types: list[ColumnType] = []
    for col in range(K):
        values = [r[col].strip() for r in ct.rows if r[col].strip()]
        types.append(_infer_one_column(values))
    return types


def _infer_one_column(values: Iterable[str]) -> ColumnType:
    vals = list(values)
    if not vals:
        return "text"
    n = len(vals)

    date_hits = sum(1 for v in vals if _is_date(v))
    if date_hits / n >= TYPE_MIN_CONFIDENCE:
        return "date"

    num_hits = sum(1 for v in vals if _looks_numeric(v))
    if num_hits / n >= TYPE_MIN_CONFIDENCE:
        return "number"

    return "text"


def _is_date(v: str) -> bool:
    s = v.strip()
    return any(p.match(s) for p in _DATE_PATTERNS)


def _looks_numeric(v: str) -> bool:
    s = _CURRENCY_PREFIX.sub("", v).strip()
    return bool(_NUM_RE.match(s))


# =====================================================================
def _renumber_sheets(tables: list[CleanTable]) -> list[CleanTable]:
    used: set[str] = set()
    for t in tables:
        if t.sheet_name in used:
            base = t.sheet_name
            i = 2
            while f"{base} ({i})" in used:
                i += 1
            t.sheet_name = f"{base} ({i})"
        used.add(t.sheet_name)
    return tables
