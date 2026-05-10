import type { Metadata } from 'next';

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

export function buildMetadata(input: SeoInput): Metadata {
  const kw = input.keywords
    ?.split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  const title = input.metaTitle?.trim() || `${input.title} - pdfintoexcel`;
  return {
    title,
    description: input.description,
    keywords: kw && kw.length > 0 ? kw : undefined,
    alternates: input.canonicalUrl ? { canonical: input.canonicalUrl } : undefined,
    openGraph: {
      title: input.ogTitle ?? title,
      description: input.ogDescription ?? input.description,
      images: input.ogImageUrl ? [input.ogImageUrl] : undefined,
    },
    twitter: {
      card: input.ogImageUrl ? 'summary_large_image' : 'summary',
      title: input.ogTitle ?? title,
      description: input.ogDescription ?? input.description,
      images: input.ogImageUrl ? [input.ogImageUrl] : undefined,
    },
  };
}
