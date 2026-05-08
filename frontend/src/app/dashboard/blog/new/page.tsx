import Link from 'next/link';

import { Button } from '@/components/ui/button';

import { BlogPostForm } from '../blog-post-form';

export default function NewBlogPostPage() {
  return (
    <div className='bg-background min-h-screen px-4 py-10 sm:px-6'>
      <div className='mx-auto max-w-3xl'>
        <div className='mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div>
            <h1 className='text-foreground text-2xl font-bold tracking-tight'>New post</h1>
            <p className='text-muted-foreground mt-1 text-sm'>
              Content and SEO fields are saved to the API.
            </p>
          </div>
          <Button variant='outline' className='rounded-xl' asChild>
            <Link href='/dashboard/blog'>All posts</Link>
          </Button>
        </div>
        <BlogPostForm mode='create' />
      </div>
    </div>
  );
}
