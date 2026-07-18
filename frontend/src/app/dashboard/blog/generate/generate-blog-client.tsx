'use client';

import { useActionState } from 'react';

import type { NextTopicResponse } from '@/app/dashboard/blog/data';
import { generateBlogPostAction, type GenerateBlogState } from '@/app/dashboard/blog/actions';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const field =
  'border-input bg-background text-foreground focus-visible:ring-ring w-full rounded-xl border px-3 py-2 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none';

type Props = {
  nextTopic: NextTopicResponse | null;
};

export function GenerateBlogClient({ nextTopic }: Props) {
  const [state, action, pending] = useActionState(generateBlogPostAction, null as GenerateBlogState);

  return (
    <form action={action} className='space-y-6'>
      {state?.error && (
        <p className='text-destructive text-sm' role='alert'>
          {state.error}
        </p>
      )}

      {nextTopic ? (
        <div className='border-border bg-card rounded-xl border p-5'>
          <p className='text-muted-foreground text-xs font-medium uppercase tracking-wide'>
            Suggested next topic
          </p>
          <h2 className='text-foreground mt-2 text-lg font-semibold'>{nextTopic.topic}</h2>
          <div className='mt-3 flex flex-wrap gap-2'>
            <Badge variant='secondary'>{nextTopic.category_slug}</Badge>
            {nextTopic.is_comparison && <Badge variant='outline'>Comparison</Badge>}
          </div>
          <dl className='text-muted-foreground mt-4 grid gap-2 text-sm sm:grid-cols-2'>
            <div>
              <dt className='font-medium'>Primary keyword</dt>
              <dd>{nextTopic.primary_keyword}</dd>
            </div>
            <div>
              <dt className='font-medium'>Selection rationale</dt>
              <dd className='text-xs leading-relaxed'>{nextTopic.rationale}</dd>
            </div>
          </dl>
        </div>
      ) : (
        <p className='text-muted-foreground text-sm'>
          Could not load the next suggested topic. You can still enter a custom topic below.
        </p>
      )}

      <div>
        <label htmlFor='topic' className='text-foreground mb-1.5 block text-sm font-medium'>
          Custom topic (optional)
        </label>
        <input
          id='topic'
          name='topic'
          placeholder={nextTopic?.topic ?? 'PDFIntoExcel vs Smallpdf: ...'}
          className={field}
        />
        <p className='text-muted-foreground mt-1.5 text-xs'>
          Leave blank to generate the suggested topic. Generation calls the LLM and saves a draft
          for review.
        </p>
      </div>

      <div className='flex flex-wrap gap-3'>
        <Button type='submit' className='rounded-xl' disabled={pending}>
          {pending ? 'Generating draft…' : 'Generate draft'}
        </Button>
        <Button type='button' variant='outline' className='rounded-xl' asChild>
          <Link href='/dashboard/blog'>Cancel</Link>
        </Button>
      </div>
    </form>
  );
}
