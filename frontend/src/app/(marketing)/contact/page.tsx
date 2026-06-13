import type { Metadata } from 'next';
import Link from 'next/link';

import { MarketingPageBody } from '@/components/exceflow/marketing-page-body';
import { MarketingPageHeader } from '@/components/exceflow/marketing-page-header';
import { BreadcrumbJsonLd } from '@/components/seo/breadcrumb-json-ld';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  LEGAL_EMAIL,
  PARTNERSHIPS_EMAIL,
  SECURITY_EMAIL,
  SUPPORT_EMAIL,
} from '@/lib/site-config';
import { staticPageMetadata } from '@/lib/seo';

export const metadata: Metadata = staticPageMetadata({
  path: '/contact',
  title: 'Contact',
  description:
    'Reach pdfintoexcel for product questions, partnerships, security reports, and support.',
});

const contactChannels = [
  {
    title: 'General & support',
    email: SUPPORT_EMAIL,
    description:
      'Product questions, conversion issues, and billing. We typically respond within one business day.',
  },
  {
    title: 'Security',
    email: SECURITY_EMAIL,
    description:
      'Responsible disclosure and security-sensitive reports. Do not attach confidential PDFs unless we have agreed on a secure channel.',
  },
  {
    title: 'Partnerships',
    email: PARTNERSHIPS_EMAIL,
    description: 'Integrations, volume licensing, and commercial partnerships.',
  },
  {
    title: 'Legal',
    email: LEGAL_EMAIL,
    description: 'Privacy requests, terms questions, and formal legal notices.',
  },
] as const;

export default function ContactPage() {
  return (
    <>
      <BreadcrumbJsonLd
        items={[
          { name: 'Home', path: '/' },
          { name: 'Contact', path: '/contact' },
        ]}
      />
      <MarketingPageHeader
        eyebrow='Contact'
        title='We are here to help'
        lead='Reach the right inbox for your question. For how we handle uploads and retention, see our FAQ on the home page or the privacy policy.'
      />
      <MarketingPageBody>
        <div className='grid gap-6'>
          {contactChannels.map((channel) => (
            <Card key={channel.title} className='shadow-sm'>
              <CardHeader>
                <CardTitle className='text-lg'>{channel.title}</CardTitle>
              </CardHeader>
              <CardContent className='space-y-2'>
                <p className='text-muted-foreground text-sm leading-relaxed'>
                  {channel.description}
                </p>
                <a
                  href={`mailto:${channel.email}`}
                  className='text-primary inline-block text-sm font-medium underline underline-offset-4'>
                  {channel.email}
                </a>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className='mt-8 shadow-sm'>
          <CardHeader>
            <CardTitle className='text-lg'>Office hours</CardTitle>
          </CardHeader>
          <CardContent>
            <p className='text-muted-foreground text-sm leading-relaxed'>
              Monday–Friday, 9:00–18:00 UTC. Weekend messages are queued for the next
              business day.
            </p>
          </CardContent>
        </Card>

        <p className='text-muted-foreground mt-8 text-sm'>
          Common questions? See the{' '}
          <Link href='/#faq' className='text-primary font-medium hover:underline'>
            FAQ on the homepage
          </Link>
          .
        </p>
      </MarketingPageBody>
    </>
  );
}
