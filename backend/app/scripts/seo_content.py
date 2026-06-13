"""SEO landing pages and blog posts for idempotent seeding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LandingSeed:
    slug: str
    title: str
    body: str
    faq_items: list[dict[str, str]]
    internal_links: list[dict[str, str]]
    status: str = "published"


@dataclass(frozen=True)
class BlogSeed:
    slug: str
    title: str
    meta_title: str | None
    meta_description: str
    body: str
    keywords: str | None = None
    status: str = "published"


LANDING_PAGES: tuple[LandingSeed, ...] = (
    LandingSeed(
        slug="bank-statement-pdf-to-excel",
        title="Bank Statement PDF to Excel",
        body="""Need to turn a monthly bank statement PDF into Excel for bookkeeping or reconciliation? pdfintoexcel reconstructs transaction tables — dates, descriptions, amounts, and running balances — as editable rows instead of a wall of pasted text.

## Why bank statements are hard to convert

Most converters treat a statement like a text dump. Multi-line descriptions, wrapped cells, and footer totals get split across rows. Our pipeline reads the geometric layout of the table and merges continuation lines before export.

## How to convert a bank statement PDF into Excel

1. Open the [pdfintoexcel converter](/).
2. Upload your statement PDF (native or scanned).
3. Choose **Tables only** and **Normal PDF** (or **Scanned** if it is image-based).
4. Click **Convert to Excel** and download the `.xlsx` file.

For multi-page statements, each detected table can export to its own sheet or merge into one — your choice at upload time.

## Tips for cleaner output

- Prefer PDFs exported directly from your bank portal over photocopied scans.
- If the scan is skewed, straighten it before upload for better OCR.
- Check the confidence sheet in accurate mode when reconciling high-value accounts.

Related: [invoice PDF to Excel](/invoice-pdf-to-excel) · [Blog: bank statement guide](/blog/bank-statement-pdf-to-excel)
""",
        faq_items=[
            {
                "q": "Can I convert a scanned bank statement PDF into Excel?",
                "a": "Yes. Enable Scanned (OCR) mode. Our engine reads image-based statements and rebuilds the transaction table.",
            },
            {
                "q": "Will running balances stay in the right column?",
                "a": "We target structural fidelity — dates, amounts, and balances land in separate columns when the source PDF has a clear table grid.",
            },
        ],
        internal_links=[
            {"href": "/", "label": "Convert PDF into Excel free"},
            {"href": "/invoice-pdf-to-excel", "label": "Invoice PDF to Excel"},
            {"href": "/blog/bank-statement-pdf-to-excel", "label": "How-to: bank statement conversion"},
        ],
    ),
    LandingSeed(
        slug="invoice-pdf-to-excel",
        title="Invoice PDF to Excel",
        body="""Supplier invoices arrive as PDFs. You need line items, quantities, unit prices, and totals in Excel for AP workflows. pdfintoexcel extracts invoice tables while keeping numbers typed as numbers.

## What we extract from invoice PDFs

- Line-item tables with SKU, description, qty, unit price, line total
- Header blocks with invoice number, date, and vendor name (full-document mode)
- Tax and subtotal rows when they sit inside the table grid

## Convert an invoice PDF to Excel free

Upload at the [homepage converter](/). Use **Tables only** for a single line-item grid, or **Full document** when the invoice mixes metadata and tables on one page.

See also our guide on [free invoice PDF to Excel conversion](/blog/pdf-invoice-to-excel-free).
""",
        faq_items=[
            {
                "q": "Is invoice PDF to Excel conversion free?",
                "a": "Yes. You can start without an account. Larger files and batch jobs are available on paid plans.",
            },
            {
                "q": "Can I convert multiple invoices at once?",
                "a": "Upload one PDF at a time on the free tier. Each multi-page PDF can contain several invoice tables on separate sheets.",
            },
        ],
        internal_links=[
            {"href": "/", "label": "Try the converter"},
            {"href": "/bank-statement-pdf-to-excel", "label": "Bank statement PDF to Excel"},
            {"href": "/blog/pdf-invoice-to-excel-free", "label": "Invoice conversion tutorial"},
        ],
    ),
    LandingSeed(
        slug="scanned-pdf-to-excel",
        title="Scanned PDF to Excel (OCR)",
        body="""Image-based and scanned PDFs need OCR before table reconstruction. pdfintoexcel runs optical character recognition, then rebuilds rows and columns geometrically — the same pipeline we use for digital PDFs.

