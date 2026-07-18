'use client';

import type { RefObject } from 'react';
import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

import type { ConverterJob, ConverterJobStatus } from '@/lib/converter-types';

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

function outputFilename(filename: string): string {
  const base = filename.includes('.')
    ? filename.slice(0, filename.lastIndexOf('.'))
    : filename;
  return `${base}.xlsx`;
}

function DownloadButton({
  downloadHref,
  downloadFilename,
  downloadRef,
}: {
  downloadHref: string;
  downloadFilename: string;
  downloadRef?: RefObject<HTMLAnchorElement | null>;
}) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    if (downloading) return;
    setDownloading(true);
    setError(null);
    try {
      const res = await fetch(downloadHref);
      if (!res.ok) {
        throw new Error(`Download failed (${res.status})`);
      }
      const blob = await res.blob();
      if (!blob.size) {
        throw new Error('Downloaded file is empty');
      }
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = downloadFilename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className='flex flex-col gap-2'>
      <Button
        type='button'
        className='w-full rounded-xl bg-excel text-excel-foreground hover:opacity-95 sm:w-auto'
        disabled={downloading}
        onClick={() => void handleDownload()}>
        {downloading ? (
          <>
            <Loader2 className='mr-2 size-4 animate-spin' />
            Preparing download…
          </>
        ) : (
          'Download .xlsx'
        )}
      </Button>
      <a ref={downloadRef} href={downloadHref} className='sr-only' tabIndex={-1}>
        Download
      </a>
      {error && <p className='text-destructive text-xs'>{error}</p>}
    </div>
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
            value={38}
            className='h-1.5 bg-muted [&>div>div]:animate-pulse'
          />
          <p className='text-muted-foreground text-xs'>Working on your file…</p>
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
        <DownloadButton
          downloadHref={downloadHref}
          downloadFilename={outputFilename(job.filename)}
          downloadRef={downloadRef}
        />
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
