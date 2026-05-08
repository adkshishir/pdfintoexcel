import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const COOKIE = 'pf_dashboard_session';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname.startsWith('/dashboard/login')) {
    return NextResponse.next();
  }

  const token = request.cookies.get(COOKIE)?.value;
  const expected = process.env.DASHBOARD_SESSION_SECRET;
  if (!expected || token !== expected) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard/login';
    url.searchParams.set('from', pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard', '/dashboard/:path*'],
};
