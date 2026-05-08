const siteUrl = 'https://pdfintoexcel.com';

export function SiteJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': `${siteUrl}/#organization`,
        name: 'pdfintoexcel',
        url: siteUrl,
        logo: `${siteUrl}/logo.png`,
      },
      {
        '@type': 'WebSite',
        '@id': `${siteUrl}/#website`,
        url: siteUrl,
        name: 'pdfintoexcel',
        publisher: { '@id': `${siteUrl}/#organization` },
      },
      {
        '@type': 'SoftwareApplication',
        name: 'pdfintoexcel',
        applicationCategory: 'BusinessApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'USD',
        },
        description:
          'Convert PDF to Excel with structure preservation. Tables, scans, and full-document export.',
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
