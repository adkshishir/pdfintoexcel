import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

import { getInternalApiBase } from '@/lib/internal-api';

type Props = { params: Promise<{ slug: string }> };

type LandingPageData = {
  slug: string;
  title: string;
  body: string;
  faq_items: Array<{ q: string; a: string }>;
  internal_links: Array<{ href: string; label: string }>;
};

async function fetchLanding(slug: string): Promise<LandingPageData | null> {
  const res = await fetch(`${getInternalApiBase()}/landing-pages/${encodeURIComponent(slug)}`, {
    next: { revalidate: 120 },
  });
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return (await res.json()) as LandingPageData;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const page = await fetchLanding(slug);
  if (!page) return {};
  return {
    title: `${page.title} - pdfintoexcel`,
    description: page.body.slice(0, 155),
  };
}

export default async function LandingPage({ params }: Props) {
  const { slug } = await params;
  const page = await fetchLanding(slug);
  if (!page) notFound();
  const faqJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: page.faq_items.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  };
  return (
    <div className='mx-auto max-w-3xl px-4 py-12 sm:px-6'>
      <script type='application/ld+json' dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      <h1 className='mb-4 text-3xl font-bold tracking-tight'>{page.title}</h1>
      <div className='prose prose-sm max-w-none'>
        <ReactMarkdown>{page.body}</ReactMarkdown>
      </div>
      {page.faq_items.length > 0 && (
        <section className='mt-10 space-y-3'>
          <h2 className='text-xl font-semibold'>FAQ</h2>
          {page.faq_items.map((f, idx) => (
            <div key={`${f.q}-${idx}`} className='rounded-lg border p-3'>
              <p className='font-medium'>{f.q}</p>
              <p className='text-muted-foreground text-sm'>{f.a}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
