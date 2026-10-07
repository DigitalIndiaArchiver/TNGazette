#!/usr/bin/env python3
"""Daily TN — merge fetched source rows, build the daily page, emit the digest.

Pipeline position: runs LOCALLY after dailytn_fetch.py --stage ocitwo has
produced scripts/.dtn_cache/sources.json (see scripts/dailytn_update.sh).

What it does:
  1. Merges each source's rows into data/dailytn/<source>.csv (URL-keyed,
     on-disk rows win — same rule as the gazette CSVs via tn_lib.merge_by_key).
  2. Diffs against state/dailytn-state.json (URL -> first_seen date); NEW urls
     get first_seen = today.
  3. Writes docs/daily/<date>.html (one frozen page per day, itemized) and
     docs/daily/index.html (latest day + archive).
  4. Emits data/dailytn/digest-latest.json = today's new items per source,
     consumed by scripts/dailytn_alert.py (Telegram) — with URL-level
     send-dedup handled by the alert's own state so morning/evening digests
     never repeat items.

First ever run: `--init` marks every row first_seen = today WITHOUT emitting a
digest (backfill suppressed), and today's page itemizes the full baseline.

Usage: python3 scripts/build_daily.py [--init]
"""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tn_lib import read_rows, merge_by_key, write_rows  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "dailytn"
STATE_PATH = PROJECT / "state" / "dailytn-state.json"
SENT_PATH = PROJECT / "data" / "dailytn" / ".sent.json"
MAX_ALERT_AGE_DAYS = 10
CACHE = PROJECT / "scripts" / ".dtn_cache" / "sources.json"
DIGEST_PATH = DATA / "digest-latest.json"
DAILY_DOCS = PROJECT / "docs" / "daily"
SITE = "https://digitalindiaarchiver.github.io/TNGazette"

SOURCES = {
    "go": "Government Orders (tn.gov.in)",
    "whatsnew": "What's New documents (tn.gov.in)",
    "tnpcb_ph": "TNPCB public hearing documents",
    "seco": "CEO-Tamil Nadu notifications",
    "circulars": "Secretariat circulars & notifications",
    "gcc_cr": "Chennai GCC council resolutions",
}
ORDER = ["go", "whatsnew", "tnpcb_ph", "seco", "circulars", "gcc_cr"]

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def parse_whatsnew_date(s):
    """'September 24, 2026' -> date | None (also passes through ISO dates)."""
    s = str(s or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        pass
    m = None
    for name, num in MONTHS.items():
        if name in s:
            m = num
            break
    if not m:
        return None
    try:
        d = s.split(",")[0].split()[-1]
        return date(int(s.split(",")[-1].strip()), m, int(d))
    except (ValueError, IndexError):
        return None


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=0, sort_keys=True),
                          encoding="utf-8")


def item_line(source, r):
    """One <li> for a source row."""
    url = esc(r.get("URL") or "")
    link = f'<a href="{url}">PDF</a>' if url else ""
    if source == "go":
        dept = esc(r.get("dept") or "")
        go = esc(r.get("go_no") or "")
        subj = esc((r.get("subject") or "")[:300])
        tag = f" — G.O {go}" if go else ""
        return f"{subj} <i>({dept}{tag})</i> {link}"
    if source == "whatsnew":
        d = parse_whatsnew_date(r.get("date"))
        ds = d.strftime("%d %b %Y") if d else ""
        t = esc(r.get("title") or "")[:300]
        return f"{t} <i>{ds}</i> {link}"
    if source == "tnpcb_ph":
        proj = esc((r.get("project") or "")[:220])
        extra = ", ".join(x for x in (r.get("hearing_date"), r.get("venue"))
                          if x)
        return f"{proj} <i>{esc(extra)}</i> {link}"
    t = esc(r.get("title") or "")[:300]
    return f"{t} {link}"


