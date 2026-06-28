"""Blog content strategy data — mirrors pdfintoexcel-blog-content-strategy.md.

Python is the source of truth for generation; frontend blog-content-strategy.data.ts
should stay in sync.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

BlogCategorySlug = Literal["tutorial", "guide", "workflow", "features"]

BLOG_CATEGORY_SLUGS: tuple[BlogCategorySlug, ...] = (
    "tutorial",
    "guide",
    "workflow",
    "features",
)

BLOG_CATEGORY_LABELS: dict[BlogCategorySlug, str] = {
    "tutorial": "Tutorial",
    "guide": "Guide",
    "workflow": "Workflow",
    "features": "Features",
}

COMPARISON_POST_RATIO = 0.45

COMPETITOR_PLATFORMS: tuple[str, ...] = (
    "Adobe Acrobat",
    "Smallpdf",
    "iLovePDF",
    "PDFTables",
    "Tabula",
    "Cometdocs",
    "Nitro PDF",
    "Soda PDF",
    "Zamzar",
    "CleverPDF",
)

_COMPARISON_RE = re.compile(
    r"\bvs\.?\b|versus|compared to|comparison|alternative",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BlogTopicStrategy:
    topic: str
    primary_keyword: str
    category_slug: BlogCategorySlug
    comparison_targets: tuple[str, ...]
    is_comparison: bool
    week: int | None = None  # calendar week; None for backlog-only topics


def infer_is_comparison(topic: str) -> bool:
    return bool(_COMPARISON_RE.search(topic))


def infer_category_slug(topic: str) -> BlogCategorySlug:
    t = topic.lower()
    if re.search(r"step-by-step|how to|tutorial|walkthrough|beginner", t):
        return "tutorial"
    if re.search(r"finance|accounting|ap |payroll|industry|workflow|team", t):
        return "workflow"
    if re.search(r"ocr|batch|api|detection|feature|accuracy|automation", t):
        return "features"
    return "guide"


def slug_from_topic(topic: str) -> str:
    s = topic.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:160]


def _topic(
    topic: str,
    primary_keyword: str,
    category_slug: BlogCategorySlug,
    *,
    is_comparison: bool | None = None,
    comparison_targets: tuple[str, ...] = (),
    week: int | None = None,
) -> BlogTopicStrategy:
    comp = infer_is_comparison(topic) if is_comparison is None else is_comparison
    return BlogTopicStrategy(
        topic=topic,
        primary_keyword=primary_keyword,
        category_slug=category_slug,
        comparison_targets=comparison_targets,
        is_comparison=comp,
        week=week,
    )


# Section 7 — 8-week content calendar
CONTENT_CALENDAR: tuple[BlogTopicStrategy, ...] = (
    _topic(
        "How to Convert a PDF Bank Statement to Excel (Step-by-Step)",
        "bank statement pdf to excel",
        "tutorial",
        is_comparison=False,
        week=1,
    ),
    _topic(
        "PDFIntoExcel vs Smallpdf: Best Tool for PDF to Excel Conversion",
        "smallpdf to excel alternative",
        "guide",
        comparison_targets=("Smallpdf",),
        is_comparison=True,
        week=2,
    ),
    _topic(
        "Scanned PDF to Excel: Complete OCR Guide",
        "scanned pdf to excel",
        "features",
        is_comparison=False,
        week=3,
    ),
    _topic(
        "Best PDF to Excel Converters Compared (2026)",
        "best pdf to excel converter",
        "guide",
        comparison_targets=COMPETITOR_PLATFORMS[:4],
        is_comparison=True,
        week=4,
    ),
    _topic(
        "Invoice PDF to Excel Workflow for Accounts Payable Teams",
        "invoice pdf to excel",
        "workflow",
        is_comparison=False,
        week=5,
    ),
    _topic(
        "PDFIntoExcel vs Adobe Acrobat for Table Extraction",
        "adobe pdf to excel alternative",
        "features",
        comparison_targets=("Adobe Acrobat",),
        is_comparison=True,
        week=6,
    ),
    _topic(
        "Why PDF Tables Break in Excel — and How to Fix Them",
        "pdf to excel keep formatting",
        "guide",
        is_comparison=False,
        week=7,
    ),
    _topic(
        "Batch PDF to Excel: Process Hundreds of Files Efficiently",
        "batch pdf to excel",
        "features",
        is_comparison=False,
        week=8,
    ),
)

# Weeks 9–16 backlog (from strategy doc)
CALENDAR_BACKLOG: tuple[BlogTopicStrategy, ...] = (
    _topic(
        "PDFIntoExcel vs iLovePDF for Batch Conversion",
        "ilovepdf to excel alternative",
        "features",
        comparison_targets=("iLovePDF",),
        is_comparison=True,
        week=9,
    ),
    _topic(
        "Extract Table from PDF to Excel Without Losing Columns",
        "extract table from pdf to excel",
        "tutorial",
        is_comparison=False,
        week=10,
    ),
    _topic(
        "Month-End Close: PDF Statements to Excel Pivot Tables",
        "financial pdf to excel",
        "workflow",
        is_comparison=False,
        week=11,
    ),
    _topic(
        "Free PDF to Excel Converter: Limits and What to Expect",
        "free pdf to excel converter",
        "guide",
        is_comparison=False,
        week=12,
    ),
    _topic(
        "PDF to Excel API for Developers",
        "batch pdf to excel",
        "features",
        is_comparison=False,
        week=13,
    ),
    _topic(
        "Credit Card Statement PDF to Excel (Step-by-Step)",
        "bank statement pdf to excel",
        "tutorial",
        is_comparison=False,
        week=14,
    ),
    _topic(
        "PDFTables vs PDFIntoExcel for Financial Documents",
        "best pdf to excel converter",
        "guide",
        comparison_targets=("PDFTables",),
        is_comparison=True,
        week=15,
    ),
    _topic(
        "Healthcare Billing PDF to Excel Workflow",
        "invoice pdf to excel",
        "workflow",
        is_comparison=False,
        week=16,
    ),
)

# Section 10 — extended topic backlog
TOPIC_BACKLOG: tuple[BlogTopicStrategy, ...] = (
    # Tutorials
    _topic("How to convert a PDF bank statement to Excel in 5 minutes", "bank statement pdf to excel", "tutorial"),
    _topic("Convert credit card statement PDF to Excel step-by-step", "bank statement pdf to excel", "tutorial"),
    _topic("Extract a table from a PDF report into Excel", "extract table from pdf to excel", "tutorial"),
    _topic("Convert a multi-page PDF to one Excel workbook", "pdf to xlsx", "tutorial"),
    _topic("PDF pay stub to Excel for tax preparation", "financial pdf to excel", "tutorial"),
    _topic("Convert PDF invoice to Excel for QuickBooks import", "invoice pdf to excel", "tutorial"),
    _topic("How to convert a password-protected PDF to Excel", "how to convert pdf to excel", "tutorial"),
    _topic("PDF to Excel on Mac without installing software", "pdf to excel online", "tutorial"),
    _topic("Convert PDF to Excel with merged cells fixed manually", "pdf to excel keep formatting", "tutorial"),
    _topic("Extract transaction list from PDF to Excel CSV format", "extract data from pdf to excel", "tutorial"),
    # Guides
    _topic("PDF to Excel conversion methods compared (online, desktop, manual)", "how to convert pdf to excel", "guide"),
    _topic("How to fix column misalignment after PDF to Excel conversion", "pdf to excel keep formatting", "guide"),
    _topic("When OCR fails: troubleshooting scanned PDF to Excel", "ocr pdf to excel", "guide"),
    _topic("PDF to Excel for accountants: compliance and audit trail", "financial pdf to excel", "guide"),
    _topic("Free vs paid PDF to Excel converters: what you actually get", "free pdf to excel converter", "guide"),
    _topic("How to validate Excel output after PDF conversion", "extract data from pdf to excel", "guide"),
    _topic("PDF table extraction glossary for non-technical users", "pdf table to excel", "guide"),
    _topic("Choosing between PDF to Excel and PDF to CSV", "convert pdf to excel", "guide"),
    # Workflows
    _topic("Accounts payable: invoice PDF to Excel reconciliation workflow", "invoice pdf to excel", "workflow"),
    _topic("Bookkeeping: monthly bank statement PDF batch to Excel", "bank statement pdf to excel", "workflow"),
    _topic("Auditors: extracting financial tables from PDF annual reports", "financial pdf to excel", "workflow"),
    _topic("HR: timesheet and pay stub PDF processing at scale", "batch pdf to excel", "workflow"),
    _topic("Real estate: rent roll PDF to Excel for analysis", "extract table from pdf to excel", "workflow"),
    _topic("Legal: discovery document table extraction to Excel", "extract data from pdf to excel", "workflow"),
    _topic("Research analysts: pulling data tables from whitepaper PDFs", "pdf table to excel", "workflow"),
    _topic("E-commerce: supplier invoice PDF to inventory spreadsheet", "invoice pdf to excel", "workflow"),
    # Features
    _topic("How PDFIntoExcel table detection works", "pdf table to excel", "features"),
    _topic("OCR settings that improve scanned PDF to Excel accuracy", "ocr pdf to excel", "features"),
    _topic("Batch PDF to Excel: limits, speed, and naming conventions", "batch pdf to excel", "features"),
    _topic("PDF to Excel API: integrate conversion into your app", "batch pdf to excel", "features"),
    _topic("Security and file deletion policy for online PDF conversion", "pdf to excel online", "features"),
    _topic("Handling rotated pages and skewed scans in OCR pipeline", "scanned pdf to excel", "features"),
    # Comparisons
    _topic(
        "PDFIntoExcel vs Adobe Acrobat for bank statements",
        "adobe pdf to excel alternative",
        "guide",
        comparison_targets=("Adobe Acrobat",),
        is_comparison=True,
    ),
    _topic(
        "PDFIntoExcel vs Smallpdf: speed and accuracy test",
        "smallpdf to excel alternative",
        "guide",
        comparison_targets=("Smallpdf",),
        is_comparison=True,
    ),
    _topic(
        "PDFIntoExcel vs iLovePDF for free PDF to Excel",
        "best pdf to excel converter",
        "guide",
        comparison_targets=("iLovePDF",),
        is_comparison=True,
    ),
    _topic(
        "PDFIntoExcel vs PDFTables for financial PDFs",
        "best pdf to excel converter",
        "guide",
        comparison_targets=("PDFTables",),
        is_comparison=True,
    ),
    _topic(
        "PDFIntoExcel vs Tabula for open-source table extraction",
        "best pdf to excel converter",
        "features",
        comparison_targets=("Tabula",),
        is_comparison=True,
    ),
    _topic(
        "Best Adobe Acrobat alternative for PDF to Excel",
        "adobe pdf to excel alternative",
        "guide",
        comparison_targets=("Adobe Acrobat",),
        is_comparison=True,
    ),
    _topic(
        "Smallpdf alternative for batch PDF to Excel",
        "smallpdf to excel alternative",
        "features",
        comparison_targets=("Smallpdf",),
        is_comparison=True,
    ),
    _topic(
        "iLovePDF vs PDFIntoExcel: which handles scanned PDFs better?",
        "scanned pdf to excel",
        "features",
        comparison_targets=("iLovePDF",),
        is_comparison=True,
    ),
)

ALL_TOPICS: tuple[BlogTopicStrategy, ...] = (
    CONTENT_CALENDAR + CALENDAR_BACKLOG + TOPIC_BACKLOG
)

BLOG_CTA_MARKDOWN = """

---

**Ready to convert?** [Upload your PDF at pdfintoexcel](/?utm_source=blog&utm_medium=article) — free to start, no sign-up required.
"""
