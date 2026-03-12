#!/usr/bin/env python3
"""
Good Morning Murfreesboro — Event Scraper
Pulls events from BaseLocal, Eventbrite, and City of Murfreesboro
Outputs: events/events.json (relative to project root)

Usage:
  python gmm_scraper.py              # scrape all sources
  python gmm_scraper.py --source baselocal
  python gmm_scraper.py --source eventbrite
  python gmm_scraper.py --source murfreesboro

Schedule (add to crontab):
  0 6 * * * cd /Users/rachelalbertson/projects/goodmorningmurfreesboro && python scraper/gmm_scraper.py && git add events/events.json && git commit -m "Auto-update events" && git push
"""

import json
import re
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Config ─────────────────────────────────────────────────────────────────
OUTPUT_FILE = Path(__file__).parent.parent / "events" / "events.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 15

# Category keyword mapping
CATEGORY_MAP = {
    "music": ["music", "concert", "band", "live", "jazz", "country", "rock", "perform"],
    "food": ["food", "drink", "wine", "beer", "restaurant", "taste", "dining", "brunch", "market"],
    "family": ["family", "kid", "child", "children", "parent", "youth", "teen"],
    "arts": ["art", "gallery", "theater", "theatre", "film", "movie", "craft", "exhibit"],
    "sports": ["sport", "run", "race", "walk", "5k", "tournament", "game", "fitness"],
    "community": ["community", "volunteer", "nonprofit", "charity", "fundrais", "church", "civic"],
    "education": ["class", "workshop", "seminar", "learn", "training", "education", "lecture"],
    "festival": ["festival", "fair", "parade", "celebration", "holiday"],
}

def guess_category(text: str) -> str:
    text = text.lower()
    for cat, keywords in CATEGORY_MAP.items():
        if any(k in text for k in keywords):
            return cat
    return "general"

def make_id(source: str, title: str, date: str) -> str:
    raw = f"{source}:{title}:{date}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def clean_text(s) -> str:
    if not s:
        return ""
    return re.sub(r'\s+', ' ', str(s)).strip()

