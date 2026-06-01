export default function MarketingLoading() {
  return (
    <div className='bg-muted/30 min-h-[50vh] px-4 py-16 sm:px-6' role='status' aria-label='Loading'>
      <div className='mx-auto max-w-3xl space-y-4'>
        <div className='bg-muted h-8 w-2/3 max-w-sm animate-pulse rounded' />
        <div className='bg-muted h-4 w-full animate-pulse rounded' />
        <div className='bg-muted h-4 w-5/6 animate-pulse rounded' />
        <div className='bg-muted mt-8 h-40 w-full animate-pulse rounded-xl' />
      </div>
    </div>
  );
}
