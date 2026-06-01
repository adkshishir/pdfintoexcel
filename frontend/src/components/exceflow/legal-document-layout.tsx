import Link from 'next/link';

import { MarketingPageBody } from '@/components/exceflow/marketing-page-body';
import { MarketingPageHeader } from '@/components/exceflow/marketing-page-header';
import { cn } from '@/lib/utils';

export type LegalSection = {
  id: string;
  title: string;
  content: React.ReactNode;
};

type LegalDocumentLayoutProps = {
  title: string;
  lead: string;
  lastUpdated: string;
  sections: LegalSection[];
  counselNote?: string;
};

export function LegalDocumentLayout({
  title,
  lead,
  lastUpdated,
  sections,
  counselNote = 'Review with legal counsel before production launch.',
}: LegalDocumentLayoutProps) {
  return (
    <>
      <MarketingPageHeader title={title} lead={lead} lastUpdated={lastUpdated} />
      <MarketingPageBody>
        <div className='lg:grid lg:grid-cols-[220px_1fr] lg:gap-12'>
          <nav
            aria-label='Table of contents'
            className='mb-8 hidden lg:block'>
            <p className='text-foreground text-xs font-semibold tracking-wider uppercase'>
              On this page
            </p>
            <ol className='border-border mt-4 space-y-2 border-l pl-4'>
              {sections.map((section) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className='text-muted-foreground hover:text-foreground text-sm transition-colors'>
                    {section.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
          <div>
            <p className='border-border bg-card text-muted-foreground mb-8 rounded-lg border px-4 py-3 text-xs leading-relaxed'>
              {counselNote}
            </p>
            <div className='space-y-10'>
              {sections.map((section, index) => (
                <section
                  key={section.id}
                  id={section.id}
                  className={cn('scroll-mt-24')}>
                  <h2 className='text-foreground text-lg font-semibold'>
                    {index + 1}. {section.title}
                  </h2>
                  <div className='text-muted-foreground mt-3 space-y-3 text-sm leading-relaxed'>
                    {section.content}
                  </div>
                </section>
              ))}
            </div>
            <p className='text-muted-foreground mt-12 text-sm'>
              Questions?{' '}
              <Link href='/contact' className='text-primary font-medium hover:underline'>
                Contact us
              </Link>
              .
            </p>
          </div>
        </div>
      </MarketingPageBody>
    </>
  );
}
