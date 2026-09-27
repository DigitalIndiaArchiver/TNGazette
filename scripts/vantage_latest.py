#!/usr/bin/env python3
"""Fetch only NEW TN Gazette rows since a known-URL state (runs on Indian vantage).

Mirrors scrape_ordinary.py / scrape_gazettes.py parsing but emits a delta:
  - ordinary: listing window issues whose detail URL is unknown -> fetch their
    detail pages, keep part rows whose PDF URL is unknown
  - extraordinary: current-year listing rows whose PDF Link is unknown
Downloads only the new PDFs. Writes delta.json + pdfs/<md5>.pdf into --out.

Exit codes: 0 ok (delta may be empty) | 2 site unreachable | 3 nothing parsed.

Usage:
  python3 vantage_latest.py --state state.json --out ./out --year 2026 [--delay 0.7]
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from tn_lib import BASE_URL, listing_url, norm_href, split_issue_text

HEADERS = ["Issue No", "Issue Date", "Extraordinary Part & Section", "PDF Link",
           "Extraordinary Type", "Subject", "Department", "G.O No"]
UA = "TNGazette Archiver (github.com/DigitalIndiaArchiver/TNGazette)"


def fetch(session, url, timeout=30, tries=2):
    last = None
    for _ in range(tries):
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            last = exc
            time.sleep(2)
    raise ConnectionError("unreachable: %s (%s)" % (url[:90], last))


def parse_issue_listing(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    issues, seen = [], set()
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link = cells[0].find("a")
        if not link:
            continue
        issue_no, date_str = split_issue_text(link.get_text(strip=True))
        detail_url = norm_href(link.get("href", ""))
        if not issue_no or not date_str or not detail_url or detail_url in seen:
            continue
        try:
            issue_date = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            continue
        seen.add(detail_url)
        issues.append({
            "Issue No": issue_no,
            "Issue No and Date": link.get_text(strip=True),
            "Date": issue_date,
            "URL": detail_url,
        })
    return issues


def parse_issue_details(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link = cells[0].find("a")
        if not link:
            continue
        part = cells[0].get_text(strip=True)
        content = cells[1].get_text(strip=True)
        rows.append((part, content, norm_href(link.get("href", ""))))
    return rows


def parse_extraordinary(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    out = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 7:
            continue
        link = cells[2].find("a")
        pdf_link = link.get("href", "") if link else ""
        if pdf_link and not pdf_link.startswith("http"):
            pdf_link = BASE_URL + pdf_link.lstrip("/")
        values = [cells[0].get_text(strip=True),
                  cells[1].get_text(strip=True),
                  cells[2].get_text(strip=True),
                  pdf_link,
                  cells[3].get_text(strip=True),
                  cells[4].get_text(strip=True),
                  cells[5].get_text(strip=True),
                  cells[6].get_text(strip=True)]
        out.append(dict(zip(HEADERS, values)))
    return out


def pdf_name(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest() + ".pdf"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", required=True, help="state.json with known URLs")
    ap.add_argument("--out", required=True, help="output dir for delta.json + pdfs/")
    ap.add_argument("--year", type=int, default=datetime.now().year)
    ap.add_argument("--delay", type=float, default=0.7)
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    out = Path(args.out)
    (out / "pdfs").mkdir(parents=True, exist_ok=True)
    state = json.loads(Path(args.state).read_text())
    known_parts = set(state.get("ordinary_parts", []))
    known_issues = set(state.get("ordinary_issues", []))
    known_extra = set(state.get("extraordinary", []))

    session = requests.Session()
    session.headers["User-Agent"] = UA

    # ordinary ----------------------------------------------------------------
    issues = parse_issue_listing(fetch(session, listing_url(args.year), args.timeout))
    if not issues:
        print("PARSE_FAIL: ordinary listing empty")
        sys.exit(3)
    new_issues = [i for i in issues if i["URL"] not in known_issues]
    new_parts = []
    for i, issue in enumerate(new_issues, 1):
        details = parse_issue_details(fetch(session, issue["URL"], args.timeout))
        for part, content, pdf_url in details:
            if not pdf_url or pdf_url in known_parts:
                continue
            known_parts.add(pdf_url)
            new_parts.append({
                "Part": part, "Content": content, "URL": pdf_url,
                "Date": issue["Date"].strftime("%Y-%m-%d"),
                "Issue": issue["Issue No"],
                "Deleted": "False", "Archived URL": "", "Archived Date": "",
            })
        print("  [ordinary %d/%d] issue %s (%s): %d new parts"
              % (i, len(new_issues), issue["Issue No"], issue["Date"].date(), len(details)))
        time.sleep(args.delay)

    # extraordinary -----------------------------------------------------------
    extra_url = ("https://www.stationeryprinting.tn.gov.in/extra_ordinary_lists.php"
                 "?id=" + __import__("base64").b64encode(str(args.year).encode()).decode())
    extra_rows = parse_extraordinary(fetch(session, extra_url, args.timeout))
    if extra_rows is None:
        extra_rows = []
    new_extra = []
    for row in extra_rows:
        link = (row.get("PDF Link") or "").strip()
        if not link or link in known_extra:
            continue
        known_extra.add(link)
        new_extra.append(row)

    # download new PDFs -------------------------------------------------------
    downloads = []
    for row in new_parts + new_extra:
        url = row["URL"] if "URL" in row else row["PDF Link"]
        dest = out / "pdfs" / pdf_name(url)
        if dest.exists() and dest.stat().st_size > 0:
            downloads.append({"url": url, "file": dest.name, "bytes": dest.stat().st_size})
            continue
        try:
            blob = fetch(session, url, timeout=45)
            if blob[:5] != b"%PDF-" and b"<html" in blob[:500].lower():
                print("  SKIP non-pdf: %s" % url[:80])
                continue
            dest.write_bytes(blob)
            downloads.append({"url": url, "file": dest.name, "bytes": len(blob)})
            print("  downloaded %s (%d KB)" % (dest.name, len(blob) // 1024))
            time.sleep(args.delay)
        except ConnectionError as exc:
            print("  DL_FAIL %s: %s" % (url[:80], exc))

    delta = {
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "year": args.year,
        "new_issues": [{"Issue No": i["Issue No"], "Issue No and Date": i["Issue No and Date"],
                        "Date": i["Date"].strftime("%Y-%m-%d"), "URL": i["URL"]} for i in new_issues],
        "new_parts": new_parts,
        "new_extraordinary": new_extra,
        "downloads": downloads,
    }
    (out / "delta.json").write_text(json.dumps(delta, ensure_ascii=False, indent=1))
    print("SUMMARY: issues=%d parts=%d extra=%d pdfs=%d"
          % (len(new_issues), len(new_parts), len(new_extra), len(downloads)))


if __name__ == "__main__":
    main()
