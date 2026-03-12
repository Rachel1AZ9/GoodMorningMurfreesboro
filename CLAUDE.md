# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Good Morning Murfreesboro (goodmorningmurfreesboro.com) — a community news and events website for Murfreesboro, Tennessee. Covers local news, events, non-profits, and local businesses.

## Architecture

- **Static site** — plain HTML/CSS/JS with no build step or framework. Open `index.html` directly in a browser to develop.
- **Single-page structure** — all CSS is inlined in `<style>` within each page's HTML; all JS is inlined in a `<script>` block at the end of `<body>`. No external CSS/JS files.
- **Hosting** — designed for Netlify (newsletter form uses `data-netlify="true"` attributes and honeypot spam protection).
- **Fonts** — Google Fonts loaded externally: Bebas Neue (headings), Montserrat (body), Lora (serif accents). Referenced via CSS custom properties `--fh`, `--fb`, `--fs`.
- **Design system** — CSS custom properties in `:root` define the color palette (gold `#C9A84C`, charcoal `#1C1C1C`), fonts, spacing, and transitions.
- **Images** — all images go in the `/images/` folder. Reference them with absolute paths (e.g., `/images/GMM_Logo.png`).

## Page Structure

Pages live in subdirectories as `index.html` files for clean URLs:
- `/index.html` — homepage
- `/about/index.html` — about & team bios
- `/nonprofits/index.html` — non-profit partners
- `/businesses/index.html` — local business directory
- `/events/` and `/contact/` — directories created, pages pending

## Patterns

- **Scroll-reveal animations** — elements with class `reveal` are observed via `IntersectionObserver` and get class `visible` added when in viewport. Delay classes `d1`–`d5` stagger animations.
- **Mobile nav** — hamburger button toggles a full-screen `.drawer` overlay. Escape key closes it. Focus is managed for accessibility.
- **Nav** — always white background with dark text. `aria-current="page"` marks the active page link.
- **Accessibility** — skip-to-content link, `aria-label`/`aria-hidden`/`aria-expanded` attributes throughout, `prefers-reduced-motion` and `prefers-contrast` media queries.
- **SEO** — structured data (JSON-LD), Open Graph meta tags, canonical URLs.
