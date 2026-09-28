#!/usr/bin/env python3
"""Alert a Telegram channel about new TN Gazette items (Bot API).

Self-healing by design: ``data/.telegram_sent.json`` records every item URL
already alerted. Items are chosen as "rows in the canonical CSVs not yet in
the state file", NOT from the run's delta — so a failed or skipped post is
retried on the next run automatically. Items older than --max-age-days are
marked sent silently (never backfill-spam). The very first run (no state
file) only initializes the state: everything known so far is marked sent and
nothing is posted.

Channel resolution: --channel arg > $TG_CHANNEL > data/telegram_channel.txt.
Bot token: $TELEGRAM_BOT_TOKEN (bot must be an admin of the channel).

Exit codes: 0 ok (posted / nothing to do / initialized) | 3 not configured |
4 Telegram API error | 5 unexpected error.

Usage:
  python3 scripts/telegram_alert.py --dry-run      # show messages, no send/state
  python3 scripts/telegram_alert.py --sample       # demo: recent items, no state write
  python3 scripts/telegram_alert.py                # real run (called by daily_update.sh)
"""
import argparse
import glob
import html
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tn_lib import read_rows, GAZATTES_COLUMNS, EXTRAORDINARY_COLUMNS  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT / "data" / ".telegram_sent.json"
CHANNEL_FILE = PROJECT / "data" / "telegram_channel.txt"
SITE = "https://digitalindiaarchiver.github.io/TNGazette"
API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_MSG = 3800  # Telegram hard cap is 4096 chars; leave headroom for HTML


# ---------------------------------------------------------------- state

def load_state():
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, indent=0, sort_keys=True), encoding="utf-8")


# ---------------------------------------------------------------- rows

def csv_columns(path, fallback):
    if path.exists():
        with open(path, encoding="utf-8", errors="replace") as fh:
            first = fh.readline().strip()
        if first:
            return [c.strip() for c in next(__import__("csv").reader([first]))]
    return fallback


def parse_ord_date(s):
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_extra_date(s):
    try:
        return datetime.strptime(str(s).strip(), "%d-%m-%Y").date()
    except ValueError:
        return None


def collect_items(today, max_age_days):
    """Return (ordinary, extraordinary) item dicts not yet sent."""
    state = load_state()
    fresh_init = state is None
    sent = {} if fresh_init else state
    cutoff = today - timedelta(days=max_age_days)

    ordinary, extraordinary, seen_all = [], [], []

    for path in sorted(glob.glob(str(PROJECT / "data" / "Gazattes_*.csv"))):
        cols = csv_columns(Path(path), GAZATTES_COLUMNS)
        for r in read_rows(Path(path), cols):
            url = str(r.get("URL") or "").strip()
            if not url:
                continue
            seen_all.append(url)
            if url in sent or str(r.get("Deleted", "")).strip().lower() == "true":
                continue
            d = parse_ord_date(r.get("Date"))
            ordinary.append({
                "key": url, "date": d, "recent": bool(d and d >= cutoff),
                "issue": str(r.get("Issue") or "").strip(),
                "part": re.sub(r"^\d+-", "", str(r.get("Part") or "").strip()),
                "content": str(r.get("Content") or "").strip(),
                "url": url,
            })

    for path in sorted(glob.glob(str(PROJECT / "data" / "ExtraOrdinaryGazattes_*.csv"))):
        cols = csv_columns(Path(path), EXTRAORDINARY_COLUMNS)
        for r in read_rows(Path(path), cols):
            url = str(r.get("PDF Link") or "").strip()
            if not url:
                continue
            seen_all.append(url)
            if url in sent:
                continue
            d = parse_extra_date(r.get("Issue Date"))
            extraordinary.append({
                "key": url, "date": d, "recent": bool(d and d >= cutoff),
                "issue": str(r.get("Issue No") or "").strip(),
                "part": str(r.get("Extraordinary Part & Section") or "").strip(),
                "etype": str(r.get("Extraordinary Type") or "").strip(),
                "subject": str(r.get("Subject") or "").strip(),
                "dept": str(r.get("Department") or "").strip(),
                "go": str(r.get("G.O No") or "").strip(),
                "url": url,
            })

    return fresh_init, sent, seen_all, ordinary, extraordinary


