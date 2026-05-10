import 'server-only';

import { getInternalApiBase } from '@/lib/internal-api';

export type BlogListItem = {
  id: string;
  slug: string;
  title: string;
  meta_description: string;
  published_at: string | null;
  updated_at: string | null;
};

export type BlogPostPublic = BlogListItem & {
  meta_title: string | null;
  body: string;
  og_title: string | null;
  og_description: string | null;
  og_image_url: string | null;
  canonical_url: string | null;
  robots_directives: string | null;
  keywords: string | null;
  schema_jsonld: Record<string, unknown> | null;
};

export async function fetchPublishedPosts(): Promise<BlogListItem[]> {
  const res = await fetch(`${getInternalApiBase()}/blog/posts`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    return [];
  }
  return (await res.json()) as BlogListItem[];
}

export async function fetchPublishedPostBySlug(
  slug: string,
): Promise<BlogPostPublic | null> {
  const res = await fetch(
    `${getInternalApiBase()}/blog/posts/${encodeURIComponent(slug)}`,
    { next: { revalidate: 60 } },
  );
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as BlogPostPublic;
}

export async function fetchPublishedSlugList(): Promise<string[]> {
  const posts = await fetchPublishedPosts();
  return posts.map((p) => p.slug);
}
