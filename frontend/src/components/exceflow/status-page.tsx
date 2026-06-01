import Link from 'next/link';

import { Button } from '@/components/ui/button';

type StatusLink = { href: string; label: string };

type StatusPageProps = {
  code: string;
  title: string;
  description: string;
  primaryHref: string;
  primaryLabel: string;
  secondary?: StatusLink[];
  /** When set, renders a Try again button instead of only links. */
  onRetry?: () => void;
  retryLabel?: string;
  tone?: 'default' | 'error';
};

export function StatusPage({
  code,
  title,
  description,
  primaryHref,
  primaryLabel,
  secondary = [],
  onRetry,
  retryLabel = 'Try again',
  tone = 'default',
}: StatusPageProps) {
  return (
    <div className='flex flex-1 flex-col items-center justify-center px-4 py-20 text-center'>
      <p
        className={
          tone === 'error'
            ? 'text-destructive text-sm font-medium'
            : 'text-muted-foreground text-sm font-medium'
        }>
        {code}
      </p>
      <h1 className='text-foreground mt-2 text-3xl font-bold tracking-tight'>{title}</h1>
      <p className='text-muted-foreground mt-3 max-w-md text-sm leading-relaxed'>
        {description}
      </p>
      <div className='mt-8 flex flex-wrap items-center justify-center gap-3'>
        {onRetry ? (
          <Button type='button' onClick={onRetry} className='rounded-xl'>
            {retryLabel}
          </Button>
        ) : null}
        <Button asChild className='rounded-xl' variant={onRetry ? 'outline' : 'default'}>
          <Link href={primaryHref}>{primaryLabel}</Link>
        </Button>
        {secondary.map((link) => (
          <Button key={link.href} asChild variant='ghost' className='rounded-xl'>
            <Link href={link.href}>{link.label}</Link>
          </Button>
        ))}
      </div>
    </div>
  );
}
