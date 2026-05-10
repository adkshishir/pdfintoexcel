'use client';

import Link from 'next/link';
import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await fetch('/api/dashboard-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setError(res.status === 401 ? 'Invalid credentials.' : 'Unable to sign in.');
        return;
      }
      const from = searchParams.get('from');
      router.replace(from && from.startsWith('/dashboard') ? from : '/dashboard');
      router.refresh();
    } catch {
      setError('Network error.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className='mx-auto w-full max-w-md shadow-md'>
      <CardHeader>
        <CardTitle className='text-xl'>Admin access</CardTitle>
        <CardDescription>Authorized staff only.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className='space-y-4'>
          <div>
            <label htmlFor='dash-email' className='text-foreground mb-1.5 block text-sm font-medium'>
              Email
            </label>
            <input
              id='dash-email'
              type='email'
              autoComplete='username'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className='border-input bg-background text-foreground focus-visible:ring-ring w-full rounded-xl border px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none'
              required
            />
          </div>
          <div>
            <label htmlFor='dash-password' className='text-foreground mb-1.5 block text-sm font-medium'>
              Password
            </label>
            <input
              id='dash-password'
              type='password'
              autoComplete='current-password'
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className='border-input bg-background text-foreground focus-visible:ring-ring w-full rounded-xl border px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none'
              required
            />
          </div>
          {error && (
            <p className='text-destructive text-sm' role='alert'>
              {error}
            </p>
          )}
          <Button type='submit' className='w-full rounded-xl' disabled={busy}>
            {busy ? 'Signing in...' : 'Sign in'}
          </Button>
          <p className='text-center'>
            <Link
              href='/'
              className='text-muted-foreground hover:text-foreground text-sm underline-offset-4 hover:underline'>
              Back to home
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}

export default function HiddenAdminLoginPage() {
  return (
    <div className='bg-muted/30 flex min-h-screen flex-col items-center justify-center px-4 py-16'>
      <Suspense fallback={<div className='text-muted-foreground text-sm'>Loading...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
