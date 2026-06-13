'use client';

import { useActionState } from 'react';

import { Button } from '@/components/ui/button';

import { saveLandingPageAction, type LandingFormState } from './actions';

const field =
  'border-input bg-background text-foreground focus-visible:ring-ring w-full rounded-xl border px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none';

export type LandingPageRecord = {
  id: string;
  slug: string;
  title: string;
  body: string;
  status: string;
  faq_items: Array<{ q: string; a: string }>;
  internal_links: Array<{ href: string; label: string }>;
};

type Props =
  | { mode: 'create' }
  | { mode: 'edit'; page: LandingPageRecord };

export function LandingPageForm(props: Props) {
  const page = props.mode === 'edit' ? props.page : null;
  const [state, action, pending] = useActionState(saveLandingPageAction, null as LandingFormState);

  return (
    <form action={action} className='space-y-6'>
      {state?.error && (
        <p className='text-destructive text-sm' role='alert'>
          {state.error}
        </p>
      )}
      {page && <input type='hidden' name='id' value={page.id} />}
      <div className='grid gap-6 md:grid-cols-2'>
        <div>
          <label htmlFor='slug' className='text-foreground mb-1.5 block text-sm font-medium'>
            Slug (URL path)
          </label>
          <input
            id='slug'
            name='slug'
            required
            defaultValue={page?.slug}
            placeholder='bank-statement-pdf-to-excel'
            className={field}
          />
        </div>
        <div>
          <label htmlFor='status' className='text-foreground mb-1.5 block text-sm font-medium'>
            Status
          </label>
          <select id='status' name='status' defaultValue={page?.status ?? 'draft'} className={field}>
            <option value='draft'>Draft</option>
            <option value='published'>Published</option>
          </select>
        </div>
        <div className='md:col-span-2'>
          <label htmlFor='title' className='text-foreground mb-1.5 block text-sm font-medium'>
            Title
          </label>
          <input id='title' name='title' required defaultValue={page?.title} className={field} />
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
            defaultValue={page?.body ?? ''}
            className={field}
          />
        </div>
        <div className='md:col-span-2'>
          <label htmlFor='faq_items' className='text-foreground mb-1.5 block text-sm font-medium'>
            FAQ items (JSON array)
          </label>
          <textarea
            id='faq_items'
            name='faq_items'
            rows={6}
            defaultValue={JSON.stringify(page?.faq_items ?? [], null, 2)}
            className={`${field} font-mono text-xs`}
          />
        </div>
        <div className='md:col-span-2'>
          <label
            htmlFor='internal_links'
            className='text-foreground mb-1.5 block text-sm font-medium'>
            Internal links (JSON array)
          </label>
          <textarea
            id='internal_links'
            name='internal_links'
            rows={4}
            defaultValue={JSON.stringify(page?.internal_links ?? [], null, 2)}
            className={`${field} font-mono text-xs`}
          />
        </div>
      </div>
      <Button type='submit' disabled={pending} className='rounded-lg'>
        {pending ? 'Saving…' : 'Save landing page'}
      </Button>
    </form>
  );
}
