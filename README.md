# Good Morning Murfreesboro

Community news and events website for Murfreesboro, Tennessee. Live every Friday at 7am CT on Facebook and YouTube.

**Website:** [goodmorningmurfreesboro.com](https://goodmorningmurfreesboro.com)

## Tech Stack

- Static HTML/CSS/JS (no framework or build step)
- Hosted on [Vercel](https://vercel.com) with auto-deploy from `main`, fronted by Cloudflare (DNS/CDN)
- YouTube Data API v3 for episode integration
- Google Apps Script + Cloudflare Turnstile for contact form submissions
- Google Workspace for email (hello@goodmorningmurfreesboro.com)

## Local Development

```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Pages

| Page | Path | Description |
|------|------|-------------|
| Home | `/` | Hero, latest YouTube episode, stats, content tiles |
| About | `/about` | Team bios and social links |
| Watch | `/watch` | YouTube episodes via API with fallbacks |
| Events | `/events` | Event calendar (list/grid/month views) |
| Non-Profits | `/nonprofits` | Non-profit partner cards + full directory (32 orgs) |
| Businesses | `/businesses` | Business spotlight cards + full directory (37 businesses) |
| Contact | `/contact` | Guest spot, non-profit, and general contact forms |

## Event Scraper

Automatically pulls events from Eventbrite and City of Murfreesboro:

```bash
pip3 install requests beautifulsoup4
python3 scraper/gmm_scraper.py
```

Output: `events/events.json`

## Deployment

Push to `main` → Vercel auto-deploys. No build command needed. After the deploy completes, purge the Cloudflare cache (Caching → Configuration → Purge Everything) so the edge serves the new HTML.

## Security

- HTTPS enforced with HSTS preload
- Full Content-Security-Policy and security headers served via `vercel.json`
- XSS protection on all dynamic content
- YouTube API key restricted by referrer and API scope
- Honeypot field + Cloudflare Turnstile spam protection on forms
