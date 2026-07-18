import Link from 'next/link';

import { Button } from '@/components/ui/button';

export function BlogPostCta() {
  return (
    <aside className='border-excel/30 bg-excel/5 mt-12 rounded-2xl border p-6 sm:p-8'>
      <h2 className='text-foreground text-xl font-semibold'>
        Convert your PDF into Excel now
      </h2>
      <p className='text-muted-foreground mt-2 text-sm leading-relaxed'>
        Upload a bank statement, invoice, or scanned table and download a clean
        .xlsx file in seconds. No sign-up required to start.
      </p>
      <Button asChild variant='excel' className='mt-4 rounded-lg font-semibold'>
        <Link href='/?utm_source=blog&utm_medium=article'>Try pdfintoexcel free</Link>
      </Button>
    </aside>
  );
}
