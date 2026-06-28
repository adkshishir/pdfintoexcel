import 'server-only';

import { adminFetch } from '@/lib/admin-auth';
import { getInternalApiBase } from '@/lib/internal-api';

export type BlogCategoryItem = {
  id: string;
  slug: string;
  name: string;
};

export type NextTopicResponse = {
  topic: string;
  primary_keyword: string;
  category_slug: string;
  is_comparison: boolean;
  comparison_targets: string[];
  category_id: string | null;
  rationale: string;
};

export type AdminBlogListItem = {
  id: string;
  slug: string;
  title: string;
  meta_description: string;
  status: 'draft' | 'scheduled' | 'published' | 'archived';
  published_at: string | null;
  updated_at: string | null;
};

export type AdminBlogPost = {
  id: string;
  slug: string;
  title: string;
  meta_title: string | null;
  meta_description: string;
  body: string;
  status: 'draft' | 'scheduled' | 'published' | 'archived';
  scheduled_at: string | null;
  cover_image_url: string | null;
  category_id: string | null;
  tag_ids: string[];
  og_title: string | null;
  og_description: string | null;
  og_image_url: string | null;
  canonical_url: string | null;
  robots_directives: string | null;
  keywords: string | null;
  schema_jsonld: Record<string, unknown> | null;
  published_at: string | null;
  updated_at: string | null;
};

export async function fetchAdminBlogCategories(): Promise<BlogCategoryItem[] | null> {
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/categories`);
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as BlogCategoryItem[];
}

export async function fetchNextBlogTopic(): Promise<NextTopicResponse | null> {
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/next-topic`);
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as NextTopicResponse;
}

export async function fetchAdminBlogPosts(): Promise<AdminBlogListItem[] | null> {
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/posts`);
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as AdminBlogListItem[];
}

export async function fetchAdminBlogPost(id: string): Promise<AdminBlogPost | null> {
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/posts/${id}`);
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as AdminBlogPost;
}