# ---------------------------------------------------------------- text

CAT_MARKERS = (
    "Secretariat Departments.", "Secretariat Departments,",
    "Heads of Departments, etc.", "Heads of Departments, Etc.",
    "Heads of departments etc.,", "Election Commission of India.",
    "Assembly Secretariat", "Collector And Local Authority",
)


def strip_category(text, limit=170):
    """Drop the boilerplate category prefix; keep the actual notification text."""
    t = " ".join(text.split())
    for marker in CAT_MARKERS:
        idx = t.find(marker)
        if 0 <= idx <= 200:
            t = t[idx + len(marker):].lstrip(" .,-")
            break
    t = re.split(r"\s*--\s*(?:G\.?O\.?|Notification No)", t, maxsplit=1)[0]
    # glue-tolerant: source PDFs often lack the space ("...RulesNotification No...")
    t = re.split(r"\s*Notification No", t, maxsplit=1)[0]
    # trailing glued department ("...act, 2003.Energy Department")
    t = re.sub(r"\s*\.[A-Z][A-Za-z&(). ]{2,60} Department\.?$", ".", t)
    if len(t) > limit:
        cut = t[:limit].rsplit(" ", 1)[0].rstrip(" .,-–—;")
        t = cut + "…"
    return t


def esc(s):
    return html.escape(" ".join(str(s or "").split()), quote=False)


def part_short(part):
    return part.replace("Section", "Sec").replace(" - ", " ")


def fmt_extra(it):
    bits = [f"• <b>#{esc(it['issue'])}</b>"]
    if it["part"]:
        bits.append(esc(part_short(it["part"])))
    if it["dept"]:
        bits.append(esc(it["dept"]))
    if it["go"]:
        bits.append(f'<a href="{esc(it["url"])}">{esc(it["go"])}</a>')
    else:
        bits.append(f'<a href="{esc(it["url"])}">PDF</a>')
    line = " · ".join(bits)
    subj = strip_category(it["subject"])
    if subj:
        line += f"\n  <i>{esc(subj)}</i>"
    return line


def fmt_ord(it):
    label = f"Issue {esc(it['issue'])}" if it["issue"] else "Ordinary"
    if it["date"]:
        label += f", {it['date'].strftime('%d %b %Y')}"
    body = strip_category(it["content"], limit=140)
    return (f"• {esc(part_short(it['part']))} — <i>{esc(body)}</i> "
            f'<a href="{esc(it["url"])}">PDF</a>'), label


def build_messages(ordinary, extraordinary, today):
    """Return list of (text, [item_keys]) chunks under the Telegram cap."""
    weekly = ""
    iso = today.isocalendar()
    wk = PROJECT / "docs" / "weekly" / f"{iso[0]}-W{iso[1]:02d}.html"
    if wk.exists():
        weekly = f'\n📊 <a href="{SITE}/weekly/{wk.stem}.html">This week in review</a>'

    extra_lines = [fmt_extra(it) for it in extraordinary]
    ord_groups = {}
    for it in ordinary:
        key = (it["issue"], it["date"])
        ord_groups.setdefault(key, []).append(it)

    head = "🏛 <b>TN Gazette update</b> · {date}\n{n} new item{s}\n"
    chunks, cur, keys = [], [], []

    def flush():
        if cur:
            chunks.append(("\n".join(cur), list(keys)))
            cur.clear()
            keys.clear()

    n = len(extraordinary) + len(ordinary)
    cur.append(head.format(date=today.strftime("%d %b %Y"), n=n,
                           s="" if n == 1 else "s"))
    if extraordinary:
        cur.append("⚡ <b>Extraordinary</b>")
        for it, line in zip(extraordinary, extra_lines):
            if sum(len(x) + 1 for x in cur) + len(line) > MAX_MSG:
                flush()
                cur.append("⚡ <b>Extraordinary (contd.)</b>")
            cur.append(line)
            keys.append(it["key"])
    for (issue, d), items in sorted(
            ord_groups.items(), key=lambda kv: (kv[0][1] is None, kv[0][1] or date.min),
            reverse=True):
        label = f"📰 <b>Ordinary — Issue {esc(issue)}"
        if d:
            label += f", {d.strftime('%d %b %Y')}"
        label += "</b>"
        if sum(len(x) + 1 for x in cur) + len(label) + 60 > MAX_MSG:
            flush()
        cur.append(label)
        for it in items:
            line, _ = fmt_ord(it)
            if sum(len(x) + 1 for x in cur) + len(line) > MAX_MSG:
                flush()
                cur.append(f"📰 <b>Ordinary (contd.)</b>")
            cur.append(line)
            keys.append(it["key"])
    if chunks or len(cur) > 1:
        cur.append(weekly + f'\n🗂 <a href="{SITE}/">Full archive</a>')
    flush()
    return chunks


