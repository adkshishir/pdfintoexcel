import { cn } from '@/lib/utils';

export function MarketingPageBody({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('bg-muted/30 min-h-[40vh]', className)}>
      <div className='mx-auto max-w-3xl px-4 py-12 sm:px-6 sm:py-14'>{children}</div>
    </div>
  );
}
