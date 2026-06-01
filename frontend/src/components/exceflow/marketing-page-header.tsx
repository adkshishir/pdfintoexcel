import { cn } from '@/lib/utils';

type MarketingPageHeaderProps = {
  eyebrow?: string;
  title: string;
  lead: string;
  lastUpdated?: string;
  className?: string;
};

export function MarketingPageHeader({
  eyebrow,
  title,
  lead,
  lastUpdated,
  className,
}: MarketingPageHeaderProps) {
  return (
    <header className={cn('border-border border-b bg-card/50 px-4 py-12 sm:px-6 sm:py-14', className)}>
      <div className='mx-auto max-w-3xl'>
        {eyebrow && (
          <p className='text-primary text-sm font-semibold tracking-wide uppercase'>
            {eyebrow}
          </p>
        )}
        <h1 className='text-foreground mt-2 text-3xl font-bold tracking-tight sm:text-4xl'>
          {title}
        </h1>
        <p className='text-muted-foreground mt-4 max-w-2xl text-lg leading-relaxed'>
          {lead}
        </p>
        {lastUpdated && (
          <p className='text-muted-foreground mt-3 text-sm'>Last updated: {lastUpdated}</p>
        )}
      </div>
    </header>
  );
}
