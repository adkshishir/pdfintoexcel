import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { adminGet } from '@/lib/admin-api';

type Meta = {
  entity_type: string;
  entity_id: string;
  title: string | null;
  description: string | null;
  canonical_url: string | null;
};

export default async function SeoPage() {
  const blogMeta = await adminGet<Meta>('/admin/seo/meta/site/home');
  const blogSchema = await adminGet<{ schema_type: string; payload_json: unknown }>(
    '/admin/seo/schema/site/home',
  );

  return (
    <div className='space-y-4'>
      <h1 className='text-2xl font-bold tracking-tight'>SEO Management</h1>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>Global metadata preview</CardTitle>
        </CardHeader>
        <CardContent className='text-sm'>
          <p>Title: {blogMeta?.title ?? 'Not set'}</p>
          <p>Description: {blogMeta?.description ?? 'Not set'}</p>
          <p>Canonical: {blogMeta?.canonical_url ?? 'Not set'}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>JSON-LD schema preview</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className='bg-muted overflow-x-auto rounded-lg p-3 text-xs'>
            {JSON.stringify(blogSchema?.payload_json ?? {}, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
