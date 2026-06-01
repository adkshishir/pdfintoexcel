"""Typed contracts between pipeline stages.

These are the *only* shapes that cross stage boundaries. Changing one is a
cross-cutting change — touch every stage that produces or consumes it.

Coordinate system: PDF user space, origin top-left, units in points (1/72 in).
We standardize on top-left so OCR coords (which are top-left in image space)
and PyMuPDF coords (which are top-left in user space) line up after a
PDF-page-height-aware flip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


PdfType = Literal["digital", "scanned", "hybrid"]
Mode = Literal["fast", "accurate"]
# How to lay out detected tables across the .xlsx workbook:
#   merged — fold consecutive tables with identical headers into one sheet
#   split  — one sheet per detected table (preserves the source PDF's page split)
OutputLayout = Literal["merged", "split"]
# tables_only — structured table path; full_document — layout workbook from all boxes
ExtractionScope = Literal["tables_only", "full_document"]
# full_document only: one worksheet vs one worksheet per PDF page
FullDocumentPages = Literal["single_sheet", "per_page"]
ImageExport = Literal["none", "figures", "only"]


@dataclass(frozen=True)
class WordBox:
    """One OCR or text-extraction token, positioned on a page."""
    text: str
    x: float
    y: float
    w: float
    h: float
    page: int
    confidence: float = 1.0  # 1.0 for digital text; OCR engines fill real values

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h


@dataclass
class RawCell:
    row: int
    col: int
    text: str
    row_span: int = 1
    col_span: int = 1
    confidence: float = 1.0


@dataclass
class RawTable:
    """Output of stage 3 (reconstruction). One per detected table region."""
    page: int
    bbox: tuple[float, float, float, float]   # (x, y, x2, y2)
    cells: list[RawCell] = field(default_factory=list)
    n_rows: int = 0
    n_cols: int = 0
    # Y-center of each row in PDF user-space points. Index parallels row idx.
    # Used by the cleaner to do geometry-aware continuation merging.
    row_y_centers: list[float] = field(default_factory=list)


ColumnType = Literal["text", "number", "date"]


@dataclass
class CleanTable:
    """Output of stage 4 (cleaning). Ready for Excel export."""
    sheet_name: str
    headers: list[str]
    rows: list[list[str]]
    confidence: list[list[float]]  # parallel to rows; per-cell confidence
    column_types: list[ColumnType] = field(default_factory=list)  # parallel to headers
    # Per-row gap from previous row (PDF points). Index 0 = +inf (no previous).
    # Cross-page boundaries also use +inf so cross-page rows never fold.
    row_gaps: list[float] = field(default_factory=list)
    # Source position — set by the cleaner from the originating RawTable.
    # Used by the full-document content classifier to place tables in reading order.
    source_page: int = 0
    source_y: float = 0.0


# ---------------------------------------------------------------------------
# Full-document content model (full_document extraction scope only)
# ---------------------------------------------------------------------------

ContentBlockKind = Literal[
    "heading", "paragraph", "bullet", "key_value", "pre_table", "table"
]


@dataclass
class ContentBlock:
    """A classified piece of content for structured full-document export."""
    kind: ContentBlockKind
    page: int
    y_start: float                                   # top-Y; used for reading-order sort
    lines: list[str] = field(default_factory=list)   # text lines (non-table kinds)
    table: "CleanTable | None" = None                # populated only when kind="table"


@dataclass
class DocumentContent:
    """Structured full-document representation produced by the content classifier."""
    header_lines: list[str]          # deduplicated; from first repeated page-header
    footer_lines: list[str]          # deduplicated; written once at the end
    body_blocks: list[ContentBlock]  # text + table blocks, sorted by (page, y_start)
    page_count: int


@dataclass
class PipelineResult:
    pdf_type: PdfType
    tables: list[CleanTable]
    page_count: int
    mean_confidence: float
    timings_ms: dict[str, int] = field(default_factory=dict)
    # Set when extraction_scope=full_document (layout export row count).
    layout_row_count: int | None = None
    # Figures sheet stats, effective OCR langs, etc. (merged into job.metrics).
    export_metrics: dict[str, Any] = field(default_factory=dict)
