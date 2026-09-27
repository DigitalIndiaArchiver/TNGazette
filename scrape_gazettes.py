#!/usr/bin/env python3
"""Scrape TN Gazette extraordinary pages and save CSVs + Parquets."""
import base64, csv, io, datetime, sys, requests
from pathlib import Path

from tn_lib import merge_by_key, read_rows
import pandas as pd
from bs4 import BeautifulSoup

years = [
    (base64.b64encode(str(y).encode()).decode(), y)
    for y in range(2024, datetime.date.today().year + 1)
]

HEADERS = ['Issue No', 'Issue Date', 'Extraordinary Part & Section', 'PDF Link',
           'Extraordinary Type', 'Subject', 'Department', 'G.O No']

def esc(val):
    s = str(val or '')
    if ',' in s or '"' in s or '\n' in s:
        return '"' + s.replace('"', '""') + '"'
    return s

failed_years = []
for b64_id, year in years:
    url = f'https://www.stationeryprinting.tn.gov.in/extra_ordinary_lists.php?id={b64_id}'
    print(f'Fetching {year}...')
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f'  Error fetching {year}: {e}')
        failed_years.append(year)
        continue
    soup = BeautifulSoup(resp.content, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f'  No table found for {year}')
        failed_years.append(year)
        continue
    rows = table.find_all('tr')
    data = []
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) >= 7:
            link = cells[2].find('a')
            pdf_link = link.get('href', '') if link else ''
            if pdf_link and not pdf_link.startswith('http'):
                pdf_link = 'https://www.stationeryprinting.tn.gov.in/' + pdf_link.lstrip('/')
            data.append([
                cells[0].get_text(strip=True),
                cells[1].get_text(strip=True),
                cells[2].get_text(strip=True),
                pdf_link,
                cells[3].get_text(strip=True),
                cells[4].get_text(strip=True),
                cells[5].get_text(strip=True),
                cells[6].get_text(strip=True),
            ])
    
    filepath_csv = f'data/ExtraOrdinaryGazattes_{year}.csv'

    # The site only lists a recent window of issues, so a plain overwrite
    # silently drops history when that window shrinks. Merge onto whatever
    # is already on disk, keyed by PDF link; on-disk rows win.
    fresh = [dict(zip(HEADERS, r)) for r in data]
    existing = [
        r for r in read_rows(Path(filepath_csv), HEADERS)
        if r.get('Issue No') != 'Issue No'          # drop a header row if present
        and not r.get('Issue Date') == 'Issue Date'
    ]
    merged = merge_by_key(existing, fresh, 'PDF Link')
    added = len(merged) - len(existing)
    if not merged:
        print(f'  Refusing to write {filepath_csv}: no rows would remain')
        failed_years.append(year)
        continue
    with open(filepath_csv, 'w', newline='', encoding='utf-8') as f:
        f.write(','.join(HEADERS) + '\n')
        for row in merged:
            f.write(','.join(esc(row.get(h, '')) for h in HEADERS) + '\n')
    print(f'  Saved {len(merged)} entries to {filepath_csv} (+{added} new)')

    # Also save as Parquet for machine-friendly consumption
    df = pd.DataFrame(merged, columns=HEADERS)
    filepath_parquet = f'data/ExtraOrdinaryGazattes_{year}.parquet'
    df.to_parquet(filepath_parquet, index=False, engine='pyarrow')
    print(f'  Saved {len(merged)} entries to {filepath_parquet}')

if len(failed_years) == len(years):
    print(f'All {len(years)} years failed to scrape - failing loudly.')
    sys.exit(1)

if failed_years:
    print(f'Partial: years failed: {failed_years}')

print('Done!')
