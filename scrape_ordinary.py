#!/usr/bin/env python3
"""Scrape ordinary TN Gazette issues (latest listing) and write CSVs + Parquets.

The redesigned site's issue listing (gazette.php) is year-independent: it
always serves the most recent ~38 weekly issues regardless of the year id
passed. This script reads the listing, fetches each issue's detail page,
merges the rows into the per-year CSVs under data/ (existing rows win so
Wayback metadata never regresses), and writes CSV + Parquet per year.

Run from an Indian vantage point: stationeryprinting.tn.gov.in times out
for non-India IPs, so GitHub-hosted runners cannot fetch it. The workflow
preflights reachability and skips this step loudly when blocked.

Usage:
  python scrape_ordinary.py                        # current year, no proxy
  python scrape_ordinary.py --proxy socks5h://127.0.0.1:31080
  python scrape_ordinary.py --year 2026 --check-deleted --delay 1.0
"""
import argparse
import base64
import os
import sys
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from tn_lib import (GAZATTES_COLUMNS, ISSUES_COLUMNS, b64_year, listing_url,
                    norm_href, split_issue_text)

BASE = "https://www.stationeryprinting.tn.gov.in/"


def build_session(proxy):
    s = requests.Session()
    s.headers["User-Agent"] = "TNGazette Archiver (github.com/DigitalIndiaArchiver/TNGazette)"
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


def norm_detail_href(href):
    """Detail-page hrefs are relative (gazette_list_details.php?id=...)."""
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return BASE + href.lstrip("/")


def fetch_listing_issues(session, year):
    """Return issue dicts for the latest ~38 issues from the listing page."""
    resp = session.get(listing_url(year), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    table = soup.find("table")
    if not table:
        raise RuntimeError("no issue-listing table found")

    issues, seen = [], set()
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        link = cells[0].find("a")
        if not link:
            continue  # rows of the nested particulars table carry no links
        url = norm_detail_href(link.get("href", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        full_text = cells[0].get_text(strip=True)
        issue_no, date_str = split_issue_text(full_text)
        issues.append({"issue_no": issue_no, "date_str": date_str,
                       "full_text": full_text, "url": url})
    if not issues:
        raise RuntimeError("issue listing parsed to zero rows")
    return issues


def fetch_issue_parts(session, issue):
    """Return (part, content, pdf_url) rows for one issue detail page."""
    resp = session.get(issue["url"], timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link = cells[0].find("a")
        pdf_url = norm_href(link.get("href", "")) if link else ""
        if not pdf_url:
            continue
        rows.append((cells[0].get_text(strip=True),
                     cells[1].get_text(strip=True),
                     pdf_url))
    return rows


def is_deleted(session, url):
    try:
        r = session.get(url, stream=True, timeout=30)
        return r.status_code != 200
    except requests.RequestException:
        return True


def load_existing(csv_path):
    if csv_path.exists():
        return pd.read_csv(csv_path, dtype=str).fillna("")
    return pd.DataFrame(columns=GAZATTES_COLUMNS)


def merge_year(existing, new_rows, cols):
    """Existing rows win so Deleted/Archived metadata never regresses."""
    if existing is not None and not existing.empty:
        combined = pd.concat([existing, new_rows], ignore_index=True)
    else:
        combined = new_rows
    combined = combined.drop_duplicates(subset="URL", keep="first")
    return combined[cols]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=pd.Timestamp.today().year)
    ap.add_argument("--proxy", default="",
                    help="proxy URL for Indian vantage, e.g. socks5h://127.0.0.1:31080")
    ap.add_argument("--check-deleted", action="store_true",
                    help="liveness-check PDF URLs for new rows (Indian vantage only)")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between issue fetches")
    args = ap.parse_args()

    session = build_session(args.proxy)

    print(f"Fetching ordinary issue listing for {args.year}...")
    issues = fetch_listing_issues(session, args.year)
    print(f"  {len(issues)} issues in listing "
          f"({issues[-1]['date_str']} .. {issues[0]['date_str']})")

    gaz_rows, issue_rows = [], []
    for i, issue in enumerate(issues, 1):
        try:
            parts = fetch_issue_parts(session, issue)
        except requests.RequestException as e:
            print(f"  [{i}/{len(issues)}] {issue['issue_no']}: fetch failed: {e}")
            continue
        gaz_rows.extend((part, content, url, issue["date_str"],
                         issue["issue_no"], "", "", "")
                        for part, content, url in parts)
        issue_rows.append((issue["issue_no"], issue["full_text"],
                           issue["date_str"], issue["url"]))
        print(f"  [{i}/{len(issues)}] issue {issue['issue_no']} "
              f"({issue['date_str']}): {len(parts)} parts")
        time.sleep(args.delay)

    if not gaz_rows:
        print("No ordinary gazette rows scraped - failing loudly.")
        sys.exit(1)

    gaz = pd.DataFrame(gaz_rows, columns=[
        "Part", "Content", "URL", "Date", "Issue",
        "Deleted", "Archived URL", "Archived Date"])
    iss = pd.DataFrame(issue_rows, columns=ISSUES_COLUMNS)

    for df, date_fmt in ((gaz, "Date"), (iss, "Date")):
        df["DateISO"] = pd.to_datetime(
            df[date_fmt], format="%d-%m-%Y", errors="coerce").dt.strftime("%Y-%m-%d")
        df.dropna(subset=["DateISO"], inplace=True)
    gaz["Date"] = gaz["DateISO"]
    iss["Date"] = iss["DateISO"]
    gaz.drop(columns="DateISO", inplace=True)
    iss.drop(columns="DateISO", inplace=True)

    if args.check_deleted:
        print("Checking liveness of new PDF URLs...")
        gaz["Deleted"] = [
            str(is_deleted(session, url)) if url else ""
            for url in gaz["URL"]
        ]
        time.sleep(0.3)

    written = []
    for year, year_gaz in gaz.groupby(gaz["Date"].str[:4]):
        year = str(year)
        csv_path = f"data/Gazattes_{year}.csv"
        existing = load_existing(csv_path)
        merged = merge_year(existing, year_gaz, GAZATTES_COLUMNS)
        merged.to_csv(csv_path, index=False)
        merged.to_parquet(f"data/Gazattes_{year}.parquet",
                          index=False, engine="pyarrow")
        written.append(f"{csv_path}: {len(merged)} rows "
                       f"({len(merged) - len(existing)} new)")

    for year, year_iss in iss.groupby(iss["Date"].str[:4]):
        year = str(year)
        csv_path = f"data/GazatteIssues_{year}.csv"
        existing = (pd.read_csv(csv_path, dtype=str).fillna("")
                    if os.path.exists(csv_path)
                    else pd.DataFrame(columns=ISSUES_COLUMNS))
        merged = existing.drop_duplicates(subset="URL", keep="first")
        merged = (pd.concat([merged, year_iss], ignore_index=True)
                  .drop_duplicates(subset="URL", keep="first"))[ISSUES_COLUMNS]
        merged.to_csv(csv_path, index=False)
        merged.to_parquet(f"data/GazatteIssues_{year}.parquet",
                          index=False, engine="pyarrow")
        written.append(f"{csv_path}: {len(merged)} rows")

    print("\n".join(f"Wrote {w}" for w in written))
    print("Done!")


if __name__ == "__main__":
    main()
