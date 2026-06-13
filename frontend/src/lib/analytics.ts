declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

export const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

export function trackEvent(
  eventName: string,
  params?: Record<string, string | number | boolean>,
) {
  if (typeof window === 'undefined' || !GA_MEASUREMENT_ID || !window.gtag) {
    return;
  }
  window.gtag('event', eventName, params);
}

export function trackUploadStart(fileName: string) {
  trackEvent('upload_attempt', {
    event_category: 'converter',
    event_label: fileName.slice(0, 100),
  });
}

export function trackConversionComplete(jobId: string) {
  trackEvent('conversion_complete', {
    event_category: 'converter',
    event_label: jobId,
  });
}
