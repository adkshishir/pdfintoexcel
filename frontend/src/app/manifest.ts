import type { MetadataRoute } from 'next';

import { SITE_NAME, SITE_URL } from '@/lib/site-config';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: SITE_NAME,
    short_name: SITE_NAME,
    description: 'Convert PDF into Excel with accurate table extraction and OCR.',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#107C41',
    icons: [
      {
        src: '/icon.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
    ],
    id: SITE_URL,
  };
}
