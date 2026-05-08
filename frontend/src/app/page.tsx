'use client';

import { useEffect, useRef, useState, startTransition } from 'react';
import {
  ArrowRight,
  FileSpreadsheet,
  HelpCircle,
  LayoutGrid,
  ScanLine,
  Shield,
  Table2,
} from 'lucide-react';

import { ExceflowJobPanel } from '@/components/exceflow/exceflow-job-views';
import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';
import { ExceflowUploadZone } from '@/components/exceflow/exceflow-upload-zone';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type {
  ConverterExtractionScope,
  ConverterFullDocumentPages,
  ConverterJob,
  ConverterMode,
  ConverterOutputLayout,
} from '@/lib/converter-types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

export default function Page() {
  const uploadRef = useRef<HTMLDivElement>(null);
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

  const displayName = job?.filename ?? file?.name ?? null;
  const displayPages =
    job?.page_count != null ? String(job.page_count) : file ? '—' : '—';

  function scrollToUpload() {
    uploadRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <>
      <ExceflowSiteHeader />
      <main className='flex-1'>
        <section className='mx-auto max-w-4xl px-4 pt-28 pb-16 text-center sm:px-6 sm:pt-32 md:pb-20'>
          <h1 className='text-foreground text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl md:leading-tight'>
            Convert PDF to Excel without losing structure
          </h1>
          <p className='text-muted-foreground mx-auto mt-5 max-w-2xl text-lg leading-relaxed'>
            Accurate table extraction with layout preservation.
          </p>
          <Button
            type='button'
            variant='outline'
            size='lg'
            className='mt-8 rounded-xl border-border shadow-sm'
            onClick={scrollToUpload}>
            Upload PDF
            <ArrowRight className='size-4' aria-hidden />
          </Button>
        </section>

        <div ref={uploadRef} className='scroll-mt-28' />

        <section className='mx-auto max-w-2xl px-4 pb-20 sm:px-6'>
          <form onSubmit={onUpload}>
            <Card className='overflow-hidden shadow-md'>
              <CardHeader className='space-y-1 pb-4'>
                <CardTitle className='text-xl'>Upload</CardTitle>
                <CardDescription>
                  Drop a PDF or choose a file. Select what to extract, then
                  convert.
                </CardDescription>
              </CardHeader>
              <CardContent className='space-y-8 pt-0'>
                <ExceflowUploadZone
                  file={file}
                  onFileChange={setFile}
                  disabled={formBusy}
                />

                <div className='space-y-3'>
                  <div className='flex items-center gap-2'>
                    <span className='text-foreground text-sm font-medium'>
                      What to convert
                    </span>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type='button'
                          className='text-muted-foreground hover:text-foreground inline-flex'
                          aria-label='Help: extraction scope'>
                          <HelpCircle className='size-4' />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>
                        Table only keeps spreadsheets; full document captures
                        all text and layout.
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <Tabs
                    value={extractionScope}
                    onValueChange={(v) =>
                      setExtractionScope(v as ConverterExtractionScope)
                    }>
                    <TabsList className='grid w-full grid-cols-2'>
                      <TabsTrigger
                        value='tables_only'
                        disabled={formBusy}
                        className='data-[state=active]:text-primary'>
                        Table only
                      </TabsTrigger>
                      <TabsTrigger
                        value='full_document'
                        disabled={formBusy}
                        className='data-[state=active]:text-primary'>
                        Full document
                      </TabsTrigger>
                    </TabsList>
                    <TabsContent value='tables_only' className='sr-only'>
                      Table only extraction
                    </TabsContent>
                    <TabsContent value='full_document' className='sr-only'>
                      Full document extraction
                    </TabsContent>
                  </Tabs>
                </div>

                <div className='flex flex-wrap items-center justify-between gap-3'>
                  <Sheet>
                    <SheetTrigger asChild>
                      <Button
                        type='button'
                        variant='ghost'
                        size='sm'
                        className='text-muted-foreground -ml-2'>
                        Advanced options
                      </Button>
                    </SheetTrigger>
                    <SheetContent
                      side='right'
                      className='w-full border-border sm:max-w-md'>
                      <SheetHeader>
                        <SheetTitle>Advanced options</SheetTitle>
                        <SheetDescription>
                          Quality and worksheet layout. Defaults work for most
                          files.
                        </SheetDescription>
                      </SheetHeader>
                      <Separator className='my-6' />
                      <div className='space-y-6'>
                        <div>
                          <p className='text-foreground mb-3 text-sm font-medium'>
                            Processing mode
                          </p>
                          <div className='grid grid-cols-2 gap-2'>
                            <Button
                              type='button'
                              variant={
                                mode === 'fast' ? 'default' : 'outline'
                              }
                              className='rounded-xl'
                              disabled={formBusy}
                              onClick={() => setMode('fast')}>
                              Fast
                            </Button>
                            <Button
                              type='button'
                              variant={
                                mode === 'accurate' ? 'default' : 'outline'
                              }
                              className='rounded-xl'
                              disabled={formBusy}
                              onClick={() => setMode('accurate')}>
                              Accurate
                            </Button>
                          </div>
                          <p className='text-muted-foreground mt-2 text-xs'>
                            Accurate uses higher DPI for scans and handwriting.
                          </p>
                        </div>
                        <Separator />
                        <div>
                          <p className='text-foreground mb-3 text-sm font-medium'>
                            {extractionScope === 'full_document'
                              ? 'Workbook layout'
                              : 'Sheet layout'}
                          </p>
                          <div className='grid grid-cols-2 gap-2'>
                            {extractionScope === 'full_document' ? (
                              <>
                                <Button
                                  type='button'
                                  variant={
                                    fullDocumentPages === 'single_sheet'
                                      ? 'default'
                                      : 'outline'
                                  }
                                  className='rounded-xl'
                                  disabled={formBusy}
                                  onClick={() =>
                                    setFullDocumentPages('single_sheet')
                                  }>
                                  One sheet
                                </Button>
                                <Button
                                  type='button'
                                  variant={
                                    fullDocumentPages === 'per_page'
                                      ? 'default'
                                      : 'outline'
                                  }
                                  className='rounded-xl'
                                  disabled={formBusy}
                                  onClick={() =>
                                    setFullDocumentPages('per_page')
                                  }>
                                  Sheet per page
                                </Button>
                              </>
                            ) : (
                              <>
                                <Button
                                  type='button'
                                  variant={
                                    outputLayout === 'merged'
                                      ? 'default'
                                      : 'outline'
                                  }
                                  className='rounded-xl'
                                  disabled={formBusy}
                                  onClick={() => setOutputLayout('merged')}>
                                  Single sheet
                                </Button>
                                <Button
                                  type='button'
                                  variant={
                                    outputLayout === 'split'
                                      ? 'default'
                                      : 'outline'
                                  }
                                  className='rounded-xl'
                                  disabled={formBusy}
                                  onClick={() => setOutputLayout('split')}>
                                  Per page
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </SheetContent>
                  </Sheet>
                  <Button
                    type='submit'
                    variant='cta'
                    size='lg'
                    className='rounded-xl px-8 font-semibold shadow-sm'
                    disabled={!file || formBusy}>
                    {uploading
                      ? 'Uploading…'
                      : inFlight
                        ? 'Converting…'
                        : 'Convert to Excel'}
                    <ArrowRight className='size-5' aria-hidden />
                  </Button>
                </div>

                <p className='text-muted-foreground text-center text-xs'>
                  Files are encrypted in transit and removed after processing.
                </p>
              </CardContent>
            </Card>

            {error && (
              <p
                role='alert'
                className='bg-destructive/10 text-destructive mt-6 rounded-2xl border border-destructive/20 px-4 py-3 text-sm'>
                {error}
              </p>
            )}
          </form>
        </section>

        <section className='border-border bg-muted/40 border-y py-20'>
          <div className='mx-auto grid max-w-6xl gap-8 px-4 sm:px-6 md:grid-cols-3'>
            <Card className='border-border/80 shadow-sm'>
              <CardHeader>
                <LayoutGrid
                  className='text-primary mb-2 size-9'
                  strokeWidth={1.25}
                  aria-hidden
                />
                <CardTitle className='text-lg'>Structure preserved</CardTitle>
                <CardDescription className='text-base leading-relaxed'>
                  Rows, columns, and merged cells reconstructed from your PDF.
                </CardDescription>
              </CardHeader>
            </Card>
            <Card className='border-border/80 shadow-sm'>
              <CardHeader>
                <ScanLine
                  className='text-primary mb-2 size-9'
                  strokeWidth={1.25}
                  aria-hidden
                />
                <CardTitle className='text-lg'>Scanned documents</CardTitle>
                <CardDescription className='text-base leading-relaxed'>
                  OCR pipeline tuned for tables in scans—not just digital text.
                </CardDescription>
              </CardHeader>
            </Card>
            <Card className='border-border/80 shadow-sm'>
              <CardHeader>
                <Shield
                  className='text-primary mb-2 size-9'
                  strokeWidth={1.25}
                  aria-hidden
                />
                <CardTitle className='text-lg'>Private by default</CardTitle>
                <CardDescription className='text-base leading-relaxed'>
                  No training on your data. Short retention window after
                  download.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        <section
          id='preview'
          ref={resultAnchorRef}
          className='mx-auto max-w-6xl scroll-mt-28 px-4 py-20 sm:px-6'>
          <h2 className='text-foreground mb-3 text-2xl font-semibold tracking-tight'>
            Preview
          </h2>
          <p className='text-muted-foreground mb-10 max-w-2xl text-sm leading-relaxed'>
            Visual comparison coming soon. Status and download appear below when
            your job finishes.
          </p>
          <div className='grid gap-8 lg:grid-cols-2 lg:gap-10'>
            <Card className='border-border/80 flex flex-col shadow-sm lg:sticky lg:top-24 lg:self-start'>
              <div className='border-border flex items-center justify-between border-b px-6 py-4'>
                <span className='text-foreground text-sm font-semibold'>
                  PDF source
                </span>
                <span className='text-muted-foreground text-xs'>
                  {displayName ? 'Selected' : 'Waiting'}
                </span>
              </div>
              <CardContent className='flex flex-1 flex-col items-center justify-center py-16'>
                <Table2
                  className='text-muted-foreground mb-4 size-14 opacity-50'
                  strokeWidth={1}
                  aria-hidden
                />
                <p className='text-foreground text-center font-medium'>
                  {displayName ?? 'No file yet'}
                </p>
                <p className='text-muted-foreground mt-1 text-sm'>
                  {displayName
                    ? `${displayPages} page${displayPages === '1' ? '' : 's'}`
                    : 'Upload a PDF to begin'}
                </p>
              </CardContent>
            </Card>

            <Card
              className={`border-border/80 flex flex-col shadow-sm lg:sticky lg:top-24 lg:self-start ${
                job?.status === 'completed'
                  ? 'border-excel/30 ring-1 ring-excel/20'
                  : ''
              }`}>
              <div
                className={`border-border flex items-center justify-between border-b px-6 py-4 ${
                  job?.status === 'completed' ? 'border-excel/20 bg-excel/5' : ''
                }`}>
                <span className='text-foreground flex items-center gap-2 text-sm font-semibold'>
                  <FileSpreadsheet
                    className={
                      job?.status === 'completed'
                        ? 'text-excel size-4'
                        : 'text-muted-foreground size-4'
                    }
                    strokeWidth={1.25}
                    aria-hidden
                  />
                  Excel output
                </span>
                {job?.status === 'completed' && (
                  <span className='text-excel-dark text-xs font-medium'>
                    Ready
                  </span>
                )}
              </div>
              <CardContent className='flex flex-1 flex-col justify-center py-10'>
                {!job && (
                  <p className='text-muted-foreground text-center text-sm'>
                    Your .xlsx preview will appear here after conversion.
                  </p>
                )}
                {job && (
                  <ExceflowJobPanel
                    embedded
                    job={job}
                    downloadHref={downloadHref}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <Dialog
        open={conversionModalOpen && !!job && job.status === 'completed'}
        onOpenChange={setConversionModalOpen}>
        <DialogContent
          className='max-w-lg gap-0 overflow-hidden p-0 sm:max-w-lg'
          onOpenAutoFocus={(e) => e.preventDefault()}>
          <DialogHeader className='border-border space-y-2 border-b bg-excel/10 p-6'>
            <DialogTitle className='text-excel-dark text-xl'>
              Conversion complete
            </DialogTitle>
            <DialogDescription className='text-foreground/80 text-base'>
              {job?.filename ?? 'Your file'} is ready. Download your Excel
              workbook below.
            </DialogDescription>
          </DialogHeader>
          <div className='p-6'>
            {job?.status === 'completed' && (
              <ExceflowJobPanel
                job={job}
                downloadHref={downloadHref}
                className='border-0 shadow-none ring-0'
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
      <ExceflowSiteFooter />
    </>
  );
}
