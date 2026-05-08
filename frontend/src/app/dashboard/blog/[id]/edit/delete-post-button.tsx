'use client';

import { Button } from '@/components/ui/button';

import { deleteBlogPostAction } from '../../actions';

export function DeletePostButton({ postId }: { postId: string }) {
  return (
    <form
      className='mt-4'
      action={deleteBlogPostAction}
      onSubmit={(e) => {
        if (!confirm('Delete this post permanently?')) {
          e.preventDefault();
        }
      }}>
      <input type='hidden' name='id' value={postId} />
      <Button
        type='submit'
        variant='outline'
        className='rounded-xl border-destructive/50 text-destructive hover:border-destructive hover:bg-destructive/10'>
        Delete post
      </Button>
    </form>
  );
}
