/** Public site constants — single source for URLs, contact, and legal dates. */
export const SITE_URL = 'https://pdfintoexcel.com';
export const SITE_NAME = 'pdfintoexcel';

export const SUPPORT_EMAIL = 'hello@pdfintoexcel.com';
export const SECURITY_EMAIL = 'security@pdfintoexcel.com';
export const PARTNERSHIPS_EMAIL = 'partnerships@pdfintoexcel.com';
export const LEGAL_EMAIL = 'legal@pdfintoexcel.com';

export const LEGAL_LAST_UPDATED = 'May 7, 2026';

export const FOOTER_COLUMNS = {
  product: [
    { label: 'Convert PDF to Excel', href: '/' },
    { label: 'Blog', href: '/blog' },
  ],
  company: [
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
  ],
  legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
  ],
} as const;

export const HEADER_NAV_ITEMS = [
  { label: 'Convert', href: '/' },
  { label: 'Blog', href: '/blog' },
  { label: 'About', href: '/about' },
  { label: 'Contact', href: '/contact' },
] as const;
