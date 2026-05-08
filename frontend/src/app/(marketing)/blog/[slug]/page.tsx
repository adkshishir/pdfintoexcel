import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

import { fetchPublishedPostBySlug } from '@/lib/blog';

type Props = { params: Promise<{ slug: string }> };

export const revalidate = 60;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await fetchPublishedPostBySlug(slug);
  if (!post) {
    return { title: 'Post not found' };
  }
  const ogTitle = post.og_title ?? post.title;
  const ogDesc = post.og_description ?? post.meta_description;
  const kw = post.keywords
    ?.split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  return {
    title: `${post.title} — pdfintoexcel`,
    description: post.meta_description,
    keywords: kw && kw.length > 0 ? kw : undefined,
    alternates: post.canonical_path
      ? { canonical: post.canonical_path }
      : undefined,
    openGraph: {
      title: ogTitle,
      description: ogDesc,
      type: 'article',
      publishedTime: post.published_at ?? undefined,
      images: post.og_image_url ? [post.og_image_url] : undefined,
    },
    twitter: {
      card: post.og_image_url ? 'summary_large_image' : 'summary',
      title: ogTitle,
      description: ogDesc,
      images: post.og_image_url ? [post.og_image_url] : undefined,
    },
  };
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = await fetchPublishedPostBySlug(slug);
  if (!post) {
    notFound();
  }

  const jsonLd = {
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

  return (
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <script
        type='application/ld+json'
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <p className='text-muted-foreground text-sm'>
        <Link href='/blog' className='hover:text-foreground font-medium'>
          Blog
        </Link>
        {dateLabel && (
          <>
            <span className='mx-2'>/</span>
            <time dateTime={dateRaw ?? undefined}>{dateLabel}</time>
          </>
        )}
      </p>
      <h1 className='text-foreground mt-4 text-3xl font-bold tracking-tight'>
        {post.title}
      </h1>
      <p className='text-muted-foreground mt-3 text-lg leading-relaxed'>
        {post.meta_description}
      </p>
      <div
        className='text-foreground mt-12 max-w-none space-y-4 leading-relaxed [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4 [&_h2]:mt-10 [&_h2]:mb-3 [&_h2]:text-xl [&_h2]:font-semibold [&_li]:mb-2 [&_strong]:font-semibold [&_ul]:my-4 [&_ul]:list-inside [&_ul]:list-disc'>
        <ReactMarkdown>{post.body}</ReactMarkdown>
      </div>
    </div>
  );
}
