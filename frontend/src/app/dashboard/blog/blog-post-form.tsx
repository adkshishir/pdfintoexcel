'use client';

import { useActionState } from 'react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

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
  const [previewBody, setPreviewBody] = useState(post?.body ?? '');

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
        <div>
          <label htmlFor='meta_title' className='text-foreground mb-1.5 block text-sm font-medium'>
            Meta title (optional)
          </label>
          <input id='meta_title' name='meta_title' defaultValue={post?.meta_title ?? ''} className={field} />
        </div>
        <div>
          <label htmlFor='status' className='text-foreground mb-1.5 block text-sm font-medium'>
            Status
          </label>
          <select id='status' name='status' defaultValue={post?.status ?? 'draft'} className={field}>
            <option value='draft'>Draft</option>
            <option value='scheduled'>Scheduled</option>
            <option value='published'>Published</option>
            <option value='archived'>Archived</option>
          </select>
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
        <div className='md:col-span-2 grid gap-4 lg:grid-cols-2'>
          <div>
          <label htmlFor='body' className='text-foreground mb-1.5 block text-sm font-medium'>
            Body (Markdown)
          </label>
          <textarea
            id='body'
            name='body'
            required
            rows={16}
            defaultValue={post?.body}
            onChange={(e) => setPreviewBody(e.target.value)}
            className={`${field} font-mono text-xs`}
          />
          </div>
          <div>
            <p className='text-foreground mb-1.5 block text-sm font-medium'>Live preview</p>
            <div className='border-input prose prose-sm max-w-none rounded-xl border p-3'>
              <ReactMarkdown>{previewBody || '_No content yet_'}</ReactMarkdown>
            </div>
          </div>
        </div>
        <div>
          <label htmlFor='scheduled_at' className='text-foreground mb-1.5 block text-sm font-medium'>
            Scheduled at (UTC, optional)
          </label>
          <input id='scheduled_at' name='scheduled_at' type='datetime-local' className={field} />
        </div>
        <div>
          <label htmlFor='cover_image_url' className='text-foreground mb-1.5 block text-sm font-medium'>
            Cover image URL
          </label>
          <input id='cover_image_url' name='cover_image_url' defaultValue={post?.cover_image_url ?? ''} className={field} />
        </div>
        <div>
          <label htmlFor='category_id' className='text-foreground mb-1.5 block text-sm font-medium'>
            Category ID (optional)
          </label>
          <input id='category_id' name='category_id' defaultValue={post?.category_id ?? ''} className={field} />
        </div>
        <div>
          <label htmlFor='tag_ids' className='text-foreground mb-1.5 block text-sm font-medium'>
            Tag IDs (comma-separated)
          </label>
          <input id='tag_ids' name='tag_ids' defaultValue={post?.tag_ids?.join(',') ?? ''} className={field} />
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
            htmlFor='canonical_url'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Canonical URL (optional)
          </label>
          <input
            id='canonical_url'
            name='canonical_url'
            defaultValue={post?.canonical_url ?? ''}
            placeholder='https://…'
            className={field}
          />
        </div>
        <div>
          <label htmlFor='robots_directives' className='text-foreground mb-1.5 block text-sm font-medium'>
            Robots directives
          </label>
          <input id='robots_directives' name='robots_directives' defaultValue={post?.robots_directives ?? ''} className={field} placeholder='index,follow' />
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
        <div className='md:col-span-2'>
          <label htmlFor='schema_jsonld' className='text-foreground mb-1.5 block text-sm font-medium'>
            Schema JSON-LD
          </label>
          <textarea
            id='schema_jsonld'
            name='schema_jsonld'
            rows={6}
            defaultValue={post?.schema_jsonld ? JSON.stringify(post.schema_jsonld, null, 2) : ''}
            className={`${field} font-mono text-xs`}
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
