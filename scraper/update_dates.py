#!/usr/bin/env python3
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
NOW = datetime.now()
MONTH_YEAR = NOW.strftime("%B %Y")

UPDATES = [
    {"file": ROOT / "accessibility" / "index.html", "pattern": r"Last Reviewed: [A-Za-z]+ \d{4}", "replacement": f"Last Reviewed: {MONTH_YEAR}"},
    {"file": ROOT / "privacy-policy" / "index.html", "pattern": r"Last Updated: [A-Za-z]+ \d{4}", "replacement": f"Last Updated: {MONTH_YEAR}"},
    {"file": ROOT / "terms-of-use" / "index.html", "pattern": r"Last Updated: [A-Za-z]+ \d{4}", "replacement": f"Last Updated: {MONTH_YEAR}"},
]

def main():
    print(f"Updating dates to {MONTH_YEAR}...")
    for item in UPDATES:
        path = item["file"]
        if not path.exists():
            print(f"  Not found: {path}")
            continue
        content = path.read_text(encoding="utf-8")
        new_content, count = re.subn(item["pattern"], item["replacement"], content)
        if count:
            path.write_text(new_content, encoding="utf-8")
            print(f"  Updated: {path.name}")

if __name__ == "__main__":
    main()
