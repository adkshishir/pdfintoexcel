import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

import { MarketingPageBody } from '@/components/exceflow/marketing-page-body';
import { BreadcrumbJsonLd } from '@/components/seo/breadcrumb-json-ld';
import { fetchPublishedPostBySlug } from '@/lib/blog';
import { buildMetadata } from '@/lib/seo';
import { cn } from '@/lib/utils';

type Props = { params: Promise<{ slug: string }> };

export const revalidate = 60;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await fetchPublishedPostBySlug(slug);
  if (!post) {
    return { title: 'Post not found', robots: { index: false, follow: false } };
  }
  return buildMetadata({
    title: post.title,
    metaTitle: post.meta_title,
    description: post.meta_description,
    keywords: post.keywords,
    canonicalUrl: post.canonical_url ?? `https://pdfintoexcel.com/blog/${slug}`,
    ogTitle: post.og_title,
    ogDescription: post.og_description,
    ogImageUrl: post.og_image_url,
  });
}

function estimateReadingMinutes(body: string): number {
  const words = body.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = await fetchPublishedPostBySlug(slug);
  if (!post) {
    notFound();
  }

  const jsonLd = post.schema_jsonld ?? {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.meta_description,
    datePublished: post.published_at,
    author: { '@type': 'Organization', name: 'pdfintoexcel' },
    publisher: { '@type': 'Organization', name: 'pdfintoexcel' },
  };

  const dateRaw = post.published_at ?? post.updated_at;
  const dateLabel = dateRaw
    ? new Date(dateRaw).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null;

  const readingMin = estimateReadingMinutes(post.body);

  return (
    <>
      <BreadcrumbJsonLd
        items={[
          { name: 'Home', path: '/' },
          { name: 'Blog', path: '/blog' },
          { name: post.title, path: `/blog/${slug}` },
        ]}
      />
      <script
        type='application/ld+json'
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <header className='border-border border-b bg-card/50 px-4 py-10 sm:px-6 sm:py-12'>
        <div className='mx-auto max-w-3xl'>
          <nav aria-label='Breadcrumb' className='text-muted-foreground text-sm'>
            <Link href='/' className='hover:text-foreground transition-colors'>
              Home
            </Link>
            <span className='mx-2'>/</span>
            <Link href='/blog' className='hover:text-foreground transition-colors'>
              Blog
            </Link>
            <span className='mx-2'>/</span>
            <span className='text-foreground font-medium'>{post.title}</span>
          </nav>
          <h1 className='text-foreground mt-6 text-3xl font-bold tracking-tight sm:text-4xl'>
            {post.title}
          </h1>
          <p className='text-muted-foreground mt-4 text-lg leading-relaxed'>
            {post.meta_description}
          </p>
          <div className='text-muted-foreground mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm'>
            {dateLabel && (
              <time dateTime={dateRaw ?? undefined}>{dateLabel}</time>
            )}
            <span>{readingMin} min read</span>
          </div>
        </div>
      </header>
      <MarketingPageBody>
        <article
          className={cn(
            'text-foreground max-w-none space-y-4 leading-relaxed',
            '[&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4',
            '[&_h2]:mt-10 [&_h2]:mb-3 [&_h2]:text-xl [&_h2]:font-semibold',
            '[&_li]:mb-2 [&_strong]:font-semibold',
            '[&_ul]:my-4 [&_ul]:list-inside [&_ul]:list-disc',
          )}>
          <ReactMarkdown>{post.body}</ReactMarkdown>
        </article>
      </MarketingPageBody>
    </>
  );
}
