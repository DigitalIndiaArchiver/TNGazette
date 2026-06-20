# TNGazette — Agent Knowledge Base

## Project Overview

Archives Tamil Nadu Government Gazettes (both Ordinary and Extraordinary) from the [Stationery and Printing Department website](https://www.stationeryprinting.tn.gov.in/). Produces CSV datasets published to FlatGitHub and archived to the Internet Archive via Wayback Machine.

## Repository Structure

```
TNGazette/
├── scrape_gazettes.py        # Lightweight scraper for Extraordinary Gazettes only
├── tn_gazette_archiver.py    # Full archiver: Ordinary + Extraordinary + Wayback archival
├── data/                     # Output CSVs
│   ├── ExtraOrdinaryGazattes*.csv
│   ├── Gazattes*.csv
│   └── GazatteIssues*.csv
├── requirements.txt
└── AGENTS.md                 # This file
```

## Website Architecture

### 2024 Website Redesign

The TN government redesigned their website around 2024. Key changes:

| Aspect | Old Site | New Site |
|--------|----------|----------|
| Extraordinary listing | `extraordinary/extraord_list{year}.php` | `extra_ordinary_lists.php?id={base64_year}` |
| Year encoding | Plain year in URL path | Base64-encoded year in `id` param |
| PDF link location | Dedicated "PDF Link" column | Link embedded in "Extraordinary Part & Section" column |
| PDF URL format | Unchanged | `extraordinary/{year}/{issue}_Ex_{part}_{section}_{year}.pdf` |

### Extraordinary Gazette Columns (new site table)

| # | Column | Notes |
|---|--------|-------|
| 0 | Issue No | Gazette issue number |
| 1 | Issue Date | DD-MM-YYYY format |
| 2 | Extraordinary Part & Section | `<a>` tag wraps this with PDF href |
| 3 | Extraordinary Type | Category description |
| 4 | Subject | Full subject text |
| 5 | Department | Issuing department |
| 6 | G.O No | Government Order reference number |

### PDF Link Extraction

In `scrape_gazettes.py`, the PDF link is extracted from `cells[2].find('a').get('href')` and normalized:
```python
if pdf_link and not pdf_link.startswith('http'):
    pdf_link = 'https://www.stationeryprinting.tn.gov.in/' + pdf_link.lstrip('/')
```

### Ordinary Gazette Pages (New Site)

| Page | URL Pattern | Columns |
|------|-------------|---------|
| Issue listing | `gazette.php?id={b64_year}` | Issue No + Date (linked to detail), Particulars |
| Issue details | `gazette_list_details.php?id={b64_issue}&date={b64_date}` | PDF link (href), Content |
| PDF URL format | `gazette/{year}/{issue}_{part}_{section}_{year}.pdf` | Backslashes in href are normalized to `/` |

### URL Deletion Check (`is_url_deleted`)

`tn_gazette_archiver.py` checks PDF availability with `is_url_deleted()`, which returns `True` when a URL returns a non-200 status (404/deleted/moved).

### Wayback Archival

`tn_gazette_archiver.py` uses `waybackpy` to:
1. Check if a URL has an existing Wayback snapshot (CDX API)
2. If not, save it (SaveAPI)
3. Append `Archived URL` and `Archived Date` columns to the DataFrame

## Year Coverage

### scrape_gazettes.py
- Currently configured for 2024, 2025, 2026
- Uses base64 encoding: `base64.b64encode(b'2026').decode()` → `MjAyNg==`
- Single-pass: no Wayback archival, just CSV output

### tn_gazette_archiver.py
- CURRENT_YEAR mode: scrapes current year (based on `datetime.today()`) — new URL pattern
- FULL mode: 2008–2026 (extended to include 2026)
- Extraordinary gazettes: migrated to new URL pattern `extra_ordinary_lists.php?id={b64}`
- Ordinary gazettes: **migrated** to new URL pattern `gazette.php?id={b64_year}`
- Wayback archival: wraps ordinary scrape in try/except so extraordinary data is still produced

## Data Output

CSVs stored in `data/` with columns:
- **ExtraOrdinaryGazattes_{year}.csv**: Issue No, Issue Date, Extraordinary Part & Section, PDF Link, Extraordinary Type, Subject, Department, G.O No
- **Gazattes_{year}.csv**: Part, Content, URL, Date, Issue, Archived URL, Archived Date, Deleted
- **GazatteIssues_{year}.csv**: Issue No and Date, Particulars, URL
