'use server';

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { analyticsHeaders, getAnalyticsKey, getInternalApiBase } from '@/lib/internal-api';

export type BlogFormState = { error?: string } | null;

async function assertDashboardSession(): Promise<void> {
  const jar = await cookies();
  const expected = process.env.DASHBOARD_SESSION_SECRET;
  if (!expected || jar.get('pf_dashboard_session')?.value !== expected) {
    throw new Error('Unauthorized');
  }
}

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
    meta_description: String(formData.get('meta_description') ?? '').trim(),
    body: String(formData.get('body') ?? ''),
    published: formData.get('published') === 'on',
    og_title: emptyToNull(formData.get('og_title')),
    og_description: emptyToNull(formData.get('og_description')),
    og_image_url: emptyToNull(formData.get('og_image_url')),
    canonical_path: emptyToNull(formData.get('canonical_path')),
    keywords: emptyToNull(formData.get('keywords')),
  };
}

export async function createBlogPostAction(
  _prev: BlogFormState,
  formData: FormData,
): Promise<BlogFormState> {
  await assertDashboardSession();
  const key = getAnalyticsKey();
  if (!key) {
    return { error: 'ANALYTICS_API_KEY is not set on the Next.js server.' };
  }
  const payload = payloadFromForm(formData);
  const res = await fetch(`${getInternalApiBase()}/admin/blog/posts`, {
    method: 'POST',
    headers: analyticsHeaders(key),
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
  await assertDashboardSession();
  const id = String(formData.get('id') ?? '');
  if (!id) {
    return { error: 'Missing post id.' };
  }
  const key = getAnalyticsKey();
  if (!key) {
    return { error: 'ANALYTICS_API_KEY is not set on the Next.js server.' };
  }
  const payload = payloadFromForm(formData);
  const res = await fetch(`${getInternalApiBase()}/admin/blog/posts/${id}`, {
    method: 'PUT',
    headers: analyticsHeaders(key),
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

export async function deleteBlogPostAction(formData: FormData): Promise<void> {
  await assertDashboardSession();
  const id = String(formData.get('id') ?? '');
  if (!id) {
    throw new Error('Missing post id.');
  }
  const key = getAnalyticsKey();
  if (!key) {
    throw new Error('ANALYTICS_API_KEY missing');
  }
  const res = await fetch(`${getInternalApiBase()}/admin/blog/posts/${id}`, {
    method: 'DELETE',
    headers: { 'X-Analytics-Key': key },
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  revalidatePath('/blog');
  revalidatePath('/dashboard/blog');
  redirect('/dashboard/blog');
}
