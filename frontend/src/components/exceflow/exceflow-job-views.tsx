'use client';

import type { RefObject } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

import type { ConverterJob, ConverterJobStatus } from '@/lib/converter-types';

const STAGE_LABEL: Record<string, string> = {
  detect: 'Analysing PDF…',
  extract: 'Extracting text…',
  ocr: 'Running OCR…',
  reconstruct: 'Reconstructing tables…',
  clean: 'Cleaning data…',
  classify: 'Classifying content…',
  export: 'Generating Excel…',
  done: 'Done',
  preprocess: 'Pre-processing sheets…',
  convert: 'Converting to PDF…',
  finalize: 'Finalising…',
};

function stageLabel(stage: string | null): string {
  if (stage && STAGE_LABEL[stage]) return STAGE_LABEL[stage];
  if (stage === 'done') return 'Done';
  return stage ? `Working on ${stage}…` : 'Working on your file…';
}

const STATUS_LABEL: Record<ConverterJobStatus, string> = {
  pending: 'Pending',
  queued: 'Queued',
  processing: 'Processing…',
  completed: 'Completed',
  failed: 'Failed',
};

function statusBadgeVariant(
  status: ConverterJobStatus,
): 'processing' | 'success' | 'destructive' | 'secondary' {
  if (status === 'failed') return 'destructive';
  if (status === 'completed') return 'success';
  if (status === 'processing' || status === 'queued') return 'processing';
  return 'secondary';
}

function JobStatusBadge({ status }: { status: ConverterJobStatus }) {
  return (
    <Badge variant={statusBadgeVariant(status)} className='gap-1.5 font-medium'>
      {status === 'processing' && (
        <span className='bg-current size-1.5 rounded-full motion-safe:animate-exceflow-soft-pulse' />
      )}
      {STATUS_LABEL[status]}
    </Badge>
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

function JobPanelBody({
  job,
  downloadHref,
  downloadRef,
}: {
  job: ConverterJob;
  downloadHref: string | null;
  downloadRef?: RefObject<HTMLAnchorElement | null>;
}) {
  const m = (job.metrics ?? {}) as Record<string, number | string>;
  const isFullDoc = job.extraction_scope === 'full_document';
  const showProgress =
    job.status === 'processing' ||
    job.status === 'queued' ||
    job.status === 'pending';

  return (
    <>
      {showProgress && (
        <div className='space-y-2'>
          <Progress
            value={job.progress_pct ?? 10}
            className='h-1.5 bg-muted [&>div>div]:animate-pulse'
          />
          <p className='text-muted-foreground text-xs'>
            {stageLabel(job.stage)}
            {job.progress_pct != null && ` (${job.progress_pct}%)`}
          </p>
        </div>
      )}
      <dl className='grid grid-cols-2 gap-x-6 gap-y-3 text-sm'>
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
        <ExceflowDlRow
          k='Document'
          v={job.document_type === 'scanned' ? 'Scanned (OCR)' : 'Normal PDF'}
        />
        {job.image_export !== 'none' && (
          <ExceflowDlRow
            k='Images'
            v={
              job.image_export === 'only'
                ? 'Images only'
                : 'Separate Figures sheet'
            }
          />
        )}
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
        <p className='bg-destructive/10 text-destructive rounded-xl border border-destructive/20 px-3 py-2 text-xs font-mono'>
          {job.error}
        </p>
      )}
      {downloadHref && (
        <Button
          asChild
          className='w-full rounded-xl bg-excel text-excel-foreground hover:opacity-95 sm:w-auto'>
          <a ref={downloadRef} href={downloadHref} download>
            Download .xlsx
          </a>
        </Button>
      )}
    </>
  );
}

export function ExceflowJobPanel({
  job,
  downloadHref,
  className,
  embedded = false,
  downloadRef,
}: {
  job: ConverterJob;
  downloadHref: string | null;
  className?: string;
  embedded?: boolean;
  downloadRef?: RefObject<HTMLAnchorElement | null>;
}) {
  if (embedded) {
    return (
      <div className={cn('flex flex-col gap-6', className)}>
        <div className='flex flex-row flex-wrap items-center justify-between gap-3'>
          <p className='text-muted-foreground text-sm font-medium'>Status</p>
          <JobStatusBadge status={job.status} />
        </div>
        <JobPanelBody
          job={job}
          downloadHref={downloadHref}
          downloadRef={downloadRef}
        />
      </div>
    );
  }

  return (
    <Card className={cn('shadow-sm', className)}>
      <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-3'>
        <CardTitle className='text-muted-foreground text-sm font-medium'>
          Job details
        </CardTitle>
        <JobStatusBadge status={job.status} />
      </CardHeader>
      <CardContent className='flex flex-col gap-6 pt-0'>
        <JobPanelBody
          job={job}
          downloadHref={downloadHref}
          downloadRef={downloadRef}
        />
      </CardContent>
    </Card>
  );
}
