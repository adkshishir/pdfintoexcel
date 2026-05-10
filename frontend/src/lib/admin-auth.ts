import 'server-only';

import { cookies } from 'next/headers';

import { getInternalApiBase } from '@/lib/internal-api';

const ACCESS_COOKIE = 'pf_admin_access_token';
const REFRESH_COOKIE = 'pf_admin_refresh_token';

export async function getAccessToken(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(ACCESS_COOKIE)?.value ?? null;
}

export async function setSessionTokens(accessToken: string, refreshToken: string): Promise<void> {
  const jar = await cookies();
  const secure = process.env.NODE_ENV === 'production';
  jar.set(ACCESS_COOKIE, accessToken, {
    httpOnly: true,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 30,
  });
  jar.set(REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 14,
  });
}

export async function clearSessionTokens(): Promise<void> {
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
}

export async function refreshAccessToken(): Promise<string | null> {
  const jar = await cookies();
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  if (!refresh) {
    return null;
  }
  const res = await fetch(`${getInternalApiBase()}/admin/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
    cache: 'no-store',
  });
  if (!res.ok) {
    await clearSessionTokens();
    return null;
  }
  const data = (await res.json()) as {
    access_token: string;
    refresh_token: string;
  };
  await setSessionTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function adminFetch(input: string, init?: RequestInit): Promise<Response> {
  let access = await getAccessToken();
  if (!access) {
    access = await refreshAccessToken();
  }
  if (!access) {
    return new Response('Unauthorized', { status: 401 });
  }
  const headers = new Headers(init?.headers ?? {});
  headers.set('Authorization', `Bearer ${access}`);
  headers.set('Content-Type', headers.get('Content-Type') ?? 'application/json');
  let res = await fetch(input, { ...init, headers, cache: 'no-store' });
  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      return res;
    }
    headers.set('Authorization', `Bearer ${refreshed}`);
    res = await fetch(input, { ...init, headers, cache: 'no-store' });
  }
  return res;
}

type AdminSession = {
  id: string;
  email: string;
  roles: string[];
};

export async function getAdminSession(): Promise<AdminSession | null> {
  const res = await adminFetch(`${getInternalApiBase()}/admin/auth/me`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as AdminSession;
}
