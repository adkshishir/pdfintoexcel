import { ExceflowSiteFooter } from '@/components/exceflow/exceflow-site-footer';
import { ExceflowSiteHeader } from '@/components/exceflow/exceflow-site-header';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <ExceflowSiteHeader />
      <div className='flex-1 pt-16'>{children}</div>
      <ExceflowSiteFooter />
    </>
  );
}
