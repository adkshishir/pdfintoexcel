import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

import { BreadcrumbJsonLd } from '@/components/seo/breadcrumb-json-ld';
import { getInternalApiBase } from '@/lib/internal-api';
import { buildMetadata } from '@/lib/seo';
import { SITE_URL } from '@/lib/site-config';

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
  const description = page.body.replace(/[#*_`[\]]/g, ' ').slice(0, 155).trim();
  return buildMetadata({
    title: page.title,
    description,
    canonicalUrl: `${SITE_URL}/${slug}`,
    keywords: 'PDF into Excel, PDF to Excel, table extraction',
  });
}

export default async function LandingPage({ params }: Props) {
  const { slug } = await params;
  const page = await fetchLanding(slug);
  if (!page) notFound();

  const faqJsonLd =
    page.faq_items.length > 0
      ? {
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: page.faq_items.map((f) => ({
            '@type': 'Question',
            name: f.q,
            acceptedAnswer: { '@type': 'Answer', text: f.a },
          })),
        }
      : null;

  return (
    <>
      <BreadcrumbJsonLd
        items={[
          { name: 'Home', path: '/' },
          { name: page.title, path: `/${slug}` },
        ]}
      />
      {faqJsonLd && (
        <script type='application/ld+json' dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      )}
      <div className='mx-auto max-w-3xl px-4 py-12 sm:px-6'>
        <nav aria-label='Breadcrumb' className='text-muted-foreground mb-6 text-sm'>
          <Link href='/' className='hover:text-foreground transition-colors'>
            Home
          </Link>
          <span className='mx-2'>/</span>
          <span className='text-foreground font-medium'>{page.title}</span>
        </nav>
        <h1 className='mb-4 text-3xl font-bold tracking-tight'>{page.title}</h1>
        <div
          className='prose prose-sm max-w-none [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4'
        >
          <ReactMarkdown>{page.body}</ReactMarkdown>
        </div>
        {page.internal_links.length > 0 && (
          <section className='mt-10'>
            <h2 className='text-xl font-semibold'>Related</h2>
            <ul className='mt-3 space-y-2'>
              {page.internal_links.map((link) => (
                <li key={`${link.href}-${link.label}`}>
                  <Link href={link.href} className='text-primary text-sm font-medium underline underline-offset-4'>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
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
        <aside className='border-excel/30 bg-excel/5 mt-10 rounded-2xl border p-6'>
          <p className='text-foreground font-semibold'>Ready to convert?</p>
          <p className='text-muted-foreground mt-1 text-sm'>
            Upload your PDF and download an editable Excel file in seconds.
          </p>
          <Link
            href='/'
            className='bg-excel hover:bg-excel-dark mt-4 inline-flex rounded-lg px-4 py-2 text-sm font-semibold text-white'>
            Convert PDF into Excel free
          </Link>
        </aside>
      </div>
    </>
  );
}
