import Link from 'next/link';
import type { Metadata } from 'next';

import { MarketingPageBody } from '@/components/exceflow/marketing-page-body';
import { MarketingPageHeader } from '@/components/exceflow/marketing-page-header';
import { BlogIndexJsonLd } from '@/components/seo/blog-index-json-ld';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { fetchPublishedPosts } from '@/lib/blog';
import { staticPageMetadata } from '@/lib/seo';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = staticPageMetadata({
  path: '/blog',
  title: 'Blog — pdfintoexcel',
  description:
    'Articles on PDF to Excel conversion, table reconstruction, OCR, and secure document handling.',
});

function formatDate(iso: string | null | undefined) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default async function BlogIndexPage() {
  const posts = await fetchPublishedPosts();

  return (
    <>
      <BlogIndexJsonLd posts={posts} />
      <MarketingPageHeader
        eyebrow='Resources'
        title='Blog'
        lead='Practical notes on PDF tables, Excel exports, and operating a trustworthy converter.'
      />
      <MarketingPageBody>
        {posts.length === 0 ? (
          <div className='border-border bg-card rounded-xl border p-8 text-center'>
            <p className='text-muted-foreground text-sm'>
              No published posts yet. Check back soon, or{' '}
              <Link href='/' className='text-primary font-medium hover:underline'>
                try the converter
              </Link>
              .
            </p>
          </div>
        ) : (
          <ul className='grid gap-6 sm:grid-cols-1'>
            {posts.map((post) => {
              const dateRaw = post.published_at ?? post.updated_at;
              const dateLabel = formatDate(dateRaw);
              return (
                <li key={post.slug}>
                  <Card className='transition-shadow hover:shadow-md'>
                    <CardHeader>
                      {dateLabel && (
                        <time
                          dateTime={dateRaw ?? undefined}
                          className='text-muted-foreground text-xs font-medium'>
                          {dateLabel}
                        </time>
                      )}
                      <CardTitle className='text-xl'>
                        <Link
                          href={`/blog/${post.slug}`}
                          className='hover:text-primary transition-colors'>
                          {post.title}
                        </Link>
                      </CardTitle>
                      <CardDescription className='line-clamp-3 text-sm leading-relaxed'>
                        {post.meta_description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Link
                        href={`/blog/${post.slug}`}
                        className='text-primary text-sm font-medium hover:underline'>
                        Read article →
                      </Link>
                    </CardContent>
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </MarketingPageBody>
    </>
  );
}
