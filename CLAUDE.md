# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Good Morning Murfreesboro (goodmorningmurfreesboro.com) — a community news and events website for Murfreesboro, Tennessee. Covers local news, events, non-profits, and local businesses. Live every Friday at 7am CT on Facebook and YouTube.

## Architecture

- **Static site** — plain HTML/CSS/JS with no build step or framework. Use a local server (`python3 -m http.server 8000`) to develop since pages use absolute paths.
- **Single-page structure** — all CSS is inlined in `<style>` within each page's HTML; all JS is inlined in a `<script>` block at the end of `<body>`. No external CSS/JS files.
- **Hosting stack** — Domain registered at GoDaddy. DNS / SSL / CDN / cache at Cloudflare. Site is hosted on Vercel (auto-deploys from GitHub `main` branch). After pushing changes, Cloudflare's edge cache typically needs to be purged (Caching → Configuration → Purge Everything) before updates are visible.
- **Domain** — goodmorningmurfreesboro.com (HTTPS enforced, non-www redirects to www).
- **Forms** — Contact forms (guest-spot, nonprofit-request, general-contact) POST to a Google Apps Script web app (`apps-script/Code.gs` is the source of truth) which verifies a Cloudflare Turnstile token and emails `hello@goodmorningmurfreesboro.com`. The newsletter form in the footer still has `data-netlify="true"` and is not yet wired up — follow-up needed (requires updating every page's footer).
- **Fonts** — Google Fonts loaded externally: Bebas Neue (headings), Montserrat (body), Lora (serif accents). Referenced via CSS custom properties `--fh`, `--fb`, `--fs`.
- **Design system** — CSS custom properties in `:root` define the color palette (gold `#C9A84C`, charcoal `#1C1C1C`), fonts, spacing, and transitions.
- **Images** — all images go in the `/images/` folder. Reference them with absolute paths (e.g., `/images/GMM_Logo.png`).

## Page Structure

Pages live in subdirectories as `index.html` files for clean URLs:
- `/index.html` — homepage (hero, intro with auto-fetched YouTube embed, stats, content tiles, features, newsletter)
- `/about/index.html` — about & team bios with social media links
- `/watch/index.html` — watch episodes (YouTube Data API v3 integration with fallback episodes)
- `/events/index.html` — events calendar (list/grid/month views, loads from `events/events.json`)
- `/nonprofits/index.html` — non-profit partners (alphabetical card grid)
- `/businesses/index.html` — local business directory (MTE headline sponsor, featured spotlights, directory grid)
- `/contact/index.html` — contact forms (guest spot, non-profit, general contact)
- `/privacy-policy/index.html` — privacy policy
- `/terms-of-use/index.html` — terms of use
- `/accessibility/index.html` — accessibility statement
- `/media-kit/index.html` — media kit with sponsorship deck PDF and promo video for prospective sponsors

## Security

- **Headers** — configured in both `_headers` and `netlify.toml`: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-XSS-Protection, HSTS (with preload), and full Content-Security-Policy.
- **XSS protection** — all external data (scraped events, YouTube API responses) is HTML-escaped via `esc()` helper before innerHTML insertion.
- **YouTube API key** — restricted by HTTP referrer to goodmorningmurfreesboro.com in Google Cloud Console, and restricted to YouTube Data API v3 only.
- **External links** — all use `target="_blank" rel="noopener noreferrer"`.

## YouTube Integration

- **API key** — hardcoded in `watch/index.html` and `index.html` (client-side, referrer-restricted).
- **Channel ID** — `UCz5AtMQFFYqgzAeg8ye2Uvw`
- **Homepage** — auto-fetches latest video via API, falls back to hardcoded embed if API fails.
- **Watch page** — fetches latest 5 videos, displays 1 featured + 4 cards. Falls back to `FALLBACK_EPISODES` array.

## Scraper

- `scraper/gmm_scraper.py` — pulls events from Eventbrite and City of Murfreesboro, outputs to `events/events.json`. Source field shows venue/organizer name, not platform name.
- `scraper/update_dates.py` — updates "Last Updated" / "Last Reviewed" dates on legal pages.
- Dependencies: `requests`, `beautifulsoup4` (`pip3 install requests beautifulsoup4`).

## Patterns

- **Scroll-reveal animations** — elements with class `reveal` are observed via `IntersectionObserver` and get class `visible` added when in viewport. Delay classes `d1`–`d5` stagger animations.
- **Mobile nav** — hamburger button toggles a full-screen `.drawer` overlay. Escape key closes it. Focus is managed for accessibility.
- **Nav** — always white background with dark text. `aria-current="page"` marks the active page link. All pages include: Home, About, Watch, Events, Non-Profits, Businesses, + Get Featured.
- **Footer** — consistent across all pages: newsletter signup, site links, social links (Facebook, Instagram, TikTok, YouTube). Heading: "START YOUR DAY WITH GOOD MORNING MURFREESBORO." Legal row includes Privacy Policy, Terms of Use, Accessibility, and (on some pages) Contact. Media Kit lives in the Get Featured footer column on pages that have one (index, about, contact, watch, events, nonprofits, businesses); on pages without a Get Featured column (media-kit, privacy-policy, terms-of-use, accessibility) the Media Kit link is omitted. Copyright line credits "Website design and creation by I Got A Guy, LLC".
- **MTE sponsor** — headline sponsor with blue gradient glow effect, uses `/images/Logo_MTE_Tagline_Horizontal_Blues_16x9.avif`.
- **615 Insurance Agency** — always refer to the full name "615 Insurance Agency" (not "615 Insurance").
- **Accessibility** — skip-to-content link, `aria-label`/`aria-hidden`/`aria-expanded` attributes throughout, `prefers-reduced-motion` and `prefers-contrast` media queries.
- **SEO** — structured data (JSON-LD), Open Graph meta tags, canonical URLs.

## Deployment

- Push to `main` branch on GitHub → Vercel auto-deploys (no GitHub webhook in repo settings; Vercel uses its own GitHub App integration).
- After Vercel deploy completes, purge Cloudflare cache (Caching → Configuration → Purge Everything) so the edge serves the new HTML.
- Repository: https://github.com/Rachel1AZ9/GoodMorningMurfreesboro.git
- DNS: Cloudflare DNS. Domain registered at GoDaddy.

## Placeholder Links

- **Nonprofits page** — Tools for Schools is unlinked (no specific Rutherford County organization identified by that exact name).

## Broken Images

All images previously hosted on the old WordPress site (`i0.wp.com/goodmorningmurfreesboro.com/wp-content/uploads/...`) are now returning 404. Affected cards have been converted to text placeholders or removed. New logos should be added to `/images/` and referenced with absolute paths.

## Page Layout

Both the nonprofits and businesses pages follow this structure:
1. **Featured cards** (top) — spotlight/logo cards with details
2. **Full directory list** (below cards) — alphabetical grid list of all featured organizations, with clickable links where available and plain text otherwise
