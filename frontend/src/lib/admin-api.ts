import 'server-only';

import { adminFetch } from '@/lib/admin-auth';
import { getInternalApiBase } from '@/lib/internal-api';

export async function adminGet<T>(path: string): Promise<T | null> {
  const res = await adminFetch(`${getInternalApiBase()}${path}`);
  if (!res.ok) return null;
  return (await res.json()) as T;
}

export async function adminPost<T>(path: string, body: unknown): Promise<T | null> {
  const res = await adminFetch(`${getInternalApiBase()}${path}`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

export async function adminPut<T>(path: string, body: unknown): Promise<T | null> {
  const res = await adminFetch(`${getInternalApiBase()}${path}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}
