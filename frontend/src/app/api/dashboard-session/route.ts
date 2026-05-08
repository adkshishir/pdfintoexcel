import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const COOKIE = 'pf_dashboard_session';

export async function POST(request: Request) {
  const secret = process.env.DASHBOARD_SESSION_SECRET;
  const expectedPassword = process.env.DASHBOARD_PASSWORD;
  if (!secret || !expectedPassword) {
    return NextResponse.json(
      { ok: false, error: 'Dashboard auth is not configured.' },
      { status: 503 },
    );
  }

  let body: { password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 });
  }

  if (body.password !== expectedPassword) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }

  const cookieStore = await cookies();
  cookieStore.set(COOKIE, secret, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
  });

  return NextResponse.json({ ok: true });
}
