import Link from 'next/link';

import { AnalyticsClient } from '@/app/dashboard/analytics-client';
import { adminFetch } from '@/lib/admin-auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getInternalApiBase } from '@/lib/internal-api';

export const dynamic = 'force-dynamic';

type Overview = {
  total_jobs: number;
  by_status: Record<string, number>;
  downloads_total: number;
  completed_last_24h: number;
  completed_last_7d: number;
  successful_conversions: number;
  failed_conversions: number;
  ocr_usage: number;
  full_document_usage: number;
  daily_active_users: number;
  conversion_rate: number;
};

async function fetchOverview(): Promise<Overview | null> {
  const base = getInternalApiBase();
  const url = `${base}/analytics/overview`;
  try {
    const res = await adminFetch(url);
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as Overview;
  } catch {
    return null;
  }
}

async function fetchSeries(range: string): Promise<Array<{ date: string; uploads: number }>> {
  const res = await adminFetch(`${getInternalApiBase()}/analytics/timeseries?range=${range}`);
  if (!res.ok) return [];
  const data = (await res.json()) as { series: Array<{ date: string; uploads: number }> };
  return data.series;
}

async function fetchTopPages(): Promise<Array<{ path: string; visits: number; conversion_rate: number }>> {
  const res = await adminFetch(`${getInternalApiBase()}/analytics/top-pages`);
  if (!res.ok) return [];
  return (await res.json()) as Array<{ path: string; visits: number; conversion_rate: number }>;
}

export default async function DashboardPage() {
  const range = '30d';
  const summary = await fetchOverview();
  const series = await fetchSeries(range);
  const topPages = await fetchTopPages();

  return (
    <div className='bg-background min-h-screen px-4 py-10 sm:px-6'>
      <div className='mx-auto max-w-5xl'>
        <div className='mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div>
            <h1 className='text-foreground text-2xl font-bold tracking-tight'>
              Analytics
            </h1>
            <p className='text-muted-foreground mt-1 text-sm'>
              Job volumes, outcomes, and download counts (internal).
            </p>
            <p className='mt-2'>
              <Button variant='secondary' className='rounded-xl' asChild>
                <Link href='/dashboard/blog'>Manage blog</Link>
              </Button>
            </p>
          </div>
          <Button variant='outline' className='rounded-xl' asChild>
            <Link href='/'>Back to site</Link>
          </Button>
        </div>
        <div className='mb-6 flex flex-wrap items-center gap-2'>
          {['7d', '30d', '90d'].map((r) => (
            <Button key={r} variant={r === range ? 'default' : 'outline'} size='sm' className='rounded-lg'>
              {r}
            </Button>
          ))}
        </div>

        {!summary ? (
          <Card className='border-destructive/30'>
            <CardHeader>
              <CardTitle className='text-lg'>Unable to load metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-muted-foreground text-sm'>
                Check{' '}
                <code className='text-foreground bg-muted rounded px-1 py-0.5 text-xs'>
                  admin auth tokens
                </code>{' '}
                are missing or expired.
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <StatCard label='Total jobs' value={summary.total_jobs} />
              <StatCard label='Successful' value={summary.successful_conversions} accent='text-excel' />
              <StatCard label='Failed' value={summary.failed_conversions} accent='text-destructive' />
              <StatCard
                label='Downloads (all time)'
                value={summary.downloads_total}
              />
            </div>
            <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <StatCard label='OCR usage' value={summary.ocr_usage} />
              <StatCard label='Full-document mode' value={summary.full_document_usage} />
              <StatCard label='Daily active users' value={summary.daily_active_users} />
              <StatCard label='Conversion rate %' value={Math.round(summary.conversion_rate)} />
            </div>
            <div className='mb-8'>
              <AnalyticsClient series={series} topPages={topPages} />
            </div>
            <Card className='shadow-sm'>
              <CardHeader>
                <CardTitle className='text-base'>By status</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className='grid grid-cols-2 gap-3 text-sm sm:grid-cols-3 md:grid-cols-5'>
                  {Object.entries(summary.by_status).map(([k, v]) => (
                    <div key={k}>
                      <dt className='text-muted-foreground capitalize'>{k}</dt>
                      <dd className='text-foreground text-lg font-semibold'>
                        {v}
                      </dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: string;
}) {
  return (
    <Card className='shadow-sm'>
      <CardHeader className='pb-2'>
        <CardTitle className='text-muted-foreground text-sm font-medium'>
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className={`text-2xl font-bold tracking-tight ${accent ?? 'text-foreground'}`}>
          {value.toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}
