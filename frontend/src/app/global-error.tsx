'use client';

import Link from 'next/link';
import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const ref = error.digest ? ` Reference: ${error.digest}` : '';

  return (
    <html lang='en'>
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'system-ui, sans-serif',
          background: '#0f1114',
          color: '#f3f4f6',
          padding: 24,
          textAlign: 'center',
        }}>
        <p style={{ color: '#ef4444', fontSize: 14, fontWeight: 600 }}>Critical error</p>
        <h1 style={{ fontSize: 28, marginTop: 8 }}>Something went wrong</h1>
        <p style={{ color: '#9ca3af', maxWidth: 420, fontSize: 14, lineHeight: 1.6, marginTop: 12 }}>
          The application could not load. Please refresh the page or try again later.
          {ref}
        </p>
        <button
          type='button'
          onClick={() => reset()}
          style={{
            marginTop: 24,
            padding: '12px 24px',
            borderRadius: 12,
            border: 'none',
            background: '#107C41',
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer',
          }}>
          Try again
        </button>
        <Link
          href='/'
          style={{ marginTop: 16, color: '#9ca3af', fontSize: 14, display: 'inline-block' }}>
          Go to homepage
        </Link>
      </body>
    </html>
  );
}
