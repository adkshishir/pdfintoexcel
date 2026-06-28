/** Blog content strategy — mirrors backend/app/services/blog_content_strategy.py */

export type BlogCategorySlug = 'tutorial' | 'guide' | 'workflow' | 'features';

export type BlogTopicStrategy = {
  topic: string;
  primaryKeyword: string;
  categorySlug: BlogCategorySlug;
  comparisonTargets: string[];
  isComparison: boolean;
  week?: number;
};

export const BLOG_CATEGORY_SLUGS: BlogCategorySlug[] = [
  'tutorial',
  'guide',
  'workflow',
  'features',
];

export const BLOG_CATEGORY_LABELS: Record<BlogCategorySlug, string> = {
  tutorial: 'Tutorial',
  guide: 'Guide',
  workflow: 'Workflow',
  features: 'Features',
};

export const COMPARISON_POST_RATIO = 0.45;

export const COMPETITOR_PLATFORMS = [
  'Adobe Acrobat',
  'Smallpdf',
  'iLovePDF',
  'PDFTables',
  'Tabula',
  'Cometdocs',
  'Nitro PDF',
  'Soda PDF',
  'Zamzar',
  'CleverPDF',
] as const;

const COMPARISON_RE = /\bvs\.?\b|versus|compared to|comparison|alternative/i;

export function inferIsComparison(topic: string): boolean {
  return COMPARISON_RE.test(topic);
}

export function inferCategorySlug(topic: string): BlogCategorySlug {
  const t = topic.toLowerCase();
  if (/step-by-step|how to|tutorial|walkthrough|beginner/.test(t)) return 'tutorial';
  if (/finance|accounting|ap |payroll|industry|workflow|team/.test(t)) return 'workflow';
  if (/ocr|batch|api|detection|feature|accuracy|automation/.test(t)) return 'features';
  return 'guide';
}

export function slugFromTopic(topic: string): string {
  return topic
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 160);
}

function topic(
  t: string,
  primaryKeyword: string,
  categorySlug: BlogCategorySlug,
  opts?: { isComparison?: boolean; comparisonTargets?: string[]; week?: number },
): BlogTopicStrategy {
  return {
    topic: t,
    primaryKeyword,
    categorySlug,
    comparisonTargets: opts?.comparisonTargets ?? [],
    isComparison: opts?.isComparison ?? inferIsComparison(t),
    week: opts?.week,
  };
}

export const CONTENT_CALENDAR: BlogTopicStrategy[] = [
  topic('How to Convert a PDF Bank Statement to Excel (Step-by-Step)', 'bank statement pdf to excel', 'tutorial', { isComparison: false, week: 1 }),
  topic('PDFIntoExcel vs Smallpdf: Best Tool for PDF to Excel Conversion', 'smallpdf to excel alternative', 'guide', { isComparison: true, comparisonTargets: ['Smallpdf'], week: 2 }),
  topic('Scanned PDF to Excel: Complete OCR Guide', 'scanned pdf to excel', 'features', { isComparison: false, week: 3 }),
  topic('Best PDF to Excel Converters Compared (2026)', 'best pdf to excel converter', 'guide', { isComparison: true, comparisonTargets: ['Adobe Acrobat', 'Smallpdf', 'iLovePDF', 'PDFTables'], week: 4 }),
  topic('Invoice PDF to Excel Workflow for Accounts Payable Teams', 'invoice pdf to excel', 'workflow', { isComparison: false, week: 5 }),
  topic('PDFIntoExcel vs Adobe Acrobat for Table Extraction', 'adobe pdf to excel alternative', 'features', { isComparison: true, comparisonTargets: ['Adobe Acrobat'], week: 6 }),
  topic('Why PDF Tables Break in Excel — and How to Fix Them', 'pdf to excel keep formatting', 'guide', { isComparison: false, week: 7 }),
  topic('Batch PDF to Excel: Process Hundreds of Files Efficiently', 'batch pdf to excel', 'features', { isComparison: false, week: 8 }),
];

export const CALENDAR_BACKLOG: BlogTopicStrategy[] = [
  topic('PDFIntoExcel vs iLovePDF for Batch Conversion', 'ilovepdf to excel alternative', 'features', { isComparison: true, comparisonTargets: ['iLovePDF'], week: 9 }),
  topic('Extract Table from PDF to Excel Without Losing Columns', 'extract table from pdf to excel', 'tutorial', { isComparison: false, week: 10 }),
  topic('Month-End Close: PDF Statements to Excel Pivot Tables', 'financial pdf to excel', 'workflow', { isComparison: false, week: 11 }),
  topic('Free PDF to Excel Converter: Limits and What to Expect', 'free pdf to excel converter', 'guide', { isComparison: false, week: 12 }),
  topic('PDF to Excel API for Developers', 'batch pdf to excel', 'features', { isComparison: false, week: 13 }),
  topic('Credit Card Statement PDF to Excel (Step-by-Step)', 'bank statement pdf to excel', 'tutorial', { isComparison: false, week: 14 }),
  topic('PDFTables vs PDFIntoExcel for Financial Documents', 'best pdf to excel converter', 'guide', { isComparison: true, comparisonTargets: ['PDFTables'], week: 15 }),
  topic('Healthcare Billing PDF to Excel Workflow', 'invoice pdf to excel', 'workflow', { isComparison: false, week: 16 }),
];

