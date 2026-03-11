# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Good Morning Murfreesboro (goodmorningmurfreesboro.com) — a community news and events website for Murfreesboro, Tennessee. Covers local news, events, non-profits, and local businesses.

## Architecture

- **Static site** — plain HTML/CSS/JS with no build step or framework. Open `index.html` directly in a browser to develop.
- **Single-page structure** — all CSS is inlined in `<style>` within `index.html`; all JS is inlined in a `<script>` block at the end of `<body>`. No external CSS/JS files.
- **Hosting** — designed for Netlify (newsletter form uses `data-netlify="true"` attributes and honeypot spam protection).
- **Fonts** — Google Fonts loaded externally: Bebas Neue (headings), Montserrat (body), Lora (serif accents). Referenced via CSS custom properties `--fh`, `--fb`, `--fs`.
- **Design system** — CSS custom properties in `:root` define the color palette (gold `#C9A84C`, charcoal `#1C1C1C`), fonts, spacing, and transitions.

## Key Sections & Pages

The homepage (`index.html`) has: fixed nav, full-viewport hero, intro/stats, content tiles grid, features grid, newsletter signup, and footer. Navigation links to planned pages: `/about`, `/events`, `/nonprofits`, `/businesses`, `/contact`, `/privacy-policy`, `/terms-of-use`, `/accessibility`.

## Patterns

- **Scroll-reveal animations** — elements with class `reveal` are observed via `IntersectionObserver` and get class `visible` added when in viewport. Delay classes `d1`–`d5` stagger animations.
- **Mobile nav** — hamburger button toggles a full-screen `.drawer` overlay. Escape key closes it. Focus is managed for accessibility.
- **Nav transparency** — nav starts transparent over the hero and gets class `solid` (white background) after 50px scroll.
- **Accessibility** — skip-to-content link, `aria-label`/`aria-hidden`/`aria-expanded` attributes throughout, `prefers-reduced-motion` and `prefers-contrast` media queries.
- **SEO** — structured data (JSON-LD) for `NewsMediaOrganization` and `FAQPage`, Open Graph meta tags, canonical URL.
- **Logo file** — `GMM Logo Wht BG.jpg` (referenced as `GMM_Logo.png` in HTML — note the filename mismatch).
