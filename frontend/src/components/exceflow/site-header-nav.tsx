'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

const navItems = [
  { label: 'Convert', href: '/' },
  { label: 'Blog', href: '/blog' },
  { label: 'About', href: '/about' },
  { label: 'Contact', href: '/contact' },
] as const;

export function SiteHeaderNav() {
  const pathname = usePathname();
  return (
    <nav className='hidden items-center gap-6 lg:gap-8 md:flex'>
      {navItems.map((item) => {
        const active =
          item.href === '/'
            ? pathname === '/'
            : pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'text-sm transition-colors duration-200',
              active
                ? 'text-primary border-primary border-b-2 pb-1 font-semibold'
                : 'text-muted-foreground hover:text-foreground font-medium',
            )}>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
