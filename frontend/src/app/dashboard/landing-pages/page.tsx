import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { adminGet } from '@/lib/admin-api';

type Landing = { id: string; slug: string; title: string; status: string; updated_at: string };

export default async function LandingPagesDashboardPage() {
  const pages = (await adminGet<Landing[]>('/admin/landing-pages')) ?? [];
  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <h1 className='text-2xl font-bold tracking-tight'>Landing Pages</h1>
        <div className='flex gap-2'>
          <Button asChild variant='outline' className='rounded-lg'>
            <Link href='/dashboard/site'>Internal link suggestions</Link>
          </Button>
          <Button asChild className='rounded-lg'>
            <Link href='/dashboard/landing-pages/new'>New landing page</Link>
          </Button>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>SEO pages</CardTitle>
        </CardHeader>
        <CardContent>
          {pages.length === 0 ? (
            <p className='text-muted-foreground text-sm'>No landing pages yet.</p>
          ) : (
            <ul className='space-y-2 text-sm'>
              {pages.map((p) => (
                <li key={p.id} className='flex items-center justify-between rounded-lg border p-2'>
                  <span>
                    <Link href={`/${p.slug}`} className='text-primary hover:underline' target='_blank'>
                      /{p.slug}
                    </Link>{' '}
                    — {p.title}
                  </span>
                  <span className='flex items-center gap-3'>
                    <span className='text-muted-foreground'>{p.status}</span>
                    <Link
                      href={`/dashboard/landing-pages/${p.id}/edit`}
                      className='text-primary font-medium hover:underline'>
                      Edit
                    </Link>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
