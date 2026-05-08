import type { MetadataRoute } from 'next';

import { fetchPublishedPosts } from '@/lib/blog';

const site = 'https://pdfintoexcel.com';

const staticPages: MetadataRoute.Sitemap = [
  { url: site, lastModified: new Date(), changeFrequency: 'weekly', priority: 1 },
  {
    url: `${site}/blog`,
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: 0.9,
  },
  {
    url: `${site}/about`,
    lastModified: new Date(),
    changeFrequency: 'yearly',
    priority: 0.7,
  },
  {
    url: `${site}/contact`,
    lastModified: new Date(),
    changeFrequency: 'yearly',
    priority: 0.7,
  },
  {
    url: `${site}/privacy`,
    lastModified: new Date(),
    changeFrequency: 'yearly',
    priority: 0.5,
  },
  {
    url: `${site}/terms`,
    lastModified: new Date(),
    changeFrequency: 'yearly',
    priority: 0.5,
  },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await fetchPublishedPosts();
  const blogPosts: MetadataRoute.Sitemap = posts.map((p) => ({
    url: `${site}/blog/${p.slug}`,
    lastModified: p.updated_at ? new Date(p.updated_at) : new Date(),
    changeFrequency: 'monthly',
    priority: 0.65,
  }));
  return [...staticPages, ...blogPosts];
}
