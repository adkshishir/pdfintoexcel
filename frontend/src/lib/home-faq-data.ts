/** Shared FAQ copy for homepage UI and FAQPage JSON-LD (must match). */
export const HOME_FAQ_ITEMS = [
  {
    q: 'Is converting PDF into Excel free?',
    a: 'Yes. You can convert PDF into Excel free, with no account needed to start. Larger files, batch conversion and unlimited daily conversions are available on a paid plan.',
  },
  {
    q: 'How accurate is the table extraction?',
    a: 'Our engine targets up to 99.4% structural accuracy on standard tables. We reconstruct the real rows, columns and merged cells so the spreadsheet matches the original.',
  },
  {
    q: 'Can I convert a scanned PDF into Excel?',
    a: 'Yes. Built-in OCR reads scanned and image-based PDFs and converts the tables into editable Excel cells, with support for over 25 languages.',
  },
  {
    q: 'Will my numbers stay as numbers I can calculate?',
    a: 'Yes. Currencies, percentages, dates and decimals are exported as real numeric values, not text.',
  },
  {
    q: 'What file formats can I export to?',
    a: 'You can export to Excel (.xlsx) to preserve multiple sheets and formatting, or to .csv for a plain data file you can import anywhere.',
  },
  {
    q: 'Is it safe to upload financial documents?',
    a: 'Yes. Files are transferred over 256-bit TLS encryption, processed in isolation, and permanently deleted within one hour.',
  },
] as const;
