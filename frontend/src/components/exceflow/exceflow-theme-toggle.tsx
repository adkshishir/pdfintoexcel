'use client';

import { startTransition, useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

import { Button } from '@/components/ui/button';

export function ExceflowThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    startTransition(() => {
      setMounted(true);
    });
  }, []);

  if (!mounted) {
    return (
      <div
        className='size-9 shrink-0'
        aria-hidden
      />
    );
  }

  const isDark = resolvedTheme === 'dark';

  return (
    <Button
      type='button'
      variant='ghost'
      size='icon'
      className='text-muted-foreground hover:text-foreground size-9 shrink-0'
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}>
      {isDark ? (
        <Sun className='size-[1.15rem]' strokeWidth={1.75} />
      ) : (
        <Moon className='size-[1.15rem]' strokeWidth={1.75} />
      )}
    </Button>
  );
}
