import type { Metadata } from 'next';

import {
  LegalDocumentLayout,
  type LegalSection,
} from '@/components/exceflow/legal-document-layout';
import { LEGAL_LAST_UPDATED, SUPPORT_EMAIL } from '@/lib/site-config';
import { staticPageMetadata } from '@/lib/seo';

export const metadata: Metadata = staticPageMetadata({
  path: '/privacy',
  title: 'Privacy Policy — pdfintoexcel',
  description:
    'How pdfintoexcel handles personal data, uploaded files, retention, cookies, and subprocessors.',
});

const sections: LegalSection[] = [
  {
    id: 'who-we-are',
    title: 'Who we are',
    content: (
      <p>
        pdfintoexcel (&quot;we&quot;, &quot;us&quot;) operates the website and conversion
        service at pdfintoexcel.com. This policy explains what we collect, why we
        collect it, and your choices.
      </p>
    ),
  },
  {
    id: 'files-you-upload',
    title: 'Files you upload',
    content: (
      <>
        <p>
          When you upload a PDF, we process it to generate an Excel file. Files are
          transmitted over HTTPS (TLS). We retain uploads and outputs only as long as
          necessary to complete the job and allow a reasonable download window.
        </p>
        <p>
          Unless law requires otherwise, uploaded PDFs and generated spreadsheets are
          automatically deleted from our servers within approximately one hour of
          upload, as described on our homepage.
        </p>
      </>
    ),
  },
  {
    id: 'data-we-collect',
    title: 'Data we collect',
    content: (
      <p>
        We may process technical data such as IP address, browser type, request
        timestamps, and job status metadata. We do not use uploaded document contents
        for advertising profiles or to train third-party models.
      </p>
    ),
  },
  {
    id: 'analytics-and-logs',
    title: 'Analytics and logs',
    content: (
      <p>
        Standard server and application logs help us detect abuse, debug failures, and
        measure reliability. Aggregated metrics (for example, job counts and error
        rates) may be retained without document contents.
      </p>
    ),
  },
  {
    id: 'cookies',
    title: 'Cookies',
    content: (
      <p>
        We use cookies and similar technologies where needed for theme preferences,
        session security, or staff-only administration tools. You can control cookies
        through your browser settings.
      </p>
    ),
  },
  {
    id: 'subprocessors',
    title: 'Subprocessors',
    content: (
      <p>
        We use infrastructure providers (hosting, storage, networking) that process
        data on our behalf under contractual obligations. A current list is available on
        request by emailing{' '}
        <a
          href={`mailto:${SUPPORT_EMAIL}`}
          className='text-primary underline underline-offset-4'>
          {SUPPORT_EMAIL}
        </a>
        .
      </p>
    ),
  },
  {
    id: 'your-rights',
    title: 'Your rights',
    content: (
      <p>
        Depending on your location, you may have rights to access, correct, delete, or
        restrict processing of personal data. Contact us and we will respond within the
        timeframes required by applicable law.
      </p>
    ),
  },
  {
    id: 'contact',
    title: 'Contact',
    content: (
      <p>
        Privacy questions:{' '}
        <a
          href='mailto:privacy@pdfintoexcel.com'
          className='text-primary underline underline-offset-4'>
          privacy@pdfintoexcel.com
        </a>
      </p>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <LegalDocumentLayout
      title='Privacy Policy'
      lead='How we handle personal data, uploaded files, and operational logs.'
      lastUpdated={LEGAL_LAST_UPDATED}
      sections={sections}
    />
  );
}
