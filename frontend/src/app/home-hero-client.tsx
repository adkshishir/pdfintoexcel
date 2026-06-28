'use client';

import { ArrowRight, Check, Shield } from 'lucide-react';

import {
  ConverterFlowProvider,
  useConverterFlow,
} from '@/components/exceflow/converter-flow-context';
import { HeroConverter } from '@/components/exceflow/hero-converter';
import { cn } from '@/lib/utils';

const TRUST_BULLETS = ['No sign-up', 'Free to start', 'Scanned PDFs (OCR)', 'Files deleted in 1 hour'] as const;

function HeroSection() {
  const { openFilePicker, heroFocused } = useConverterFlow();

  return (
    <section
      className='overflow-hidden bg-background'
      style={{
        backgroundImage: `
          radial-gradient(900px 420px at 88% -8%, rgba(24,165,88,0.16), transparent 60%),
          radial-gradient(700px 360px at 4% 8%, rgba(225,75,60,0.07), transparent 55%)
        `,
      }}>
      <div className='mx-auto max-w-6xl px-6 py-16 md:py-20'>
        <div
          className={cn(
            'grid grid-cols-1 gap-12 transition-all duration-300 ease-out',
            heroFocused ? 'mx-auto max-w-xl' : 'md:grid-cols-2',
          )}>
          {!heroFocused && (
            <div>
              <div className='bg-secondary text-secondary-foreground mb-6 inline-flex items-center gap-2 rounded-full border border-border px-3 py-2 text-sm font-semibold'>
                <span className='bg-exceflow-cta size-2 rounded-full' />
                Up to 5x more accurate table extraction
              </div>
              <h1 className='text-foreground text-4xl leading-tight font-bold tracking-tight md:text-5xl'>
                Convert{' '}
                <span className='text-primary relative'>PDF</span>
                <span className='text-excel'> into Excel</span> with the rows,
                columns and numbers intact
              </h1>
              <p className='text-muted-foreground mt-6 max-w-md text-lg'>
                Turn any PDF table into a clean, editable{' '}
                <strong className='text-foreground'>.xlsx spreadsheet</strong>{' '}
                in seconds. Built to read complex tables that other converters
                scramble.
              </p>
              <ul className='mt-6 flex flex-wrap gap-4 gap-y-3'>
                {TRUST_BULLETS.map((item) => (
                  <li
                    key={item}
                    className='text-foreground flex items-center gap-2 text-sm font-medium'>
                    <Check className='text-exceflow-cta size-4' />
                    {item}
                  </li>
                ))}
              </ul>
              <div className='mt-8 flex flex-wrap gap-3'>
                <button
                  type='button'
                  onClick={openFilePicker}
                  className='bg-excel hover:bg-excel-dark inline-flex items-center gap-2 rounded-xl px-6 py-3 font-semibold text-white transition-colors'>
                  <ArrowRight className='size-5' />
                  Upload your PDF
                </button>
                <a
                  href='#how'
                  className='text-foreground hover:border-excel hover:text-excel inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3 font-semibold transition-colors'>
                  See how it works
                </a>
              </div>
              <p className='text-muted-foreground mt-6 flex items-center gap-2 text-xs'>
                <Shield className='text-excel size-4' />
                256-bit TLS encryption. We never store or read your data.
              </p>
            </div>
          )}
          <div className={cn('relative', heroFocused && 'w-full')}>
            <HeroConverter />
          </div>
        </div>
      </div>
    </section>
  );
}

export function HomeHeroClient() {
  return (
    <ConverterFlowProvider>
      <HeroSection />
    </ConverterFlowProvider>
  );
}
