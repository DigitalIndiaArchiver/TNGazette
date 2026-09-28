#!/usr/bin/env python3
"""Post the Daily TN digest (underreported TN govt document feeds) to Telegram.

Reads data/dailytn/digest-latest.json (written by build_daily.py) and posts
one message to the channel from data/telegram_channel.txt. Silent (exit 0,
no message) when the digest is empty or already sent; a sent-marker
(data/dailytn/.digest_sent.json) keyed on the digest's "generated" timestamp
prevents double posts within the same digest window.

Exit codes: 0 ok/silent · 3 not configured · 4 Telegram API error.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIGEST = REPO / "data" / "dailytn" / "digest-latest.json"
SENT_MARKER = REPO / "data" / "dailytn" / ".sent.json"
CHANNEL_FILE = REPO / "data" / "telegram_channel.txt"
MAX_MSG = 3800

SOURCE_LABELS = {
    "go": "📜 G.O.s (cms.tn.gov.in)",
    "whatsnew": "🗂 What's New on tn.gov.in",
    "tnpcb_ph": "🌍 TNPCB public hearings",
    "seco": "🗳 CEO-TN notifications",
}
FIELD_ORDER = {
    "go": [("go_no", ""), ("dept", ""), ("date", "")],
    "whatsnew": [("date", ""), ("category", "")],
    "tnpcb_ph": [("hearing_date", ""), ("deo", "")],
    "seco": [],
}


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def item_line(source, row):
    url = str(row.get("URL") or "").replace("\\", "/")
    link = f'<a href="{esc(url)}">PDF</a>' if url.startswith("http") else "—"
    title = str(row.get("subject") or row.get("title") or "")[:200]
    bits = []
    for key, _ in FIELD_ORDER.get(source, []):
        v = str(row.get(key) or "").strip()
        if v:
            bits.append(esc(v[:80]))
    meta = " · ".join(bits)
    line = f"• {esc(title)} — {meta} · {link}" if meta else f"• {esc(title)} · {link}"
    return line


def build_messages(digest):
    total = sum(digest.get("counts", {}).values())
    if total == 0:
        return []
    date_str = digest.get("date", "")
    head = (f"🗄 <b>Daily TN</b> · {esc(date_str)}\n"
            f"{total} new underreported document(s)")
    chunks, cur = [], [head]

    def flush():
        chunks.append("\n".join(cur))
        cur.clear()

    for source, rows in digest.get("sections", {}).items():
        count = digest.get("counts", {}).get(source, 0)
        if not count:
            continue
        block = [f"\n{SOURCE_LABELS.get(source, source)} ({count})"]
        for row in rows:
            line = item_line(source, row)
            if sum(len(x) + 1 for x in cur) + len(line) > MAX_MSG - 120:
                block.append("… more in the daily page")
                break
            block.append(line)
        block.append(f'\n🗂 <a href="https://digitalindiaarchiver.github.io/TNGazette/daily/">Daily page</a>')
        if sum(len(x) + 1 for x in cur) + sum(len(x) + 1 for x in block) > MAX_MSG:
            flush()
        cur.extend(block)
    flush()
    return [c for c in chunks if c.strip()]


def send(token, channel, text):
    data = urllib.parse.urlencode({
        "chat_id": channel, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print, don't send")
    args = ap.parse_args()

    if not DIGEST.exists():
        print("DTN_ALERT: no digest yet")
        return 0
    digest = json.loads(DIGEST.read_text())

    messages = build_messages(digest)
    if not messages:
        print("DTN_ALERT: nothing new — silent")
        return 0

    if args.dry_run:
        for i, m in enumerate(messages, 1):
            print(f"----- message {i} ({len(m)} chars) -----")
            print(m)
        print(f"DTN_DRY_RUN: {len(messages)} message(s)")
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = (os.environ.get("TG_CHANNEL")
               or (CHANNEL_FILE.read_text().strip() if CHANNEL_FILE.exists() else ""))
    if not token or not channel:
        print("DTN_ALERT: missing token or channel; not sending")
        return 3
    ok = 0
    for m in messages:
        try:
            res = send(token, channel, m)
            if res.get("ok"):
                ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"DTN_ALERT: send error: {exc}")
            return 4
    today = digest.get("date", "")
    try:
        sent_map = json.loads(SENT_MARKER.read_text())
    except (OSError, ValueError):
        sent_map = {}
    for u in digest.get("urls", []):
        sent_map[u] = today
    SENT_MARKER.write_text(json.dumps(sent_map, indent=0, sort_keys=True))
    total = sum(digest.get("counts", {}).values())
    print(f"DTN_ALERT: posted {ok} message(s) to {channel} ({total} new items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
