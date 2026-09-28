#!/usr/bin/env python3
"""Daily TN — under-reported Tamil Nadu government document feeds.

Sources (all primary documents, no press releases):
  go         — Government Orders, dept-wise, www.tn.gov.in/go.php (PDFs on cms.tn.gov.in)
  whatsnew   — tn.gov.in What's New (G.O.s / policy notes / circulars as posted)
  tnpcb_ph   — TNPCB public hearing notices (EIA/exec-summary PDFs)
  seco       — CEO-Tamil Nadu notifications (election commission orders)

Stages:
  --stage ocitwo   run ON an Indian vantage host; prints one JSON blob to stdout
  --stage merge    (local, default) reads that JSON on stdin, merges rows into
                   data/dailytn/*.csv via tn_lib (URL-keyed, on-disk rows win)

Merge key = canonical document URL, so deletions/re-adds never duplicate and
failed Telegram sends retry next run (same design as the gazette alert).
"""

import argparse
import base64
import json
import re
import sys
import time
import urllib.request
from html import unescape
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tn_lib import read_rows, merge_by_key  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) TNGazetteArchiver/1.0"
BASE = "https://www.tn.gov.in"
SECO = "https://www.elections.tn.gov.in"
TNPCB = "https://www.tnpcb.gov.in"
DELAY = 0.4

DATA_DIR = REPO / "data" / "dailytn"

SCHEMAS = {
    "go": ["dept_id", "dept", "go_no", "date", "subject", "URL"],
    "whatsnew": ["category", "title", "date", "URL"],
    "tnpcb_ph": ["project", "extent", "hearing_date", "venue", "deo", "URL", "eia_url"],
    "seco": ["title", "URL"],
}


def b64(s):
    return base64.b64encode(s.encode()).decode()


def get_cookiejar(seed_url):
    """Opener with a PHPSESSID cookie jar seeded from seed_url (some tn.gov.in
    pages 302 to home when the session cookie is missing)."""
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(seed_url, headers={"User-Agent": UA})
    try:
        opener.open(req, timeout=40).read()
    except Exception:
        pass
    return opener


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------- sources

def dept_list():
    """[(dept_id, name)] from the G.O. department A-Z page."""
    h = fetch(f"{BASE}/godept_list.php")
    out = []
    for m in re.finditer(
            r"href=[\"']?go\.php\?dep_id=([A-Za-z0-9+=/]+)&year=[A-Za-z0-9+=/]+[\"']?[^>]*>([^<]+)", h):
        out.append((m.group(1), clean(m.group(2))))
    return out


def scrape_go():
    rows = []
    for dep_id, name in dept_list():
        try:
            h = fetch(f"{BASE}/go.php?dep_id={dep_id}&year={b64('2026')}")
        except Exception:
            continue
        for chunk in h.split('<div class="row go-list">')[1:]:
            dm = re.search(r"<center><b>(\d{2}-\d{2}-\d{4})</b></center>", chunk)
            lm = re.search(
                r"href=['\"](https://cms\.tn\.gov\.in/cms_migrated/document/GO/[^'\"]+)['\"]\s*>([^<]+)<",
                chunk)
            sm = re.search(r'class="event-detail">\s*(.*?)<a\s+target', chunk, re.S)
            if not (dm and lm and sm):
                continue
            rows.append({
                "dept_id": dep_id, "dept": name,
                "go_no": clean(lm.group(2)), "date": dm.group(1),
                "subject": clean(sm.group(1))[:400], "URL": lm.group(1),
            })
        time.sleep(DELAY)
    return rows


