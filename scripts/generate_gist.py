#!/usr/bin/env python3
"""Generate the citizen-impact gist for one week's gazette via /zo/ask.

Writes data/gists/{isoYear}-W{ww}.json; build_weekly.py renders it as the
"What this means for you" section. Never invents facts: the prompt contains
only the week's actual items and forbids additions.

Usage:
  python3 scripts/generate_gist.py               # current ISO week
  python3 scripts/generate_gist.py --year 2026 --week 39
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tn_lib import read_rows, GAZATTES_COLUMNS, EXTRAORDINARY_COLUMNS

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_weekly import parse_extra_date, parse_ord_date, week_key  # noqa: E402

API = "https://api.zo.computer/zo/ask"
MODEL = os.environ.get("GIST_MODEL", "byok:f13b5a3d-aca5-43b5-a88a-31e1058bc075")
PROJECT = Path(__file__).resolve().parent.parent
GISTS = PROJECT / "data" / "gists"


def week_items(year, wk):
    """Same item list the TL;DR block renders, as plain text for the prompt."""
    wy, ww = wk
    items = []
    cats = {}
    for r in read_rows(PROJECT / f"data/Gazattes_{year}.csv", GAZATTES_COLUMNS):
        d = parse_ord_date(r.get("Date", ""))
        if d and week_key(d) == wk:
            cat = " ".join(str(r.get("Content") or "").split())
            cats.setdefault(cat or str(r.get("Part") or ""), 0)
            cats[cat or str(r.get("Part") or "")] += 1
    for cat, n in sorted(cats.items(), key=lambda kv: -kv[1]):
        items.append(f"ORDINARY ({n} part{'s' if n > 1 else ''}): {cat[:200]}")
    for r in read_rows(PROJECT / f"data/ExtraOrdinaryGazattes_{year}.csv", EXTRAORDINARY_COLUMNS):
        d = parse_extra_date(r.get("Issue Date", ""))
        if d and week_key(d) == wk:
            subject = " ".join(str(r.get("Subject") or "").split())
            dept = str(r.get("Department") or "").strip()
            if dept and len(subject) > len(dept):
                idx = subject.find(dept)
                if idx > 0:
                    subject = subject[:idx].rstrip(" .-–—;")
            items.append(f"EXTRAORDINARY no.{r.get('Issue No')} ({r.get('Issue Date')}) "
                         f"[{dept}]: {subject[:300]}")
    return items


def prompt_for(items, wk):
    return (
        "You write for the TN Gazette Archive, an independent citizen-facing archive of "
        "the Tamil Nadu Government Gazette. Below is EVERY item the gazette published in "
        f"ISO week {wk[1]} of {wk[0]}.\n\n"
        + "\n".join(items)
        + "\n\nWrite 3-7 bullet lines telling an ordinary Tamil Nadu citizen what these "
        "mean in practice: fees changed, appointments made, rules amended, land, temple "
        "staff, elections, RTI disclosures, name changes and so on. Plain simple English, "
        "at most 25 words per line, one idea per line. Cover every extraordinary "
        "notification; mention ordinary categories only if they matter to daily life. "
        "Strictly no facts beyond the list above; if an item is unclear, describe it "
        "exactly as listed. No preamble, no markdown formatting."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--week", type=int, default=None,
                    help="ISO week number (default: current week)")
    args = ap.parse_args()

    if args.week is None:
        cur = date.today()
        for back in range(4):
            cand = week_key(cur - timedelta(days=7 * back))
            if week_items(args.year, cand):
                wk = cand
                break
        else:
            print("No gazette items in the last 4 weeks; no gist written")
            return
    else:
        wk = (args.year, args.week)
        if not week_items(args.year, wk):
            print(f"No gazette items for {wk[0]} week {wk[1]}; no gist written")
            return
    items = week_items(args.year, wk)
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        print("ZO_CLIENT_IDENTITY_TOKEN missing; cannot call /zo/ask")
        sys.exit(1)

    resp = requests.post(
        API,
        headers={"authorization": token, "content-type": "application/json"},
        json={
            "input": prompt_for(items, wk),
            "model_name": MODEL,
            "output_format": {
                "type": "object",
                "properties": {"lines": {"type": "array", "items": {"type": "string"}}},
                "required": ["lines"],
            },
        },
        timeout=240,
    )
    resp.raise_for_status()
    output = resp.json().get("output")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except ValueError:
            output = None
    lines = output.get("lines") if isinstance(output, dict) else None
    if not lines or not isinstance(lines, list):
        print("Model returned no usable lines")
        sys.exit(1)
    lines = [str(x).strip() for x in lines if str(x).strip()][:8]

    GISTS.mkdir(parents=True, exist_ok=True)
    out = GISTS / f"{wk[0]}-W{wk[1]:02d}.json"
    out.write_text(json.dumps({
        "week": list(wk),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": MODEL,
        "lines": lines,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gist written: {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
