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
}: {
  pathname: string;
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <>
      {HEADER_NAV_ITEMS.map((item) => {
        const active = isNavActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              'text-sm transition-colors duration-200',
              active
                ? 'text-primary font-semibold'
                : 'text-muted-foreground hover:text-foreground font-medium',
              className,
            )}>
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

export function SiteHeaderNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <nav className='hidden items-center gap-6 md:flex lg:gap-8'>
        <NavLinks pathname={pathname} />
      </nav>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            type='button'
            variant='ghost'
            size='icon'
            className='md:hidden'
            aria-label='Open menu'>
            <Menu className='size-5' />
          </Button>
        </SheetTrigger>
        <SheetContent side='right' className='flex flex-col gap-6'>
          <SheetHeader>
            <SheetTitle>Menu</SheetTitle>
          </SheetHeader>
          <nav className='flex flex-col gap-4'>
            <NavLinks
              pathname={pathname}
              onNavigate={() => setOpen(false)}
              className='py-1 text-base'
            />
          </nav>
        </SheetContent>
      </Sheet>
    </>
  );
}