def scrape_whatsnew():
    """tn.gov.in What's New via the pagination endpoint the page JS calls
    (test-paginate.php?year=b64). Rows: date | title-link | category."""
    rows = []
    for year in ("2026", "2025"):
        try:
            h = fetch(f"{BASE}/test-paginate.php?year={b64(year)}")
        except Exception:
            continue
        for chunk in re.split(r"<tr", h)[1:]:
            m = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', chunk, re.S)
            if not m:
                continue
            url, title = m.group(1), clean(m.group(2))
            if not title or title.lower().startswith(("click", "read more", "view all", "archive")):
                continue
            if url.startswith(("sites/", "css/", "js/", "#")):
                continue
            if not url.startswith("http"):
                url = f"{BASE}/{url.lstrip('/')}"
            if not any(d in url for d in ("tn.gov.in", "cms.tn.gov.in")):
                continue
            cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", chunk, re.S)]
            date_s = next((c for c in cells if re.search(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", c)), "")
            cat = next((c for c in cells if c and c != date_s and c != title[:len(c)]), "")
            press = "press_release" in url or title.lower().startswith("press release")
            rows.append({"category": "press" if press else (cat or "document"),
                         "title": title[:300], "date": date_s, "URL": url})
    return dedupe(rows)



def scrape_tnpcb():
    h = fetch(f"{TNPCB}/projectstatic.php")
    rows = []
    for chunk in re.split(r"<tr[^>]*>", h):
        if "ExeSum" not in chunk and "EIARpt" not in chunk:
            continue
        tds = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", chunk, re.S)]
        if len(tds) < 5:
            continue
        pdfs = [f"{TNPCB}/{u.lstrip('./')}" for u in
                re.findall(r'href=["\']([^"\']+\.pdf)["\']', chunk)]
        exesum = next((u for u in pdfs if "ExeSumEng" in u), None)
        eia = next((u for u in pdfs if "EIARptEng" in u), None)
        key = exesum or eia
        if not key:
            continue
        # cols: sl, project, extent, hearing date/venue..., venue, DEE office, exesum, -, eia
        rows.append({
            "project": (tds[1] if len(tds) > 1 else "")[:300],
            "extent": (tds[2] if len(tds) > 2 else "")[:150],
            "hearing_date": (tds[3] if len(tds) > 3 else "")[:60],
            "venue": (tds[4] if len(tds) > 4 else "")[:250],
            "deo": (tds[5] if len(tds) > 5 else "")[:250],
            "URL": key, "eia_url": eia or "",
        })
    return dedupe(rows)


def scrape_seco():
    h = fetch(f"{SECO}/Notifications.aspx")
    rows = []
    for chunk in re.split(r"<tr[^>]*>", h):
        if ".pdf" not in chunk.lower():
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", chunk, re.S)
        lm = re.search(r'href=["\']([^"\']+\.pdf)["\']', chunk, re.I)
        if not lm:
            continue
        url = lm.group(1)
        if not url.startswith("http"):
            url = f"{SECO}/{url.lstrip('./')}"
        title = clean(tds[0])[:300] if tds else ""
        if not title:
            title = url.rsplit("/", 1)[-1]
        rows.append({"title": title, "URL": url})
    return dedupe(rows)


def dedupe(rows):
    seen, out = set(), []
    for r in rows:
        k = r["URL"]
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


SOURCES = {
    "go": scrape_go,
    "whatsnew": scrape_whatsnew,
    "tnpcb_ph": scrape_tnpcb,
    "seco": scrape_seco,
}


# --------------------------------------------------------------- stages

def stage_ocitwo():
    out = {}
    for name, fn in SOURCES.items():
        try:
            rows = fn()
        except Exception as e:
            print(f"source {name} failed: {e}", file=sys.stderr)
            rows = []
        out[name] = rows
        print(f"  {name}: {len(rows)}", file=sys.stderr)
    print("SOURCES_JSON_BEGIN")
    print(json.dumps(out, ensure_ascii=False))
    print("SOURCES_JSON_END")


def stage_merge():
    import pandas as pd
    blob = sys.stdin.read()
    m = re.search(r"SOURCES_JSON_BEGIN\n(.*)\nSOURCES_JSON_END", blob, re.S)
    if not m:
        print("DAILYTN: no sources JSON found on stdin")
        return 1
    sources = json.loads(m.group(1))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in sources.items():
        cols = SCHEMAS[name]
        path = DATA_DIR / f"{name}.csv"
        existing = read_rows(path, cols) if path.exists() else []
        merged = merge_by_key(existing, rows, "URL")
        fresh = len(merged) - len(existing)
        pd.DataFrame(merged, columns=cols).astype(str).to_csv(
            path, index=False)
        print(f"DAILYTN_MERGE: {name} existing={len(existing)} total={len(merged)} new={max(fresh, 0)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["ocitwo", "merge"], default="merge")
    args = ap.parse_args()
    if args.stage == "ocitwo":
        stage_ocitwo()
        return 0
    return stage_merge()


if __name__ == "__main__":
    sys.exit(main())
