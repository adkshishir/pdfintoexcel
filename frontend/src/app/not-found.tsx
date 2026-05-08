import Link from 'next/link';

import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className='flex min-h-screen flex-col'>
      <ExceflowSiteHeader />
      <main className='flex flex-1 flex-col items-center justify-center px-4 pt-24 pb-20 text-center'>
        <p className='text-muted-foreground text-sm font-medium'>404</p>
        <h1 className='text-foreground mt-2 text-3xl font-bold tracking-tight'>
          Page not found
        </h1>
        <p className='text-muted-foreground mt-3 max-w-md text-sm leading-relaxed'>
          That URL does not exist or may have moved. Try the converter home,
          blog, or contact page.
        </p>
        <div className='mt-8 flex flex-wrap items-center justify-center gap-3'>
          <Button asChild className='rounded-xl'>
            <Link href='/'>Go home</Link>
          </Button>
          <Button asChild variant='outline' className='rounded-xl'>
            <Link href='/blog'>Blog</Link>
          </Button>
          <Button asChild variant='ghost' className='rounded-xl'>
            <Link href='/contact'>Contact</Link>
          </Button>
        </div>
      </main>
      <ExceflowSiteFooter />
    </div>
  );
}
