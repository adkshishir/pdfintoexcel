import type { Metadata } from 'next';

import { HomePageClient } from '@/app/home-page-client';
import { HomeFaqJsonLd } from '@/components/seo/home-faq-json-ld';
import { SITE_URL } from '@/lib/site-config';

const title =
  'Convert PDF into Excel Online — Free, Accurate Table Extraction | pdfintoexcel';
const description =
  'Convert PDF into Excel online with accurate table extraction. OCR for scanned PDFs, no sign-up, files auto-deleted in 1 hour. PDF to Excel export in seconds.';

export const metadata: Metadata = {
  title: { absolute: title },
  description,
  alternates: { canonical: SITE_URL },
  keywords: [
    'convert PDF into Excel',
    'PDF into Excel online',
    'PDF to Excel',
    'PDF to xlsx',
    'table extraction',
    'scanned PDF OCR',
    'free PDF into Excel',
    'pdfintoexcel',
  ],
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'pdfintoexcel',
    title,
    description,
    url: SITE_URL,
    images: [{ url: '/opengraph-image', width: 1200, height: 630, alt: 'pdfintoexcel' }],
  },
  twitter: {
    card: 'summary_large_image',
    title,
    description,
    images: ['/opengraph-image'],
  },
};

export default function HomePage() {
  return (
    <>
      <HomeFaqJsonLd />
      <HomePageClient />
    </>
  );
}
