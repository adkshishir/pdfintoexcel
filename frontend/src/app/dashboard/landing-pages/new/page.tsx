import Link from 'next/link';

import { LandingPageForm } from '@/app/dashboard/landing-pages/landing-page-form';

export default function NewLandingPage() {
  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <h1 className='text-2xl font-bold tracking-tight'>New landing page</h1>
        <Link href='/dashboard/landing-pages' className='text-primary text-sm hover:underline'>
          Back to list
        </Link>
      </div>
      <LandingPageForm mode='create' />
    </div>
  );
}
