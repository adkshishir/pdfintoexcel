import Image from 'next/image';
import Link from 'next/link';

const exceflowFooterLinks = [
  { label: 'Blog', href: '/blog' },
  { label: 'About', href: '/about' },
  { label: 'Contact', href: '/contact' },
  { label: 'Privacy', href: '/privacy' },
  { label: 'Terms', href: '/terms' },
] as const;

export function ExceflowSiteFooter() {
  return (
    <footer className='border-border bg-exceflow-footer mt-auto w-full border-t'>
      <div className='mx-auto flex max-w-6xl flex-col items-center justify-between gap-8 px-4 py-16 text-center sm:px-6 md:flex-row md:items-start md:text-left'>
        <div className='flex flex-col gap-3'>
          <Link href='/' className='inline-flex' aria-label='pdfintoexcel home'>
            <Image
              src='/logo.png'
              alt='pdfintoexcel'
              width={180}
              height={44}
              className='h-7 w-auto max-w-[160px] object-contain object-left opacity-90'
            />
          </Link>
          <p className='text-muted-foreground max-w-xs text-sm leading-relaxed'>
            © {new Date().getFullYear()} pdfintoexcel. Precision PDF-to-Excel
            conversion for teams.
          </p>
        </div>
        <div className='flex flex-wrap justify-center gap-x-8 gap-y-3 md:justify-end'>
          {exceflowFooterLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className='text-muted-foreground hover:text-foreground text-xs font-semibold tracking-wide underline-offset-4 transition-colors hover:underline'>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}
