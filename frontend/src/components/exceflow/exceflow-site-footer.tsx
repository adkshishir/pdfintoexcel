import Link from 'next/link';

const exceflowFooterLinks = [
  { label: 'Terms of Service', href: '#' },
  { label: 'Privacy Policy', href: '#' },
  { label: 'Contact Support', href: '#' },
  { label: 'Security', href: '#' },
] as const;

export function ExceflowSiteFooter() {
  return (
    <footer className='border-border bg-exceflow-footer mt-12 w-full border-t'>
      <div className='mx-auto flex w-full max-w-[1280px] flex-col items-center justify-between gap-4 px-4 py-8 text-center md:flex-row md:items-start md:px-6 md:text-left'>
        <div className='flex flex-col gap-1'>
          <div className='text-foreground text-xl font-black'>Exceflow PDF</div>
          <p className='text-muted-foreground text-xs'>
            © {new Date().getFullYear()} Exceflow PDF. Precision PDF-to-Excel
            conversion.
          </p>
        </div>
        <div className='flex flex-wrap justify-center gap-x-8 gap-y-2 md:justify-end'>
          {exceflowFooterLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className='text-muted-foreground hover:text-primary text-xs font-semibold tracking-wide underline-offset-4 transition-colors hover:underline'>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}
