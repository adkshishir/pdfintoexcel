export default function RootLoading() {
  return (
    <div
      className='bg-background flex min-h-[50vh] flex-col items-center justify-center px-4'
      role='status'
      aria-label='Loading'>
      <div className='border-muted-foreground/20 border-primary/60 size-10 animate-spin rounded-full border-2 border-t-transparent' />
      <p className='text-muted-foreground mt-4 text-sm'>Loading…</p>
    </div>
  );
}
