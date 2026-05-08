import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { fetchAdminBlogPosts } from './data';

export const dynamic = 'force-dynamic';

export default async function DashboardBlogListPage() {
  const posts = await fetchAdminBlogPosts();

  return (
    <div className='bg-background min-h-screen px-4 py-10 sm:px-6'>
      <div className='mx-auto max-w-5xl'>
        <div className='mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div>
            <h1 className='text-foreground text-2xl font-bold tracking-tight'>Blog</h1>
            <p className='text-muted-foreground mt-1 text-sm'>
              Create and edit posts and SEO metadata (stored in Postgres).
            </p>
          </div>
          <div className='flex flex-wrap gap-2'>
            <Button variant='outline' className='rounded-xl' asChild>
              <Link href='/dashboard'>Analytics</Link>
            </Button>
            <Button className='rounded-xl' asChild>
              <Link href='/dashboard/blog/new'>New post</Link>
            </Button>
          </div>
        </div>

        {posts == null ? (
          <Card className='border-destructive/30'>
            <CardHeader>
              <CardTitle className='text-lg'>Unable to load posts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className='text-muted-foreground text-sm'>
                Check{' '}
                <code className='text-foreground bg-muted rounded px-1 py-0.5 text-xs'>
                  INTERNAL_API_URL
                </code>{' '}
                and{' '}
                <code className='text-foreground bg-muted rounded px-1 py-0.5 text-xs'>
                  ANALYTICS_API_KEY
                </code>{' '}
                on the Next.js server. They must match the FastAPI service.
              </p>
            </CardContent>
          </Card>
        ) : posts.length === 0 ? (
          <p className='text-muted-foreground text-sm'>
            No posts yet.{' '}
            <Link href='/dashboard/blog/new' className='text-primary font-medium underline-offset-4 hover:underline'>
              Create one
            </Link>
            .
          </p>
        ) : (
          <ul className='space-y-3'>
            {posts.map((p) => (
              <li key={p.id}>
                <Card className='shadow-sm'>
                  <CardHeader className='flex flex-row items-start justify-between gap-4 pb-2'>
                    <div className='min-w-0'>
                      <CardTitle className='text-base'>
                        <Link
                          href={`/dashboard/blog/${p.id}/edit`}
                          className='hover:text-primary transition-colors'>
                          {p.title}
                        </Link>
                      </CardTitle>
                      <p className='text-muted-foreground mt-1 truncate text-sm'>/{p.slug}</p>
                    </div>
                    <div className='flex shrink-0 flex-col items-end gap-1'>
                      {p.published ? (
                        <Badge variant='success' className='rounded-lg'>
                          Live
                        </Badge>
                      ) : (
                        <Badge variant='secondary' className='rounded-lg'>
                          Draft
                        </Badge>
                      )}
                      <span className='text-muted-foreground text-xs'>
                        Updated {p.updated_at?.slice(0, 10) ?? '—'}
                      </span>
                    </div>
                  </CardHeader>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
