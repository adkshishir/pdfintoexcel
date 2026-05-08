import 'server-only';

/** FastAPI mount prefix (routes are `/api/...` behind nginx). */
function apiRootFromUrl(raw: string): string {
  const u = raw.replace(/\/+$/, '');
  if (!u.startsWith('http://') && !u.startsWith('https://')) {
    return 'http://127.0.0.1:8000/api';
  }
  return u.endsWith('/api') ? u : `${u}/api`;
}

/**
 * Origin + `/api` for server-side calls to FastAPI.
 * Uses INTERNAL_API_URL when set; otherwise NEXT_PUBLIC_API_BASE_URL if it is absolute;
 * otherwise localhost (relative `/api` in NEXT_PUBLIC is browser-only).
 */
export function getInternalApiBase(): string {
  const internal = process.env.INTERNAL_API_URL?.trim();
  if (internal) {
    return apiRootFromUrl(internal);
  }
  const pub = (process.env.NEXT_PUBLIC_API_BASE_URL ?? '').trim();
  if (pub.startsWith('http://') || pub.startsWith('https://')) {
    return apiRootFromUrl(pub);
  }
  return apiRootFromUrl('http://127.0.0.1:8000');
}

export function getAnalyticsKey(): string | null {
  return process.env.ANALYTICS_API_KEY ?? null;
}

export function analyticsHeaders(key: string): Record<string, string> {
  return {
    'X-Analytics-Key': key,
    'Content-Type': 'application/json',
  };
}
