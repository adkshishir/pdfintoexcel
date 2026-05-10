import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        disallow: ['/'],
        // disallow: ['/dashboard', '/dashboard/*', '/admin', '/admin/*', '/api', '/api/*'],
      },
    ],
    sitemap: 'https://pdfintoexcel.com/sitemap.xml',
  };
}
