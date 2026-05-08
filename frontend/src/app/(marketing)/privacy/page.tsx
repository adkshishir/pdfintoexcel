import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy — pdfintoexcel',
  description:
    'How pdfintoexcel handles personal data, files, retention, and subprocessors.',
};

export default function PrivacyPage() {
  return (
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <h1 className='text-foreground text-3xl font-bold tracking-tight'>
        Privacy Policy
      </h1>
      <p className='text-muted-foreground mt-2 text-sm'>
        Last updated: May 7, 2026 · Placeholder — review with legal counsel before
        production.
      </p>
      <div className='text-muted-foreground mt-10 space-y-6 text-sm leading-relaxed'>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            1. Who we are
          </h2>
          <p>
            pdfintoexcel (&quot;we&quot;, &quot;us&quot;) operates the website and
            conversion service at pdfintoexcel.com. This policy explains what we
            collect, why we collect it, and your choices.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            2. Files you upload
          </h2>
          <p>
            When you upload a PDF, we process it to generate an Excel file. Files
            are transmitted over HTTPS. We retain uploads and outputs only as
            long as necessary to complete the job and allow a reasonable download
            window, then delete them according to our operational schedule unless
            law requires otherwise.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            3. Analytics and logs
          </h2>
          <p>
            We may keep standard server logs (IP, user agent, timestamps) for
            security and reliability. Internal analytics may aggregate job counts
            and outcomes without retaining document contents.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            4. Cookies
          </h2>
          <p>
            We use cookies where needed for theme preferences, securely completing
            your session, or staff-only tools. You can control cookies through
            your browser.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            5. Contact
          </h2>
          <p>
            Questions about privacy:{' '}
            <a
              className='text-primary underline underline-offset-4'
              href='mailto:privacy@pdfintoexcel.com'>
              privacy@pdfintoexcel.com
            </a>
          </p>
        </section>
      </div>
    </div>
  );
}
