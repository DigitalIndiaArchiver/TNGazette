"""Tests for tn_lib helpers and dataset schema integrity. No network needed."""
import pandas as pd
import pytest
from pathlib import Path

from tn_lib import (EXTRAORDINARY_COLS, GAZZATTE_COLS, ISSUE_COLS, b64_year,
                    listing_url, norm_href, split_issue_text)

DATA = Path(__file__).parent / "data"


def test_b64_year():
    assert b64_year(2026) == "MjAyNg=="
    assert b64_year(2024) == "MjAyNA=="
    assert b64_year(2008) == "MjAwOA=="


def test_listing_url_contains_b64_id():
    url = listing_url(2026)
    assert url.startswith("https://www.stationeryprinting.tn.gov.in/gazette.php?id=")
    assert "MjAyNg==" in url


def test_norm_href_absolute_passthrough():
    assert norm_href("https://x.gov.in/a.pdf") == "https://x.gov.in/a.pdf"


def test_norm_href_relative_and_backslashes():
    assert norm_href("gazette\\2026\\38_II_1_2026.pdf") == \
        "https://www.stationeryprinting.tn.gov.in/gazette/2026/38_II_1_2026.pdf"
    assert norm_href("/extraordinary/2026/a.pdf") == \
        "https://www.stationeryprinting.tn.gov.in/extraordinary/2026/a.pdf"
    assert norm_href("") == ""


def test_split_issue_text():
    issue_no, date = split_issue_text("38 dated:23-09-2026")
    assert issue_no == "38"
    assert (date.year, date.month, date.day) == (2026, 9, 23)


def test_split_issue_text_malformed():
    assert split_issue_text("") == ("", None)
    assert split_issue_text("42 - dt. 18-10-2023")[1] is None
    assert split_issue_text("7 dated:not-a-date")[1] is None


def _csv(name):
    return pd.read_csv(DATA / name)


def _new_format_csvs(pattern):
    """Yearly CSVs from 2024 onward use the new-site schema; 2023 and earlier
    are legacy old-site formats kept for history."""
    return sorted(p for p in DATA.glob(pattern)
                  if int(p.stem.rsplit("_", 1)[1]) >= 2024)


def test_gazattes_schema():
    for year_csv in _new_format_csvs("Gazattes_2*.csv"):
        df = pd.read_csv(year_csv, nrows=5)
        assert list(df.columns) == GAZZATTE_COLS, year_csv.name


def test_gazatte_issues_schema():
    for year_csv in _new_format_csvs("GazatteIssues_2*.csv"):
        df = pd.read_csv(year_csv, nrows=5)
        assert list(df.columns) == ISSUE_COLS, year_csv.name


def test_extraordinary_schema():
    for year_csv in DATA.glob("ExtraOrdinaryGazattes_2*.csv"):
        df = pd.read_csv(year_csv, nrows=5)
        assert list(df.columns) == EXTRAORDINARY_COLS, year_csv.name


def test_no_duplicate_urls_in_yearly_gazattes():
    for year_csv in _new_format_csvs("Gazattes_2*.csv"):
        df = pd.read_csv(year_csv)
        dupes = df["URL"].astype(str).duplicated().sum()
        assert dupes == 0, f"{year_csv.name}: {dupes} duplicate URLs"


def test_issue_numbers_parse_as_dates():
    for year_csv in _new_format_csvs("GazatteIssues_2*.csv"):
        df = pd.read_csv(year_csv)
        parsed = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
        assert parsed.notna().all(), f"{year_csv.name}: unparseable Date values"
