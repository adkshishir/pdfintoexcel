'use client';

import { useEffect } from 'react';

import { ExceflowSiteShell } from '@/components/exceflow/exceflow-site-shell';
import { ExceflowThemeProvider } from '@/components/exceflow/exceflow-theme-provider';
import { StatusPage } from '@/components/exceflow/status-page';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const ref = error.digest ? ` (ref: ${error.digest})` : '';

  return (
    <html lang='en' suppressHydrationWarning>
      <body className='bg-background text-foreground flex min-h-screen flex-col antialiased'>
        <ExceflowThemeProvider>
          <ExceflowSiteShell mainClassName='flex flex-col'>
            <StatusPage
              code='Error'
              title='We could not complete that action'
              description={`Please try again. If the problem continues, contact support with the time of the error${ref}.`}
              primaryHref='/'
              primaryLabel='Home'
              secondary={[{ href: '/contact', label: 'Contact' }]}
              onRetry={() => reset()}
              tone='error'
            />
          </ExceflowSiteShell>
        </ExceflowThemeProvider>
      </body>
    </html>
  );
}
