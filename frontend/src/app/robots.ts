import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/dashboard',
          '/dashboard/*',
          '/api',
          '/api/*',
          '/auth',
          '/auth/*',
        ],
      },
    ],
    sitemap: 'https://pdfintoexcel.com/sitemap.xml',
  };
}
