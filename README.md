# TN Gazette Extractor & Archiver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FlatGithub](https://img.shields.io/badge/FlatGithub-View%20Data-green?style=flat-square&logo=github)](https://flatgithub.com/srikanthlogic/TNGazette)
[![Open in Gitpod](https://img.shields.io/badge/Open%20in-Gitpod-blue?logo=gitpod)](https://gitpod.io/#https://github.com/srikanthlogic/TNGazette)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7855631.svg)](https://doi.org/10.5281/zenodo.7855631)

Archives Tamil Nadu Government Gazettes (Ordinary & Extraordinary) from the [Stationery and Printing Department website](https://www.stationeryprinting.tn.gov.in/). Produces CSV and Parquet datasets published to FlatGitHub and archived to the Internet Archive via Wayback Machine.

## Data Formats

Both CSV and [Parquet](https://parquet.apache.org/) files are generated:

| Format | Size (2025) | Use case |
|--------|-------------|----------|
| CSV | 179 MB | Human-readable, editable in any spreadsheet or text editor |
| Parquet | 42 MB | Machine-friendly, fast analytical queries, type-preserving |

Parquet compresses ~4× smaller than CSV and preserves column types (dates, integers) — ideal for programmatic analysis with pandas, DuckDB, or any Parquet-compatible tool.

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Quick scrape — Extraordinary Gazettes only (2024–2026)
python scrape_gazettes.py

# Full archive — Ordinary + Extraordinary + Wayback archival
python tn_gazette_archiver.py [--archive-mode full|current-year]
```

### scrape_gazettes.py

Lightweight single-pass scraper for Extraordinary Gazettes. Currently configured for 2024–2026. Saves CSV + Parquet to `data/`.

### tn_gazette_archiver.py

Full archiver that:
- Scrapes both Ordinary and Extraordinary Gazettes
- Runs Wayback Machine archival on PDF links
- Supports `current-year` (default) and `full` (2008–2026) modes

## Output

Files are saved to `data/`:

- `ExtraOrdinaryGazattes_{year}.csv` / `.parquet` — Extraordinary gazette entries
- `Gazattes_{year}.csv` / `.parquet` — Ordinary gazette entries
- `GazatteIssues_{year}.csv` / `.parquet` — Ordinary gazette issue listing

### Extraordinary Gazette Columns

| Column | Description |
|--------|-------------|
| Issue No | Gazette issue number |
| Issue Date | Publication date |
| Extraordinary Part & Section | Section identifier (PDF link embedded) |
| PDF Link | Direct URL to the PDF |
| Extraordinary Type | Category description |
| Subject | Full subject text |
| Department | Issuing department |
| G.O No | Government Order reference number |

## License

MIT