## When to use scanned mode

Choose **Scanned (OCR)** when your PDF is a photo, scan, or print-to-PDF from a flatbed. Native text PDFs should stay on **Normal PDF** for faster, more accurate results.

## OCR + table extraction workflow

1. Upload the scanned PDF at [pdfintoexcel](/).
2. Select **Scanned (OCR)** and **Accurate** mode for complex tables.
3. Download Excel with typed numeric columns where OCR confidence is high.

Read the full tutorial: [extract tables from scanned PDF](/blog/extract-tables-scanned-pdf).
""",
        faq_items=[
            {
                "q": "Which languages does OCR support?",
                "a": "We support 25+ languages for scanned table extraction.",
            },
            {
                "q": "Will merged header cells survive OCR?",
                "a": "Yes. After OCR, our reconstructor preserves merged regions when the grid lines or column alignment are visible.",
            },
        ],
        internal_links=[
            {"href": "/", "label": "Convert scanned PDF into Excel"},
            {"href": "/blog/extract-tables-scanned-pdf", "label": "Scanned PDF table extraction guide"},
            {"href": "/bank-statement-pdf-to-excel", "label": "Bank statements from scans"},
        ],
    ),
    LandingSeed(
        slug="research-data-pdf-to-excel",
        title="Research Data PDF to Excel",
        body="""Scientific papers and survey reports often publish results as PDF tables. Manual retyping wastes hours and introduces errors. pdfintoexcel converts research tables into Excel for stats packages and charting.

## Typical research PDF use cases

- Clinical trial outcome tables
- Survey crosstabs and frequency tables
- Lab instrument exports embedded in reports
- Supplementary data tables from journals

## Export research tables to Excel

Use **Tables only** when the PDF is mostly data grids. Use **Full document** when you need section headings plus inline tables on one sheet.

More detail: [PDF research data to Excel](/blog/pdf-research-data-to-excel).
""",
        faq_items=[
            {
                "q": "Will statistical notation convert correctly?",
                "a": "Standard numeric cells, percentages, and p-values export as typed values when OCR or digital text is clear.",
            },
            {
                "q": "Can I convert multi-page supplementary tables?",
                "a": "Yes. Multi-page PDFs map to multiple sheets or a merged layout depending on your output settings.",
            },
        ],
        internal_links=[
            {"href": "/", "label": "Convert research PDF into Excel"},
            {"href": "/blog/pdf-research-data-to-excel", "label": "Research data conversion guide"},
            {"href": "/scanned-pdf-to-excel", "label": "Scanned journal PDFs (OCR)"},
        ],
    ),
)

_BLOG_CTA = """

---

**Ready to convert?** [Upload your PDF at pdfintoexcel](/) — free to start, no sign-up required.
"""

_BLOG_POSTS_RAW: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "bank-statement-pdf-to-excel",
        "How to Convert Bank Statement PDF to Excel",
        "How to Convert Bank Statement PDF to Excel (Step by Step)",
        "Turn bank statement PDFs into editable Excel workbooks with accurate transaction rows. Step-by-step guide using pdfintoexcel.",
        """Finance teams reconcile faster when statements live in Excel. Here is a reliable workflow to convert bank statement PDF to Excel without mangled rows.

## Step 1: Export or download your statement as PDF

Log into your bank portal and download the official PDF. Native digital PDFs convert faster than phone photos.

## Step 2: Upload to pdfintoexcel

Open the [converter](/) and drag your statement onto the drop zone. Files up to 50 MB are supported.

## Step 3: Choose the right mode

Select **Tables only** for transaction grids. Pick **Scanned (OCR)** if the PDF is image-based. Use **Accurate** mode when balances must reconcile to the penny.

## Step 4: Download and verify

