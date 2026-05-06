'use client';

import { useEffect, useId, useRef, useState, startTransition } from 'react';
import {
  ArrowRight,
  BadgeCheck,
  FileText,
  Layers,
  Square,
  Table2,
  Zap,
} from 'lucide-react';

import { ExceflowJobPanel } from '@/components/exceflow/exceflow-job-views';
import { ExceflowFieldLegend } from '@/components/exceflow/exceflow-field-legend';
import { ExceflowRadioTile } from '@/components/exceflow/exceflow-radio-tile';
import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';
import { ExceflowUploadZone } from '@/components/exceflow/exceflow-upload-zone';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { RadioGroup } from '@/components/ui/radio-group';
import type {
  ConverterExtractionScope,
  ConverterFullDocumentPages,
  ConverterJob,
  ConverterMode,
  ConverterOutputLayout,
} from '@/lib/converter-types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

export default function Page() {
  const exceflowFormId = useId();
  const resultAnchorRef = useRef<HTMLDivElement>(null);
  const [conversionModalOpen, setConversionModalOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ConverterMode>('accurate');
  const [outputLayout, setOutputLayout] = useState<ConverterOutputLayout>('merged');
  const [extractionScope, setExtractionScope] =
    useState<ConverterExtractionScope>('tables_only');
  const [fullDocumentPages, setFullDocumentPages] =
    useState<ConverterFullDocumentPages>('single_sheet');
  const [job, setJob] = useState<ConverterJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

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

  useEffect(() => {
    if (job?.status !== 'completed') return;
    startTransition(() => {
      setConversionModalOpen(true);
    });
    requestAnimationFrame(() => {
      resultAnchorRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    });
  }, [job?.status, job?.id]);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    setJob(null);
    setConversionModalOpen(false);
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
  const formBusy = uploading || inFlight;

  const iconMuted = 'text-muted-foreground group-hover:text-primary mb-2 size-7';
  const iconPrimary = 'text-primary mb-2 size-7';

  return (
    <>
      <ExceflowSiteHeader />
      <main className='mx-auto w-full max-w-[1000px] flex-1 px-4 pb-16 pt-24 md:px-6 md:pt-28'>
        <section className='mb-12 text-center'>
          <h1 className='text-foreground mb-2 text-3xl font-bold tracking-tight md:text-4xl'>
            PDF to Excel Converter
          </h1>
          <p className='text-muted-foreground mx-auto max-w-xl text-base leading-relaxed'>
            Extract data with mechanical precision. Transform complex PDF tables
            into structured Excel spreadsheets instantly.
          </p>
        </section>

        <form id={exceflowFormId} onSubmit={onUpload}>
          <div className='grid grid-cols-1 gap-8 lg:grid-cols-12 lg:gap-8'>
            <div className='lg:col-span-7'>
              <ExceflowUploadZone
                file={file}
                onFileChange={setFile}
                disabled={formBusy}
              />
            </div>

            <div className='flex flex-col gap-8 lg:col-span-5'>
              <div className='space-y-4'>
                <ExceflowFieldLegend>Extraction Scope</ExceflowFieldLegend>
                <RadioGroup
                  className='grid grid-cols-2 gap-4'
                  value={extractionScope}
                  onValueChange={(v) =>
                    setExtractionScope(v as ConverterExtractionScope)
                  }
                  disabled={formBusy}>
                  <ExceflowRadioTile
                    value='tables_only'
                    currentValue={extractionScope}
                    id={`${exceflowFormId}-scope-tables`}
                    disabled={formBusy}
                    leadingIcon={
                      <Table2
                        className={
                          extractionScope === 'tables_only'
                            ? iconPrimary
                            : iconMuted
                        }
                        strokeWidth={1.5}
                      />
                    }>
                    <span className='text-base font-semibold'>Tables only</span>
                    <span className='text-muted-foreground text-xs leading-snug'>
                      Extract tabular data only
                    </span>
                  </ExceflowRadioTile>
                  <ExceflowRadioTile
                    value='full_document'
                    currentValue={extractionScope}
                    id={`${exceflowFormId}-scope-full`}
                    disabled={formBusy}
                    leadingIcon={
                      <FileText
                        className={
                          extractionScope === 'full_document'
                            ? iconPrimary
                            : iconMuted
                        }
                        strokeWidth={1.5}
                      />
                    }>
                    <span className='text-base font-semibold'>
                      Full document
                    </span>
                    <span className='text-muted-foreground text-xs leading-snug'>
                      Convert all text and content
                    </span>
                  </ExceflowRadioTile>
                </RadioGroup>
              </div>

              <div className='space-y-4'>
                <ExceflowFieldLegend>Mode</ExceflowFieldLegend>
                <RadioGroup
                  className='grid grid-cols-2 gap-4'
                  value={mode}
                  onValueChange={(v) => setMode(v as ConverterMode)}
                  disabled={formBusy}>
                  <ExceflowRadioTile
                    value='fast'
                    currentValue={mode}
                    id={`${exceflowFormId}-mode-fast`}
                    disabled={formBusy}
                    leadingIcon={
                      <Zap
                        className={
                          mode === 'fast' ? iconPrimary : iconMuted
                        }
                        strokeWidth={1.5}
                      />
                    }>
                    <span className='text-base font-semibold'>Fast (200 DPI)</span>
                    <span className='text-muted-foreground text-xs leading-snug'>
                      Optimized for speed
                    </span>
                  </ExceflowRadioTile>
                  <ExceflowRadioTile
                    value='accurate'
                    currentValue={mode}
                    id={`${exceflowFormId}-mode-accurate`}
                    disabled={formBusy}
                    leadingIcon={
                      <BadgeCheck
                        className={
                          mode === 'accurate' ? iconPrimary : iconMuted
                        }
                        strokeWidth={1.5}
                      />
                    }>
                    <span className='text-base font-semibold'>
                      Accurate (300 DPI)
                    </span>
                    <span className='text-muted-foreground text-xs leading-snug'>
                      Highest OCR precision
                    </span>
                  </ExceflowRadioTile>
                </RadioGroup>
              </div>

              {extractionScope === 'full_document' ? (
                <div className='space-y-4'>
                  <ExceflowFieldLegend>Full document layout</ExceflowFieldLegend>
                  <RadioGroup
                    className='grid grid-cols-2 gap-4'
                    value={fullDocumentPages}
                    onValueChange={(v) =>
                      setFullDocumentPages(v as ConverterFullDocumentPages)
                    }
                    disabled={formBusy}>
                    <ExceflowRadioTile
                      value='single_sheet'
                      currentValue={fullDocumentPages}
                      id={`${exceflowFormId}-doc-one-sheet`}
                      disabled={formBusy}
                      leadingIcon={
                        <Square
                          className={
                            fullDocumentPages === 'single_sheet'
                              ? iconPrimary
                              : iconMuted
                          }
                          strokeWidth={1.5}
                        />
                      }>
                      <span className='text-base font-semibold'>
                        One worksheet
                      </span>
                      <span className='text-muted-foreground text-xs leading-snug'>
                        Entire PDF on one sheet
                      </span>
                    </ExceflowRadioTile>
                    <ExceflowRadioTile
                      value='per_page'
                      currentValue={fullDocumentPages}
                      id={`${exceflowFormId}-doc-per-page`}
                      disabled={formBusy}
                      leadingIcon={
                        <Layers
                          className={
                            fullDocumentPages === 'per_page'
                              ? iconPrimary
                              : iconMuted
                          }
                          strokeWidth={1.5}
                        />
                      }>
                      <span className='text-base font-semibold'>
                        Sheet per page
                      </span>
                      <span className='text-muted-foreground text-xs leading-snug'>
                        Individual sheets per page
                      </span>
                    </ExceflowRadioTile>
                  </RadioGroup>
                </div>
              ) : (
                <div className='space-y-4'>
                  <ExceflowFieldLegend>Sheet Layout</ExceflowFieldLegend>
                  <RadioGroup
                    className='grid grid-cols-2 gap-4'
                    value={outputLayout}
                    onValueChange={(v) =>
                      setOutputLayout(v as ConverterOutputLayout)
                    }
                    disabled={formBusy}>
                    <ExceflowRadioTile
                      value='merged'
                      currentValue={outputLayout}
                      id={`${exceflowFormId}-layout-merged`}
                      disabled={formBusy}
                      leadingIcon={
                        <Square
                          className={
                            outputLayout === 'merged' ? iconPrimary : iconMuted
                          }
                          strokeWidth={1.5}
                        />
                      }>
                      <span className='text-base font-semibold'>
                        Single sheet
                      </span>
                      <span className='text-muted-foreground text-xs leading-snug'>
                        All pages in one sheet
                      </span>
                    </ExceflowRadioTile>
                    <ExceflowRadioTile
                      value='split'
                      currentValue={outputLayout}
                      id={`${exceflowFormId}-layout-split`}
                      disabled={formBusy}
                      leadingIcon={
                        <Layers
                          className={
                            outputLayout === 'split' ? iconPrimary : iconMuted
                          }
                          strokeWidth={1.5}
                        />
                      }>
                      <span className='text-base font-semibold'>
                        Sheet per page
                      </span>
                      <span className='text-muted-foreground text-xs leading-snug'>
                        Individual sheets per page
                      </span>
                    </ExceflowRadioTile>
                  </RadioGroup>
                </div>
              )}

              <div className='space-y-4'>
                <Button
                  type='submit'
                  variant='cta'
                  size='lg'
                  className='h-auto w-full rounded-xl py-4 text-lg font-semibold shadow-lg shadow-exceflow-cta/20'
                  disabled={!file || formBusy}>
                  {uploading
                    ? 'Uploading…'
                    : inFlight
                      ? 'Working…'
                      : 'Convert to Excel'}
                  <ArrowRight className='size-5' aria-hidden />
                </Button>
                <p className='text-muted-foreground text-center text-xs'>
                  Your files are encrypted and automatically deleted after
                  processing.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <p className='bg-destructive/15 text-destructive mt-8 rounded-md px-3 py-2 text-sm'>
              {error}
            </p>
          )}

          {job && (
            <div
              ref={resultAnchorRef}
              className='scroll-mt-28 mt-10'>
              <ExceflowJobPanel job={job} downloadHref={downloadHref} />
            </div>
          )}
        </form>
      </main>
      <Dialog
        open={conversionModalOpen && !!job && job.status === 'completed'}
        onOpenChange={setConversionModalOpen}>
        <DialogContent
          className='max-w-lg gap-0 p-0 sm:max-w-lg'
          onOpenAutoFocus={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Conversion complete</DialogTitle>
            <DialogDescription>
              {job?.filename ?? 'Your file'} is ready. Download your Excel
              workbook below.
            </DialogDescription>
          </DialogHeader>
          <div className='px-2 pb-4 sm:px-4'>
            {job?.status === 'completed' && (
              <ExceflowJobPanel
                job={job}
                downloadHref={downloadHref}
                className='mt-0 border-0 shadow-md'
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
      <ExceflowSiteFooter />
    </>
  );
}
