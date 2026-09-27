"""Tests for tn_lib helpers and dataset schema guards. No network needed."""
import base64
import csv
from pathlib import Path

import pandas as pd
import pytest

from tn_lib import (EXTRAORDINARY_COLUMNS, GAZATTES_COLUMNS, LEGACY_ISSUES_COLUMNS,
                    ISSUES_COLUMNS, b64_year, listing_url, merge_by_key,
                    norm_href, read_rows, split_issue_text)

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


class TestMergeByKey:
    """The weekly scrapers must union onto disk, never overwrite history."""

    def test_disk_rows_win_over_fresh(self):
        existing = [{"u": "a", "v": "archived"}, {"u": "b", "v": "kept"}]
        fresh = [{"u": "b", "v": "rescraped"}, {"u": "c", "v": "new"}]
        merged = merge_by_key(existing, fresh, "u")
        by_key = {r["u"]: r["v"] for r in merged}
        assert by_key == {"a": "archived", "b": "kept", "c": "new"}

    def test_duplicates_on_disk_are_collapsed(self):
        existing = [{"u": "a", "v": 1}, {"u": "a", "v": 1}]
        assert len(merge_by_key(existing, [], "u")) == 1

    def test_blank_keys_never_collapse(self):
        """Rows without a URL are distinct records, not one shared key."""
        existing = [{"u": "", "v": 1}, {"u": "", "v": 2}]
        fresh = [{"u": "", "v": 3}]
        merged = merge_by_key(existing, fresh, "u")
        assert [r["v"] for r in merged] == [1, 2, 3]

    def test_missing_key_field_is_tolerated(self):
        merged = merge_by_key([{"v": 1}], [{"v": 2}], "u")
        assert len(merged) == 2


class TestReadRows:
    def test_survives_fields_over_the_csv_default_limit(self, tmp_path):
        big = "x" * 200_000  # csv's default cap is 131072 bytes
        p = tmp_path / "big.csv"
        p.write_text(f"a,b\n{big},tail\n", encoding="utf-8")
        rows = read_rows(p, ["a", "b"])
        assert rows[-1]["b"] == "tail"
        assert len(rows[-1]["a"]) == 200_000

    def test_strips_nul_and_normalises_cr_inside_quoted_fields(self, tmp_path):
        # A bare CR is a CSV line terminator; CRs that matter arrive quoted
        # from extracted gazette text and would otherwise break pandas/parquet.
        p = tmp_path / "nul.csv"
        p.write_bytes(b'a,b\nhe\x00llo,"wor\rld"\n')
        rows = read_rows(p, ["a", "b"])
        assert rows[-1]["a"] == "hello"
        assert rows[-1]["b"] == "wor ld"

    def test_skips_blank_lines_and_empty_rows(self, tmp_path):
        p = tmp_path / "blank.csv"
        p.write_text("a,b\n1,2\n\n,\n3,4\n", encoding="utf-8")
        rows = read_rows(p, ["a", "b"])
        assert [r["a"] for r in rows] == ["a", "1", "3"]

    def test_missing_file_is_empty(self, tmp_path):
        assert read_rows(tmp_path / "nope.csv", ["a"]) == []


class TestMergeByKey:
    def test_on_disk_rows_win(self):
        existing = [{"PDF Link": "u1", "Deleted": "false", "Subject": "old"}]
        fresh = [{"PDF Link": "u1", "Deleted": "true", "Subject": "new"}]
        merged = merge_by_key(existing, fresh, "PDF Link")
        assert len(merged) == 1
        assert merged[0]["Deleted"] == "false" and merged[0]["Subject"] == "old"

    def test_fresh_rows_appended_and_order_preserved(self):
        existing = [{"PDF Link": "u1"}, {"PDF Link": "u2"}]
        fresh = [{"PDF Link": "u2"}, {"PDF Link": "u3"}]
        merged = merge_by_key(existing, fresh, "PDF Link")
        assert [r["PDF Link"] for r in merged] == ["u1", "u2", "u3"]

    def test_duplicate_keys_collapse(self):
        fresh = [{"PDF Link": "u1"}, {"PDF Link": "u1"}, {"PDF Link": "u1"}]
        assert len(merge_by_key([], fresh, "PDF Link")) == 1

    def test_rows_without_key_are_not_dropped(self):
        existing = [{"PDF Link": ""}, {"PDF Link": "u1"}]
        merged = merge_by_key(existing, [{"PDF Link": "u2"}], "PDF Link")
        assert len(merged) == 3

    def test_shrinking_source_window_does_not_lose_history(self):
        """The site lists only recent issues; the merge must keep older rows."""
        existing = [{"PDF Link": f"old{i}"} for i in range(100)]
        fresh = [{"PDF Link": f"old{i}"} for i in range(5)]
        assert len(merge_by_key(existing, fresh, "PDF Link")) == 100


class TestReadRows:
    def test_reads_rows_beyond_default_field_limit(self, tmp_path):
        big = "x" * 200_000
        p = tmp_path / "big.csv"
        p.write_text(f"A,B\n1,{big}\n2,small\n", encoding="utf-8")
        rows = read_rows(p, ["A", "B"])
        assert len(rows) == 2 and rows[0]["B"] == big

    def test_strips_nul_so_parquet_can_write(self, tmp_path):
        p = tmp_path / "nul.csv"
        p.write_bytes(b"A\n" + b"bad\x00byte" + b"\n")
        rows = read_rows(p, ["A"])
        assert rows[0]["A"] == "badbyte"

    def test_bare_cr_still_ends_a_row_like_csv_does(self, tmp_path):
        """Unquoted CR is a row terminator to csv; the reader keeps that rule.

        Mangled PDF text can leave a bare CR inside a cell, which splits the
        row rather than corrupting it in place. Recorded here so the
        behaviour is explicit rather than accidental.
        """
        p = tmp_path / "cr.csv"
        p.write_bytes(b"A\n" + b"part1\rpart2" + b"\n")
        assert [r["A"] for r in read_rows(p, ["A"])] == ["part1", "part2"]

    def test_skips_blank_lines(self, tmp_path):
        p = tmp_path / "blank.csv"
        p.write_text("A\n1\n\n2\n   \n", encoding="utf-8")
        assert len(read_rows(p, ["A"])) == 2

    def test_missing_file_returns_empty(self, tmp_path):
        assert read_rows(tmp_path / "nope.csv", ["A"]) == []