def telegram_line(source, r):
    """One digest bullet (Telegram HTML)."""
    url = str(r.get("URL") or "")
    if source == "go":
        dept = esc((r.get("dept") or "").replace(" Department", ""))
        go = esc(r.get("go_no") or "")
        subj = esc((r.get("subject") or "")[:140])
        head = f"{subj} <i>({dept}"
        if go:
            head += f", G.O {go}"
        return head + f')</i> <a href="{url}">PDF</a>'
    if source == "whatsnew":
        return f'{esc((r.get("title") or "")[:160])} <a href="{url}">PDF</a>'
    if source == "tnpcb_ph":
        proj = esc((r.get("project") or "")[:130])
        return f"{proj} <i>{esc(r.get('hearing_date') or '')}</i> <a href=\"{url}\">PDF</a>"
    return f'{esc((r.get("title") or "")[:160])} <a href="{url}">PDF</a>'


def page_shell(title, body, rel_root="../"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — TN Gazette</title>
<link rel="stylesheet" href="{rel_root}style.css">
</head>
<body>
<header>
  <nav>
    <a href="{rel_root}../index.html">Overview</a>
    <a href="{rel_root}../data.html">Data</a>
    <a href="{rel_root}../archives.html">Archives</a>
    <a href="{rel_root}../weekly/">Weekly</a>
    <a href="{rel_root}">Daily</a>
    <a href="{rel_root}../about.html">About</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <p>Machine-collected from official Tamil Nadu government sources. Links point to the original documents. Not associated with the Government of Tamil Nadu.</p>
</footer>
</body>
</html>
"""


def build_day_page(day, by_source, counts, is_init=False):
    total = sum(counts.values())
    secs = []
    if is_init:
        secs.append(
            "<p><b>Baseline import.</b> Items below are the pre-existing "
            "inventory at the time Daily TN started; from here on, each day's "
            "page lists only newly-appeared documents.</p>")
    for src in ORDER:
        rows = by_source.get(src, [])
        if not rows:
            continue
        items = "\n".join(f"  <li>{item_line(src, r)}</li>" for r in rows)
        secs.append(f"<h3>{esc(SOURCES[src])} ({len(rows)})</h3>\n<ul>\n{items}\n</ul>")
    head = (f"<h2>Daily TN — {day.strftime('%d %B %Y')}</h2>\n"
            f"<p>{total} new document(s) across {sum(1 for c in counts.values() if c)} source(s). "
            f"Digest channel: <a href=\"https://t.me/tngazette_alerts\">@tngazette_alerts</a>.</p>")
    return page_shell(f"Daily TN {day.isoformat()}", head + "\n".join(secs))


def build_index(days):
    rows = "\n".join(
        f'  <li><a href="{d.isoformat()}.html">{d.strftime("%d %b %Y")}</a> — '
        f'{n} item(s)</li>' for d, n in days)
    body = ("<h2>Daily TN — underreported document feeds</h2>\n"
            "<p>Each day the pipeline diffs official feeds — Government Orders, "
            "the What's New document board (audit reports, circulars, policy "
            "notes), TNPCB public-hearing documents and CEO-Tamil Nadu "
            "notifications — and records what appeared. Press releases are "
            "excluded on purpose; the media already carry those. This is the "
            "paper trail behind them.</p>\n"
            f"<h3>Days</h3>\n<ul>\n{rows}\n</ul>")
    return page_shell("Daily TN", body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true",
                    help="first run: mark all rows seen, no digest")
    ap.add_argument("--seed-source", metavar="NAME",
                    help="mark one source's rows seen, no digest (add a new "
                         "source without backfill-posting its archive)")
    args = ap.parse_args()

    if not CACHE.exists():
        print("DTN_BUILD: no sources.json — run the ocitwo stage first")
        return 1
    raw = CACHE.read_text().split("SOURCES_JSON_BEGIN\n", 1)[1]
    fetched = json.loads(raw.split("\nSOURCES_JSON_END", 1)[0])

    today = date.today()
    today_s = today.isoformat()
    state = load_state()
    DATA.mkdir(parents=True, exist_ok=True)
    DAILY_DOCS.mkdir(parents=True, exist_ok=True)

    csv_rows, new_by_source, counts = {}, {}, {}
    for src, rows in fetched.items():
        path = DATA / f"{src}.csv"
        schema = list(rows[0].keys()) if rows else SCHEMA_FALLBACK[src]
        existing = read_rows(path, schema) if path.exists() else []
        merged = merge_by_key(existing, rows, "URL")
        write_rows(path, schema, merged)
        csv_rows[src] = merged
        seen = {r.get("URL") for r in existing}
        fresh = [r for r in rows if r.get("URL") and r["URL"] not in seen]
        if args.init:
            fresh = []
        new_by_source[src] = fresh
        counts[src] = len(fresh)

    # state: every fetched URL gets first_seen (today for new ones)
    for src, rows in fetched.items():
        for r in rows:
            u = r.get("URL")
            if u and u not in state:
                state[u] = today_s
    save_state(state)

    # pending = merged rows never sent to Telegram and within the alert window.
    # The alert (not this script) owns successful-send marking, so a failed
    # send retries in the next digest automatically.
    import json as _json
    try:
        sent_map = _json.loads(SENT_PATH.read_text())
    except (OSError, ValueError):
        sent_map = {}
    expired = []
    for u, seen in state.items():
        if u in sent_map:
            continue
        try:
            age = (date.fromisoformat(today_s) - date.fromisoformat(str(seen))).days
        except ValueError:
            age = 0
        if age > MAX_ALERT_AGE_DAYS:
            expired.append(u)
    if expired and not args.init:
        for u in expired:
            sent_map[u] = today_s
        SENT_PATH.write_text(_json.dumps(sent_map, indent=0, sort_keys=True))

    def pending(src):
        return [r for r in csv_rows[src]
                if r.get("URL") and r["URL"] not in sent_map]

    seed = [args.seed_source] if args.seed_source else (
        list(ORDER) if args.init else [])
    for src in seed:
        for r in csv_rows[src]:
            u = r.get("URL")
            if u:
                sent_map[u] = "init"
    if seed:
        SENT_PATH.write_text(_json.dumps(sent_map, indent=0, sort_keys=True))
    if seed:
        counts = {s: 0 for s in ORDER}
        new_by_source = {s: [] for s in ORDER}
        seen_now = set(sent_map)
        for src in ORDER:
            if src in seed:
                continue
            for r in csv_rows[src]:
                u = r.get("URL")
                if u and u not in seen_now:
                    counts[src] += 1
                    new_by_source[src].append(r)

    pend = {s: pending(s) for s in ORDER}
    pcounts = {s: len(pend[s]) for s in ORDER}

    digest = {"date": today_s, "generated": datetime.now().isoformat(),
              "counts": pcounts, "is_init": bool(args.init),
              "urls": [r["URL"] for s in ORDER for r in pend[s]],
              "sections": {s: pend[s] for s in ORDER}}
    DIGEST_PATH.write_text(json.dumps(digest, indent=1), encoding="utf-8")

    # daily page for today (itemized; init page shows the baseline inventory)
    day_page_rows = {}
    if args.init:
        day_page_rows = {s: csv_rows[s] for s in ORDER}
    else:
        # fall back to pending items so a late/skipped prior run still shows
        # the documents on the day page instead of a blank listing
        day_page_rows = (new_by_source if any(new_by_source.values())
                         else {s: pend[s] for s in ORDER if pend[s]})
    (DAILY_DOCS / f"{today_s}.html").write_text(
        build_day_page(today, day_page_rows, counts, is_init=args.init),
        encoding="utf-8")

    # index: walk all dated pages
    days = sorted(
        ((date.fromisoformat(p.stem), None)
         for p in DAILY_DOCS.glob("????-??-??.html")),
        reverse=True)
    (DAILY_DOCS / "index.html").write_text(
        build_index(days), encoding="utf-8")

    total_new = sum(counts.values())
    total_pend = sum(pcounts.values())
    print(f"DTN_BUILD: new={total_new} "
          + " ".join(f"{s}={counts[s]}" for s in ORDER)
          + f" | pending={total_pend}"
          + (" (init)" if args.init else ""))
    return 0


SCHEMA_FALLBACK = {
    "go": ["dept_id", "dept", "go_no", "date", "subject", "URL"],
    "whatsnew": ["category", "title", "date", "URL"],
    "tnpcb_ph": ["project", "extent", "hearing_date", "venue", "deo", "URL",
                 "eia_url"],
    "seco": ["title", "URL"],
    "circulars": ["title", "date", "URL"],
    "gcc_cr": ["title", "date", "URL"],
}


if __name__ == "__main__":
    sys.exit(main())
