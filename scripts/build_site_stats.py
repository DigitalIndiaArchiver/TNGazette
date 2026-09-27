#!/usr/bin/env python3
"""Build docs/stats.json for the GitHub Pages site.

Computes totals, per-year counts and a merged year-by-year view for
ordinary gazettes, extraordinary notifications, issue listings and the
extracted-text (markdown) corpus from the files in data/. Runs in CI after
the scrape steps and before the commit step, so the published site always
matches the committed dataset.

Counting rules (mirrors AGENTS.md):
- a yearly file supersedes the legacy master slice for its year (no
  double-counting 2023);
- only git-tracked files are counted, so locally produced but unpublished
  files (e.g. the 186 MB 2025 extraordinary index) never leak into the
  public numbers;
- rows are documents: duplicate PDF links within a file are collapsed.
Pure stdlib (git ls-files via subprocess), no network.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MD_ROOT = DATA / "markdown"
OUT = ROOT / "docs" / "stats.json"

GAZ_PREFIX = "Gazattes_"
ISSUE_PREFIX = "GazatteIssues_"
EXTRA_PREFIX = "ExtraOrdinaryGazattes_"

LEGACY_GAZ = "Gazattes.csv"
LEGACY_ISSUES = "GazatteIssues.csv"
LEGACY_EXTRA = "ExtraOrdinaryGazattes.csv"

DATE_RE = re.compile(r"(\d{2})-(\d{2})-(\d{4})")


def tracked(rel: str) -> bool:
    """True when path is committed — untracked files stay off the public site."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--", rel], cwd=ROOT,
            capture_output=True, text=True, timeout=30, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    return bool(out.stdout.strip())


