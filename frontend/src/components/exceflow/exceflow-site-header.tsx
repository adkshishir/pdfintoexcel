import Image from 'next/image';
import Link from 'next/link';

import { ExceflowThemeToggle } from '@/components/exceflow/exceflow-theme-toggle';
import { SiteHeaderNav } from '@/components/exceflow/site-header-nav';
import { Button } from '@/components/ui/button';

export function ExceflowSiteHeader() {
  return (
    <header className='border-border bg-exceflow-header fixed top-0 z-50 w-full border-b'>
      <div className='mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6'>
        <Link
          href='/'
          className='flex shrink-0 items-center'
          aria-label='pdfintoexcel home'>
          <Image
            src='/logo.png'
            alt='pdfintoexcel'
            width={200}
            height={48}
            className='h-8 w-auto max-w-[min(200px,45vw)] object-contain object-left'
            priority
          />
        </Link>
        <SiteHeaderNav />
        <div className='flex items-center gap-2'>
          <ExceflowThemeToggle />
          <Button
            type='button'
            variant='ghost'
            size='sm'
            className='text-muted-foreground hover:text-foreground hidden sm:inline-flex'>
            Log in
          </Button>
          <Button
            type='button'
            variant='cta'
            size='sm'
            className='rounded-xl font-semibold sm:h-9 sm:px-5 sm:text-sm'>
            Sign up
          </Button>
        </div>
      </div>
    </header>
  );
}
