import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { adminGet } from '@/lib/admin-api';

type Suggestion = {
  id: string;
  target_path: string;
  anchor_text: string;
  score: number;
};

export default async function SiteOpsPage() {
  const links = (await adminGet<Suggestion[]>('/admin/site/internal-links')) ?? [];
  const exclusions = (await adminGet<Array<{ id: string; path: string; reason: string | null }>>(
    '/admin/site/sitemap/exclusions',
  )) ?? [];
  return (
    <div className='space-y-4'>
      <h1 className='text-2xl font-bold tracking-tight'>Site Ops</h1>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>Internal linking suggestions</CardTitle>
        </CardHeader>
        <CardContent className='space-y-2 text-sm'>
          {links.length === 0 ? (
            <p className='text-muted-foreground'>No suggestions generated yet.</p>
          ) : (
            links.map((l) => (
              <p key={l.id}>
                {l.anchor_text} {'->'} {l.target_path} ({Math.round(l.score * 100)}%)
              </p>
            ))
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>Sitemap exclusions</CardTitle>
        </CardHeader>
        <CardContent className='space-y-2 text-sm'>
          {exclusions.length === 0 ? (
            <p className='text-muted-foreground'>No exclusions.</p>
          ) : (
            exclusions.map((e) => (
              <p key={e.id}>
                {e.path} {e.reason ? `- ${e.reason}` : ''}
              </p>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
