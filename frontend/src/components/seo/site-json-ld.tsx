import { SUPPORT_EMAIL, SITE_URL } from '@/lib/site-config';

export function SiteJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': `${SITE_URL}/#organization`,
        name: 'pdfintoexcel',
        url: SITE_URL,
        logo: `${SITE_URL}/logo.png`,
        contactPoint: {
          '@type': 'ContactPoint',
          contactType: 'customer support',
          email: SUPPORT_EMAIL,
          availableLanguage: 'English',
        },
      },
      {
        '@type': 'WebSite',
        '@id': `${SITE_URL}/#website`,
        url: SITE_URL,
        name: 'pdfintoexcel',
        publisher: { '@id': `${SITE_URL}/#organization` },
      },
      {
        '@type': 'SoftwareApplication',
        '@id': `${SITE_URL}/#software`,
        name: 'pdfintoexcel',
        applicationCategory: 'BusinessApplication',
        operatingSystem: 'Web',
        browserRequirements: 'Requires JavaScript. Requires HTML5.',
        url: SITE_URL,
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'USD',
        },
        featureList: [
          'PDF into Excel table extraction',
          'OCR for scanned PDFs',
          'Merged cell preservation',
          'Multi-page and full-document export',
          'Bank statement and invoice table extraction',
        ],
        description:
          'Free online tool to convert PDF into Excel with accurate table reconstruction and OCR for scanned documents.',
      },
    ],
  };
  return (
    <script
      type='application/ld+json'
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
