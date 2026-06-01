'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { HEADER_NAV_ITEMS } from '@/lib/site-config';
import { cn } from '@/lib/utils';

function isNavActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({
  pathname,
  onNavigate,
  className,
  linkClassName,
}: {
  pathname: string;
  onNavigate?: () => void;
  className?: string;
  linkClassName?: string;
}) {
  return (
    <div className={className}>
      {HEADER_NAV_ITEMS.map((item) => {
        const active = isNavActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              'transition-colors duration-200',
              active
                ? 'text-primary font-semibold'
                : 'text-muted-foreground hover:text-foreground font-medium',
              linkClassName,
            )}>
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}

export function SiteHeaderNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className='flex items-center'>
      {/* Desktop */}
      <nav
        className='hidden items-center gap-6 md:flex lg:gap-8'
        aria-label='Main navigation'>
        <NavLinks
          pathname={pathname}
          className='flex items-center gap-6 lg:gap-8'
          linkClassName='text-sm'
        />
      </nav>

      {/* Mobile — hamburger always visible below md */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            type='button'
            variant='outline'
            size='icon'
            className='text-foreground border-border hover:bg-accent flex size-10 shrink-0 md:hidden'
            aria-label='Open navigation menu'
            aria-expanded={open}
            aria-controls='mobile-site-nav'>
            <Menu className='size-5' strokeWidth={2} aria-hidden />
          </Button>
        </SheetTrigger>
        <SheetContent
          id='mobile-site-nav'
          side='right'
          className='flex w-[min(100vw,20rem)] flex-col gap-6'>
          <SheetHeader className='text-left'>
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <nav className='flex flex-col gap-1' aria-label='Mobile navigation'>
            <NavLinks
              pathname={pathname}
              onNavigate={() => setOpen(false)}
              className='flex flex-col gap-1'
              linkClassName='rounded-lg px-3 py-3 text-base'
            />
          </nav>
        </SheetContent>
      </Sheet>
    </div>
  );
}
