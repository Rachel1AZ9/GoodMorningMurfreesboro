# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Good Morning Murfreesboro (goodmorningmurfreesboro.com) — a community news and events website for Murfreesboro, Tennessee. Covers local news, events, non-profits, and local businesses. Live every Friday at 7am CT on Facebook and YouTube.

## Architecture

- **Static site** — plain HTML/CSS/JS with no build step or framework. Use a local server (`python3 -m http.server 8000`) to develop since pages use absolute paths.
- **Single-page structure** — all CSS is inlined in `<style>` within each page's HTML; all JS is inlined in a `<script>` block at the end of `<body>`. No external CSS/JS files.
- **Hosting** — designed for Netlify (forms use `data-netlify="true"` attributes and honeypot spam protection).
- **Fonts** — Google Fonts loaded externally: Bebas Neue (headings), Montserrat (body), Lora (serif accents). Referenced via CSS custom properties `--fh`, `--fb`, `--fs`.
- **Design system** — CSS custom properties in `:root` define the color palette (gold `#C9A84C`, charcoal `#1C1C1C`), fonts, spacing, and transitions.
- **Images** — all images go in the `/images/` folder. Reference them with absolute paths (e.g., `/images/GMM_Logo.png`).

## Page Structure

Pages live in subdirectories as `index.html` files for clean URLs:
- `/index.html` — homepage (hero, intro with YouTube embed, stats, content tiles, features, newsletter)
- `/about/index.html` — about & team bios
- `/watch/index.html` — watch episodes (YouTube API integration with fallback episodes)
- `/events/index.html` — events calendar (list/grid/month views, loads from `events/events.json`)
- `/nonprofits/index.html` — non-profit partners (alphabetical card grid)
- `/businesses/index.html` — local business directory (MTE headline sponsor, featured spotlights, directory grid)
- `/contact/index.html` — contact forms (guest spot, non-profit, shoutout)
- `/privacy-policy/index.html` — privacy policy
- `/terms-of-use/index.html` — terms of use
- `/accessibility/index.html` — accessibility statement

## Scraper

- `scraper/gmm_scraper.py` — pulls events from Eventbrite and City of Murfreesboro, outputs to `events/events.json`. Source field shows venue/organizer name, not platform name.
- `scraper/update_dates.py` — updates "Last Updated" / "Last Reviewed" dates on legal pages.
- Dependencies: `requests`, `beautifulsoup4` (`pip3 install requests beautifulsoup4`).

## Patterns

- **Scroll-reveal animations** — elements with class `reveal` are observed via `IntersectionObserver` and get class `visible` added when in viewport. Delay classes `d1`–`d5` stagger animations.
- **Mobile nav** — hamburger button toggles a full-screen `.drawer` overlay. Escape key closes it. Focus is managed for accessibility.
- **Nav** — always white background with dark text. `aria-current="page"` marks the active page link. All pages include: Home, About, Watch, Events, Non-Profits, Businesses, + Get Featured.
- **Footer** — consistent across all pages: newsletter signup, site links, social links (Facebook, Instagram, TikTok, YouTube). Heading: "START YOUR DAY WITH GOOD MORNING MURFREESBORO."
- **MTE sponsor** — headline sponsor with blue gradient glow effect, uses `/images/Logo_MTE_Tagline_Horizontal_Blues_16x9.avif`.
- **Accessibility** — skip-to-content link, `aria-label`/`aria-hidden`/`aria-expanded` attributes throughout, `prefers-reduced-motion` and `prefers-contrast` media queries.
- **SEO** — structured data (JSON-LD), Open Graph meta tags, canonical URLs.
