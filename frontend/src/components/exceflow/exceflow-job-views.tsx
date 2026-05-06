'use client';

import { FileSpreadsheet, Table2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

import type { ConverterJob, ConverterJobStatus } from '@/lib/converter-types';

const STATUS_LABEL: Record<ConverterJobStatus, string> = {
  pending: 'Pending',
  queued: 'Queued',
  processing: 'Processing…',
  completed: 'Completed',
  failed: 'Failed',
};

function ExceflowStatusPill({ status }: { status: ConverterJobStatus }) {
  const colors: Record<ConverterJobStatus, string> = {
    pending: 'bg-muted/80 text-muted-foreground',
    queued: 'bg-secondary/20 text-secondary',
    processing: 'bg-primary/15 text-primary',
    completed: 'bg-primary/12 text-primary',
    failed: 'bg-destructive/15 text-destructive',
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${colors[status]}`}>
      {status === 'processing' && (
        <span className='bg-current size-1.5 rounded-full motion-safe:animate-exceflow-soft-pulse' />
      )}
      {STATUS_LABEL[status]}
    </span>
  );
}

function ExceflowDlRow({ k, v }: { k: string; v: string }) {
  return (
    <>
      <dt className='text-muted-foreground'>{k}</dt>
      <dd className='truncate font-medium' title={v}>
        {v}
      </dd>
    </>
  );
}

export function ExceflowJobPanel({
  job,
  downloadHref,
  className,
}: {
  job: ConverterJob;
  downloadHref: string | null;
  className?: string;
}) {
  const m = (job.metrics ?? {}) as Record<string, number | string>;
  const isFullDoc = job.extraction_scope === 'full_document';

  return (
    <Card
      className={cn(
        'border-border bg-card/50 mt-2 shadow-sm shadow-black/20',
        className,
      )}>
      <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
        <CardTitle className='text-muted-foreground text-sm font-medium'>
          Conversion status
        </CardTitle>
        <ExceflowStatusPill status={job.status} />
      </CardHeader>
      <CardContent className='space-y-4'>
        <dl className='grid grid-cols-2 gap-x-4 gap-y-2 text-sm'>
          <ExceflowDlRow k='ID' v={job.id.slice(0, 8) + '…'} />
          <ExceflowDlRow k='File' v={job.filename} />
          {job.page_count != null && (
            <ExceflowDlRow k='Pages' v={String(job.page_count)} />
          )}
          {job.pdf_type && <ExceflowDlRow k='Type' v={job.pdf_type} />}
          <ExceflowDlRow
            k='Scope'
            v={isFullDoc ? 'Full document' : 'Tables only'}
          />
          {isFullDoc && (
            <ExceflowDlRow
              k='Doc layout'
              v={
                job.full_document_pages === 'per_page'
                  ? 'Sheet per PDF page'
                  : 'Single worksheet'
              }
            />
          )}
          {!isFullDoc && (
            <ExceflowDlRow
              k='Layout'
              v={
                job.output_layout === 'split' ? 'Sheet per page' : 'Single sheet'
              }
            />
          )}
          {!isFullDoc && typeof m.table_count === 'number' && (
            <ExceflowDlRow k='Sheets' v={String(m.table_count)} />
          )}
          {isFullDoc && typeof m.layout_row_count === 'number' && (
            <ExceflowDlRow k='Rows written' v={String(m.layout_row_count)} />
          )}
          {typeof m.elapsed_ms === 'number' && (
            <ExceflowDlRow k='Time' v={`${(m.elapsed_ms / 1000).toFixed(1)}s`} />
          )}
          {typeof m.mean_confidence === 'number' && (
            <ExceflowDlRow
              k='Confidence'
              v={`${(m.mean_confidence * 100).toFixed(0)}%`}
            />
          )}
        </dl>

        {job.error && (
          <p className='bg-destructive/15 text-destructive rounded-md px-3 py-2 text-xs font-mono'>
            {job.error}
          </p>
        )}

        {downloadHref && (
          <Button variant='default' asChild className='w-full sm:w-auto'>
            <a href={downloadHref} download>
              Download .xlsx
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function ExceflowConvertActionBar({
  readyTitle,
  readySubtitle,
  submitLabel,
  disabled,
}: {
  readyTitle: string;
  readySubtitle: string;
  submitLabel: string;
  disabled: boolean;
}) {
  return (
    <div className='border-border flex flex-col items-stretch justify-between gap-6 border-t border-dashed pt-8 md:flex-row md:items-center'>
      <div className='text-muted-foreground flex items-center gap-4'>
        <div
          className='border-border from-card to-muted/40 flex size-[4.5rem] items-center justify-center rounded-xl border bg-gradient-to-br shadow-sm shadow-black/15'
          aria-hidden>
          <FileSpreadsheet className='text-primary size-9' strokeWidth={1.25} />
        </div>
        <div className='min-w-0'>
          <p className='text-foreground font-medium tracking-tight'>
            {readyTitle}
          </p>
          <p className='text-sm leading-relaxed'>{readySubtitle}</p>
        </div>
      </div>
      <Separator className='md:hidden' />
      <Button
        type='submit'
        size='lg'
        className='w-full shrink-0 font-semibold md:w-auto'
        disabled={disabled}>
        <Table2 className='size-5' aria-hidden strokeWidth={1.75} />
        {submitLabel}
      </Button>
    </div>
  );
}
