"""Pull the events list from lionrampantpub.com and write events.json.

Run by .github/workflows/sync-events.yml on a schedule. Uses only the
standard library. If no events can be read, events.json is left as it is
and the script exits non-zero so the failed run shows up on GitHub.
"""
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

SOURCE = "https://www.lionrampantpub.com/"
OUT = "events.json"
TZ = ZoneInfo("America/Vancouver")
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
DATE_RE = re.compile(
    r"^(?P<title>.*?)[\s\-–|:,]*\b(?:(?:mon|tues?|wed(?:nes)?|thu(?:rs)?|fri|sat(?:ur)?|sun)(?:day)?,?\s+)?"
    r"(?P<month>" + "|".join(MONTHS) + r"|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)\.?\s+"
    r"(?P<day>\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(?P<year>20\d\d))?\s*$",
    re.I,
)
GAME_RE = re.compile(r"bingo|karaoke|trivia|quiz|open mic", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "lion-rampant-app-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def events_section(page):
    """Return the HTML of the events section, or the whole page if it can't be found."""
    m = re.search(r"<(section|div)[^>]*id=[\"']events[\"'][^>]*>", page, re.I)
    if not m:
        return page
    rest = page[m.end():]
    end = re.search(r"<(section|div)[^>]*id=[\"'](?!events)[a-z-]+[\"']", rest, re.I)
    return rest[: end.start()] if end else rest


def to_lines(fragment):
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>|</?(p|div|h[1-6]|li|ul|ol|section|article|tr|td|header|footer|figure|figcaption)\b[^>]*>", "\n", fragment)
    fragment = re.sub(r"(?i)</?span\b[^>]*>", "  ", fragment)
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return [re.sub(r"\s+", " ", l).strip() for l in text.split("\n") if l.strip()]


def month_num(name):
    name = name.lower()[:3]
    return [m[:3] for m in MONTHS].index(name) + 1


def pick_year(month, day, today):
    """Listings omit the year: use this year, unless the date is more than
    six months in the past, in which case it's next year's listing."""
    d = dt.date(today.year, month, day)
    return today.year + 1 if (today - d).days > 183 else today.year


def parse(lines, today):
    events, i = [], 0
    while i < len(lines):
        m = DATE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        title = m.group("title").strip(" -–|:,")
        if not title and i > 0:
            title = lines[i - 1]
        desc = ""
        if i + 1 < len(lines) and not DATE_RE.match(lines[i + 1]) and len(lines[i + 1]) < 200:
            desc = lines[i + 1]
            i += 1
        month, day = month_num(m.group("month")), int(m.group("day"))
        year = int(m.group("year")) if m.group("year") else pick_year(month, day, today)
        try:
            date = dt.date(year, month, day).isoformat()
        except ValueError:
            i += 1
            continue
        if title:
            pretty = title.title() if title.isupper() else title
            events.append({
                "date": date,
                "title": pretty,
                "desc": desc,
                "kind": "game" if GAME_RE.search(title) else "live",
            })
        i += 1
    return sorted(events, key=lambda e: e["date"])


def main(argv):
    page = open(argv[1], encoding="utf-8").read() if len(argv) > 1 else fetch(SOURCE)
    today = dt.datetime.now(TZ).date()
    events = parse(to_lines(events_section(page)), today)
    if not events:
        print("No events found on the website; leaving events.json unchanged.", file=sys.stderr)
        return 1
    try:
        old = json.load(open(OUT))
    except (OSError, ValueError):
        old = {}
    if old.get("events") == events:
        print(f"No change ({len(events)} events).")
        return 0
    json.dump({
        "source": SOURCE,
        "updated": dt.datetime.now(TZ).isoformat(timespec="minutes"),
        "events": events,
    }, open(OUT, "w"), indent=2, ensure_ascii=False)
    open(OUT, "a").write("\n")
    print(f"Wrote {len(events)} events to {OUT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
