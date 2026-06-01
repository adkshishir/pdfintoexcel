import { ImageResponse } from 'next/og';

export const alt = 'pdfintoexcel — PDF to Excel';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: 80,
          background: 'linear-gradient(135deg, #0B5D31 0%, #107C41 45%, #0f1114 100%)',
          color: 'white',
          fontFamily: 'system-ui, sans-serif',
        }}>
        <div
          style={{
            fontSize: 28,
            fontWeight: 600,
            opacity: 0.9,
            marginBottom: 16,
          }}>
          pdfintoexcel
        </div>
        <div style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.15, maxWidth: 900 }}>
          Convert PDF to Excel with tables intact
        </div>
        <div style={{ fontSize: 26, marginTop: 24, opacity: 0.85, maxWidth: 800 }}>
          OCR for scans · No sign-up · Files deleted in 1 hour
        </div>
      </div>
    ),
    { ...size },
  );
}
