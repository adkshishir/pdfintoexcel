import Link from 'next/link';
import { notFound } from 'next/navigation';

import { LandingPageForm, type LandingPageRecord } from '@/app/dashboard/landing-pages/landing-page-form';
import { adminGet } from '@/lib/admin-api';

type Props = { params: Promise<{ id: string }> };

export default async function EditLandingPage({ params }: Props) {
  const { id } = await params;
  const page = await adminGet<LandingPageRecord>(`/admin/landing-pages/${id}`);
  if (!page) notFound();

  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-2xl font-bold tracking-tight'>Edit landing page</h1>
          <p className='text-muted-foreground text-sm'>
            Public URL:{' '}
            <Link href={`/${page.slug}`} className='text-primary hover:underline' target='_blank'>
              /{page.slug}
            </Link>
          </p>
        </div>
        <Link href='/dashboard/landing-pages' className='text-primary text-sm hover:underline'>
          Back to list
        </Link>
      </div>
      <LandingPageForm mode='edit' page={page} />
    </div>
  );
}
