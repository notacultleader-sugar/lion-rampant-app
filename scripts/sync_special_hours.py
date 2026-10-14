"""Read the staff "special hours" Google Sheet and write special-hours.json.

The sheet is published to the web as CSV (File > Share > Publish to web >
CSV) and its link is stored in the repo secret SHEET_CSV_URL. Columns:

    Date | Open? | Opens | Closes | Note

  Date    any normal date: 2026-12-25, 12/25/2026, Dec 25, December 25 2026
  Open?   Yes or No (blank counts as No when Opens/Closes are blank)
  Opens   e.g. 11am, 11:30 am, noon
  Closes  e.g. 9pm, midnight, 1am (after midnight is fine)
  Note    shown to customers, e.g. "Merry Christmas!"

Rows that can't be read are skipped and listed in the log. Past dates are
dropped. Standard library only.
"""
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

OUT = "special-hours.json"
TZ = ZoneInfo("America/Vancouver")
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def parse_date(s, today):
    s = s.strip().lower().replace(",", " ")
    s = re.sub(r"^(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?\s+", "", s)
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", s)
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return dt.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:  # Google Sheets in North America writes M/D/YYYY
        y = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
        return dt.date(y, int(m[1]), int(m[2]))
    m = re.match(r"^([a-z]+)\.?\s+(\d{1,2})(?:\s+(\d{4}))?$", s) or re.match(r"^(\d{1,2})\s+([a-z]+)\.?(?:\s+(\d{4}))?$", s)
    if m:
        a, b, y = m[1], m[2], m[3]
        mon, day = (a, b) if a.isalpha() else (b, a)
        month = MONTHS.index(mon[:3]) + 1
        year = int(y) if y else today.year
        d = dt.date(year, month, int(day))
        if not y and (today - d).days > 31:
            d = dt.date(year + 1, month, int(day))
        return d
    raise ValueError(f"can't read date {s!r}")


def parse_time(s):
    """Return (label, minutes after midnight) or None for blank."""
    s = s.strip().lower().replace(".", "")
    if not s:
        return None
    if s in ("midnight", "12 midnight"):
        return "midnight", 24 * 60
    if s == "noon":
        return "noon", 12 * 60
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm|a|p)?$", s)
    if not m:
        raise ValueError(f"can't read time {s!r}")
    h, mi, ap = int(m[1]), int(m[2] or 0), (m[3] or "")[:1]
    if ap == "p" and h != 12:
        h += 12
    if ap == "a" and h == 12:
        h = 0
    if h > 24 or mi > 59:
        raise ValueError(f"can't read time {s!r}")
    hh = h % 12 or 12
    label = f"{hh}{':%02d' % mi if mi else ''}{'am' if h % 24 < 12 else 'pm'}"
    return label, h * 60 + mi


def parse(rows, today):
    days, problems = [], []
    for n, row in enumerate(rows, start=2):
        row = (row + [""] * 5)[:5]
        if not any(c.strip() for c in row):
            continue
        try:
            date = parse_date(row[0], today)
            opens, closes = parse_time(row[2]), parse_time(row[3])
            flag = row[1].strip().lower()
            is_open = flag.startswith("y") or (not flag and bool(opens or closes))
            entry = {"date": date.isoformat(), "open": is_open, "note": row[4].strip()}
            if is_open:
                if not (opens and closes):
                    raise ValueError("open days need both Opens and Closes")
                c = closes[1] if closes[1] > opens[1] else closes[1] + 24 * 60
                entry.update(opens=opens[0], closes=closes[0], opensMin=opens[1], closesMin=c)
            if date >= today - dt.timedelta(days=1):
                days.append(entry)
        except (ValueError, IndexError) as e:
            problems.append(f"row {n}: {e}")
    days.sort(key=lambda d: d["date"])
    return days, problems


def main():
    url = os.environ.get("SHEET_CSV_URL", "").strip()
    if not url:
        print("SHEET_CSV_URL is not set yet; skipping special hours.")
        return 0
    req = urllib.request.Request(url, headers={"User-Agent": "lion-rampant-app-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8-sig", "replace")
    rows = list(csv.reader(io.StringIO(text)))[1:]  # skip header row
    today = dt.datetime.now(TZ).date()
    days, problems = parse(rows, today)
    for p in problems:
        print("Skipped", p)
    try:
        old = json.load(open(OUT)).get("days")
    except (OSError, ValueError):
        old = None
    if old == days:
        print(f"No change ({len(days)} special days).")
        return 0
    with open(OUT, "w") as f:
        json.dump({"updated": dt.datetime.now(TZ).isoformat(timespec="minutes"), "days": days}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(days)} special days to {OUT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
