# Google Search Console setup — pdfintoexcel.com

## 1. Create property

1. Go to [Google Search Console](https://search.google.com/search-console).
2. Add property **pdfintoexcel.com** (Domain property recommended).

## 2. Verify ownership

**Recommended: DNS TXT record**

1. In GSC, choose **Domain** verification.
2. Copy the TXT record Google provides (`google-site-verification=…`).
3. Add it at your DNS host (registrar or Cloudflare).
4. Wait for propagation (minutes to 48 hours), then click **Verify**.

**Alternative: HTML file**

1. Download Google's verification file.
2. Place it in `frontend/public/` (e.g. `google123.html`).
3. Deploy and confirm `https://pdfintoexcel.com/google123.html` loads.
4. Click **Verify** in GSC.

## 3. Submit sitemap

1. After deploy, open `https://pdfintoexcel.com/sitemap.xml` — confirm 200 OK and URLs listed.
2. In GSC → **Sitemaps** → enter `sitemap.xml` → **Submit**.

## 4. Link GA4 (after GA4 is live)

1. GSC → **Settings** → **Associations**.
2. Link the GA4 property created for pdfintoexcel.com.

## 5. Monthly checks

- **Pages** → indexing status for new blog posts and landing pages
- **Experience** → Core Web Vitals
- **Settings** → Crawl stats for spikes or blocks