export const TOPIC_BACKLOG: BlogTopicStrategy[] = [
  topic('How to convert a PDF bank statement to Excel in 5 minutes', 'bank statement pdf to excel', 'tutorial'),
  topic('Convert credit card statement PDF to Excel step-by-step', 'bank statement pdf to excel', 'tutorial'),
  topic('Extract a table from a PDF report into Excel', 'extract table from pdf to excel', 'tutorial'),
  topic('Convert a multi-page PDF to one Excel workbook', 'pdf to xlsx', 'tutorial'),
  topic('PDF pay stub to Excel for tax preparation', 'financial pdf to excel', 'tutorial'),
  topic('Convert PDF invoice to Excel for QuickBooks import', 'invoice pdf to excel', 'tutorial'),
  topic('How to convert a password-protected PDF to Excel', 'how to convert pdf to excel', 'tutorial'),
  topic('PDF to Excel on Mac without installing software', 'pdf to excel online', 'tutorial'),
  topic('Convert PDF to Excel with merged cells fixed manually', 'pdf to excel keep formatting', 'tutorial'),
  topic('Extract transaction list from PDF to Excel CSV format', 'extract data from pdf to excel', 'tutorial'),
  topic('PDF to Excel conversion methods compared (online, desktop, manual)', 'how to convert pdf to excel', 'guide'),
  topic('How to fix column misalignment after PDF to Excel conversion', 'pdf to excel keep formatting', 'guide'),
  topic('When OCR fails: troubleshooting scanned PDF to Excel', 'ocr pdf to excel', 'guide'),
  topic('PDF to Excel for accountants: compliance and audit trail', 'financial pdf to excel', 'guide'),
  topic('Free vs paid PDF to Excel converters: what you actually get', 'free pdf to excel converter', 'guide'),
  topic('How to validate Excel output after PDF conversion', 'extract data from pdf to excel', 'guide'),
  topic('PDF table extraction glossary for non-technical users', 'pdf table to excel', 'guide'),
  topic('Choosing between PDF to Excel and PDF to CSV', 'convert pdf to excel', 'guide'),
  topic('Accounts payable: invoice PDF to Excel reconciliation workflow', 'invoice pdf to excel', 'workflow'),
  topic('Bookkeeping: monthly bank statement PDF batch to Excel', 'bank statement pdf to excel', 'workflow'),
  topic('Auditors: extracting financial tables from PDF annual reports', 'financial pdf to excel', 'workflow'),
  topic('HR: timesheet and pay stub PDF processing at scale', 'batch pdf to excel', 'workflow'),
  topic('Real estate: rent roll PDF to Excel for analysis', 'extract table from pdf to excel', 'workflow'),
  topic('Legal: discovery document table extraction to Excel', 'extract data from pdf to excel', 'workflow'),
  topic('Research analysts: pulling data tables from whitepaper PDFs', 'pdf table to excel', 'workflow'),
  topic('E-commerce: supplier invoice PDF to inventory spreadsheet', 'invoice pdf to excel', 'workflow'),
  topic('How PDFIntoExcel table detection works', 'pdf table to excel', 'features'),
  topic('OCR settings that improve scanned PDF to Excel accuracy', 'ocr pdf to excel', 'features'),
  topic('Batch PDF to Excel: limits, speed, and naming conventions', 'batch pdf to excel', 'features'),
  topic('PDF to Excel API: integrate conversion into your app', 'batch pdf to excel', 'features'),
  topic('Security and file deletion policy for online PDF conversion', 'pdf to excel online', 'features'),
  topic('Handling rotated pages and skewed scans in OCR pipeline', 'scanned pdf to excel', 'features'),
  topic('PDFIntoExcel vs Adobe Acrobat for bank statements', 'adobe pdf to excel alternative', 'guide', { isComparison: true, comparisonTargets: ['Adobe Acrobat'] }),
  topic('PDFIntoExcel vs Smallpdf: speed and accuracy test', 'smallpdf to excel alternative', 'guide', { isComparison: true, comparisonTargets: ['Smallpdf'] }),
  topic('PDFIntoExcel vs iLovePDF for free PDF to Excel', 'best pdf to excel converter', 'guide', { isComparison: true, comparisonTargets: ['iLovePDF'] }),
  topic('PDFIntoExcel vs PDFTables for financial PDFs', 'best pdf to excel converter', 'guide', { isComparison: true, comparisonTargets: ['PDFTables'] }),
  topic('PDFIntoExcel vs Tabula for open-source table extraction', 'best pdf to excel converter', 'features', { isComparison: true, comparisonTargets: ['Tabula'] }),
  topic('Best Adobe Acrobat alternative for PDF to Excel', 'adobe pdf to excel alternative', 'guide', { isComparison: true, comparisonTargets: ['Adobe Acrobat'] }),
  topic('Smallpdf alternative for batch PDF to Excel', 'smallpdf to excel alternative', 'features', { isComparison: true, comparisonTargets: ['Smallpdf'] }),
  topic('iLovePDF vs PDFIntoExcel: which handles scanned PDFs better?', 'scanned pdf to excel', 'features', { isComparison: true, comparisonTargets: ['iLovePDF'] }),
];

export const ALL_TOPICS: BlogTopicStrategy[] = [
  ...CONTENT_CALENDAR,
  ...CALENDAR_BACKLOG,
  ...TOPIC_BACKLOG,
];
