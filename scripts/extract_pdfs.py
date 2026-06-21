#!/usr/bin/env python3
"""
PDF → Markdown extraction pipeline for TNGazette.

Usage:
  python scripts/extract_pdfs.py                         # full run
  python scripts/extract_pdfs.py --years 2026 2025       # specific years
  python scripts/extract_pdfs.py --max 10                # limit entries per year
  python scripts/extract_pdfs.py --gazette extraordinary # only extraordinary
  python scripts/extract_pdfs.py --gazette ordinary      # only ordinary
"""
import argparse, logging, sys, time
from pathlib import Path

import pandas as pd

from extract_utils import (
    PROJECT_ROOT, DATA_DIR, MARKDOWN_DIR,
    fetch_pdf, extract_text, resolve_pdf_url,
    output_path, build_metadata,
    RateLimiter, logger as utils_logger,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract")
utils_logger.setLevel(logging.WARNING)  # less noise from utils

RATE_LIMITER = RateLimiter(delay=0.3)


# ── Data loaders ───────────────────────────────────────────────────────────

def load_extraordinary_source(year):
    if year >= 2024:
        parquet_path = Path(f"/tmp/parquet_data/ExtraOrdinaryGazattes_{year}.parquet")
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            df["year"] = year
            return df, "parquet (direct URL)"
        csv_path = DATA_DIR / f"ExtraOrdinaryGazattes_{year}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df["year"] = year
            return df, "CSV (direct URL)"
        logger.warning("No source for extraordinary %s", year)
        return None, None
    csv_path = DATA_DIR / "ExtraOrdinaryGazattes.csv"
    if not csv_path.exists():
        logger.warning("ExtraOrdinaryGazattes.csv not found")
        return None, None
    df = pd.read_csv(csv_path)
    df["year"] = pd.to_datetime(df["Issue Date"]).dt.year
    df = df[df["year"] == year].copy()
    return df, "CSV (Wayback + fallback)"


def load_ordinary_source(year):
    csv_path = DATA_DIR / "Gazattes.csv"
    if not csv_path.exists():
        logger.warning("Gazattes.csv not found")
        return None, None
    df = pd.read_csv(csv_path)
    df["year"] = pd.to_datetime(df["Date"]).dt.year
    df = df[df["year"] == year].copy()
    return df, "CSV (Wayback + fallback)"


# ── Processing ─────────────────────────────────────────────────────────────

def process_one(row, gazette_type, year):
    pdf_url, url_source = resolve_pdf_url(row)
    if not pdf_url:
        logger.debug("No URL for row, skipping")
        return None

    issue_no = row.get("Issue No") or row.get("Issue") or "unknown"
    part_label = row.get("Gazette Number") or row.get("Extraordinary Part & Section") or row.get("Part") or ""

    out_file = output_path(gazette_type, year, issue_no, part_label)
    if out_file.exists():
        logger.debug("Already exists: %s", out_file.name)
        return out_file

    RATE_LIMITER.wait()
    wb_timeout = 20 if url_source == "wayback" else 45
    pdf_bytes = fetch_pdf(pdf_url, timeout=wb_timeout)
    if not pdf_bytes:
        if url_source == "wayback":
            orig = row.get("URL") or row.get("PDF Link") or ""
            if orig:
                logger.info("Wayback fail, fallback to original URL for issue %s", issue_no)
                RATE_LIMITER.wait()
                pdf_bytes = fetch_pdf(str(orig).strip(), timeout=45)
                if pdf_bytes:
                    url_source = "original_fallback"
    if not pdf_bytes:
        logger.warning("Failed to fetch PDF for issue %s (%s)", issue_no, pdf_url[:80])
        return None

    text = extract_text(pdf_bytes)
    if not text:
        logger.warning("No text extracted for issue %s", issue_no)
        return None

    text_clean = text.strip() if text.strip() else "(No extractable text in PDF)"
    metadata = build_metadata(row, gazette_type, year, url_source, pdf_url)
    frontmatter = _make_frontmatter(metadata)
    content = f"{frontmatter}\n\n{text_clean}\n"
    out_file.write_text(content, encoding="utf-8")
    logger.info("Wrote %s (%s, %s KB)", out_file.name, url_source, len(pdf_bytes) // 1024)
    return out_file


def _make_frontmatter(metadata):
    parts = ["---"]
    for key, value in metadata.items():
        if value is None or (isinstance(value, float) and value != value):
            continue
        s = str(value).strip()
        if not s:
            continue
        escaped = s.replace('"', '\\"')
        parts.append(f'{key}: "{escaped}"')
    parts.append("---")
    return "\n".join(parts)


def process_year(year, gazette_type, max_entries=None):
    if gazette_type == "extraordinary":
        df, source_label = load_extraordinary_source(year)
    else:
        df, source_label = load_ordinary_source(year)

    if df is None or df.empty:
        logger.info("No %s data for %s", gazette_type, year)
        return 0, 0

    logger.info("─ %s %s: %s entries from %s", gazette_type, year, len(df), source_label)

    if max_entries:
        df = df.head(max_entries)

    ok = 0
    fail = 0
    for idx, row in df.iterrows():
        result = process_one(row, gazette_type, year)
        if result:
            ok += 1
        else:
            fail += 1

    return ok, fail


def main():
    parser = argparse.ArgumentParser(description="Extract TNGazette PDFs to Markdown")
    parser.add_argument("--years", nargs="+", type=int, default=None,
                        help="Years to process (default: all available, highest to lowest)")
    parser.add_argument("--gazette", choices=["extraordinary", "ordinary"], default=None,
                        help="Gazette type to process (default: both)")
    parser.add_argument("--max", type=int, default=None,
                        help="Max entries per year (for testing)")
    args = parser.parse_args()

    all_extra_years = list(range(2026, 2007, -1))
    all_ord_years = list(range(2023, 2007, -1))

    if args.years:
        extra_years = [y for y in args.years if y in all_extra_years]
        ord_years = [y for y in args.years if y in all_ord_years]
    else:
        extra_years = all_extra_years
        ord_years = all_ord_years

    total_ok = 0
    total_fail = 0
    total_skip = 0

    types_to_run = ["extraordinary", "ordinary"] if args.gazette is None else [args.gazette]

    for gt in types_to_run:
        logger.info("")
        logger.info("═══════════════════════════════════════════════════════")
        logger.info("  %s gazettes", gt.upper())
        logger.info("═══════════════════════════════════════════════════════")

        years = extra_years if gt == "extraordinary" else ord_years
        for year in years:
            ok, fail = process_year(year, gt, max_entries=args.max)
            total_ok += ok
            total_fail += fail

    logger.info("")
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("  DONE  ●  %d extracted  ●  %d failed", total_ok, total_fail)
    logger.info("  Output: %s", MARKDOWN_DIR)
    logger.info("═══════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
