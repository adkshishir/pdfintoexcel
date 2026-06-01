import Image from 'next/image';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { FOOTER_COLUMNS, SITE_NAME } from '@/lib/site-config';

export function ExceflowSiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className='border-border bg-exceflow-footer mt-auto w-full border-t'>
      <div className='mx-auto max-w-6xl px-4 py-14 sm:px-6'>
        <div className='grid gap-10 sm:grid-cols-2 lg:grid-cols-4'>
          <div className='flex flex-col gap-4 sm:col-span-2 lg:col-span-1'>
            <Link href='/' className='inline-flex' aria-label={`${SITE_NAME} home`}>
              <Image
                src='/logo.png'
                alt={SITE_NAME}
                width={180}
                height={44}
                className='h-7 w-auto max-w-[160px] object-contain object-left opacity-90'
              />
            </Link>
            <p className='text-muted-foreground max-w-xs text-sm leading-relaxed'>
              Precision PDF-to-Excel conversion for teams. Tables, scans, and full
              documents — structure preserved.
            </p>
            <Button asChild size='sm' className='w-fit rounded-xl'>
              <Link href='/'>Convert a PDF</Link>
            </Button>
          </div>

          <div>
            <h2 className='text-foreground text-xs font-semibold tracking-wider uppercase'>
              Product
            </h2>
            <ul className='mt-4 space-y-2.5'>
              {FOOTER_COLUMNS.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className='text-muted-foreground hover:text-foreground text-sm transition-colors'>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className='text-foreground text-xs font-semibold tracking-wider uppercase'>
              Company
            </h2>
            <ul className='mt-4 space-y-2.5'>
              {FOOTER_COLUMNS.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className='text-muted-foreground hover:text-foreground text-sm transition-colors'>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className='text-foreground text-xs font-semibold tracking-wider uppercase'>
              Legal
            </h2>
            <ul className='mt-4 space-y-2.5'>
              {FOOTER_COLUMNS.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className='text-muted-foreground hover:text-foreground text-sm transition-colors'>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className='border-border text-muted-foreground mt-12 flex flex-col items-center justify-between gap-4 border-t pt-8 text-center text-xs sm:flex-row sm:text-left'>
          <p>
            © {year} {SITE_NAME}. All rights reserved.
          </p>
          <p className='max-w-md leading-relaxed'>
            Files are processed securely and deleted per our retention policy. See{' '}
            <Link href='/privacy' className='text-foreground hover:underline'>
              Privacy
            </Link>{' '}
            for details.
          </p>
        </div>
      </div>
    </footer>
  );
}
