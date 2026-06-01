import type { Metadata } from 'next';
import Link from 'next/link';

import { MarketingPageBody } from '@/components/exceflow/marketing-page-body';
import { MarketingPageHeader } from '@/components/exceflow/marketing-page-header';
import { AboutPageJsonLd } from '@/components/seo/about-page-json-ld';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { staticPageMetadata } from '@/lib/seo';

export const metadata: Metadata = staticPageMetadata({
  path: '/about',
  title: 'About us — pdfintoexcel',
  description:
    'pdfintoexcel builds accurate PDF to Excel conversion with structure preservation and serious OCR for production workflows.',
});

const pillars = [
  {
    title: 'Layout fidelity',
    body: 'Rows, columns, and merged regions reconstructed geometrically — not guessed from pasted text.',
  },
  {
    title: 'Scanned documents',
    body: 'OCR and table detection tuned for real-world noise, handwriting, and multilingual pages.',
  },
  {
    title: 'Operational discipline',
    body: 'Short retention, encrypted transit, and clear job status from upload through download.',
  },
] as const;

export default function AboutPage() {
  return (
    <>
      <AboutPageJsonLd />
      <MarketingPageHeader
        eyebrow='Company'
        title='About pdfintoexcel'
        lead='We focus on one job: turning complex PDFs — especially tables and scanned documents — into Excel workbooks you can trust in production workflows.'
      />
      <MarketingPageBody>
        <div className='space-y-10'>
          <section>
            <h2 className='text-foreground text-xl font-semibold'>Our mission</h2>
            <p className='text-muted-foreground mt-3 text-sm leading-relaxed'>
              Most converters treat a PDF like a bag of words. We treat it like a
              layout: cells have coordinates, headers span columns, and numbers must
              land in the right place. That is how finance, operations, and research
              teams actually work in Excel.
            </p>
          </section>

          <div className='grid gap-6 sm:grid-cols-1'>
            {pillars.map((item) => (
              <Card key={item.title} className='shadow-sm'>
                <CardHeader>
                  <CardTitle className='text-lg'>{item.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className='text-muted-foreground text-sm leading-relaxed'>
                    {item.body}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          <section className='border-border rounded-xl border bg-card p-6'>
            <h2 className='text-foreground text-lg font-semibold'>Built for teams</h2>
            <p className='text-muted-foreground mt-3 text-sm leading-relaxed'>
              Whether you are reconciling statements, digitizing invoices, or
              extracting research tables, pdfintoexcel is designed to reduce manual
              cleanup — not add another format problem.
            </p>
            <p className='mt-4'>
              <Link
                href='/contact'
                className='text-primary text-sm font-medium underline underline-offset-4'>
                Get in touch →
              </Link>
            </p>
          </section>

          <p className='text-muted-foreground text-xs'>
            This page describes product intent. It is not legal or financial advice.
          </p>
        </div>
      </MarketingPageBody>
    </>
  );
}
