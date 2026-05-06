'use client';

import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

type Mode = 'fast' | 'accurate';
type OutputLayout = 'merged' | 'split';
type ExtractionScope = 'tables_only' | 'full_document';
type FullDocumentPages = 'single_sheet' | 'per_page';
type Status = 'pending' | 'queued' | 'processing' | 'completed' | 'failed';

interface Job {
  id: string;
  status: Status;
  mode: Mode;
  output_layout: OutputLayout;
  extraction_scope: ExtractionScope;
  full_document_pages: FullDocumentPages;
  filename: string;
  size_bytes: number;
  page_count: number | null;
  pdf_type: string | null;
  error: string | null;
  metrics: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
}

const STATUS_LABEL: Record<Status, string> = {
  pending: 'Pending',
  queued: 'Queued',
  processing: 'Processing…',
  completed: 'Completed',
  failed: 'Failed',
};

export default function Page() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Mode>('fast');
  const [outputLayout, setOutputLayout] = useState<OutputLayout>('merged');
  const [extractionScope, setExtractionScope] = useState<ExtractionScope>('tables_only');
  const [fullDocumentPages, setFullDocumentPages] =
    useState<FullDocumentPages>('single_sheet');
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Poll status while the job is in flight.
  useEffect(() => {
    if (!job || job.status === 'completed' || job.status === 'failed') return;
    const handle = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${job.id}`);
        if (!res.ok) throw new Error(`status ${res.status}`);
        setJob(await res.json());
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    }, 1500);
    return () => clearInterval(handle);
  }, [job]);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    setJob(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('mode', mode);
      fd.append('output_layout', outputLayout);
      fd.append('extraction_scope', extractionScope);
      fd.append('full_document_pages', fullDocumentPages);
      const res = await fetch(`${API_BASE}/jobs`, { method: 'POST', body: fd });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`upload failed (${res.status}): ${txt}`);
      }
      setJob(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  }

  const downloadHref =
    job?.status === 'completed' ? `${API_BASE}/jobs/${job.id}/download` : null;
  const inFlight =
    !!job && (job.status === 'queued' || job.status === 'processing');

  return (
    <main className='flex flex-1 items-center justify-center p-6 bg-zinc-50 dark:bg-black'>
      <div className='w-full max-w-xl rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-8 shadow-sm'>
        <header className='mb-6'>
          <h1 className='text-2xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50'>
            PDF → Excel Converter
          </h1>
          <p className='mt-1 text-sm text-zinc-600 dark:text-zinc-400'>
            Drop a PDF (digital, scanned, or mixed). Tables come back as a
            structured workbook.
          </p>
        </header>

        <form onSubmit={onUpload} className='flex flex-col gap-5'>
          <FilePicker file={file} onChange={setFile} />
          <ScopeSelect
            scope={extractionScope}
            onChange={setExtractionScope}
            disabled={uploading || inFlight}
          />
          {extractionScope === 'full_document' && (
            <FullDocumentPagesSelect
              value={fullDocumentPages}
              onChange={setFullDocumentPages}
              disabled={uploading || inFlight}
            />
          )}
          <ModeSelect
            mode={mode}
            onChange={setMode}
            disabled={uploading || inFlight}
          />
          {extractionScope === 'tables_only' && (
            <LayoutSelect
              layout={outputLayout}
              onChange={setOutputLayout}
              disabled={uploading || inFlight}
            />
          )}
          <button
            type='submit'
            disabled={!file || uploading || inFlight}
            className='rounded-full bg-zinc-950 dark:bg-zinc-50 px-5 h-11 text-sm font-medium text-white dark:text-zinc-950 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity'>
            {uploading ? 'Uploading…' : inFlight ? 'Working…' : 'Convert'}
          </button>
        </form>

        {error && (
          <p className='mt-5 rounded-md bg-red-50 dark:bg-red-950/40 px-3 py-2 text-sm text-red-800 dark:text-red-200'>
            {error}
          </p>
        )}

        {job && <JobPanel job={job} downloadHref={downloadHref} />}
      </div>
    </main>
  );
}

function FilePicker({
  file,
  onChange,
}: {
  file: File | null;
  onChange: (f: File | null) => void;
}) {
  return (
    <label className='flex flex-col gap-2'>
      <span className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
        PDF file
      </span>
      <div className='flex items-center gap-3 rounded-lg border border-dashed border-zinc-300 dark:border-zinc-700 px-4 py-3'>
        <input
          type='file'
          accept='application/pdf,.pdf'
          onChange={(e) => onChange(e.target.files?.[0] ?? null)}
          className='block w-full text-sm text-zinc-700 dark:text-zinc-300 file:mr-3 file:rounded-md file:border-0 file:bg-zinc-100 dark:file:bg-zinc-800 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-zinc-700 dark:file:text-zinc-200 file:cursor-pointer'
        />
      </div>
      {file && (
        <span className='text-xs text-zinc-500 dark:text-zinc-500'>
          {file.name} · {(file.size / 1024).toFixed(0)} KB
        </span>
      )}
    </label>
  );
}

function ScopeSelect({
  scope,
  onChange,
  disabled,
}: {
  scope: ExtractionScope;
  onChange: (s: ExtractionScope) => void;
  disabled: boolean;
}) {
  const opts: { value: ExtractionScope; label: string; hint: string }[] = [
    { value: 'tables_only', label: 'Tables only', hint: 'structured table export' },
    { value: 'full_document', label: 'Full document', hint: 'text + tables in reading order' },
  ];
  return (
    <fieldset className='flex flex-col gap-2' disabled={disabled}>
      <legend className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
        Extraction scope
      </legend>
      <div className='flex gap-2'>
        {opts.map((o) => (
          <label
            key={o.value}
            className={`flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-sm transition-colors ${
              scope === o.value
                ? 'border-zinc-950 bg-zinc-100 dark:border-zinc-50 dark:bg-zinc-800 text-zinc-950 dark:text-zinc-50'
                : 'border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'
            }`}>
            <input
              type='radio'
              name='extraction_scope'
              value={o.value}
              checked={scope === o.value}
              onChange={() => onChange(o.value)}
              className='sr-only'
            />
            <span>{o.label}</span>
            <span className='ml-2 text-xs text-zinc-500 dark:text-zinc-500'>
              {o.hint}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function FullDocumentPagesSelect({
  value,
  onChange,
  disabled,
}: {
  value: FullDocumentPages;
  onChange: (v: FullDocumentPages) => void;
  disabled: boolean;
}) {
  const opts: { value: FullDocumentPages; label: string; hint: string }[] = [
    {
      value: 'single_sheet',
      label: 'One worksheet',
      hint: 'entire PDF on one sheet',
    },
    {
      value: 'per_page',
      label: 'Sheet per PDF page',
      hint: 'Page_1, Page_2, …',
    },
  ];
  return (
    <fieldset className='flex flex-col gap-2' disabled={disabled}>
      <legend className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
        Full document layout
      </legend>
      <div className='flex gap-2'>
        {opts.map((o) => (
          <label
            key={o.value}
            className={`flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-sm transition-colors ${
              value === o.value
                ? 'border-zinc-950 bg-zinc-100 dark:border-zinc-50 dark:bg-zinc-800 text-zinc-950 dark:text-zinc-50'
                : 'border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'
            }`}>
            <input
              type='radio'
              name='full_document_pages'
              value={o.value}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
              className='sr-only'
            />
            <span>{o.label}</span>
            <span className='ml-2 text-xs text-zinc-500 dark:text-zinc-500'>
              {o.hint}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function ModeSelect({
  mode,
  onChange,
  disabled,
}: {
  mode: Mode;
  onChange: (m: Mode) => void;
  disabled: boolean;
}) {
  return (
    <fieldset className='flex flex-col gap-2' disabled={disabled}>
      <legend className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
        Mode
      </legend>
      <div className='flex gap-2'>
        {(['fast', 'accurate'] as const).map((m) => (
          <label
            key={m}
            className={`flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-sm transition-colors ${
              mode === m
                ? 'border-zinc-950 bg-zinc-100 dark:border-zinc-50 dark:bg-zinc-800 text-zinc-950 dark:text-zinc-50'
                : 'border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'
            }`}>
            <input
              type='radio'
              name='mode'
              value={m}
              checked={mode === m}
              onChange={() => onChange(m)}
              className='sr-only'
            />
            <span className='capitalize'>{m}</span>
            <span className='ml-2 text-xs text-zinc-500 dark:text-zinc-500'>
              {m === 'fast' ? '200 DPI' : '300 DPI · merged rows'}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function LayoutSelect({
  layout,
  onChange,
  disabled,
}: {
  layout: OutputLayout;
  onChange: (l: OutputLayout) => void;
  disabled: boolean;
}) {
  const opts: { value: OutputLayout; label: string; hint: string }[] = [
    { value: 'merged', label: 'Single sheet', hint: 'all pages combined' },
    {
      value: 'split',
      label: 'Sheet per page',
      hint: 'preserves PDF page split',
    },
  ];
  return (
    <fieldset className='flex flex-col gap-2' disabled={disabled}>
      <legend className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
        Sheet layout
      </legend>
      <div className='flex gap-2'>
        {opts.map((o) => (
          <label
            key={o.value}
            className={`flex-1 cursor-pointer rounded-md border px-3 py-2 text-center text-sm transition-colors ${
              layout === o.value
                ? 'border-zinc-950 bg-zinc-100 dark:border-zinc-50 dark:bg-zinc-800 text-zinc-950 dark:text-zinc-50'
                : 'border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-900'
            }`}>
            <input
              type='radio'
              name='output_layout'
              value={o.value}
              checked={layout === o.value}
              onChange={() => onChange(o.value)}
              className='sr-only'
            />
            <span>{o.label}</span>
            <span className='ml-2 text-xs text-zinc-500 dark:text-zinc-500'>
              {o.hint}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function JobPanel({
  job,
  downloadHref,
}: {
  job: Job;
  downloadHref: string | null;
}) {
  const m = (job.metrics ?? {}) as Record<string, number | string>;
  const isFullDoc = job.extraction_scope === 'full_document';
  return (
    <section className='mt-6 flex flex-col gap-3 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4'>
      <div className='flex items-center justify-between'>
        <span className='text-sm font-medium text-zinc-700 dark:text-zinc-300'>
          Job
        </span>
        <StatusPill status={job.status} />
      </div>
      <dl className='grid grid-cols-2 gap-x-4 gap-y-1 text-sm'>
        <Row k='ID' v={job.id.slice(0, 8) + '…'} />
        <Row k='File' v={job.filename} />
        {job.page_count != null && <Row k='Pages' v={String(job.page_count)} />}
        {job.pdf_type && <Row k='Type' v={job.pdf_type} />}
        <Row
          k='Scope'
          v={isFullDoc ? 'Full document' : 'Tables only'}
        />
        {isFullDoc && (
          <Row
            k='Doc layout'
            v={
              job.full_document_pages === 'per_page'
                ? 'sheet per PDF page'
                : 'single worksheet'
            }
          />
        )}
        {!isFullDoc && (
          <Row
            k='Layout'
            v={job.output_layout === 'split' ? 'sheet per page' : 'single sheet'}
          />
        )}
        {!isFullDoc && typeof m.table_count === 'number' && (
          <Row k='Sheets' v={String(m.table_count)} />
        )}
        {isFullDoc && typeof m.layout_row_count === 'number' && (
          <Row k='Rows written' v={String(m.layout_row_count)} />
        )}
        {typeof m.elapsed_ms === 'number' && (
          <Row k='Time' v={`${(m.elapsed_ms / 1000).toFixed(1)}s`} />
        )}
        {typeof m.mean_confidence === 'number' && (
          <Row k='Confidence' v={`${(m.mean_confidence * 100).toFixed(0)}%`} />
        )}
      </dl>
      {job.error && (
        <p className='rounded-md bg-red-50 dark:bg-red-950/40 px-3 py-2 text-xs font-mono text-red-800 dark:text-red-200'>
          {job.error}
        </p>
      )}
      {downloadHref && (
        <a
          href={downloadHref}
          download
          className='self-start rounded-full bg-emerald-600 hover:bg-emerald-700 px-4 h-9 text-sm font-medium text-white inline-flex items-center'>
          Download .xlsx
        </a>
      )}
    </section>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <>
      <dt className='text-zinc-500 dark:text-zinc-500'>{k}</dt>
      <dd className='text-zinc-800 dark:text-zinc-200 truncate' title={v}>
        {v}
      </dd>
    </>
  );
}

function StatusPill({ status }: { status: Status }) {
  const colors: Record<Status, string> = {
    pending: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
    queued: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200',
    processing:
      'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
    completed:
      'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
    failed: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colors[status]}`}>
      {status === 'processing' && (
        <span className='h-1.5 w-1.5 rounded-full bg-current animate-pulse' />
      )}
      {STATUS_LABEL[status]}
    </span>
  );
}
