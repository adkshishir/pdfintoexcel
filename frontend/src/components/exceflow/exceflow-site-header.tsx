import Image from 'next/image';
import Link from 'next/link';

import { ExceflowThemeToggle } from '@/components/exceflow/exceflow-theme-toggle';
import { SiteHeaderNav } from '@/components/exceflow/site-header-nav';

export function ExceflowSiteHeader() {
  return (
    <header className='border-border bg-exceflow-header fixed top-0 z-50 w-full border-b'>
      <div className='mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-3 px-4 sm:px-6'>
        <Link
          href='/'
          className='flex min-w-0 shrink-0 items-center'
          aria-label='pdfintoexcel home'>
          <Image
            src='/logo.png'
            alt='pdfintoexcel'
            width={200}
            height={48}
            className='h-8 w-auto max-w-[min(180px,40vw)] object-contain object-left'
            priority
          />
        </Link>

        <div className='flex shrink-0 items-center gap-1 sm:gap-2'>
          <SiteHeaderNav />
          <ExceflowThemeToggle />
        </div>
      </div>
    </header>
  );
}
