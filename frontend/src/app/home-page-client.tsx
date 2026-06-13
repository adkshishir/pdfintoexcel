'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Check, Shield } from 'lucide-react';

import {
  ConverterFlowProvider,
  useConverterFlow,
} from '@/components/exceflow/converter-flow-context';
import { HeroConverter } from '@/components/exceflow/hero-converter';
import { HOME_FAQ_ITEMS } from '@/lib/home-faq-data';
import { cn } from '@/lib/utils';

function HomePageContent() {
  const [showFaq, setShowFaq] = useState<string | null>(null);
  const { openFilePicker, heroFocused } = useConverterFlow();

  function scrollToConverter() {
    openFilePicker();
  }

  return (
    <>
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
                    {[
                      'No sign-up',
                      'Free to start',
                      'Scanned PDFs (OCR)',
                      'Files deleted in 1 hour',
                    ].map((item) => (
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
                      className='text-foreground hover:border-excel hover:text-excel inline-flex items-center gap-2 rounded-xl border-border border bg-card px-6 py-3 font-semibold transition-colors'>
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

        <section className='border-border border-t border-b bg-background'>
          <div className='mx-auto max-w-6xl px-6 py-12'>
            <div className='grid grid-cols-2 gap-6 md:grid-cols-4'>
              {[
                { num: '3.8', unit: 'M+', label: 'PDFs converted to Excel' },
                { num: '99.4', unit: '%', label: 'Table extraction accuracy' },
                { num: '~6', unit: 's', label: 'Average conversion time' },
                { num: '190', unit: '+', label: 'Countries served' },
              ].map((stat, idx) => (
                <div key={idx} className='text-center'>
                  <div className='text-foreground text-3xl font-bold'>
                    {stat.num}
                    <span className='text-excel'>{stat.unit}</span>
                  </div>
                  <div className='text-muted-foreground mt-1 text-sm'>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id='how' className='bg-background py-20'>
          <div className='mx-auto max-w-6xl px-6'>
            <div className='mb-16 text-center'>
              <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                How it works
              </p>
              <h2 className='text-foreground mt-3 text-3xl font-bold md:text-4xl'>
                Convert a PDF into Excel in three steps
              </h2>
              <p className='text-muted-foreground mt-4 text-lg'>
                No software to install and no learning curve. Upload, convert,
                and download a working spreadsheet.
              </p>
            </div>
            <div className='grid gap-6 md:grid-cols-3'>
              {[
                {
                  num: '01',
                  title: 'Upload your PDF',
                  desc: 'Drag and drop your file or pick it from your device. Native PDFs and scanned documents both work, including multi-page reports.',
                },
                {
                  num: '02',
                  title: 'We detect every table',
                  desc: 'Our engine reads the layout, finds the table borders, and maps each value to the correct row and column, even when cells are merged.',
                },
                {
                  num: '03',
                  title: 'Download your Excel file',
                  desc: 'Get a clean .xlsx (or .csv) with numbers as real numbers, ready to sort, filter, and run formulas on. No retyping.',
                },
              ].map((stepItem, idx) => (
                <div
                  key={idx}
                  className='border-border relative rounded-2xl border bg-card p-6'>
                  {idx < 2 && (
                    <div className='bg-border absolute top-12 -right-3 h-1 w-6' />
                  )}
                  <div className='bg-secondary text-excel mb-4 inline-flex h-9 w-9 items-center justify-center rounded-2xl text-sm font-bold'>
                    {stepItem.num}
                  </div>
                  <h3 className='text-foreground text-lg font-bold'>
                    {stepItem.title}
                  </h3>
                  <p className='text-muted-foreground mt-2 text-sm'>{stepItem.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className='border-border border-t border-b bg-background'>
          <div className='mx-auto max-w-6xl px-6 py-20'>
            <div className='mb-16 text-center'>
              <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                Why we are different
              </p>
              <h2 className='text-foreground mt-3 text-3xl font-bold md:text-4xl'>
                The most accurate way to convert PDF into Excel
              </h2>
              <p className='text-muted-foreground mt-4 text-lg'>
                Most converters dump your PDF into one messy column. We rebuild
                the spreadsheet the way it was meant to look.
              </p>
            </div>
            <div className='grid gap-6 md:grid-cols-3'>
              {[
                {
                  icon: '📋',
                  title: 'True table recognition',
                  desc: 'AI-powered layout analysis keeps rows and columns aligned, so a 40-column financial statement comes out exactly as it went in.',
                },
                {
                  icon: '🔍',
                  title: 'Scanned PDF OCR',
                  desc: 'Built-in optical character recognition turns image-based and scanned PDFs into editable Excel data in over 25 languages.',
                  href: '/scanned-pdf-to-excel',
                },
                {
                  icon: '🔢',
                  title: 'Numbers stay numbers',
                  desc: 'Currencies, percentages, dates and decimals are preserved as real numeric values, so your formulas and totals work immediately.',
                },
                {
                  icon: '📄',
                  title: 'Multi-page and batch',
                  desc: 'Convert a 200-page report or queue multiple PDFs at once. Each page maps to its own sheet so nothing gets jumbled together.',
                },
                {
                  icon: '🔗',
                  title: 'Merged cells handled',
                  desc: 'Spanning headers and merged cells are reconstructed faithfully instead of being flattened into a single broken row.',
                },
                {
                  icon: '🔒',
                  title: 'Private by default',
                  desc: 'Every transfer is encrypted, files are processed in isolation, and everything is automatically deleted within one hour.',
                },
              ].map((feature, idx) => {
                const card = (
                  <div
                    className={cn(
                      'border-border rounded-2xl border bg-card p-6 transition-all hover:border-excel/40 hover:shadow-md',
                      feature.href && 'h-full',
                    )}>
                    <div className='mb-3 text-3xl'>{feature.icon}</div>
                    <h3 className='text-foreground font-bold'>{feature.title}</h3>
                    <p className='text-muted-foreground mt-2 text-sm'>{feature.desc}</p>
                    {feature.href && (
                      <span className='text-excel mt-3 inline-flex items-center gap-1 text-sm font-medium'>
                        Learn more <ArrowRight className='size-3.5' />
                      </span>
                    )}
                  </div>
                );
                return feature.href ? (
                  <Link key={idx} href={feature.href} className='block h-full'>
                    {card}
                  </Link>
                ) : (
                  <div key={idx}>{card}</div>
                );
              })}
            </div>
          </div>
        </section>

        <section id='compare' className='bg-background py-20'>
          <div className='mx-auto max-w-6xl px-6'>
            <div className='mb-12 text-center'>
              <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                PDFintoExcel vs the rest
              </p>
              <h2 className='text-foreground mt-3 text-3xl font-bold md:text-4xl'>
                How we compare to iLovePDF, Smallpdf and Adobe
              </h2>
              <p className='text-muted-foreground mt-4 text-lg'>
                General PDF suites do a bit of everything. We do one thing, PDF
                to Excel, and we do it better.
              </p>
            </div>
            <div className='border-border overflow-x-auto rounded-2xl border shadow-md'>
              <table className='w-full min-w-max text-sm'>
                <thead>
                  <tr className='border-border bg-secondary border-b'>
                    <th className='text-foreground px-6 py-4 text-left font-semibold'>
                      Feature
                    </th>
                    <th className='bg-excel px-6 py-4 text-center font-semibold text-white'>
                      PDFintoExcel
                    </th>
                    <th className='text-foreground px-6 py-4 text-center font-semibold'>
                      iLovePDF
                    </th>
                    <th className='text-foreground px-6 py-4 text-center font-semibold'>
                      Smallpdf
                    </th>
                    <th className='text-foreground px-6 py-4 text-center font-semibold'>
                      Adobe
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      feat: 'Table structure accuracy',
                      us: '99.4%',
                      ilove: 'Basic',
                      small: 'Basic',
                      adobe: 'Good',
                    },
                    {
                      feat: 'Complex / merged-cell tables',
                      us: '✓',
                      ilove: '✗',
                      small: 'Partial',
                      adobe: 'Partial',
                    },
                    {
                      feat: 'Scanned PDF (OCR) to Excel',
                      us: '✓',
                      ilove: 'Paid',
                      small: 'Paid',
                      adobe: '✓',
                    },
                    {
                      feat: 'Numbers stay calculable',
                      us: '✓',
                      ilove: 'Sometimes',
                      small: 'Sometimes',
                      adobe: '✓',
                    },
                    {
                      feat: 'Free conversions without sign-up',
                      us: '✓',
                      ilove: 'Limited',
                      small: '✗',
                      adobe: '✗',
                    },
                    {
                      feat: 'Price to convert',
                      us: 'Free',
                      ilove: 'From $7/mo',
                      small: 'From $9/mo',
                      adobe: 'From $20/mo',
                    },
                  ].map((row, idx) => (
                    <tr
                      key={idx}
                      className='border-border hover:bg-secondary/60 border-b'>
                      <td className='text-foreground px-6 py-4 font-semibold'>
                        {row.feat}
                      </td>
                      <td className='bg-secondary text-excel-dark px-6 py-4 text-center font-semibold'>
                        {row.us}
                      </td>
                      <td className='text-muted-foreground px-6 py-4 text-center'>
                        {row.ilove}
                      </td>
                      <td className='text-muted-foreground px-6 py-4 text-center'>
                        {row.small}
                      </td>
                      <td className='text-muted-foreground px-6 py-4 text-center'>
                        {row.adobe}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className='mt-8 text-center'>
              <button
                type='button'
                onClick={scrollToConverter}
                className='bg-excel hover:bg-excel-dark inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-colors'>
                Try the more accurate converter
                <ArrowRight className='size-5' />
              </button>
            </div>
          </div>
        </section>

        <section className='border-border border-t border-b bg-background'>
          <div className='mx-auto max-w-6xl px-6 py-20'>
            <div className='grid grid-cols-1 gap-12 md:grid-cols-2'>
              <div>
                <div className='mb-8 grid grid-cols-3 gap-2'>
                  <div className='border-border rounded-lg border bg-card p-3'>
                    <div className='border-border text-primary mb-2 flex items-center gap-2 border-b pb-2 text-xs font-semibold'>
                      statement.pdf
                    </div>
                    <div className='text-muted-foreground space-y-1 font-mono text-xs'>
                      <div className='bg-secondary h-2 rounded' />
                      <div className='bg-secondary h-2 rounded' />
                      <div className='bg-secondary h-2 rounded' />
                    </div>
                  </div>
                  <div className='flex items-center justify-center'>
                    <div className='bg-excel flex size-10 items-center justify-center rounded-full text-white'>
                      →
                    </div>
                  </div>
                  <div className='border-border rounded-lg border bg-card p-3'>
                    <div className='border-border text-excel mb-2 flex items-center gap-2 border-b pb-2 text-xs font-semibold'>
                      statement.xlsx
                    </div>
                    <table className='w-full text-xs leading-normal'>
                      <tbody>
                        <tr className='bg-secondary'>
                          <td className='border-border text-excel-dark border px-1 py-0.5 font-bold'>
                            Date
                          </td>
                          <td className='border-border text-excel-dark border px-1 py-0.5 font-bold'>
                            Detail
                          </td>
                          <td className='border-border text-excel-dark border px-1 py-0.5 text-center font-bold'>
                            Amt
                          </td>
                        </tr>
                        <tr>
                          <td className='border-border border px-1 py-0.5'>
                            03 Apr
                          </td>
                          <td className='border-border border px-1 py-0.5'>
                            Invoice
                          </td>
                          <td className='border-border border px-1 py-0.5 text-right'>
                            1,240
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              <div>
                <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                  Accuracy you can trust
                </p>
                <h2 className='text-foreground mt-3 text-3xl font-bold'>
                  A spreadsheet you can actually use, not a cleanup project
                </h2>
                <ul className='mt-8 space-y-6'>
                  {[
                    {
                      icon: '📋',
                      title: 'Columns line up',
                      desc: 'Each value lands in its own cell. No splitting text or fixing alignment by hand.',
                    },
                    {
                      icon: '✓',
                      title: 'Formulas work right away',
                      desc: 'Totals, averages and pivots run on the first try because numbers are stored as numbers.',
                    },
                    {
                      icon: '⏱️',
                      title: 'Hours saved per document',
                      desc: 'A finance report that took 30 minutes to retype is done in under ten seconds.',
                    },
                  ].map((item, idx) => (
                    <li key={idx} className='flex gap-4'>
                      <span className='shrink-0 text-2xl'>{item.icon}</span>
                      <div>
                        <strong className='text-foreground'>{item.title}</strong>
                        <p className='text-muted-foreground mt-1 text-sm'>{item.desc}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className='bg-background py-20'>
          <div className='mx-auto max-w-6xl px-6'>
            <div className='mb-16 text-center'>
              <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                Use cases
              </p>
              <h2 className='text-foreground mt-3 text-3xl font-bold md:text-4xl'>
                What people convert from PDF into Excel
              </h2>
              <p className='text-muted-foreground mt-4 text-lg'>
                If your PDF has tables, we turn them into a usable spreadsheet.
                These are the documents we see most.
              </p>
            </div>
            <div className='grid gap-6 md:grid-cols-3'>
              {[
                {
                  icon: '🏦',
                  title: 'Bank statements',
                  desc: 'Convert monthly statements into Excel for bookkeeping, reconciliation and expense tracking.',
                  href: '/bank-statement-pdf-to-excel',
                },
                {
                  icon: '📋',
                  title: 'Invoices and receipts',
                  desc: 'Pull line items, quantities and totals out of supplier invoices and into your accounting sheet.',
                  href: '/invoice-pdf-to-excel',
                },
                {
                  icon: '📊',
                  title: 'Financial reports',
                  desc: 'Move balance sheets and P&L tables into Excel to model, chart and analyse the numbers.',
                },
                {
                  icon: '👥',
                  title: 'Contact and CRM lists',
                  desc: 'Extract directories, attendee lists and contact tables into clean rows for import.',
                },
                {
                  icon: '📦',
                  title: 'Inventory and price lists',
                  desc: 'Turn catalogues and stock sheets into editable tables for pricing updates and uploads.',
                },
                {
                  icon: '🔬',
                  title: 'Research and lab data',
                  desc: 'Convert scientific tables and survey results so you can run stats without manual entry.',
                  href: '/research-data-pdf-to-excel',
                },
              ].map((usecase, idx) => {
                const card = (
                  <div
                    className={cn(
                      'border-border rounded-2xl border bg-card p-6 transition-all hover:border-excel/50 hover:shadow-md',
                      usecase.href && 'h-full',
                    )}>
                    <div className='mb-3 text-3xl'>{usecase.icon}</div>
                    <h3 className='text-foreground font-bold'>{usecase.title}</h3>
                    <p className='text-muted-foreground mt-2 text-sm'>{usecase.desc}</p>
                    {usecase.href && (
                      <span className='text-excel mt-3 inline-flex items-center gap-1 text-sm font-medium'>
                        Learn more <ArrowRight className='size-3.5' />
                      </span>
                    )}
                  </div>
                );
                return usecase.href ? (
                  <Link key={idx} href={usecase.href} className='block h-full'>
                    {card}
                  </Link>
                ) : (
                  <div key={idx}>{card}</div>
                );
              })}
            </div>
          </div>
        </section>

        <section className='bg-excel-dark py-20'>
          <div className='mx-auto max-w-6xl px-6'>
            <div className='mb-16 text-center'>
              <p className='font-mono text-xs font-semibold tracking-widest text-[var(--lime)] uppercase'>
                Security and privacy
              </p>
              <h2 className='mt-3 text-3xl font-bold text-white md:text-4xl'>
                Your data leaves no trace
              </h2>
              <p className='mt-4 text-lg text-gray-300'>
                Financial documents and personal records deserve real protection.
                Here is exactly what we do.
              </p>
            </div>
            <div className='grid gap-8 md:grid-cols-3'>
              {[
                {
                  icon: '🔐',
                  title: 'Encrypted end to end',
                  desc: 'Every upload and download runs over 256-bit TLS, so files are unreadable in transit.',
                },
                {
                  icon: '🗑️',
                  title: 'Auto-deleted in 1 hour',
                  desc: 'Your PDF and the Excel output are permanently erased from our servers within 60 minutes.',
                },
                {
                  icon: '🛡️',
                  title: 'No account, no tracking',
                  desc: 'Convert without signing up. We never read, sell, or train models on your documents.',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className='rounded-2xl border border-white/10 bg-white/5 p-8'>
                  <div className='mb-4 text-3xl'>{item.icon}</div>
                  <h3 className='mb-2 font-bold text-white'>{item.title}</h3>
                  <p className='text-sm text-gray-300'>{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className='border-border border-t border-b bg-background py-20'>
          <div className='mx-auto max-w-6xl px-6'>
            <div className='grid gap-12 md:grid-cols-2'>
              <div>
                <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                  Step-by-step guide
                </p>
                <h2 className='text-foreground mt-3 text-3xl font-bold'>
                  How to convert a PDF into Excel
                </h2>
                <ol className='mt-8 space-y-6'>
                  {[
                    {
                      title: 'Open the converter',
                      desc: 'Use the converter at the top of this page. Nothing to download or install — it runs in your browser.',
                    },
                    {
                      title: 'Add your PDF file',
                      desc: 'Drag the file onto the drop zone or click to browse. You can add a native or scanned PDF up to 50 MB.',
                    },
                    {
                      title: 'Let the engine map the tables',
                      desc: 'We scan the document, detect every table, and rebuild the row and column structure automatically.',
                    },
                    {
                      title: 'Choose your output',
                      desc: 'Select Excel (.xlsx) to keep formatting and sheets, or .csv for a plain data export.',
                    },
                    {
                      title: 'Download and open',
                      desc: 'Save the file and open it in Excel, Numbers or Google Sheets. Your data is ready to sort and calculate.',
                    },
                  ].map((stepItem, idx) => (
                    <li key={idx} className='flex gap-4'>
                      <span className='bg-excel inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white'>
                        {idx + 1}
                      </span>
                      <div>
                        <h3 className='text-foreground font-semibold'>
                          {stepItem.title}
                        </h3>
                        <p className='text-muted-foreground mt-1 text-sm'>{stepItem.desc}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div className='border-border bg-secondary sticky top-24 h-fit rounded-2xl border p-8'>
                <h3 className='text-foreground mb-4 text-lg font-bold'>
                  Tips for the cleanest result
                </h3>
                <ul className='space-y-3'>
                  {[
                    'Use the original PDF rather than a phone photo when you can, for sharper text recognition.',
                    'For scanned files, make sure the page is straight and the table lines are visible.',
                    'Choose .xlsx if you need multiple sheets, and .csv if you are importing into another system.',
                    'Open Advanced in the converter for OCR language and full-document export.',
                  ].map((tip, idx) => (
                    <li key={idx} className='flex gap-3'>
                      <Check className='text-excel size-5 shrink-0' />
                      <span className='text-foreground text-sm'>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section id='faq' className='bg-background py-20'>
          <div className='mx-auto max-w-2xl px-6'>
            <div className='mb-12 text-center'>
              <p className='text-excel font-mono text-xs font-semibold tracking-widest uppercase'>
                FAQ
              </p>
              <h2 className='text-foreground mt-3 text-3xl font-bold'>
                Questions about converting PDF into Excel
              </h2>
            </div>
            <div className='space-y-3'>
              {HOME_FAQ_ITEMS.map((faq, idx) => (
                <details
                  key={idx}
                  open={showFaq === idx.toString()}
                  onToggle={() =>
                    setShowFaq(showFaq === idx.toString() ? null : idx.toString())
                  }
                  className='border-border group overflow-hidden rounded-xl border'>
                  <summary className='text-foreground hover:bg-secondary flex cursor-pointer items-center justify-between px-6 py-4 font-semibold'>
                    {faq.q}
                    <span className='size-5 transition-transform group-open:rotate-90'>
                      +
                    </span>
                  </summary>
                  <div className='border-border text-muted-foreground border-t bg-card px-6 py-4 text-sm'>
                    {faq.a}
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className='from-excel to-excel-dark bg-gradient-to-br py-24'>
          <div className='mx-auto max-w-2xl px-6 text-center'>
            <h2 className='text-4xl font-bold text-white md:text-5xl'>
              Convert your first PDF into Excel now
            </h2>
            <p className='mt-6 text-lg text-white/90'>
              Drop in a file and see the difference accurate table recognition
              makes. No sign-up, no software, no cleanup.
            </p>
            <button
              type='button'
              onClick={scrollToConverter}
              className='text-excel-dark hover:bg-secondary mt-8 inline-flex items-center gap-2 rounded-xl bg-card px-8 py-4 font-semibold transition-colors'>
              <ArrowRight className='size-5' />
              Upload your PDF
            </button>
            <p className='mt-6 text-sm text-white/80'>
              Free to start · Files deleted in 1 hour · 256-bit encryption
            </p>
          </div>
        </section>
    </>
  );
}

export function HomePageClient() {
  return (
    <ConverterFlowProvider>
      <HomePageContent />
    </ConverterFlowProvider>
  );
}
