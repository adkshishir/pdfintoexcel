import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getAnalyticsKey, getInternalApiBase } from '@/lib/internal-api';

export const dynamic = 'force-dynamic';

type Summary = {
  total_jobs: number;
  by_status: Record<string, number>;
  downloads_total: number;
  completed_last_24h: number;
  completed_last_7d: number;
};

async function fetchSummary(): Promise<Summary | null> {
  const base = getInternalApiBase();
  const key = getAnalyticsKey();
  if (!key) {
    return null;
  }
  const url = `${base}/analytics/summary`;
  try {
    const res = await fetch(url, {
      headers: { 'X-Analytics-Key': key },
      cache: 'no-store',
    });
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as Summary;
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const summary = await fetchSummary();
  const completed = summary?.by_status?.completed ?? 0;
  const failed = summary?.by_status?.failed ?? 0;
  const finished = completed + failed;
  const successRate =
    finished > 0 ? Math.round((completed / finished) * 1000) / 10 : null;

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

        {!summary ? (
          <Card className='border-destructive/30'>
            <CardHeader>
              <CardTitle className='text-lg'>Unable to load metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-muted-foreground text-sm'>
                Check{' '}
                <code className='text-foreground bg-muted rounded px-1 py-0.5 text-xs'>
                  INTERNAL_API_URL
                </code>{' '}
                and{' '}
                <code className='text-foreground bg-muted rounded px-1 py-0.5 text-xs'>
                  ANALYTICS_API_KEY
                </code>{' '}
                on the Next.js server. They must match the FastAPI service.
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className='mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              <StatCard label='Total jobs' value={summary.total_jobs} />
              <StatCard label='Completed' value={completed} accent='text-excel' />
              <StatCard label='Failed' value={failed} accent='text-destructive' />
              <StatCard
                label='Downloads (all time)'
                value={summary.downloads_total}
              />
            </div>
            <div className='mb-6 grid gap-4 sm:grid-cols-2'>
              <StatCard
                label='Completed (last 24h)'
                value={summary.completed_last_24h}
              />
              <StatCard
                label='Completed (last 7d)'
                value={summary.completed_last_7d}
              />
            </div>
            {successRate != null && (
              <p className='text-muted-foreground mb-8 text-sm'>
                Success rate (completed / completed+failed):{' '}
                <span className='text-foreground font-semibold'>
                  {successRate}%
                </span>
              </p>
            )}
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
