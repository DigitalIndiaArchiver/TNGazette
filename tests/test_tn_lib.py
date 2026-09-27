"""Tests for tn_lib helpers and dataset schema guards. No network needed."""
import base64
import csv
from pathlib import Path

import pandas as pd
import pytest

from tn_lib import (EXTRAORDINARY_COLUMNS, GAZATTES_COLUMNS, LEGACY_ISSUES_COLUMNS,
                    ISSUES_COLUMNS, b64_year, listing_url, norm_href,
                    split_issue_text)

DATA = Path(__file__).parent.parent / "data"


class TestB64Year:
    @pytest.mark.parametrize("year,expected", [
        (2026, "MjAyNg=="),
        (2024, "MjAyNA=="),
        (2008, "MjAwOA=="),
    ])
    def test_known_encodings(self, year, expected):
        assert b64_year(year) == expected

    def test_roundtrip(self):
        for year in range(2008, 2027):
            assert base64.b64decode(b64_year(year)).decode() == str(year)


class TestListingUrl:
    def test_contains_b64_id(self):
        url = listing_url(2026)
        assert url.startswith(
            "https://www.stationeryprinting.tn.gov.in/gazette.php?id=")
        assert "MjAyNg==" in url


class TestNormHref:
    def test_absolute_passthrough(self):
        url = "https://www.stationeryprinting.tn.gov.in/gazette/2026/38.pdf"
        assert norm_href(url) == url

    def test_http_absolute_passthrough(self):
        assert norm_href("http://x.gov.in/a.pdf") == "http://x.gov.in/a.pdf"

    def test_backslash_relative(self):
        assert norm_href("gazette\\2026\\38_II_1_2026.pdf") == (
            "https://www.stationeryprinting.tn.gov.in/gazette/2026/38_II_1_2026.pdf")

    def test_slash_relative(self):
        assert norm_href("/extraordinary/2026/x.pdf") == (
            "https://www.stationeryprinting.tn.gov.in/extraordinary/2026/x.pdf")

    def test_empty_and_none(self):
        assert norm_href("") == ""
        assert norm_href(None) == ""


class TestSplitIssueText:
    def test_current_format(self):
        assert split_issue_text("38 dated:23-09-2026") == ("38", "23-09-2026")

    def test_whitespace(self):
        assert split_issue_text(" 42 dated: 18-10-2023 ") == ("42", "18-10-2023")

    def test_no_marker(self):
        assert split_issue_text("42") == ("42", "")
        assert split_issue_text("42 - dt. 18-10-2023") == ("42 - dt. 18-10-2023", "")

    def test_malformed_date(self):
        assert split_issue_text("7 dated:not-a-date") == ("7", "")
        assert split_issue_text("7 dated:31-02-2026") == ("7", "")

    def test_empty_and_none(self):
        assert split_issue_text("") == ("", "")
        assert split_issue_text(None) == ("", "")


def _new_format_csvs(pattern):
    """Yearly CSVs from 2024 onward use the new-site schema; 2023 and
    earlier are legacy old-site formats kept for history."""
    return sorted(p for p in DATA.glob(pattern)
                  if int(p.stem.rsplit("_", 1)[1]) >= 2024)


class TestDatasetSchemas:
    """Guard the on-disk CSV contract against silent drift."""

    def test_gazattes_columns_new_format(self):
        for year_csv in _new_format_csvs("Gazattes_2*.csv"):
            with open(year_csv, newline="", encoding="utf-8") as f:
                assert next(csv.reader(f)) == GAZATTES_COLUMNS, year_csv.name

    def test_gazatte_issues_columns(self):
        for year_csv in _new_format_csvs("GazatteIssues_2*.csv"):
            with open(year_csv, newline="", encoding="utf-8") as f:
                header = next(csv.reader(f))
            assert header == ISSUES_COLUMNS, year_csv.name

    def test_gazatte_issues_2023_legacy_format(self):
        path = DATA / "GazatteIssues_2023.csv"
        if not path.exists():
            pytest.skip("GazatteIssues_2023.csv not present")
        with open(path, newline="", encoding="utf-8") as f:
            assert next(csv.reader(f)) == LEGACY_ISSUES_COLUMNS

    def test_extraordinary_columns(self):
        for year_csv in _new_format_csvs("ExtraOrdinaryGazattes_2*.csv"):
            df = pd.read_csv(year_csv, nrows=5)
            assert list(df.columns) == EXTRAORDINARY_COLUMNS, year_csv.name

    def test_no_duplicate_urls_in_yearly_gazattes(self):
        for year_csv in _new_format_csvs("Gazattes_2*.csv"):
            df = pd.read_csv(year_csv)
            dupes = df["URL"].astype(str).duplicated().sum()
            assert dupes == 0, f"{year_csv.name}: {dupes} duplicate URLs"

    def test_issue_dates_parse(self):
        for year_csv in _new_format_csvs("Gazattes_2*.csv"):
            df = pd.read_csv(year_csv)
            parsed = pd.to_datetime(df["Date"], format="%Y-%m-%d",
                                    errors="coerce")
            assert parsed.notna().all(), f"{year_csv.name}: unparseable Date"

    def test_gazattes_2026_has_rows(self):
        path = DATA / "Gazattes_2026.csv"
        if not path.exists():
            pytest.skip("Gazattes_2026.csv not present (backfill pending)")
        assert len(pd.read_csv(path)) > 0