Open the `.xlsx` file. Confirm date, description, debit/credit, and balance columns align. Use Excel filters to spot-check five random transactions against the PDF.

## Step 5: Import into your workflow

Import into QuickBooks, Xero, or your reconciliation template. Typed amount columns mean SUM and VLOOKUP work immediately.

For scanned statements see our [scanned PDF to Excel landing page](/scanned-pdf-to-excel).
""",
    ),
    (
        "extract-tables-scanned-pdf",
        "Extract Tables from Scanned PDF",
        "Extract Tables from Scanned PDF — OCR to Excel Guide",
        "Learn how to extract tables from scanned PDF files using OCR and geometric table reconstruction.",
        """Scanned PDFs do not contain selectable text — you need OCR plus layout analysis. Here is how to extract tables from scanned PDF documents into Excel.

## Step 1: Assess scan quality

Straighten skewed pages and ensure table borders or column gaps are visible. Higher DPI scans improve OCR accuracy.

## Step 2: Upload with Scanned (OCR) enabled

At [pdfintoexcel](/), choose **Scanned (OCR)** and **Accurate** mode for dense tables.

## Step 3: Let the pipeline run OCR then reconstruction

We run optical character recognition to produce word boxes, then cluster rows and columns geometrically — the same core algorithm as digital PDFs.

## Step 4: Review the Excel output

Check header rows, merged cells, and numeric columns. Re-run with accurate mode if wrap text created extra rows.

See also [scanned PDF to Excel](/scanned-pdf-to-excel) for invoice and statement use cases.
""",
    ),
    (
        "pdf-invoice-to-excel-free",
        "PDF Invoice to Excel Free",
        "PDF Invoice to Excel Free — Convert AP Tables Online",
        "Convert supplier invoice PDFs to Excel for free. Extract line items, quantities, and totals with pdfintoexcel.",
        """Accounts payable teams need invoice line items in Excel, not copy-pasted text. This guide covers PDF invoice to Excel free conversion online.

## Step 1: Gather invoice PDFs

Use vendor portal downloads or email attachments. Multi-page PDFs with one invoice per page work well.

## Step 2: Upload to the free converter

Visit [pdfintoexcel](/) — no account required to start. Drop your invoice PDF.

## Step 3: Select Tables only

For standard line-item grids, **Tables only** exports just the item table. Choose **Full document** when metadata and tables should stay together.

## Step 4: Download XLSX and validate totals

Compare the Excel subtotal row against the PDF. Numbers export as numeric cells for easy SUM checks.

More on [invoice PDF to Excel](/invoice-pdf-to-excel).
""",
    ),
    (
        "pdf-multiple-tables-to-excel",
        "Convert PDF with Multiple Tables to Excel",
        "Convert PDF with Multiple Tables to Excel — Multi-Sheet Export",
        "Export PDFs that contain several tables into Excel with separate sheets or merged layouts.",
        """Reports often pack several tables on one page or across chapters. Here is how to convert PDF with multiple tables to Excel without mixing them together.

## Step 1: Upload the full PDF

Use [pdfintoexcel](/) and keep the entire document — do not split manually unless tables are on unrelated pages you want to skip.

## Step 2: Pick output layout

Choose **Split** to put each detected table on its own sheet. Choose **Merged** when consecutive tables share the same header row.

## Step 3: Use Tables only or Full document

**Tables only** ignores prose paragraphs. **Full document** keeps headings and key-value blocks between tables.

## Step 4: Review sheet names and order

Each sheet should map to a logical table from the PDF. Rename sheets in Excel for your model.

Related: [research data PDF to Excel](/research-data-pdf-to-excel).
""",
    ),
    (
        "pdf-to-excel-without-losing-formatting",
        "How to Convert PDF to Excel Without Losing Formatting",
        "Convert PDF to Excel Without Losing Formatting",
        "Preserve rows, columns, merged cells, and number formats when converting PDF into Excel.",
        """Generic converters flatten layout. To convert PDF to Excel without losing formatting, you need geometric table reconstruction — not a text paste.

## Step 1: Avoid copy-paste from PDF viewers

