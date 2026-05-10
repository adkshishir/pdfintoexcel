'use client';

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

type Props = {
  series: Array<{ date: string; uploads: number }>;
  topPages: Array<{ path: string; visits: number; conversion_rate: number }>;
};

export function AnalyticsClient({ series, topPages }: Props) {
  return (
    <div className='grid gap-4 lg:grid-cols-2'>
      <Card className='shadow-sm lg:col-span-2'>
        <CardHeader>
          <CardTitle className='text-base'>Uploads trend</CardTitle>
        </CardHeader>
        <CardContent className='h-72'>
          <ResponsiveContainer width='100%' height='100%'>
            <LineChart data={series}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis dataKey='date' />
              <YAxis />
              <Tooltip />
              <Line type='monotone' dataKey='uploads' stroke='#AE3200' strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card className='shadow-sm'>
        <CardHeader>
          <CardTitle className='text-base'>Uploads area</CardTitle>
        </CardHeader>
        <CardContent className='h-72'>
          <ResponsiveContainer width='100%' height='100%'>
            <AreaChart data={series}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis dataKey='date' />
              <YAxis />
              <Tooltip />
              <Area type='monotone' dataKey='uploads' stroke='#FF5A1F' fill='#FF5A1F33' />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card className='shadow-sm'>
        <CardHeader>
          <CardTitle className='text-base'>Top pages by visits</CardTitle>
        </CardHeader>
        <CardContent className='h-72'>
          <ResponsiveContainer width='100%' height='100%'>
            <BarChart data={topPages}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis dataKey='path' />
              <YAxis />
              <Tooltip />
              <Bar dataKey='visits' fill='#2E9B3E' />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
