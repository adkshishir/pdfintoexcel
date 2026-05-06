export type ConverterMode = 'fast' | 'accurate';
export type ConverterOutputLayout = 'merged' | 'split';
export type ConverterExtractionScope = 'tables_only' | 'full_document';
export type ConverterFullDocumentPages = 'single_sheet' | 'per_page';
export type ConverterJobStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed';

export interface ConverterJob {
  id: string;
  status: ConverterJobStatus;
  mode: ConverterMode;
  output_layout: ConverterOutputLayout;
  extraction_scope: ConverterExtractionScope;
  full_document_pages: ConverterFullDocumentPages;
  filename: string;
  size_bytes: number;
  page_count: number | null;
  pdf_type: string | null;
  error: string | null;
  metrics: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
}
