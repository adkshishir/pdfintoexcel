import type { BlogListItem } from '@/lib/blog';
import { SITE_URL } from '@/lib/site-config';

export function BlogIndexJsonLd({ posts }: { posts: BlogListItem[] }) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: 'pdfintoexcel Blog',
    url: `${SITE_URL}/blog`,
    publisher: { '@id': `${SITE_URL}/#organization` },
    blogPost: posts.slice(0, 20).map((post) => ({
      '@type': 'BlogPosting',
      headline: post.title,
      url: `${SITE_URL}/blog/${post.slug}`,
      datePublished: post.published_at ?? undefined,
      dateModified: post.updated_at ?? undefined,
    })),
  };
  return (
    <script
      type='application/ld+json'
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
