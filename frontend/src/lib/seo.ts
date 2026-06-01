import type { Metadata } from 'next';

import { SITE_URL } from '@/lib/site-config';

type SeoInput = {
  title: string;
  metaTitle?: string | null;
  description: string;
  keywords?: string | null;
  canonicalUrl?: string | null;
  ogTitle?: string | null;
  ogDescription?: string | null;
  ogImageUrl?: string | null;
};

const DEFAULT_OG_PATH = '/opengraph-image';

export function buildMetadata(input: SeoInput): Metadata {
  const kw = input.keywords
    ?.split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  const title = input.metaTitle?.trim() || `${input.title} - pdfintoexcel`;
  const ogImages = input.ogImageUrl
    ? [input.ogImageUrl]
    : [{ url: DEFAULT_OG_PATH, width: 1200, height: 630, alt: 'pdfintoexcel' }];
  return {
    title,
    description: input.description,
    keywords: kw && kw.length > 0 ? kw : undefined,
    alternates: input.canonicalUrl ? { canonical: input.canonicalUrl } : undefined,
    openGraph: {
      title: input.ogTitle ?? title,
      description: input.ogDescription ?? input.description,
      images: ogImages,
    },
    twitter: {
      card: 'summary_large_image',
      title: input.ogTitle ?? title,
      description: input.ogDescription ?? input.description,
      images: ogImages.map((img) => (typeof img === 'string' ? img : img.url)),
    },
  };
}

type StaticPageMetadataInput = {
  path: string;
  title: string;
  description: string;
  keywords?: string[];
  ogImage?: string;
  robots?: Metadata['robots'];
};

export function staticPageMetadata(input: StaticPageMetadataInput): Metadata {
  const canonical = input.path === '/' ? SITE_URL : `${SITE_URL}${input.path}`;
  const ogImage = input.ogImage ?? DEFAULT_OG_PATH;
  return {
    title: input.title,
    description: input.description,
    keywords: input.keywords,
    alternates: { canonical },
    robots: input.robots ?? { index: true, follow: true },
    openGraph: {
      type: 'website',
      locale: 'en_US',
      siteName: 'pdfintoexcel',
      title: input.title,
      description: input.description,
      url: canonical,
      images: [{ url: ogImage, width: 1200, height: 630, alt: 'pdfintoexcel' }],
    },
    twitter: {
      card: 'summary_large_image',
      title: input.title,
      description: input.description,
      images: [ogImage],
    },
  };
}

/** Fixed last-modified for static marketing pages in sitemap.xml */
export const STATIC_SITEMAP_LAST_MODIFIED = new Date('2026-05-07T00:00:00.000Z');
