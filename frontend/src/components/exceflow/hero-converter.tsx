'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  Check,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Loader2,
  ScanLine,
  Table2,
} from 'lucide-react';

import { useConverterFlow } from '@/components/exceflow/converter-flow-context';
import { ExceflowJobPanel } from '@/components/exceflow/exceflow-job-views';
import { ExceflowUploadZone } from '@/components/exceflow/exceflow-upload-zone';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type {
  ConverterDocumentType,
  ConverterExtractionScope,
  ConverterFullDocumentPages,
  ConverterImageExport,
  ConverterJob,
  ConverterMode,
  ConverterOutputLayout,
} from '@/lib/converter-types';
import { useJobWebSocket } from '@/lib/use-job-websocket';
import { cn } from '@/lib/utils';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

type WizardPhase = 'upload' | 'configure' | 'processing' | 'result';

const HEADER_STATUS: Record<
  WizardPhase,
  { label: string; className: string }
> = {
  upload: {
    label: 'Ready',
    className: 'bg-secondary text-secondary-foreground',
  },
  configure: {
    label: 'Choose mode',
    className: 'bg-secondary text-secondary-foreground',
  },
  processing: {
    label: 'Converting…',
    className: 'bg-processing text-processing-foreground',
  },
  result: {
    label: 'Done',
    className: 'bg-excel/15 text-excel-dark',
  },
};

