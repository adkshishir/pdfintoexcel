import Link from 'next/link';

import { ExceflowThemeToggle } from '@/components/exceflow/exceflow-theme-toggle';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const exceflowNavItems = [
  { label: 'Convert', href: '/', current: true },
  { label: 'Merge', href: '#', current: false },
  { label: 'Compress', href: '#', current: false },
  { label: 'Split', href: '#', current: false },
] as const;

export function ExceflowSiteHeader() {
  return (
    <header className='border-border bg-exceflow-header fixed top-0 z-50 w-full border-b backdrop-blur-xl'>
      <div className='mx-auto flex h-16 w-full max-w-[1280px] items-center justify-between px-4 md:px-6'>
        <Link
          href='/'
          className='text-foreground text-lg font-bold tracking-tight'>
          Exceflow PDF
        </Link>
        <nav className='hidden items-center gap-8 md:flex'>
          {exceflowNavItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                'text-sm transition-colors duration-200',
                item.current
                  ? 'text-primary border-primary border-b-2 pb-1 font-bold'
                  : 'text-muted-foreground hover:text-primary font-medium',
              )}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className='flex items-center gap-2 md:gap-3'>
          <ExceflowThemeToggle />
          <Button
            type='button'
            variant='ghost'
            size='sm'
            className='text-muted-foreground hover:text-primary hidden sm:inline-flex'>
            Log In
          </Button>
          <Button
            type='button'
            variant='cta'
            size='sm'
            className='font-bold sm:h-9 sm:rounded-lg sm:px-5 sm:text-sm'>
            Sign Up
          </Button>
        </div>
      </div>
    </header>
  );
}
