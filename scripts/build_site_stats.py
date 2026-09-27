#!/usr/bin/env python3
"""Build docs/stats.json for the GitHub Pages site.

Computes totals and per-year counts for ordinary gazettes, extraordinary
notifications, issue listings and the extracted-text (markdown) corpus
from the files in data/. Runs in CI after the scrape steps and before the
commit step, so the published site always matches the committed dataset.
Pure stdlib, no network.
"""
from __future__ import annotations

import csv
import json
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


def year_of(name: str, prefix: str) -> int | None:
    if name.startswith(prefix) and name.endswith(".csv"):
        tail = name[len(prefix):-4]
        if tail.isdigit():
            return int(tail)
    return None


def count_csv(path: Path, date_col: str | None = None) -> dict:
    rows = 0
    first = last = None
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for row in csv.DictReader(f):
            rows += 1
            if date_col:
                raw = (row.get(date_col) or "").strip()
                if raw:
                    first = raw if first is None else min(first, raw)
                    last = raw if last is None else max(last, raw)
    return {"rows": rows, "first_date": first, "last_date": last}


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
    gaz_yearly = []
    total_parts = 0
    for path in sorted(DATA.glob(f"{GAZ_PREFIX}*.csv")):
        year = year_of(path.name, GAZ_PREFIX)
        if year is None:
            continue
        stats = count_csv(path, "Date")
        total_parts += stats["rows"]
        gaz_yearly.append({
            "year": year,
            "parts": stats["rows"],
            "first_date": stats["first_date"],
            "last_date": stats["last_date"],
        })
    gaz_yearly.sort(key=lambda x: x["year"])
    if (DATA / LEGACY_GAZ).exists():
        total_parts += count_csv(DATA / LEGACY_GAZ, "Date")["rows"]

    issues_yearly = []
    total_issues = 0
    for path in sorted(DATA.glob(f"{ISSUE_PREFIX}*.csv")):
        year = year_of(path.name, ISSUE_PREFIX)
        if year is None:
            continue
        rows = count_csv(path)["rows"]
        total_issues += rows
        issues_yearly.append({"year": year, "issues": rows})
    issues_yearly.sort(key=lambda x: x["year"])
    if (DATA / LEGACY_ISSUES).exists():
        total_issues += count_csv(DATA / LEGACY_ISSUES)["rows"]

    extra_yearly = []
    total_extra = 0
    for path in sorted(DATA.glob(f"{EXTRA_PREFIX}*.csv")):
        year = year_of(path.name, EXTRA_PREFIX)
        if year is None:
            continue
        stats = count_csv(path, "Issue Date")
        total_extra += stats["rows"]
        extra_yearly.append({
            "year": year,
            "rows": stats["rows"],
            "first_date": stats["first_date"],
            "last_date": stats["last_date"],
        })
    extra_yearly.sort(key=lambda x: x["year"])
    if (DATA / LEGACY_EXTRA).exists():
        total_extra += count_csv(DATA / LEGACY_EXTRA, "Issue Date")["rows"]

    md_ordinary = count_markdown("ordinary")
    md_extra = count_markdown("extraordinary")
    md_all_years = sorted({y["year"] for y in md_ordinary} | {y["year"] for y in md_extra})
    markdown = {
        "ordinary": sum(y["docs"] for y in md_ordinary),
        "extraordinary": sum(y["docs"] for y in md_extra),
        "total": sum(y["docs"] for y in md_ordinary) + sum(y["docs"] for y in md_extra),
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
            "gazette_parts": total_parts,
            "gazette_issues": total_issues,
            "extraordinary": total_extra,
            "part_years": len(gaz_yearly),
            "markdown_docs": markdown["total"],
        },
        "latest_issue": latest_issue,
        "ordinary_years": gaz_yearly,
        "issue_years": issues_yearly,
        "extraordinary_years": extra_yearly,
        "markdown": markdown,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"[stats] wrote {OUT}")
    print(f"[stats] parts={total_parts} issues={total_issues} "
          f"extra={total_extra} markdown={markdown['total']}")


if __name__ == "__main__":
    main()