# ── BaseLocal ──────────────────────────────────────────────────────────────
def scrape_baselocal() -> list:
    print("📡 Scraping BaseLocal...")
    events = []
    urls = [
        "https://baselocal.com/tn/murfreesboro/events/",
        "https://baselocal.com/tn/murfreesboro/events/?page=2",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Try JSON-LD first
            for tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(tag.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") not in ("Event", "SocialEvent"):
                            continue
                        title = clean_text(item.get("name", ""))
                        date_raw = item.get("startDate", "")
                        end_raw = item.get("endDate", "")
                        loc = item.get("location", {})
                        location = clean_text(
                            loc.get("name", "") if isinstance(loc, dict) else loc
                        )
                        desc = clean_text(item.get("description", ""))
                        link = item.get("url", url)
                        image = item.get("image", "")
                        if isinstance(image, list):
                            image = image[0] if image else ""
                        if isinstance(image, dict):
                            image = image.get("url", "")
                        price = item.get("offers", {})
                        is_free = False
                        price_str = ""
                        if isinstance(price, dict):
                            p = str(price.get("price", ""))
                            is_free = p in ("0", "0.0", "Free", "")
                            price_str = "Free" if is_free else f"${p}"
                        if not title or not date_raw:
                            continue
                        events.append({
                            "id": make_id("baselocal", title, date_raw),
                            "title": title,
                            "date": date_raw,
                            "endDate": end_raw,
                            "location": location,
                            "description": desc,
                            "category": guess_category(title + " " + desc),
                            "isFree": is_free,
                            "price": price_str,
                            "image": image,
                            "link": link,
                            "source": "BaseLocal",
                        })
                except Exception:
                    pass

            # CSS selector fallback
            if not events:
                for card in soup.select(".event-card, .event-item, article.event, [class*='event']"):
                    title_el = card.select_one("h2, h3, h4, .event-title, .title")
                    date_el = card.select_one("time, .date, .event-date, [class*='date']")
                    loc_el = card.select_one(".location, .venue, [class*='location'], [class*='venue']")
                    link_el = card.select_one("a[href]")
                    title = clean_text(title_el) if title_el else ""
                    date_raw = (date_el.get("datetime") or clean_text(date_el)) if date_el else ""
                    location = clean_text(loc_el) if loc_el else "Murfreesboro, TN"
                    link = link_el["href"] if link_el else url
                    if not link.startswith("http"):
                        link = "https://baselocal.com" + link
                    if not title:
                        continue
                    events.append({
                        "id": make_id("baselocal", title, date_raw),
                        "title": title,
                        "date": date_raw,
                        "endDate": "",
                        "location": location,
                        "description": "",
                        "category": guess_category(title),
                        "isFree": False,
                        "price": "",
                        "image": "",
                        "link": link,
                        "source": "BaseLocal",
                    })
        except Exception as e:
            print(f"  ⚠️  BaseLocal error ({url}): {e}")

    print(f"  ✅ BaseLocal: {len(events)} events")
    return events


# ── Eventbrite ─────────────────────────────────────────────────────────────
def scrape_eventbrite() -> list:
    print("📡 Scraping Eventbrite...")
    events = []
    url = "https://www.eventbrite.com/d/tn--murfreesboro/all-events/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # JSON-LD
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") not in ("Event", "SocialEvent"):
                        continue
                    title = clean_text(item.get("name", ""))
                    date_raw = item.get("startDate", "")
                    end_raw = item.get("endDate", "")
                    loc = item.get("location", {})
                    if isinstance(loc, dict):
                        addr = loc.get("address", {})
                        location = clean_text(loc.get("name", "")) or clean_text(
                            addr.get("streetAddress", "") + " " + addr.get("addressLocality", "")
                        )
                    else:
                        location = clean_text(loc)
                    desc = clean_text(item.get("description", ""))
                    link = item.get("url", url)
                    image = item.get("image", "")
                    if isinstance(image, list): image = image[0] if image else ""
                    if isinstance(image, dict): image = image.get("url", "")
                    offers = item.get("offers", {})
                    price = ""
                    is_free = False
                    if isinstance(offers, dict):
                        p = str(offers.get("price", ""))
                        is_free = p in ("0", "0.0", "")
                        price = "Free" if is_free else f"${p}"
                    if not title or not date_raw:
                        continue
                    events.append({
                        "id": make_id("eventbrite", title, date_raw),
                        "title": title,
                        "date": date_raw,
                        "endDate": end_raw,
                        "location": location or "Murfreesboro, TN",
                        "description": desc,
                        "category": guess_category(title + " " + desc),
                        "isFree": is_free,
                        "price": price,
                        "image": image,
                        "link": link,
                        "source": "Eventbrite",
                    })
            except Exception:
                pass

        # Fallback: search cards
        if not events:
            for card in soup.select("[data-testid='event-card'], .search-event-card, article"):
                title_el = card.select_one("h2, h3, [class*='title']")
                date_el = card.select_one("time, [class*='date']")
                loc_el = card.select_one("[class*='location'], [class*='venue']")
                link_el = card.select_one("a[href*='eventbrite.com']")
                img_el = card.select_one("img")
                title = clean_text(title_el) if title_el else ""
                date_raw = (date_el.get("datetime") or clean_text(date_el)) if date_el else ""
                location = clean_text(loc_el) if loc_el else "Murfreesboro, TN"
                link = link_el["href"] if link_el else url
                image = img_el.get("src", "") if img_el else ""
                if not title:
                    continue
                events.append({
                    "id": make_id("eventbrite", title, date_raw),
                    "title": title,
                    "date": date_raw,
                    "endDate": "",
                    "location": location,
                    "description": "",
                    "category": guess_category(title),
                    "isFree": False,
                    "price": "",
                    "image": image,
                    "link": link,
                    "source": "Eventbrite",
                })
    except Exception as e:
        print(f"  ⚠️  Eventbrite error: {e}")

    print(f"  ✅ Eventbrite: {len(events)} events")
    return events


# ── City of Murfreesboro ───────────────────────────────────────────────────
def scrape_murfreesboro_city() -> list:
    print("📡 Scraping City of Murfreesboro...")
    events = []
    urls = [
        "https://www.murfreesborotn.gov/calendar.aspx",
        "https://www.murfreesborotn.gov/events",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # JSON-LD
            for tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(tag.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") not in ("Event", "SocialEvent"):
                            continue
                        title = clean_text(item.get("name", ""))
                        date_raw = item.get("startDate", "")
                        if not title or not date_raw:
                            continue
                        events.append({
                            "id": make_id("murfreesboro", title, date_raw),
                            "title": title,
                            "date": date_raw,
                            "endDate": item.get("endDate", ""),
                            "location": clean_text(item.get("location", {}).get("name", "Murfreesboro, TN")) if isinstance(item.get("location"), dict) else "Murfreesboro, TN",
                            "description": clean_text(item.get("description", "")),
                            "category": guess_category(title),
                            "isFree": True,
                            "price": "Free",
                            "image": "",
                            "link": item.get("url", url),
                            "source": "City of Murfreesboro",
                        })
                except Exception:
                    pass

            # CivicPlus calendar fallback
            if not events:
                for row in soup.select(".calendar-event, .event-row, tr.event, .fc-event, li.event"):
                    title_el = row.select_one("a, .event-title, h3, h4")
                    date_el = row.select_one("time, .date, td.date, [class*='date']")
                    title = clean_text(title_el) if title_el else ""
                    date_raw = (date_el.get("datetime") or clean_text(date_el)) if date_el else ""
                    link = title_el.get("href", url) if title_el and title_el.name == "a" else url
                    if not link.startswith("http"):
                        link = "https://www.murfreesborotn.gov" + link
                    if not title:
                        continue
                    events.append({
                        "id": make_id("murfreesboro", title, date_raw),
                        "title": title,
                        "date": date_raw,
                        "endDate": "",
                        "location": "Murfreesboro, TN",
                        "description": "",
                        "category": guess_category(title),
                        "isFree": True,
                        "price": "Free",
                        "image": "",
                        "link": link,
                        "source": "City of Murfreesboro",
                    })
            if events:
                break
        except Exception as e:
            print(f"  ⚠️  City of Murfreesboro error ({url}): {e}")

    print(f"  ✅ City of Murfreesboro: {len(events)} events")
    return events


# ── Deduplicate ────────────────────────────────────────────────────────────
def deduplicate(events: list) -> list:
    seen = {}
    for e in events:
        key = (e["title"].lower()[:40], e["date"][:10])
        if key not in seen:
            seen[key] = e
    return list(seen.values())


# ── Sort & save ────────────────────────────────────────────────────────────
def save(events: list):
    # Sort: events with parseable dates first, then by date
    def sort_key(e):
        d = e.get("date", "")
        try:
            return datetime.fromisoformat(d.replace("Z", "+00:00"))
        except Exception:
            return datetime(9999, 1, 1, tzinfo=timezone.utc)

    events.sort(key=sort_key)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "events": events,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n✅ Saved {len(events)} events → {OUTPUT_FILE}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GMM Event Scraper")
    parser.add_argument("--source", choices=["baselocal", "eventbrite", "murfreesboro"], help="Scrape a single source")
    args = parser.parse_args()

    all_events = []

    if args.source == "baselocal":
        all_events = scrape_baselocal()
    elif args.source == "eventbrite":
        all_events = scrape_eventbrite()
    elif args.source == "murfreesboro":
        all_events = scrape_murfreesboro_city()
    else:
        all_events += scrape_baselocal()
        all_events += scrape_eventbrite()
        all_events += scrape_murfreesboro_city()

    all_events = deduplicate(all_events)
    save(all_events)
    print(f"\n🎉 Done! {len(all_events)} unique events ready.")


if __name__ == "__main__":
    main()
