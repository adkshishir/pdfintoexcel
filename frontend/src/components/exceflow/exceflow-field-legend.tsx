import { cn } from '@/lib/utils';

export function ExceflowFieldLegend({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'text-muted-foreground mb-2 block text-xs font-semibold uppercase tracking-wider',
        className,
      )}>
      {children}
    </span>
  );
}
