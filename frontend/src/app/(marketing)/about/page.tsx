import type { Metadata } from 'next';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const metadata: Metadata = {
  title: 'About us — pdfintoexcel',
  description:
    'pdfintoexcel builds accurate PDF to Excel conversion with structure preservation and serious OCR.',
};

export default function AboutPage() {
  return (
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <h1 className='text-foreground text-3xl font-bold tracking-tight'>
        About pdfintoexcel
      </h1>
      <p className='text-muted-foreground mt-4 text-lg leading-relaxed'>
        We focus on one job: turning complex PDFs—especially tables and scanned
        documents—into Excel workbooks you can trust in production workflows.
      </p>
      <Card className='mt-10 shadow-sm'>
        <CardHeader>
          <CardTitle className='text-lg'>What we optimize for</CardTitle>
        </CardHeader>
        <CardContent className='text-muted-foreground space-y-4 text-sm leading-relaxed'>
          <p>
            <strong className='text-foreground'>Layout fidelity</strong> — rows,
            columns, and merged regions reconstructed geometrically, not guessed
            from pasted text.
          </p>
          <p>
            <strong className='text-foreground'>Scanned documents</strong> — OCR
            and table detection tuned for real-world noise, not just clean
            digital PDFs.
          </p>
          <p>
            <strong className='text-foreground'>Operational discipline</strong>{' '}
            — short retention, encrypted transit, and clear status for every
            conversion job.
          </p>
        </CardContent>
      </Card>
      <p className='text-muted-foreground mt-8 text-xs'>
        This page describes product intent. It is not legal or financial advice.
      </p>
    </div>
  );
}
