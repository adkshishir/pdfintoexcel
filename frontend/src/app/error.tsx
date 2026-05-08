'use client';

import { useEffect } from 'react';
import Link from 'next/link';

import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';
import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang='en' suppressHydrationWarning>
      <body className='flex min-h-screen flex-col bg-background text-foreground antialiased'>
        <div className='flex min-h-screen flex-col'>
          <ExceflowSiteHeader />
          <main className='flex flex-1 flex-col items-center justify-center px-4 pt-24 pb-20 text-center'>
            <p className='text-destructive text-sm font-medium'>Something went wrong</p>
            <h1 className='text-foreground mt-2 text-2xl font-bold tracking-tight'>
              We could not complete that action
            </h1>
            <p className='text-muted-foreground mt-3 max-w-md text-sm leading-relaxed'>
              Please try again. If the problem continues, contact support with the
              time of the error
              {error.digest ? ` (ref: ${error.digest})` : ''}.
            </p>
            <div className='mt-8 flex flex-wrap justify-center gap-3'>
              <Button type='button' onClick={() => reset()} className='rounded-xl'>
                Try again
              </Button>
              <Button asChild variant='outline' className='rounded-xl'>
                <Link href='/'>Home</Link>
              </Button>
              <Button asChild variant='ghost' className='rounded-xl'>
                <Link href='/contact'>Contact</Link>
              </Button>
            </div>
          </main>
          <ExceflowSiteFooter />
        </div>
      </body>
    </html>
  );
}
