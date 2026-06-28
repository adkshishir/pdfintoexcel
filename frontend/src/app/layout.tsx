import type { Metadata, Viewport } from 'next';
import localFont from 'next/font/local';

import { ExceflowThemeProvider } from '@/components/exceflow/exceflow-theme-provider';
import { GoogleAnalytics } from '@/components/seo/google-analytics';
import { SiteJsonLd } from '@/components/seo/site-json-ld';
import { TooltipProvider } from '@/components/ui/tooltip';

import './globals.css';

const inter = localFont({
  src: '../fonts/inter-latin.woff2',
  variable: '--font-inter',
  display: 'swap',
  weight: '100 900',
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#107C41' },
    { media: '(prefers-color-scheme: dark)', color: '#0f1114' },
  ],
};

export const metadata: Metadata = {
  metadataBase: new URL('https://pdfintoexcel.com'),
  title: {
    default: 'pdfintoexcel — Convert PDF into Excel',
    template: '%s | pdfintoexcel',
  },
  description:
    'Convert PDF into Excel online with accurate table extraction. OCR for scanned PDFs; also supports PDF to Excel export.',
  keywords: [
    'pdfintoexcel',
    'PDF into Excel',
    'PDF to Excel',
    'convert PDF into Excel',
    'convert PDF to Excel',
    'table extraction',
    'OCR PDF',
    'spreadsheet',
  ],
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'pdfintoexcel',
    title: 'pdfintoexcel — Convert PDF into Excel',
    description:
      'Accurate PDF into Excel conversion with layout preservation for tables and scans.',
    url: 'https://pdfintoexcel.com',
    images: [{ url: '/opengraph-image', width: 1200, height: 630, alt: 'pdfintoexcel' }],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@pdfintoexcel',
    title: 'pdfintoexcel — Convert PDF into Excel',
    description:
      'Accurate PDF into Excel conversion with layout preservation for tables and scans.',
    images: ['/opengraph-image'],
  },
  manifest: '/manifest.webmanifest',
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
      <head>
        <link rel='preconnect' href='https://www.googletagmanager.com' />
        <link rel='dns-prefetch' href='https://www.googletagmanager.com' />
        <link rel='preconnect' href='https://www.google-analytics.com' />
        <link rel='dns-prefetch' href='https://www.google-analytics.com' />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');var d=t==='dark'||(t!=='light'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d)}catch(e){}})();`,
          }}
        />
      </head>
      <body className='flex min-h-screen flex-col'>
        <GoogleAnalytics />
        <SiteJsonLd />
        <ExceflowThemeProvider>
          <TooltipProvider delayDuration={300}>{children}</TooltipProvider>
        </ExceflowThemeProvider>
      </body>
    </html>
  );
}
