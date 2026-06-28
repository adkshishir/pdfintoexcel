'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

import { adminFetch } from '@/lib/admin-auth';
import { getInternalApiBase } from '@/lib/internal-api';

export type BlogFormState = { error?: string } | null;

function emptyToNull(v: FormDataEntryValue | null): string | null {
  if (v == null || typeof v !== 'string') {
    return null;
  }
  const s = v.trim();
  return s === '' ? null : s;
}

function payloadFromForm(formData: FormData) {
  return {
    slug: String(formData.get('slug') ?? '').trim(),
    title: String(formData.get('title') ?? '').trim(),
    meta_title: emptyToNull(formData.get('meta_title')),
    meta_description: String(formData.get('meta_description') ?? '').trim(),
    body: String(formData.get('body') ?? ''),
    status: String(formData.get('status') ?? 'draft'),
    scheduled_at: emptyToNull(formData.get('scheduled_at')),
    cover_image_url: emptyToNull(formData.get('cover_image_url')),
    category_id: emptyToNull(formData.get('category_id')),
    tag_ids: String(formData.get('tag_ids') ?? '')
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean),
    og_title: emptyToNull(formData.get('og_title')),
    og_description: emptyToNull(formData.get('og_description')),
    og_image_url: emptyToNull(formData.get('og_image_url')),
    canonical_url: emptyToNull(formData.get('canonical_url')),
    robots_directives: emptyToNull(formData.get('robots_directives')),
    keywords: emptyToNull(formData.get('keywords')),
    schema_jsonld: (() => {
      const raw = String(formData.get('schema_jsonld') ?? '').trim();
      if (!raw) return null;
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    })(),
  };
}

export async function createBlogPostAction(
  _prev: BlogFormState,
  formData: FormData,
): Promise<BlogFormState> {
  const payload = payloadFromForm(formData);
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/posts`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return { error: (await res.text()) || res.statusText };
  }
  const data = (await res.json()) as { id: string; slug: string };
  revalidatePath('/blog');
  revalidatePath(`/blog/${data.slug}`);
  revalidatePath('/dashboard/blog');
  redirect(`/dashboard/blog/${data.id}/edit`);
}

export async function updateBlogPostAction(
  _prev: BlogFormState,
  formData: FormData,
): Promise<BlogFormState> {
  const id = String(formData.get('id') ?? '');
  if (!id) {
    return { error: 'Missing post id.' };
  }
  const payload = payloadFromForm(formData);
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/posts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return { error: (await res.text()) || res.statusText };
  }
  const data = (await res.json()) as { slug: string };
  revalidatePath('/blog');
  revalidatePath(`/blog/${data.slug}`);
  revalidatePath('/dashboard/blog');
  redirect(`/dashboard/blog/${id}/edit`);
}

export type GenerateBlogState = { error?: string } | null;

export async function generateBlogPostAction(
  _prev: GenerateBlogState,
  formData: FormData,
): Promise<GenerateBlogState> {
  const topic = String(formData.get('topic') ?? '').trim();
  const body: Record<string, string> = {};
  if (topic) {
    body.topic = topic;
  }
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/generate`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    return { error: (await res.text()) || res.statusText };
  }
  const data = (await res.json()) as {
    post: { id: string; slug: string };
    quality_warnings: string[];
  };
  revalidatePath('/blog');
  revalidatePath('/dashboard/blog');
  const warn = data.quality_warnings.length
    ? `?generated=1&warnings=${encodeURIComponent(data.quality_warnings.join('|'))}`
    : '?generated=1';
  redirect(`/dashboard/blog/${data.post.id}/edit${warn}`);
}

export async function deleteBlogPostAction(formData: FormData): Promise<void> {
  const id = String(formData.get('id') ?? '');
  if (!id) {
    throw new Error('Missing post id.');
  }
  const res = await adminFetch(`${getInternalApiBase()}/admin/blog/posts/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  revalidatePath('/blog');
  revalidatePath('/dashboard/blog');
  redirect('/dashboard/blog');
}
