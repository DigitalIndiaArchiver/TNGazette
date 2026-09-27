"""Unit tests for tn_lib helpers and dataset schema stability (#20)."""
import base64
import csv
from pathlib import Path

import pandas as pd
import pytest

from tn_lib import (
    b64_year,
    norm_href,
    split_issue_text,
    GAZATTES_COLUMNS,
    ISSUES_COLUMNS,
)

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


class TestNormHref:
    def test_absolute_passthrough(self):
        url = "https://www.stationeryprinting.tn.gov.in/gazette/2026/38.pdf"
        assert norm_href(url) == url

    def test_backslash_relative(self):
        assert norm_href("gazette\\2026\\38_II_1_2026.pdf") == (
            "https://www.stationeryprinting.tn.gov.in/gazette/2026/38_II_1_2026.pdf"
        )

    def test_slash_relative(self):
        assert norm_href("/extraordinary/2026/x.pdf") == (
            "https://www.stationeryprinting.tn.gov.in/extraordinary/2026/x.pdf"
        )

    def test_empty(self):
        assert norm_href("") == ""
        assert norm_href(None) == ""


class TestSplitIssueText:
    def test_current_format(self):
        assert split_issue_text("38 dated:23-09-2026") == ("38", "23-09-2026")

    def test_whitespace(self):
        assert split_issue_text(" 42 dated: 18-10-2023 ") == ("42", "18-10-2023")

    def test_no_marker(self):
        assert split_issue_text("42") == ("42", "")

    def test_empty(self):
        assert split_issue_text("") == ("", "")
        assert split_issue_text(None) == ("", "")


class TestDatasetSchemas:
    """Guard the on-disk CSV contract against silent drift (#20)."""

    @pytest.mark.parametrize("filename", [
        "Gazattes_2023.csv", "Gazattes_2026.csv",
    ])
    def test_gazattes_columns(self, filename):
        path = DATA / filename
        if not path.exists():
            pytest.skip(f"{filename} not present")
        with open(path, newline="", encoding="utf-8") as f:
            assert next(csv.reader(f)) == GAZATTES_COLUMNS

    @pytest.mark.parametrize("filename", [
        "GazatteIssues_2023.csv", "GazatteIssues_2026.csv",
    ])
    def test_issues_columns(self, filename):
        path = DATA / filename
        if not path.exists():
            pytest.skip(f"{filename} not present")
        with open(path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        assert header in (ISSUES_COLUMNS, ["", "Issue No and Date", "Particulars", "URL"])

    def test_gazattes_2026_has_rows(self):
        path = DATA / "Gazattes_2026.csv"
        if not path.exists():
            pytest.skip("Gazattes_2026.csv not present")
        assert len(pd.read_csv(path)) > 0

    def test_gazattes_dates_parse(self):
        path = DATA / "Gazattes_2026.csv"
        if not path.exists():
            pytest.skip("Gazattes_2026.csv not present")
        df = pd.read_csv(path)
        parsed = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
        assert parsed.notna().all(), "unparseable Date values present"
