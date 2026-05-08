'use client';

import { useActionState } from 'react';

import type { AdminBlogPost } from '@/app/dashboard/blog/data';
import { Button } from '@/components/ui/button';

import {
  createBlogPostAction,
  updateBlogPostAction,
  type BlogFormState,
} from './actions';

const field =
  'border-input bg-background text-foreground focus-visible:ring-ring w-full rounded-xl border px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none';

type Props =
  | { mode: 'create' }
  | { mode: 'edit'; post: AdminBlogPost };

export function BlogPostForm(props: Props) {
  const formAction = props.mode === 'create' ? createBlogPostAction : updateBlogPostAction;
  const [state, action, pending] = useActionState(formAction, null as BlogFormState);

  const post = props.mode === 'edit' ? props.post : null;

  return (
    <form action={action} className='space-y-6'>
      {state?.error && (
        <p className='text-destructive text-sm' role='alert'>
          {state.error}
        </p>
      )}
      {post && <input type='hidden' name='id' value={post.id} />}
      <div className='grid gap-6 md:grid-cols-2'>
        <div className='md:col-span-2'>
          <label htmlFor='slug' className='text-foreground mb-1.5 block text-sm font-medium'>
            Slug (URL path)
          </label>
          <input
            id='slug'
            name='slug'
            required
            defaultValue={post?.slug}
            placeholder='my-post-title'
            className={field}
          />
        </div>
        <div className='md:col-span-2'>
          <label htmlFor='title' className='text-foreground mb-1.5 block text-sm font-medium'>
            Title
          </label>
          <input
            id='title'
            name='title'
            required
            defaultValue={post?.title}
            className={field}
          />
        </div>
        <div className='md:col-span-2'>
          <label
            htmlFor='meta_description'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Meta description (SEO)
          </label>
          <textarea
            id='meta_description'
            name='meta_description'
            required
            rows={3}
            defaultValue={post?.meta_description}
            className={field}
          />
        </div>
        <div className='md:col-span-2'>
          <label htmlFor='body' className='text-foreground mb-1.5 block text-sm font-medium'>
            Body (Markdown)
          </label>
          <textarea
            id='body'
            name='body'
            required
            rows={16}
            defaultValue={post?.body}
            className={`${field} font-mono text-xs`}
          />
        </div>
        <div className='md:col-span-2 flex items-center gap-2'>
          <input
            id='published'
            name='published'
            type='checkbox'
            value='on'
            defaultChecked={post?.published ?? false}
            className='border-input size-4 rounded'
          />
          <label htmlFor='published' className='text-foreground text-sm font-medium'>
            Published (visible on the public blog)
          </label>
        </div>
        <div>
          <label htmlFor='og_title' className='text-foreground mb-1.5 block text-sm font-medium'>
            Open Graph title (optional)
          </label>
          <input
            id='og_title'
            name='og_title'
            defaultValue={post?.og_title ?? ''}
            className={field}
          />
        </div>
        <div>
          <label
            htmlFor='og_image_url'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Open Graph image URL
          </label>
          <input
            id='og_image_url'
            name='og_image_url'
            type='url'
            defaultValue={post?.og_image_url ?? ''}
            className={field}
          />
        </div>
        <div className='md:col-span-2'>
          <label
            htmlFor='og_description'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Open Graph description
          </label>
          <textarea
            id='og_description'
            name='og_description'
            rows={2}
            defaultValue={post?.og_description ?? ''}
            className={field}
          />
        </div>
        <div>
          <label
            htmlFor='canonical_path'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Canonical URL (optional)
          </label>
          <input
            id='canonical_path'
            name='canonical_path'
            defaultValue={post?.canonical_path ?? ''}
            placeholder='https://…'
            className={field}
          />
        </div>
        <div>
          <label htmlFor='keywords' className='text-foreground mb-1.5 block text-sm font-medium'>
            Keywords (comma-separated)
          </label>
          <input
            id='keywords'
            name='keywords'
            defaultValue={post?.keywords ?? ''}
            className={field}
          />
        </div>
      </div>
      <div className='flex flex-wrap gap-3'>
        <Button type='submit' className='rounded-xl' disabled={pending}>
          {pending ? 'Saving…' : props.mode === 'create' ? 'Create post' : 'Save changes'}
        </Button>
      </div>
    </form>
  );
}
