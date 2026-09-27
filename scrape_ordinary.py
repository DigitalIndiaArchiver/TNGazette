#!/usr/bin/env python3
"""Scrape ordinary gazette issues + part listings from the redesigned site.

Writes/merges data/Gazattes_{year}.csv (+ .parquet) and
data/GazatteIssues_{year}.csv (+ .parquet), split by issue-date year.

The listing page exposes only the most recent ~38 weekly issues, so each
run merges freshly fetched rows into the existing year files (URL is the
join key; rows already on disk win, preserving their Wayback status).

The site blocks non-India IPs — run from an Indian vantage point (see
README, 'Where scraping runs'). Exits 1 when zero issues are fetched.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from tn_lib import (BASE_URL, GAZATTES_COLUMNS, ISSUES_COLUMNS, b64_year,
                    listing_url, norm_href, split_issue_text)

DATA_DIR = "data"


def fetch(session, url, timeout=30):
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def parse_issue_listing(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    issues = []
    seen = set()
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link = cells[0].find("a")
        if not link:
            continue  # nested particulars rows carry no issue link
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


def read_existing(path):
    if not path.exists():
        cols = GAZATTES_COLUMNS if "Gazattes_" in path.name else ISSUES_COLUMNS
        return pd.DataFrame(columns=cols)
    return pd.read_csv(path, dtype={"Issue": str, "Issue No": str})


def merge_year_frames(existing, fresh, key_cols):
    if existing.empty:
        return fresh
    combined = pd.concat([existing, fresh], ignore_index=True)
    return combined.drop_duplicates(subset=key_cols, keep="first")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=datetime.today().year,
                        help="Year id to request from the listing page")
    parser.add_argument("--delay", type=float, default=0.7,
                        help="Seconds between requests (be polite)")
    args = parser.parse_args()

    import requests
    session = requests.Session()
    session.headers["User-Agent"] = (
        "TNGazette Archiver (github.com/DigitalIndiaArchiver/TNGazette)")

    url = listing_url(args.year)
    print(f"Fetching ordinary gazette issue listing for {args.year}...")
    issues = parse_issue_listing(fetch(session, url))
    print(f"  {len(issues)} issues listed")
    if not issues:
        print("No issues parsed from listing — site layout changed or blocked.")
        sys.exit(1)

    issues_df = pd.DataFrame(issues, columns=ISSUES_COLUMNS)
    issues_df["Date"] = pd.to_datetime(issues_df["Date"])

    rows = []
    for i, issue in enumerate(issues, 1):
        detail = parse_issue_details(fetch(session, issue["URL"]))
        for part, content, pdf_url in detail:
            rows.append([part, content, pdf_url,
                         issue["Date"].strftime("%Y-%m-%d"),
                         issue["Issue No"], False, "", ""])
        print(f"  [{i}/{len(issues)}] issue {issue['Issue No']} "
              f"({issue['Date'].date()}): {len(detail)} parts")
        time.sleep(args.delay)

    gazattes_df = pd.DataFrame(rows, columns=GAZATTES_COLUMNS)

    years = sorted({d.year for d in issues_df["Date"]})
    for year in years:
        issues_year = issues_df[issues_df["Date"].dt.year == year].copy()
        gazattes_year = gazattes_df[pd.to_datetime(
            gazattes_df["Date"], format="%Y-%m-%d").dt.year == year].copy()

        issues_path = f"{DATA_DIR}/GazatteIssues_{year}.csv"
        gazattes_path = f"{DATA_DIR}/Gazattes_{year}.csv"
        issues_merged = merge_year_frames(
            read_existing(Path(issues_path)), issues_year, ["URL"])
        gazattes_merged = merge_year_frames(
            read_existing(Path(gazattes_path)), gazattes_year, ["URL"])

        issues_merged.to_csv(issues_path, index=False, date_format="%Y-%m-%d")
        gazattes_merged.to_csv(gazattes_path, index=False, date_format="%Y-%m-%d")
        issues_merged.to_parquet(issues_path.replace(".csv", ".parquet"),
                                 index=False, engine="pyarrow")
        gazattes_merged.to_parquet(gazattes_path.replace(".csv", ".parquet"),
                                   index=False, engine="pyarrow")
        print(f"  {year}: {len(gazattes_merged)} parts, "
              f"{len(issues_merged)} issues -> {gazattes_path}")

    total_fetched = len(gazattes_df)
    if total_fetched == 0:
        print("Fetched issues but zero part rows parsed — site layout changed.")
        sys.exit(1)
    print(f"Done: {len(issues_df)} issues, {total_fetched} part rows fetched.")


if __name__ == "__main__":
    main()
