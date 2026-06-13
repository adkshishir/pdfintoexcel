'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

import { adminFetch } from '@/lib/admin-auth';
import { getInternalApiBase } from '@/lib/internal-api';

export type LandingFormState = { error?: string } | null;

function parseJsonArray(raw: string): unknown[] {
  const trimmed = raw.trim();
  if (!trimmed) return [];
  try {
    const parsed = JSON.parse(trimmed);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function payloadFromForm(formData: FormData) {
  const id = String(formData.get('id') ?? '').trim();
  return {
    ...(id ? { id } : {}),
    slug: String(formData.get('slug') ?? '').trim(),
    title: String(formData.get('title') ?? '').trim(),
    body: String(formData.get('body') ?? ''),
    status: String(formData.get('status') ?? 'draft'),
    faq_items: parseJsonArray(String(formData.get('faq_items') ?? '[]')),
    internal_links: parseJsonArray(String(formData.get('internal_links') ?? '[]')),
  };
}

export async function saveLandingPageAction(
  _prev: LandingFormState,
  formData: FormData,
): Promise<LandingFormState> {
  const payload = payloadFromForm(formData);
  const res = await adminFetch(`${getInternalApiBase()}/admin/landing-pages`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return { error: (await res.text()) || res.statusText };
  }
  const data = (await res.json()) as { id: string; slug: string };
  revalidatePath(`/${data.slug}`);
  revalidatePath('/dashboard/landing-pages');
  redirect(`/dashboard/landing-pages/${data.id}/edit`);
}
