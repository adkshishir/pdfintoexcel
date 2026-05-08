import type { Metadata } from 'next';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const metadata: Metadata = {
  title: 'Contact — pdfintoexcel',
  description: 'Reach pdfintoexcel for product questions, partnerships, and support.',
};

export default function ContactPage() {
  return (
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <h1 className='text-foreground text-3xl font-bold tracking-tight'>
        Contact
      </h1>
      <p className='text-muted-foreground mt-4 text-lg leading-relaxed'>
        We respond to business and technical inquiries as quickly as we can.
        For security-sensitive issues, please avoid sending confidential PDFs by
        email unless we have an NDA in place.
      </p>
      <Card className='mt-10 shadow-sm'>
        <CardHeader>
          <CardTitle className='text-lg'>Email</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <p className='text-muted-foreground text-sm'>
            General & support:{' '}
            <a
              href='mailto:hello@pdfintoexcel.com'
              className='text-primary font-medium underline underline-offset-4'>
              hello@pdfintoexcel.com
            </a>
          </p>
          <p className='text-muted-foreground text-xs leading-relaxed'>
            Replace the address above with your production inbox. This is a
            placeholder for local development and SEO structure.
          </p>
        </CardContent>
      </Card>
      <Card className='mt-6 shadow-sm'>
        <CardHeader>
          <CardTitle className='text-lg'>Office hours</CardTitle>
        </CardHeader>
        <CardContent>
          <p className='text-muted-foreground text-sm'>
            Monday–Friday, 9:00–18:00 UTC (response times vary on weekends).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
