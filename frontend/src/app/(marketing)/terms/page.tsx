import type { Metadata } from 'next';

import {
  LegalDocumentLayout,
  type LegalSection,
} from '@/components/exceflow/legal-document-layout';
import { LEGAL_EMAIL, LEGAL_LAST_UPDATED } from '@/lib/site-config';
import { staticPageMetadata } from '@/lib/seo';

export const metadata: Metadata = staticPageMetadata({
  path: '/terms',
  title: 'Terms of Service — pdfintoexcel',
  description:
    'Terms governing use of pdfintoexcel PDF to Excel conversion and related services.',
});

const sections: LegalSection[] = [
  {
    id: 'agreement',
    title: 'Agreement',
    content: (
      <p>
        By using pdfintoexcel, you agree to these terms. If you disagree, do not use
        the service.
      </p>
    ),
  },
  {
    id: 'acceptable-use',
    title: 'Acceptable use',
    content: (
      <p>
        You may not use the service to violate law, infringe intellectual property,
        upload malware, or attempt to disrupt our systems. You are responsible for the
        content you upload and for obtaining any consent required from data subjects.
      </p>
    ),
  },
  {
    id: 'service-availability',
    title: 'Service availability',
    content: (
      <p>
        We strive for high availability but do not guarantee uninterrupted access.
        Features may change with notice where reasonable.
      </p>
    ),
  },
  {
    id: 'disclaimers',
    title: 'Disclaimers',
    content: (
      <p>
        The service is provided &quot;as is&quot;. Automated conversion may introduce
        errors. You should validate outputs before relying on them for compliance,
        financial, or safety-critical decisions.
      </p>
    ),
  },
  {
    id: 'liability',
    title: 'Limitation of liability',
    content: (
      <p>
        To the maximum extent permitted by law, our aggregate liability arising from
        these terms or the service is limited to the greater of fees you paid us in
        the prior month or fifty dollars (USD).
      </p>
    ),
  },
  {
    id: 'contact',
    title: 'Contact',
    content: (
      <p>
        Legal notices:{' '}
        <a
          href={`mailto:${LEGAL_EMAIL}`}
          className='text-primary underline underline-offset-4'>
          {LEGAL_EMAIL}
        </a>
      </p>
    ),
  },
];

export default function TermsPage() {
  return (
    <LegalDocumentLayout
      title='Terms of Service'
      lead='Terms governing your use of pdfintoexcel and our conversion services.'
      lastUpdated={LEGAL_LAST_UPDATED}
      sections={sections}
    />
  );
}
