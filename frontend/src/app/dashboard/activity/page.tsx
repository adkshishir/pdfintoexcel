import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { adminGet } from '@/lib/admin-api';

type LogRow = {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string | null;
  created_at: string;
};

export default async function ActivityPage() {
  const logs = (await adminGet<LogRow[]>('/admin/audit-logs')) ?? [];
  return (
    <div className='space-y-4'>
      <h1 className='text-2xl font-bold tracking-tight'>Activity logs</h1>
      <Card>
        <CardHeader>
          <CardTitle className='text-base'>Recent changes</CardTitle>
        </CardHeader>
        <CardContent className='space-y-3 text-sm'>
          {logs.length === 0 ? (
            <p className='text-muted-foreground'>No changes recorded yet.</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className='border-b pb-2 last:border-0'>
                <p className='font-medium'>
                  {log.action} - {log.entity_type}:{log.entity_id}
                </p>
                <p className='text-muted-foreground'>{log.summary ?? 'No summary'}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
