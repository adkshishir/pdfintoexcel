import type { MetadataRoute } from 'next';

import { fetchPublishedPosts } from '@/lib/blog';
import { getInternalApiBase } from '@/lib/internal-api';
import { STATIC_SITEMAP_LAST_MODIFIED } from '@/lib/seo';

/** Regenerate at most once per hour; not pre-built at build time because backend is absent. */
export const revalidate = 3600;

const site = 'https://pdfintoexcel.com';

const staticLastMod = STATIC_SITEMAP_LAST_MODIFIED;

const staticPages: MetadataRoute.Sitemap = [
  { url: site, lastModified: staticLastMod, changeFrequency: 'weekly', priority: 1 },
  {
    url: `${site}/blog`,
    lastModified: staticLastMod,
    changeFrequency: 'weekly',
    priority: 0.9,
  },
  {
    url: `${site}/about`,
    lastModified: staticLastMod,
    changeFrequency: 'yearly',
    priority: 0.7,
  },
  {
    url: `${site}/contact`,
    lastModified: staticLastMod,
    changeFrequency: 'yearly',
    priority: 0.7,
  },
  {
    url: `${site}/privacy`,
    lastModified: staticLastMod,
    changeFrequency: 'yearly',
    priority: 0.5,
  },
  {
    url: `${site}/terms`,
    lastModified: staticLastMod,
    changeFrequency: 'yearly',
    priority: 0.5,
  },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const posts = await fetchPublishedPosts();
  let landing: Array<{ slug: string; updated_at: string }> = [];
  try {
    const landingRes = await fetch(`${getInternalApiBase()}/landing-pages`, { next: { revalidate: 300 } });
    landing = landingRes.ok ? ((await landingRes.json()) as Array<{ slug: string; updated_at: string }>) : [];
  } catch {
    landing = [];
  }
  const blogPosts: MetadataRoute.Sitemap = posts.map((p) => ({
    url: `${site}/blog/${p.slug}`,
    lastModified: p.updated_at ? new Date(p.updated_at) : new Date(),
    changeFrequency: 'monthly',
    priority: 0.65,
  }));
  const landingPages: MetadataRoute.Sitemap = landing.map((p) => ({
    url: `${site}/${p.slug}`,
    lastModified: p.updated_at ? new Date(p.updated_at) : new Date(),
    changeFrequency: 'weekly',
    priority: 0.85,
  }));
  return [...staticPages, ...blogPosts, ...landingPages];
}
