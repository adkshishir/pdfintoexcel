import { ExceflowSiteShell } from '@/components/exceflow/exceflow-site-shell';

export default function RootLoading() {
  return (
    <ExceflowSiteShell mainClassName='flex flex-col'>
      <div
        className='flex flex-1 flex-col items-center justify-center px-4 py-20'
        role='status'
        aria-label='Loading'>
        <div className='bg-muted h-4 w-48 animate-pulse rounded' />
        <div className='bg-muted mt-6 h-32 w-full max-w-md animate-pulse rounded-xl' />
        <div className='bg-muted mt-4 h-4 w-64 animate-pulse rounded' />
        <p className='text-muted-foreground mt-8 text-sm'>Loading…</p>
      </div>
    </ExceflowSiteShell>
  );
}
