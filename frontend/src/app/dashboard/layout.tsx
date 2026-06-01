import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import type { ReactNode } from 'react';

import { getAdminSession } from '@/lib/admin-auth';

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const session = await getAdminSession();
  if (!session) {
    redirect('/');
  }
  return (
    <div className='bg-background min-h-screen'>
      <div className='mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 md:grid-cols-[220px_minmax(0,1fr)]'>
        <aside className='border-border bg-card h-fit rounded-xl border p-3'>
          <p className='text-foreground mb-3 text-sm font-semibold'>pdfintoexcel admin</p>
          <nav className='space-y-1 text-sm'>
            <NavLink href='/dashboard'>Analytics</NavLink>
            <NavLink href='/dashboard/blog'>Blog</NavLink>
            <NavLink href='/dashboard/seo'>SEO</NavLink>
            <NavLink href='/dashboard/landing-pages'>Landing Pages</NavLink>
            <NavLink href='/dashboard/site'>Site Ops</NavLink>
            <NavLink href='/dashboard/activity'>Activity</NavLink>
          </nav>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}

function NavLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className='text-muted-foreground hover:text-foreground block rounded-md px-2 py-1.5'>
      {children}
    </Link>
  );
}
