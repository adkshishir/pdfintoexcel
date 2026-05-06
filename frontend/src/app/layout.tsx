import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { ExceflowThemeProvider } from '@/components/exceflow/exceflow-theme-provider';

import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Exceflow PDF — PDF to Excel',
  description:
    'Convert digital, scanned, and handwritten PDFs into structured Excel files.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en' className={inter.variable} suppressHydrationWarning>
      <body className='flex min-h-screen flex-col'>
        <ExceflowThemeProvider>{children}</ExceflowThemeProvider>
      </body>
    </html>
  );
}
