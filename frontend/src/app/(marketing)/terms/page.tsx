import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service — pdfintoexcel',
  description:
    'Terms governing use of pdfintoexcel PDF to Excel conversion and related services.',
};

export default function TermsPage() {
  return (
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <h1 className='text-foreground text-3xl font-bold tracking-tight'>
        Terms of Service
      </h1>
      <p className='text-muted-foreground mt-2 text-sm'>
        Last updated: May 7, 2026 · Placeholder — review with legal counsel before
        production.
      </p>
      <div className='text-muted-foreground mt-10 space-y-6 text-sm leading-relaxed'>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            1. Agreement
          </h2>
          <p>
            By using pdfintoexcel, you agree to these terms. If you disagree, do
            not use the service.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            2. Acceptable use
          </h2>
          <p>
            You may not use the service to violate law, infringe intellectual
            property, upload malware, or attempt to disrupt our systems. You are
            responsible for the content you upload and for obtaining any consent
            required from data subjects.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            3. Service availability
          </h2>
          <p>
            We strive for high availability but do not guarantee uninterrupted
            access. Features may change with notice where reasonable.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            4. Disclaimers
          </h2>
          <p>
            The service is provided &quot;as is&quot;. Automated conversion may
            introduce errors. You should validate outputs before relying on them
            for compliance, financial, or safety-critical decisions.
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            5. Liability cap
          </h2>
          <p>
            To the maximum extent permitted by law, our aggregate liability
            arising from these terms or the service is limited to the greater of
            fees you paid us in the prior month or fifty dollars (USD).
          </p>
        </section>
        <section>
          <h2 className='text-foreground mb-2 text-lg font-semibold'>
            6. Contact
          </h2>
          <p>
            Legal notices:{' '}
            <a
              className='text-primary underline underline-offset-4'
              href='mailto:legal@pdfintoexcel.com'>
              legal@pdfintoexcel.com
            </a>
          </p>
        </section>
      </div>
    </div>
  );
}
