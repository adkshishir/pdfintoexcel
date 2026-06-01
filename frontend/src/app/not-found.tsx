import type { Metadata } from 'next';

import { ExceflowSiteShell } from '@/components/exceflow/exceflow-site-shell';
import { StatusPage } from '@/components/exceflow/status-page';

export const metadata: Metadata = {
  title: 'Page not found',
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <ExceflowSiteShell mainClassName='flex flex-col'>
      <StatusPage
        code='404'
        title='Page not found'
        description='That URL does not exist or may have moved. Try the converter, blog, or contact page.'
        primaryHref='/'
        primaryLabel='Go home'
        secondary={[
          { href: '/blog', label: 'Blog' },
          { href: '/contact', label: 'Contact' },
        ]}
      />
    </ExceflowSiteShell>
  );
}
