import { NextResponse } from 'next/server';

import { clearSessionTokens, setSessionTokens } from '@/lib/admin-auth';
import { getInternalApiBase } from '@/lib/internal-api';

export async function POST(request: Request) {
  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 });
  }
  if (!body.email || !body.password) {
    return NextResponse.json({ ok: false, error: 'Missing credentials.' }, { status: 400 });
  }
  const res = await fetch(`${getInternalApiBase()}/admin/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: body.email, password: body.password }),
    cache: 'no-store',
  });
  if (!res.ok) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const data = (await res.json()) as { access_token: string; refresh_token: string };
  await setSessionTokens(data.access_token, data.refresh_token);
  return NextResponse.json({ ok: true });
}

export async function DELETE() {
  await clearSessionTokens();
  return NextResponse.json({ ok: true });
}
