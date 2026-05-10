import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const ACCESS_COOKIE = 'pf_admin_access_token';
const REFRESH_COOKIE = 'pf_admin_refresh_token';

export function middleware(request: NextRequest) {
  const token = request.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!token && !refresh) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard', '/dashboard/:path*'],
};