Copy-paste breaks merged headers and splits amounts across rows. Use a layout-aware converter instead.

## Step 2: Upload to pdfintoexcel

Our engine detects column boundaries and merged regions before writing Excel.

## Step 3: Choose accurate mode for complex layouts

Financial statements and invoices benefit from **Accurate** mode when wrap text and tall cells appear.

## Step 4: Verify merged cells and number types

Open the workbook and confirm currencies are numeric, dates parse correctly, and header spans match the PDF.

Try the [homepage converter](/) on your hardest table first.
""",
    ),
    (
        "best-free-pdf-to-excel-converter",
        "Best Free PDF to Excel Converter",
        "Best Free PDF to Excel Converter in 2026 — Comparison",
        "Compare free PDF to Excel converters on table accuracy, OCR, privacy, and formatting preservation.",
        """Searching for the best free PDF to Excel converter? Evaluate tools on table fidelity, not just price.

## What to look for

- **Table reconstruction** — rows and columns aligned, not one giant column
- **OCR for scans** — image PDFs need optical character recognition
- **Number typing** — amounts should be numeric, not text
- **Privacy** — short file retention and encrypted upload

## Why pdfintoexcel

We focus exclusively on PDF into Excel conversion. That means a geometric pipeline tuned for bank statements, invoices, and research tables — not a generic PDF Swiss Army knife.

## Try it free

[Upload a PDF](/) and compare the output to iLovePDF or Adobe on the same file. No sign-up required to start.

See use cases: [bank statements](/bank-statement-pdf-to-excel) · [invoices](/invoice-pdf-to-excel) · [scanned PDFs](/scanned-pdf-to-excel).
""",
    ),
    (
        "image-pdf-to-excel-spreadsheet",
        "Convert Image PDF to Excel Spreadsheet",
        "Convert Image PDF to Excel Spreadsheet with OCR",
        "Turn image-only PDFs and photo scans into editable Excel spreadsheets using OCR table extraction.",
        """An image PDF is a picture of a page — common from phone scanners and fax archives. Here is how to convert image PDF to Excel spreadsheet format.

## Step 1: Confirm the PDF has no selectable text

Try selecting text in a viewer. If you cannot, enable **Scanned (OCR)** on [pdfintoexcel](/).

## Step 2: Prefer accurate mode

Dense grids and small fonts benefit from accurate table reconstruction after OCR.

## Step 3: Check column alignment in Excel

Zoom out in Excel to verify columns did not shift. Re-scan at higher resolution if OCR misread digits.

## Step 4: Use typed columns for formulas

Once amounts are numeric, build pivot tables and charts without FIND/REPLACE cleanup.

Related: [extract tables from scanned PDF](/blog/extract-tables-scanned-pdf).
""",
    ),
    (
        "pdf-research-data-to-excel",
        "PDF Research Data to Excel",
        "PDF Research Data to Excel — Scientific Tables Guide",
        "Convert scientific and survey tables from PDF into Excel for analysis and charting.",
        """Researchers lose days retyping supplementary tables. This guide covers PDF research data to Excel conversion for stats workflows.

## Step 1: Download the publisher PDF

Use the official supplementary PDF when available — it usually has cleaner vector text than prints.

## Step 2: Upload with Tables only

At [pdfintoexcel](/), extract just the data grids when prose sections are not needed.

## Step 3: Export multi-page tables

Long supplementary files may produce multiple sheets. Use split layout to keep distinct tables separate.

## Step 4: Import into R, SPSS, or Python

CSV export is available from Excel if your pipeline prefers plain text. Numeric cells import cleanly.

Landing page: [research data PDF to Excel](/research-data-pdf-to-excel).
""",
    ),
)

SEO_BLOG_POSTS: tuple[BlogSeed, ...] = tuple(
    BlogSeed(
        slug=slug,
        title=title,
        meta_title=meta_title,
        meta_description=meta_description,
        body=body.strip() + _BLOG_CTA,
        keywords="PDF into Excel, PDF to Excel, table extraction",
    )
    for slug, title, meta_title, meta_description, body in _BLOG_POSTS_RAW
)
