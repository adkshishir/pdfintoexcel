'use client';

import { useEffect, useRef } from 'react';

import type { ConverterJob } from '@/lib/converter-types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

function jobWebSocketUrl(jobId: string): string {
  if (typeof window === 'undefined') return '';
  const base = API_BASE.startsWith('http')
    ? API_BASE
    : `${window.location.origin}${API_BASE}`;
  const parsed = new URL(base, window.location.origin);
  parsed.protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
  parsed.pathname = `${parsed.pathname.replace(/\/$/, '')}/jobs/${jobId}/ws`;
  parsed.search = '';
  parsed.hash = '';
  return parsed.toString();
}

const TERMINAL = new Set(['completed', 'failed']);

export function useJobWebSocket(
  jobId: string | undefined,
  enabled: boolean,
  callbacks: {
    onUpdate: (job: ConverterJob) => void;
    onTerminal: (job: ConverterJob) => void;
    onError: (message: string) => void;
  },
) {
  const callbacksRef = useRef(callbacks);

  useEffect(() => {
    callbacksRef.current = callbacks;
  });

  useEffect(() => {
    if (!enabled || !jobId) return;

    const generation = Symbol('ws-gen');
    let activeGeneration: symbol | null = generation;
    let ws: WebSocket | null = null;
    let closed = false;

    function cleanupSocket(code = 1000, reason = 'unmount') {
      if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
        return;
      }
      closed = true;
      try {
        ws.close(code, reason);
      } catch {
        /* ignore */
      }
    }

    async function restFallback() {
      try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        if (!res.ok) return;
        const job = (await res.json()) as ConverterJob;
        if (activeGeneration !== generation) return;
        callbacksRef.current.onUpdate(job);
        if (TERMINAL.has(job.status)) {
          callbacksRef.current.onTerminal(job);
        }
      } catch {
        /* ignore */
      }
    }

    const url = jobWebSocketUrl(jobId);
    if (!url) return;

    try {
      ws = new WebSocket(url);
    } catch (e) {
      void restFallback();
      callbacksRef.current.onError(
        e instanceof Error ? e.message : 'WebSocket connection failed',
      );
      return;
    }

    ws.onmessage = (ev) => {
      if (activeGeneration !== generation) return;
      try {
        const job = JSON.parse(String(ev.data)) as ConverterJob;
        callbacksRef.current.onUpdate(job);
        if (TERMINAL.has(job.status)) {
          closed = true;
          callbacksRef.current.onTerminal(job);
          cleanupSocket(1000, 'done');
        }
      } catch {
        callbacksRef.current.onError('Invalid job update from server');
      }
    };

    ws.onerror = () => {
      if (activeGeneration !== generation || closed) return;
      void restFallback();
    };

    ws.onclose = (ev) => {
      if (activeGeneration !== generation || closed) return;
      if (ev.code !== 1000) {
        void restFallback();
      }
    };

    return () => {
      activeGeneration = null;
      cleanupSocket(1000, 'unmount');
    };
  }, [jobId, enabled]);
}