def norm_date(raw: str) -> str | None:
    """Normalise YYYY-MM-DD or DD-MM-YYYY to ISO, else None."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    m = DATE_RE.search(raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"
    return None


def year_of(name: str, prefix: str) -> int | None:
    if name.startswith(prefix) and name.endswith(".csv"):
        tail = name[len(prefix):-4]
        if tail.isdigit():
            return int(tail)
    return None


class YearCounts(dict):
    """year -> {count, first, last}; merging keeps counts additive per source."""

    def add(self, year: int, when: str | None) -> None:
        slot = self.setdefault(year, {"count": 0, "first": None, "last": None})
        slot["count"] += 1
        if when:
            slot["first"] = when if slot["first"] is None else min(slot["first"], when)
            slot["last"] = when if slot["last"] is None else max(slot["last"], when)

    def merged(self, other: "YearCounts") -> "YearCounts":
        out = YearCounts()
        for year in sorted(set(self) | set(other)):
            if year in other:
                out[year] = dict(other[year])
            else:
                out[year] = dict(self[year])
        return out


def scan(path: Path, date_col: str, key_col: str | None = None) -> YearCounts:
    """Count documents per year in one CSV.

    date_col names the column holding the date; key_col names the PDF-link
    column when duplicates must collapse to documents. Year comes from the
    date when parseable, else from the key's /YYYY/ segment, else the row
    is skipped.
    """
    years: YearCounts = YearCounts()
    seen: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if key_col:
                key = (row.get(key_col) or "").strip()
                if key:
                    if key in seen:
                        continue
                    seen.add(key)
            when = norm_date(row.get(date_col) or "")
            year = None
            if when:
                year = int(when[:4])
            else:
                m = re.search(r"/(\d{4})/", row.get(key_col or "", "") or "")
                if m:
                    year = int(m.group(1))
            if year is None:
                continue
            years.add(year, when)
    return years


def scan_legacy_issues(path: Path) -> YearCounts:
    """Legacy GazatteIssues.csv: year hides in '16 - dt. 19-04-2023'."""
    years: YearCounts = YearCounts()
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            m = DATE_RE.search(row.get("Issue No and Date") or "")
            if not m:
                continue
            d, mo, y = m.groups()
            years.add(int(y), f"{y}-{mo}-{d}")
    return years


def count_markdown(kind: str) -> list[dict]:
    """Document counts per year for one markdown kind ('ordinary'/'extraordinary')."""
    out: list[dict] = []
    base = MD_ROOT / kind
    if not base.exists():
        return out
    for year_dir in sorted(p for p in base.iterdir() if p.is_dir() and p.name.isdigit()):
        docs = sum(1 for _ in year_dir.glob("*.md"))
        if docs:
            out.append({"year": int(year_dir.name), "docs": docs})
    return out


def main() -> None:
    # Weekly parts: yearly files first, legacy master fills the other years.
    parts = YearCounts()
    for path in sorted(DATA.glob(f"{GAZ_PREFIX}*.csv")):
        year = year_of(path.name, GAZ_PREFIX)
        if year is not None and tracked(f"data/{path.name}"):
            for y, slot in scan(path, "Date", "URL").items():
                slot["file"] = path.name
                parts[y] = dict(slot)
    legacy_parts = scan(DATA / LEGACY_GAZ, "Date", "URL") if (DATA / LEGACY_GAZ).exists() else YearCounts()
    parts = legacy_parts.merged(parts)
    for slot in parts.values():
        slot.setdefault("file", LEGACY_GAZ)

    # Weekly issues.
    issues = YearCounts()
    for path in sorted(DATA.glob(f"{ISSUE_PREFIX}*.csv")):
        year = year_of(path.name, ISSUE_PREFIX)
        if year is not None and tracked(f"data/{path.name}"):
            for y, slot in scan_issues_yearly(path).items():
                slot["file"] = path.name
                issues[y] = dict(slot)
    legacy_issues = scan_legacy_issues(DATA / LEGACY_ISSUES) if (DATA / LEGACY_ISSUES).exists() else YearCounts()
    issues = legacy_issues.merged(issues)
    for slot in issues.values():
        slot.setdefault("file", LEGACY_ISSUES)

    # Extraordinary notifications.
    extra = YearCounts()
    for path in sorted(DATA.glob(f"{EXTRA_PREFIX}*.csv")):
        year = year_of(path.name, EXTRA_PREFIX)
        if year is not None and tracked(f"data/{path.name}"):
            got = scan(path, "Issue Date", "URL")
            for y, slot in got.items():
                slot["file"] = path.name
                extra[y] = dict(slot)
    legacy_extra = scan(DATA / LEGACY_EXTRA, "Issue Date", "URL") if (DATA / LEGACY_EXTRA).exists() else YearCounts()
    extra = legacy_extra.merged(extra)
    for slot in extra.values():
        slot.setdefault("file", LEGACY_EXTRA)

    md_ordinary = count_markdown("ordinary")
    md_extra = count_markdown("extraordinary")
    md_ord_by_year = {y["year"]: y["docs"] for y in md_ordinary}
    md_extra_by_year = {y["year"]: y["docs"] for y in md_extra}

    all_years = sorted(
        set(parts) | set(issues) | set(extra)
        | set(md_ord_by_year) | set(md_extra_by_year)
    )
    years = []
    for y in all_years:
        years.append({
            "year": y,
            "parts": parts.get(y, {}).get("count", 0),
            "issues": issues.get(y, {}).get("count", 0),
            "extraordinary": extra.get(y, {}).get("count", 0),
            "ordinary_md": md_ord_by_year.get(y, 0),
            "extra_md": md_extra_by_year.get(y, 0),
            "files": {
                "parts": parts.get(y, {}).get("file"),
                "issues": issues.get(y, {}).get("file"),
                "extraordinary": extra.get(y, {}).get("file"),
            },
        })

    def year_list(src: YearCounts, count_key: str) -> list[dict]:
        out = [
            {"year": y, count_key: s["count"], "first_date": s["first"], "last_date": s["last"]}
            for y, s in sorted(src.items())
        ]
        return out

    gaz_yearly = year_list(parts, "parts")
    issues_yearly = [{"year": y, "issues": s["count"]} for y, s in sorted(issues.items())]
    extra_yearly = year_list(extra, "rows")

    md_all_years = sorted(set(md_ord_by_year) | set(md_extra_by_year))
    markdown = {
        "ordinary": sum(md_ord_by_year.values()),
        "extraordinary": sum(md_extra_by_year.values()),
        "total": sum(md_ord_by_year.values()) + sum(md_extra_by_year.values()),
        "first_year": md_all_years[0] if md_all_years else None,
        "last_year": md_all_years[-1] if md_all_years else None,
        "ordinary_years": md_ordinary,
        "extraordinary_years": md_extra,
    }

    latest_issue = ""
    latest_file = DATA / f"{ISSUE_PREFIX}{date.today().year}.csv"
    if latest_file.exists():
        nums = []
        with latest_file.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    nums.append(int((row.get("Issue No") or "0").split()[0]))
                except (ValueError, IndexError):
                    continue
        if nums:
            latest_issue = max(nums)

    stats = {
        "generated_at": date.today().isoformat(),
        "totals": {
            "gazette_parts": sum(y["parts"] for y in years),
            "gazette_issues": sum(y["issues"] for y in years),
            "extraordinary": sum(y["extraordinary"] for y in years),
            "part_years": len([y for y in years if y["parts"]]),
            "markdown_docs": markdown["total"],
        },
        "latest_issue": latest_issue,
        "ordinary_years": gaz_yearly,
        "issue_years": issues_yearly,
        "extraordinary_years": extra_yearly,
        "years": years,
        "markdown": markdown,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"[stats] wrote {OUT}")
    print(f"[stats] parts={stats['totals']['gazette_parts']} "
          f"issues={stats['totals']['gazette_issues']} "
          f"extra={stats['totals']['extraordinary']} markdown={markdown['total']}")


def scan_issues_yearly(path: Path) -> YearCounts:
    """Yearly GazatteIssues files: modern columns (Issue No, Date, URL)."""
    years: YearCounts = YearCounts()
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            when = norm_date(row.get("Date") or "")
            year = int(when[:4]) if when else None
            if year is None:
                m = DATE_RE.search(row.get("Issue No and Date") or "")
                if m:
                    d, mo, y = m.groups()
                    year, when = int(y), f"{y}-{mo}-{d}"
            if year is None:
                m = re.search(r"/(\d{4})/", row.get("URL") or "")
                if m:
                    year = int(m.group(1))
            if year is not None:
                years.add(year, when)
    return years


if __name__ == "__main__":
    main()
