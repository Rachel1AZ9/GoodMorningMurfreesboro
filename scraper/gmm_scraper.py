#!/usr/bin/env python3
"""
Good Morning Murfreesboro — Event Scraper
Pulls events from Eventbrite and City of Murfreesboro
Outputs: events/events.json (relative to project root)

Usage:
  python gmm_scraper.py              # scrape all sources
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
    "sports": ["sport", "run", "race", "walk", "5k", "tournament", "game", "fitness", "yoga", "wrestling"],
    "community": ["community", "volunteer", "nonprofit", "charity", "fundrais", "church", "civic", "celebration"],
    "education": ["class", "workshop", "seminar", "learn", "training", "education", "lecture", "tedx"],
    "festival": ["festival", "fair", "parade", "holiday"],
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
    # If it's a BeautifulSoup Tag, get its text content
    if hasattr(s, 'get_text'):
        s = s.get_text(separator=' ')
    return re.sub(r'\s+', ' ', str(s)).strip()

def extract_organizer(item: dict) -> str:
    """Extract organizer/venue name from JSON-LD data."""
    # Try organizer field first
    org = item.get("organizer", {})
    if isinstance(org, dict):
        name = org.get("name", "")
        if name:
            return clean_text(name)
    elif isinstance(org, str):
        return clean_text(org)

    # Fall back to location/venue name
    loc = item.get("location", {})
    if isinstance(loc, dict):
        name = loc.get("name", "")
        if name:
            return clean_text(name)

    return ""


# ── Eventbrite ─────────────────────────────────────────────────────────────
def scrape_eventbrite() -> list:
    print("📡 Scraping Eventbrite...")
    events = []
    url = "https://www.eventbrite.com/d/tn--murfreesboro/all-events/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        html = r.text

        # Extract __SERVER_DATA__ JSON blob using raw_decode
        server_data = None
        sd_idx = html.find('__SERVER_DATA__')
        if sd_idx != -1:
            eq_idx = html.index('=', sd_idx)
            raw = html[eq_idx + 1:].strip()
            try:
                server_data, _ = json.JSONDecoder().raw_decode(raw)
            except (json.JSONDecodeError, ValueError):
                pass

        if server_data:
            results = []
            # Navigate to search results
            try:
                results = server_data.get("search_data", {}).get("events", {}).get("results", [])
            except (AttributeError, TypeError):
                pass

            for item in results:
                title = clean_text(item.get("name", ""))
                if not title:
                    continue

                # Build ISO date from start_date + start_time
                start_date = item.get("start_date", "")
                start_time = item.get("start_time", "")
                end_date = item.get("end_date", "")
                end_time = item.get("end_time", "")
                date_raw = f"{start_date}T{start_time}" if start_date and start_time else start_date
                end_raw = f"{end_date}T{end_time}" if end_date and end_time else end_date

                if not date_raw:
                    continue

                # Venue / location
                venue = item.get("primary_venue", {}) or {}
                venue_name = clean_text(venue.get("name", ""))
                addr = venue.get("address", {}) or {}
                addr_parts = [addr.get("address_1", ""), addr.get("city", ""), addr.get("region", "")]
                location = venue_name or ", ".join(p for p in addr_parts if p) or "Murfreesboro, TN"

                # Description
                desc = clean_text(item.get("summary", ""))

                # Link
                link = item.get("url", url)

                # Image
                image = ""
                img_data = item.get("image", {})
                if isinstance(img_data, dict):
                    image = img_data.get("url", "") or img_data.get("original", {}).get("url", "")
                elif isinstance(img_data, str):
                    image = img_data

                # Price
                is_free = item.get("is_free", False)
                price = "Free" if is_free else ""
                ticket_info = item.get("ticket_availability", {}) or {}
                if not is_free and ticket_info.get("minimum_ticket_price"):
                    p = ticket_info["minimum_ticket_price"].get("major_value", "")
                    if p:
                        price = f"${p}"

                # Source = venue name (the business/organizer, not "Eventbrite")
                source = venue_name or "Murfreesboro Event"

                events.append({
                    "id": make_id("eventbrite", title, date_raw),
                    "title": title,
                    "date": date_raw,
                    "endDate": end_raw,
                    "location": location,
                    "description": desc,
                    "category": guess_category(title + " " + desc),
                    "isFree": is_free,
                    "price": price,
                    "image": image,
                    "link": link,
                    "source": source,
                })

        # Fallback: JSON-LD
        if not events:
            soup = BeautifulSoup(html, "html.parser")
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
                        source = extract_organizer(item) or "Murfreesboro Event"
                        loc = item.get("location", {})
                        location = clean_text(loc.get("name", "")) if isinstance(loc, dict) else "Murfreesboro, TN"
                        events.append({
                            "id": make_id("eventbrite", title, date_raw),
                            "title": title,
                            "date": date_raw,
                            "endDate": item.get("endDate", ""),
                            "location": location or "Murfreesboro, TN",
                            "description": clean_text(item.get("description", "")),
                            "category": guess_category(title),
                            "isFree": False,
                            "price": "",
                            "image": "",
                            "link": item.get("url", url),
                            "source": source,
                        })
                except Exception:
                    pass

    except Exception as e:
        print(f"  ⚠️  Eventbrite error: {e}")

    print(f"  ✅ Eventbrite: {len(events)} events")
    return events


# ── City of Murfreesboro ───────────────────────────────────────────────────
def scrape_murfreesboro_city() -> list:
    print("📡 Scraping City of Murfreesboro...")
    events = []
    url = "https://www.murfreesborotn.gov/calendar.aspx"
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
                    loc = item.get("location", {})
                    location = clean_text(loc.get("name", "Murfreesboro, TN")) if isinstance(loc, dict) else "Murfreesboro, TN"
                    source = extract_organizer(item) or location or "City of Murfreesboro"
                    events.append({
                        "id": make_id("murfreesboro", title, date_raw),
                        "title": title,
                        "date": date_raw,
                        "endDate": item.get("endDate", ""),
                        "location": location,
                        "description": clean_text(item.get("description", "")),
                        "category": guess_category(title),
                        "isFree": True,
                        "price": "Free",
                        "image": "",
                        "link": item.get("url", url),
                        "source": source,
                    })
            except Exception:
                pass

        # CivicPlus calendar fallback
        if not events:
            for row in soup.select(".calendar-event, .event-row, tr.event, .fc-event, li.event, .calendarEvent"):
                title_el = row.select_one("a, .event-title, h3, h4")
                date_el = row.select_one("time, .date, td.date, [class*='date']")
                title = clean_text(title_el) if title_el else ""
                date_raw = ""
                if date_el:
                    date_raw = date_el.get("datetime", "") or clean_text(date_el)
                link = ""
                if title_el and title_el.name == "a":
                    link = title_el.get("href", url)
                else:
                    link = url
                if link and not link.startswith("http"):
                    link = "https://www.murfreesborotn.gov" + link

                if not title or "<" in title:
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
    except Exception as e:
        print(f"  ⚠️  City of Murfreesboro error: {e}")

    print(f"  ✅ City of Murfreesboro: {len(events)} events")
    return events


# ── Deduplicate ────────────────────────────────────────────────────────────
def deduplicate(events: list) -> list:
    seen = {}
    for e in events:
        key = (e["title"].lower()[:40], e["date"][:10] if e["date"] else "")
        if key not in seen:
            seen[key] = e
    return list(seen.values())


# ── Sort & save ────────────────────────────────────────────────────────────
def save(events: list):
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
    parser.add_argument("--source", choices=["eventbrite", "murfreesboro"], help="Scrape a single source")
    args = parser.parse_args()

    all_events = []

    if args.source == "eventbrite":
        all_events = scrape_eventbrite()
    elif args.source == "murfreesboro":
        all_events = scrape_murfreesboro_city()
    else:
        all_events += scrape_eventbrite()
        all_events += scrape_murfreesboro_city()

    all_events = deduplicate(all_events)
    save(all_events)
    print(f"\n🎉 Done! {len(all_events)} unique events ready.")


if __name__ == "__main__":
    main()
