# GA4 setup — pdfintoexcel.com

## 1. Create the property

1. Sign in to [Google Analytics](https://analytics.google.com).
2. **Admin** → **Create** → **Property** → name: `pdfintoexcel`.
3. Set reporting time zone and currency.
4. Create a **Web** data stream for `https://pdfintoexcel.com`.
5. Copy the **Measurement ID** (`G-XXXXXXXXXX`).

## 2. Configure environment

Add to production env (root `.env` or hosting secrets):

```bash
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

Rebuild/restart the frontend container after setting the variable.

The site loads GA4 only when this variable is set. See `frontend/src/components/seo/google-analytics.tsx`.

## 3. Mark conversions

In GA4 → **Admin** → **Events**:

| Event name | When fired | Suggested action |
|------------|------------|------------------|
| `upload_attempt` | User starts PDF conversion | Mark as conversion |
| `conversion_complete` | Job completes successfully | Mark as conversion |

## 4. Connect Search Console

Follow [google-search-console.md](./google-search-console.md) § Link GA4.

## 5. Privacy

The privacy policy (`/privacy`) mentions GA4. Cookie consent banners are optional for many jurisdictions but review with counsel if you target EU traffic.