function CompactConfig({
  extractionScope,
  setExtractionScope,
  documentType,
  setDocumentType,
  imageExport,
  setImageExport,
  mode,
  setMode,
  outputLayout,
  setOutputLayout,
  fullDocumentPages,
  setFullDocumentPages,
  disabled,
}: {
  extractionScope: ConverterExtractionScope;
  setExtractionScope: (s: ConverterExtractionScope) => void;
  documentType: ConverterDocumentType;
  setDocumentType: (d: ConverterDocumentType) => void;
  imageExport: ConverterImageExport;
  setImageExport: (i: ConverterImageExport) => void;
  mode: ConverterMode;
  setMode: (m: ConverterMode) => void;
  outputLayout: ConverterOutputLayout;
  setOutputLayout: (l: ConverterOutputLayout) => void;
  fullDocumentPages: ConverterFullDocumentPages;
  setFullDocumentPages: (p: ConverterFullDocumentPages) => void;
  disabled?: boolean;
}) {
  const scopeButtons: {
    id: ConverterExtractionScope;
    label: string;
    icon: typeof Table2;
  }[] = [
    { id: 'tables_only', label: 'Tables only', icon: Table2 },
    { id: 'full_document', label: 'Full document', icon: FileSpreadsheet },
  ];

  const docTypeButtons: {
    id: ConverterDocumentType;
    label: string;
    icon: typeof FileText;
  }[] = [
    { id: 'normal', label: 'Normal PDF', icon: FileText },
    { id: 'scanned', label: 'Scanned (OCR)', icon: ScanLine },
  ];

  const imageButtons: {
    id: ConverterImageExport;
    label: string;
  }[] = [
    { id: 'none', label: 'No images' },
    { id: 'figures', label: 'Separate sheet' },
    { id: 'only', label: 'Images only' },
  ];

  const imagesOnly = imageExport === 'only';

  return (
    <div className='space-y-4'>
      <div>
        <Label className='text-muted-foreground text-xs font-medium uppercase tracking-wide'>
          What to extract
        </Label>
        <div className='mt-2 flex flex-wrap gap-2'>
          {scopeButtons.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type='button'
              disabled={disabled || imagesOnly}
              onClick={() => setExtractionScope(id)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                extractionScope === id
                  ? 'border-excel bg-excel text-white'
                  : 'border-border text-foreground hover:border-primary/40 bg-card',
                imagesOnly && 'opacity-50',
              )}>
              <Icon className='size-4' />
              {label}
            </button>
          ))}
        </div>
      </div>

      {extractionScope === 'tables_only' && !imagesOnly && (
        <Tabs
          value={outputLayout}
          onValueChange={(v) => setOutputLayout(v as ConverterOutputLayout)}>
          <TabsList className='grid h-9 w-full grid-cols-2'>
            <TabsTrigger value='merged' disabled={disabled} className='text-xs'>
              Single sheet
            </TabsTrigger>
            <TabsTrigger value='split' disabled={disabled} className='text-xs'>
              Per page
            </TabsTrigger>
          </TabsList>
        </Tabs>
      )}

      {extractionScope === 'full_document' && !imagesOnly && (
        <Tabs
          value={fullDocumentPages}
          onValueChange={(v) =>
            setFullDocumentPages(v as ConverterFullDocumentPages)
          }>
          <TabsList className='grid h-9 w-full grid-cols-2'>
            <TabsTrigger value='single_sheet' disabled={disabled} className='text-xs'>
              One worksheet
            </TabsTrigger>
            <TabsTrigger value='per_page' disabled={disabled} className='text-xs'>
              Sheet per page
            </TabsTrigger>
          </TabsList>
        </Tabs>
      )}

      <div>
        <Label className='text-muted-foreground text-xs font-medium uppercase tracking-wide'>
          Document type
        </Label>
        <div className='mt-2 flex flex-wrap gap-2'>
          {docTypeButtons.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type='button'
              disabled={disabled || imagesOnly}
              onClick={() => setDocumentType(id)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                documentType === id
                  ? 'border-excel bg-excel text-white'
                  : 'border-border text-foreground hover:border-primary/40 bg-card',
                imagesOnly && 'opacity-50',
              )}>
              <Icon className='size-4' />
              {label}
            </button>
          ))}
        </div>
      </div>

      {documentType === 'scanned' && !imagesOnly && (
        <Tabs value={mode} onValueChange={(v) => setMode(v as ConverterMode)}>
          <Label className='text-muted-foreground mb-2 block text-xs font-medium uppercase tracking-wide'>
            OCR quality
          </Label>
          <TabsList className='grid h-9 w-full grid-cols-2'>
            <TabsTrigger value='fast' disabled={disabled} className='text-xs'>
              Fast
            </TabsTrigger>
            <TabsTrigger value='accurate' disabled={disabled} className='text-xs'>
              Accurate
            </TabsTrigger>
          </TabsList>
        </Tabs>
      )}

      <div>
        <Label className='text-muted-foreground text-xs font-medium uppercase tracking-wide'>
          Images
        </Label>
        <div className='mt-2 flex flex-wrap gap-2'>
          {imageButtons.map(({ id, label }) => (
            <button
              key={id}
              type='button'
              disabled={disabled}
              onClick={() => setImageExport(id)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                imageExport === id
                  ? 'border-excel bg-excel text-white'
                  : 'border-border text-foreground hover:border-primary/40 bg-card',
              )}>
              {id !== 'none' && <ImageIcon className='size-4' aria-hidden />}
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function HeroConverter() {
  const { registerFileInput, registerRequestUploadStep, setHeroFocused } =
    useConverterFlow();
  const downloadRef = useRef<HTMLAnchorElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<WizardPhase>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [extractionScope, setExtractionScope] =
    useState<ConverterExtractionScope>('tables_only');
  const [documentType, setDocumentType] =
    useState<ConverterDocumentType>('normal');
  const [imageExport, setImageExport] = useState<ConverterImageExport>('none');
  const [mode, setMode] = useState<ConverterMode>('fast');
  const [outputLayout, setOutputLayout] =
    useState<ConverterOutputLayout>('merged');
  const [fullDocumentPages, setFullDocumentPages] =
    useState<ConverterFullDocumentPages>('single_sheet');
  const [job, setJob] = useState<ConverterJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const effectiveMode: ConverterMode =
    documentType === 'scanned' ? mode : 'fast';

  const downloadHref =
    job?.status === 'completed' ? `${API_BASE}/jobs/${job.id}/download` : null;

  const status = HEADER_STATUS[phase];
  const isSuccess = phase === 'result' && job?.status === 'completed';
  const isFailed =
    phase === 'result' && (error != null || job?.status === 'failed');

  const goUpload = useCallback(() => {
    setPhase('upload');
  }, []);

  useEffect(() => {
    setHeroFocused(phase !== 'upload');
  }, [phase, setHeroFocused]);

  useEffect(() => {
    registerFileInput(fileInputRef.current);
    return () => registerFileInput(null);
  }, [registerFileInput]);

  useEffect(() => {
    registerRequestUploadStep(goUpload);
    return () => registerRequestUploadStep(null);
  }, [registerRequestUploadStep, goUpload]);

  useJobWebSocket(job?.id, phase === 'processing', {
    onUpdate: (next) => setJob(next),
    onTerminal: (next) => {
      setJob(next);
      setPhase('result');
      if (next.status === 'failed') {
        setError(next.error ?? 'Conversion failed');
      }
    },
    onError: (message) => {
      setError(message);
      setPhase('result');
    },
  });

  useEffect(() => {
    if (isSuccess) {
      requestAnimationFrame(() => downloadRef.current?.focus());
    }
  }, [isSuccess, job?.id]);

  function resetConversion() {
    setFile(null);
    setJob(null);
    setError(null);
    setUploading(false);
    setPhase('upload');
    setExtractionScope('tables_only');
    setDocumentType('normal');
    setImageExport('none');
    setMode('fast');
  }

  function onFilePicked(next: File | null) {
    setFile(next);
    setError(null);
    if (next) setPhase('configure');
    else setPhase('upload');
  }

  async function startConversion() {
    if (!file) return;
    setUploading(true);
    setError(null);
    setJob(null);
    setPhase('processing');
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('mode', effectiveMode);
      fd.append('output_layout', outputLayout);
      fd.append('extraction_scope', extractionScope);
      fd.append('full_document_pages', fullDocumentPages);
      fd.append('document_type', documentType);
      fd.append('image_export', imageExport);
      const res = await fetch(`${API_BASE}/jobs`, { method: 'POST', body: fd });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Upload failed (${res.status}): ${txt}`);
      }
      const created = (await res.json()) as ConverterJob;
      setJob(created);
      if (created.status === 'completed') setPhase('result');
      else if (created.status === 'failed') {
        setPhase('result');
        setError(created.error ?? 'Conversion failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase('result');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div
      id='converter'
      className='relative scroll-mt-24'
      aria-live='polite'>
      <input
        ref={fileInputRef}
        type='file'
        accept='application/pdf,.pdf'
        className='hidden'
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (
            f &&
            (f.type === 'application/pdf' ||
              f.name.toLowerCase().endsWith('.pdf'))
          ) {
            onFilePicked(f);
          }
          e.target.value = '';
        }}
      />

      <div className='rounded-2xl border-border border bg-card p-3 shadow-lg'>
        <div className='border-border flex items-center justify-between border-b px-3 py-3 text-sm text-muted-foreground'>
          <span>PDF to Excel converter</span>
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold',
              status.className,
            )}>
            {(phase === 'processing' || uploading) && (
              <Loader2 className='size-3 animate-spin' />
            )}
            {isSuccess && <Check className='size-3' />}
            {status.label}
          </span>
        </div>

        {phase === 'upload' && (
          <>
            <div className='p-4'>
              <ExceflowUploadZone
                file={file}
                onFileChange={onFilePicked}
                disabled={uploading}
                maxLabel='or click to browse · up to 50 MB'
              />
            </div>
            <div className='border-border flex items-center justify-between border-t px-3 py-4'>
              <div className='flex items-center gap-2 text-sm'>
                <span className='border-primary/25 bg-primary/6 text-primary rounded-lg border px-2 py-1 text-xs'>
                  PDF
                </span>
                <ArrowRight className='text-border size-4' />
                <span className='border-excel/25 bg-excel/10 text-excel-dark rounded-lg border px-2 py-1 text-xs'>
                  XLSX
                </span>
              </div>
            </div>
          </>
        )}

        {phase === 'configure' && file && (
          <div className='space-y-4 p-4'>
            <p className='truncate text-sm font-semibold text-foreground'>
              {file.name}
              <button
                type='button'
                className='text-primary ml-2 text-xs font-medium hover:underline'
                onClick={() => fileInputRef.current?.click()}>
                Change
              </button>
            </p>
            <CompactConfig
              extractionScope={extractionScope}
              setExtractionScope={setExtractionScope}
              documentType={documentType}
              setDocumentType={setDocumentType}
              imageExport={imageExport}
              setImageExport={setImageExport}
              mode={mode}
              setMode={setMode}
              outputLayout={outputLayout}
              setOutputLayout={setOutputLayout}
              fullDocumentPages={fullDocumentPages}
              setFullDocumentPages={setFullDocumentPages}
            />
            <Button
              type='button'
              variant='excel'
              className='w-full rounded-lg font-semibold'
              onClick={() => void startConversion()}>
              Convert to Excel
            </Button>
          </div>
        )}

        {phase === 'processing' && (
          <div className='space-y-4 p-6'>
            <div className='flex items-center gap-3'>
              <Loader2 className='text-excel size-8 shrink-0 animate-spin' />
              <div className='min-w-0'>
                <p className='font-semibold text-foreground'>Converting…</p>
                <p className='text-muted-foreground truncate text-xs'>
                  {file?.name}
                </p>
              </div>
            </div>
            {job && (
              <ExceflowJobPanel embedded job={job} downloadHref={null} />
            )}
          </div>
        )}

        {isSuccess && job && (
          <div className='space-y-4 p-4'>
            <p className='text-excel-dark text-center text-sm font-semibold'>
              Your Excel is ready
            </p>
            <ExceflowJobPanel
              embedded
              job={job}
              downloadHref={downloadHref}
              downloadRef={downloadRef}
            />
            <Button
              type='button'
              variant='outline'
              className='w-full rounded-lg'
              onClick={resetConversion}>
              Convert another PDF
            </Button>
          </div>
        )}

        {isFailed && (
          <div className='space-y-4 p-4'>
            <p className='text-destructive text-center text-sm font-semibold'>
              {error ?? job?.error ?? 'Conversion failed'}
            </p>
            {job && <ExceflowJobPanel embedded job={job} downloadHref={null} />}
            <div className='flex gap-2'>
              <Button
                type='button'
                variant='excel'
                className='flex-1 rounded-lg'
                onClick={() => {
                  setError(null);
                  setJob(null);
                  setPhase('configure');
                }}>
                Try again
              </Button>
              <Button
                type='button'
                variant='outline'
                className='flex-1 rounded-lg'
                onClick={resetConversion}>
                New PDF
              </Button>
            </div>
          </div>
        )}
      </div>

      {phase === 'upload' && (
        <>
          <div className='border-border absolute -right-6 -top-6 hidden rounded-2xl border bg-card p-3 shadow-md md:block'>
            <div className='flex items-center gap-2'>
              <div className='bg-secondary text-excel flex size-8 items-center justify-center rounded-lg'>
                <FileSpreadsheet className='size-4' />
              </div>
              <div className='text-xs'>
                <div className='font-semibold'>Table accuracy</div>
                <div className='text-excel font-mono font-bold'>99.4%</div>
              </div>
            </div>
          </div>
          <div className='border-border absolute -bottom-6 -left-6 hidden rounded-2xl border bg-card p-3 shadow-md md:block'>
            <div className='flex items-center gap-2'>
              <div className='bg-primary/10 text-primary flex size-8 items-center justify-center rounded-lg'>
                ⚡
              </div>
              <div className='text-xs'>
                <div className='font-semibold'>Avg. convert time</div>
                <div className='text-primary font-mono font-bold'>~6 sec</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
