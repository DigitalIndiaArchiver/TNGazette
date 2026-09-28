#!/usr/bin/env python3
"""Generate the citizen-impact gist for one week's gazette via /zo/ask.

Writes data/gists/{isoYear}-W{ww}.json; build_weekly.py renders it as the
"What this means for you" section. The prompt is grounded in the DISTILLED
TEXT of the week's gazette PDFs (data/markdown/...); items without extracted
text fall back to their CSV listing line. Every prompt block records its
source in the JSON ("sources") so each gist line is traceable. Never invents
facts: the prompt contains only week materials and forbids additions.

Usage:
  python3 scripts/generate_gist.py               # latest week with items
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
from tn_lib import read_rows, GAZATTES_COLUMNS, EXTRAORDINARY_COLUMNS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_weekly import MARKDOWN, parse_extra_date, parse_ord_date, slugify, week_key  # noqa: E402

API = "https://api.zo.computer/zo/ask"
MODEL = os.environ.get("GIST_MODEL", "byok:f13b5a3d-aca5-43b5-a88a-31e1058bc075")
PROJECT = Path(__file__).resolve().parent.parent
GISTS = PROJECT / "data" / "gists"
ORD_BUDGET = 4000      # chars of text per ordinary category (one representative part)
EX_BUDGET = 6000       # chars of text per extraordinary notification
TOTAL_BUDGET = 46000   # prompt cap for all text together


def md_file(gaz, year, issue, part):
    return MARKDOWN / gaz / str(year) / f"{issue}-{slugify(part)}.md"


def doc_text(path, budget):
    """Extracted gazette text, frontmatter stripped, whitespace collapsed."""
    if not path.exists():
        return ""
    t = path.read_text(encoding="utf-8", errors="replace")
    if t.startswith("---"):
        end = t.find("---", 3)
        if end != -1:
            t = t[end + 3:]
    t = " ".join(t.split())
    if "(No extractable text in PDF)" in t:
        return ""
    return t[:budget]


def cut_subject(subject, dept):
    if dept and len(subject) > len(dept):
        idx = subject.find(dept)
        if idx > 0:
            subject = subject[:idx].rstrip(" .-–—;")
    return subject


def week_blocks(year, wk):
    """Prompt blocks for the week, grounded in distilled text where available."""
    wy, ww = wk
    blocks, sources = [], []
    cats = {}
    for r in read_rows(PROJECT / f"data/Gazattes_{year}.csv", GAZATTES_COLUMNS):
        d = parse_ord_date(r.get("Date", ""))
        if d and week_key(d) == wk:
            cat = " ".join(str(r.get("Content") or "").split()) or str(r.get("Part") or "")
            cats.setdefault(cat, []).append(r)
    spent = 0
    for cat, rows in sorted(cats.items(), key=lambda kv: -len(kv[1])):
        text = ""
        src = ""
        for r in rows:  # first part of the category that has distilled text
            p = md_file("ordinary", year, str(r.get("Issue") or ""), str(r.get("Part") or ""))
            budget = min(ORD_BUDGET, max(500, TOTAL_BUDGET - spent))
            text = doc_text(p, budget)
            if text:
                src = str(p.relative_to(PROJECT))
                spent += len(text)
                break
        head = f"ORDINARY, {len(rows)} part(s) in this week: {cat[:160]}"
        if text:
            blocks.append(f"{head}\nDOCUMENT TEXT (truncated): {text}")
            sources.append({"file": src, "kind": "markdown", "chars": len(text)})
        else:
            blocks.append(f"{head}\n(no extracted text available)")
            sources.append({"file": None, "kind": "listing-only", "chars": 0})
    for r in read_rows(PROJECT / f"data/ExtraOrdinaryGazattes_{year}.csv", EXTRAORDINARY_COLUMNS):
        d = parse_extra_date(r.get("Issue Date", ""))
        if not d or week_key(d) != wk:
            continue
        subject = cut_subject(" ".join(str(r.get("Subject") or "").split()),
                              str(r.get("Department") or "").strip())
        dept = str(r.get("Department") or "").strip()
        head = (f"EXTRAORDINARY no.{r.get('Issue No')} ({r.get('Issue Date')}) "
                f"[{dept}]: {subject[:300]}")
        p = md_file("extraordinary", year, str(r.get("Issue No") or ""),
                    str(r.get("Extraordinary Part & Section") or ""))
        text = doc_text(p, min(EX_BUDGET, max(500, TOTAL_BUDGET - spent)))
        if text:
            blocks.append(f"{head}\nDOCUMENT TEXT (truncated): {text}")
            sources.append({"file": str(p.relative_to(PROJECT)), "kind": "markdown",
                            "chars": len(text)})
        else:
            blocks.append(f"{head}\n(no extracted text available)")
            sources.append({"file": None, "kind": "listing-only", "chars": 0})
    return blocks, sources


def prompt_for(blocks, wk):
    return (
        "You write for the TN Gazette Archive, an independent citizen-facing archive of "
        "the Tamil Nadu Government Gazette. Below are the gazette documents published in "
        f"ISO week {wk[1]} of {wk[0]}: for each item the actual document text (truncated) "
        "when extraction succeeded, otherwise just the listing line.\n\n"
        + "\n\n====\n\n".join(blocks)
        + "\n\nWrite 3-8 bullet lines telling an ordinary Tamil Nadu citizen what these "
        "mean in practice: fees changed, appointments made, rules amended, land, temple "
        "staff, elections, RTI disclosures, exam results, schemes and so on. Plain simple "
        "English, at most 25 words per line, one idea per line. Base every line ONLY on "
        "the document text and listing lines above - no outside knowledge, no guessing "
        "beyond what is written; if the text is only a list of names (e.g. name changes), "
        "say so in one short line rather than listing names. Cover every extraordinary "
        "notification; mention ordinary categories only if they matter to daily life. "
        "No preamble, no markdown formatting."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=date.today().year)
    ap.add_argument("--week", type=int, default=None,
                    help="ISO week number (default: latest week with items)")
    args = ap.parse_args()

    def has_items(y, w):
        wy, ww = w
        for r in read_rows(PROJECT / f"data/Gazattes_{y}.csv", GAZATTES_COLUMNS):
            d = parse_ord_date(r.get("Date", ""))
            if d and week_key(d) == w:
                return True
        for r in read_rows(PROJECT / f"data/ExtraOrdinaryGazattes_{y}.csv", EXTRAORDINARY_COLUMNS):
            d = parse_extra_date(r.get("Issue Date", ""))
            if d and week_key(d) == w:
                return True
        return False

    if args.week is None:
        cur = date.today()
        for back in range(4):
            cand = week_key(cur - timedelta(days=7 * back))
            if has_items(args.year, cand):
                wk = cand
                break
        else:
            print("No gazette items in the last 4 weeks; no gist written")
            return
    else:
        wk = (args.year, args.week)
        if not has_items(args.year, wk):
            print(f"No gazette items for {wk[0]} week {wk[1]}; no gist written")
            return

    blocks, sources = week_blocks(args.year, wk)
    n_text = sum(1 for s in sources if s["kind"] == "markdown")
    print(f"Week {wk[0]}-W{wk[1]:02d}: {len(blocks)} items, {n_text} with extracted text, "
          f"{sum(s['chars'] for s in sources)} chars grounded")

    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        print("ZO_CLIENT_IDENTITY_TOKEN missing; cannot call /zo/ask")
        sys.exit(1)

    resp = requests.post(
        API,
        headers={"authorization": token, "content-type": "application/json"},
        json={
            "input": prompt_for(blocks, wk),
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
        "grounding": f"{n_text}/{len(blocks)} items from extracted PDF text",
        "sources": sources,
        "lines": lines,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gist written: {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
