import { ExceflowSiteShell } from '@/components/exceflow/exceflow-site-shell';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ExceflowSiteShell>{children}</ExceflowSiteShell>;
}
