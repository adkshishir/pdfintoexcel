import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { ExceflowThemeProvider } from '@/components/exceflow/exceflow-theme-provider';
import { SiteJsonLd } from '@/components/seo/site-json-ld';
import { TooltipProvider } from '@/components/ui/tooltip';

import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://pdfintoexcel.com'),
  title: {
    default: 'pdfintoexcel — PDF to Excel',
    template: '%s | pdfintoexcel',
  },
  description:
    'Convert digital, scanned, and handwritten PDFs into structured Excel files.',
  keywords: [
    'PDF to Excel',
    'convert PDF',
    'table extraction',
    'OCR PDF',
    'spreadsheet',
    'pdfintoexcel',
  ],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'pdfintoexcel',
    title: 'pdfintoexcel — PDF to Excel',
    description:
      'Accurate PDF to Excel conversion with layout preservation for tables and scans.',
    url: 'https://pdfintoexcel.com',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'pdfintoexcel — PDF to Excel',
    description:
      'Accurate PDF to Excel conversion with layout preservation for tables and scans.',
  },
  icons: {
    icon: [{ url: '/icon.png', type: 'image/png', sizes: 'any' }],
    apple: [{ url: '/icon.png', type: 'image/png' }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en' className={inter.variable} suppressHydrationWarning>
      <body className='flex min-h-screen flex-col'>
        <SiteJsonLd />
        <ExceflowThemeProvider>
          <TooltipProvider delayDuration={300}>{children}</TooltipProvider>
        </ExceflowThemeProvider>
      </body>
    </html>
  );
}
