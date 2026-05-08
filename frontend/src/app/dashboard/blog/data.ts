import 'server-only';

import { getAnalyticsKey, getInternalApiBase } from '@/lib/internal-api';

export type AdminBlogListItem = {
  id: string;
  slug: string;
  title: string;
  meta_description: string;
  published: boolean;
  published_at: string | null;
  updated_at: string | null;
};

export type AdminBlogPost = {
  id: string;
  slug: string;
  title: string;
  meta_description: string;
  body: string;
  published: boolean;
  og_title: string | null;
  og_description: string | null;
  og_image_url: string | null;
  canonical_path: string | null;
  keywords: string | null;
  published_at: string | null;
  updated_at: string | null;
};

export async function fetchAdminBlogPosts(): Promise<AdminBlogListItem[] | null> {
  const key = getAnalyticsKey();
  if (!key) {
    return null;
  }
  const res = await fetch(`${getInternalApiBase()}/admin/blog/posts`, {
    headers: { 'X-Analytics-Key': key },
    cache: 'no-store',
  });
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as AdminBlogListItem[];
}

export async function fetchAdminBlogPost(id: string): Promise<AdminBlogPost | null> {
  const key = getAnalyticsKey();
  if (!key) {
    return null;
  }
  const res = await fetch(`${getInternalApiBase()}/admin/blog/posts/${id}`, {
    headers: { 'X-Analytics-Key': key },
    cache: 'no-store',
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as AdminBlogPost;
}
