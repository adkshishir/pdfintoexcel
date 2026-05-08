import Link from 'next/link';
import type { Metadata } from 'next';

import { fetchPublishedPosts } from '@/lib/blog';

export const metadata: Metadata = {
  title: 'Blog — pdfintoexcel',
  description:
    'Articles on PDF to Excel conversion, table reconstruction, OCR, and secure document handling.',
};

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
    <div className='mx-auto max-w-3xl px-4 py-16 sm:px-6'>
      <h1 className='text-foreground text-3xl font-bold tracking-tight'>
        Blog
      </h1>
      <p className='text-muted-foreground mt-3 text-lg leading-relaxed'>
        Practical notes on PDF tables, Excel exports, and operating a trustworthy
        converter.
      </p>
      <ul className='mt-12 space-y-10'>
        {posts.length === 0 ? (
          <li className='text-muted-foreground text-sm'>
            No published posts yet. Add one from the dashboard.
          </li>
        ) : (
          posts.map((post) => {
            const dateRaw = post.published_at ?? post.updated_at;
            const dateLabel = formatDate(dateRaw);
            return (
              <li key={post.slug}>
                <article>
                  {dateLabel && (
                    <time
                      dateTime={dateRaw ?? undefined}
                      className='text-muted-foreground text-sm font-medium'>
                      {dateLabel}
                    </time>
                  )}
                  <h2 className='mt-1 text-xl font-semibold'>
                    <Link
                      href={`/blog/${post.slug}`}
                      className='text-foreground hover:text-primary transition-colors'>
                      {post.title}
                    </Link>
                  </h2>
                  <p className='text-muted-foreground mt-2 leading-relaxed'>
                    {post.meta_description}
                  </p>
                  <Link
                    href={`/blog/${post.slug}`}
                    className='text-primary mt-3 inline-block text-sm font-medium'>
                    Read more
                  </Link>
                </article>
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
}
