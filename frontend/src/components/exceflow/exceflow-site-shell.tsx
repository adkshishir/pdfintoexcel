import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';
import { cn } from '@/lib/utils';

type ExceflowSiteShellProps = {
  children: React.ReactNode;
  /** When false, children fill the shell without extra main padding (e.g. full-bleed home hero). */
  mainClassName?: string;
  className?: string;
};

export function ExceflowSiteShell({
  children,
  mainClassName,
  className,
}: ExceflowSiteShellProps) {
  return (
    <div className={cn('flex min-h-screen flex-col', className)}>
      <ExceflowSiteHeader />
      <main className={cn('flex-1 pt-16', mainClassName)}>{children}</main>
      <ExceflowSiteFooter />
    </div>
  );
}
