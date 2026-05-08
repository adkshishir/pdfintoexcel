import Link from 'next/link';
import { notFound } from 'next/navigation';

import { Button } from '@/components/ui/button';

import { fetchAdminBlogPost } from '../../data';
import { BlogPostForm } from '../../blog-post-form';
import { DeletePostButton } from './delete-post-button';

type Props = { params: Promise<{ id: string }> };

export default async function EditBlogPostPage({ params }: Props) {
  const { id } = await params;
  const post = await fetchAdminBlogPost(id);
  if (!post) {
    notFound();
  }

  return (
    <div className='bg-background min-h-screen px-4 py-10 sm:px-6'>
      <div className='mx-auto max-w-3xl'>
        <div className='mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div>
            <h1 className='text-foreground text-2xl font-bold tracking-tight'>Edit post</h1>
            <p className='text-muted-foreground mt-1 text-sm'>
              {post.published ? (
                <Link
                  href={`/blog/${post.slug}`}
                  className='text-primary font-medium underline-offset-4 hover:underline'>
                  View on site
                </Link>
              ) : (
                <span>Draft — not shown on the public blog until published.</span>
              )}
            </p>
          </div>
          <Button variant='outline' className='rounded-xl' asChild>
            <Link href='/dashboard/blog'>All posts</Link>
          </Button>
        </div>
        <BlogPostForm mode='edit' post={post} />
        <div className='border-border mt-12 border-t pt-8'>
          <h2 className='text-foreground text-sm font-semibold'>Danger zone</h2>
          <p className='text-muted-foreground mt-1 text-sm'>
            Deleting removes this post from the database. Public URLs will 404.
          </p>
          <DeletePostButton postId={post.id} />
        </div>
      </div>
    </div>
  );
}