# ---------------------------------------------------------------- send

def tg(token, method, payload):
    r = requests.post(API_BASE.format(token=token, method=method), json=payload,
                      timeout=30)
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if not data.get("ok"):
        raise RuntimeError(f"{method}: HTTP {r.status_code} {data or r.text[:200]}")
    return data["result"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--channel", help="e.g. @tngazette (else $TG_CHANNEL / data file)")
    ap.add_argument("--max-age-days", type=int, default=10,
                    help="only post items dated within this many days (default 10)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be sent; never send, never write state")
    ap.add_argument("--sample", action="store_true",
                    help="demo: format recent items ignoring sent-state; no send/state")
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    today = date.today()

    try:
        fresh_init, sent, seen_all, ordinary, extraordinary = collect_items(
            today, args.max_age_days)
    except Exception as exc:  # noqa: BLE001
        print(f"TG_ALERT: error collect: {exc}")
        return 5

    if fresh_init or args.sample:
        # First run (or demo): never post history. In --sample mode show the
        # most recent items purely to preview formatting.
        if args.sample:
            ordinary = [it for it in ordinary if it["recent"]][-8:]
            extraordinary = [it for it in extraordinary if it["recent"]][-8:]
            fresh_init = False
        else:
            save_state({url: today.isoformat() for url in seen_all})
            print(f"TG_ALERT: initialized state with {len(seen_all)} known items; "
                  f"nothing posted (backfill suppressed)")
            return 0

    recent_o = [it for it in ordinary if it["recent"]]
    recent_e = [it for it in extraordinary if it["recent"]]
    stale = [it["key"] for it in ordinary + extraordinary if not it["recent"]]

    if not recent_o and not recent_e:
        if stale:
            sent.update({k: today.isoformat() for k in stale})
            if not args.dry_run:
                save_state(sent)
        print("TG_ALERT: nothing new")
        return 0

    messages = build_messages(recent_o, recent_e, today)

    if args.dry_run or args.sample:
        for text, keys in messages:
            print(f"----- message ({len(text)} chars, {len(keys)} items) -----")
            print(text)
        print(f"TG_DRY_RUN: {len(messages)} message(s), "
              f"{len(recent_o)} ordinary + {len(recent_e)} extraordinary")
        return 0

    channel = (args.channel or os.environ.get("TG_CHANNEL", "")
               or (CHANNEL_FILE.read_text().strip() if CHANNEL_FILE.exists() else ""))
    if not channel:
        print("TG_ALERT: no channel configured (set data/telegram_channel.txt)")
        return 3
    if not token:
        print("TG_ALERT: TELEGRAM_BOT_TOKEN not set")
        return 3

    posted_keys = []
    try:
        for text, keys in messages:
            tg(token, "sendMessage", {
                "chat_id": channel, "text": text, "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
            })
            posted_keys.extend(keys)
            time.sleep(1.5)
    except RuntimeError as exc:
        print(f"TG_ALERT: post failed after {len(posted_keys)} item(s): {exc}")
        if posted_keys:
            sent.update({k: today.isoformat() for k in posted_keys})
            save_state(sent)
        return 4

    sent.update({k: today.isoformat() for k in posted_keys + stale})
    save_state(sent)
    print(f"TG_ALERT: posted {len(messages)} message(s) to {channel}: "
          f"{len(recent_o)} ordinary + {len(recent_e)} extraordinary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
