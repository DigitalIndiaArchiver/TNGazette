#!/usr/bin/env python3
"""Fail the build when a weekly run loses data instead of gaining it.

The scrape steps are best-effort: a partial site outage can leave a file
present but empty, or a merge bug can drop rows that were already
committed. "The command exited 0" is not evidence that anything was
archived, so this runs after the scrapes and compares the working tree
against the committed state (HEAD) for all three dataset families.

Contract: for each family, on-disk rows must be >= the row count committed
at HEAD, and the current-year file must exist with at least one row. A run
that archived nothing is fine only if the site genuinely had nothing new;
a run that *lost* anything is a build failure.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CURRENT_YEAR = "2026"

FAMILIES = {
    "ordinary gazettes": ("Gazattes_", "Gazattes.csv"),
    "weekly issues": ("GazatteIssues_", "GazatteIssues.csv"),
    "extraordinary gazettes": ("ExtraOrdinaryGazattes_", "ExtraOrdinaryGazattes.csv"),
}


def count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def head_text(rel: str) -> str | None:
    """Return the file content committed at HEAD, or None if absent there."""
    try:
        out = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def head_rows(rel: str) -> int | None:
    """Rows committed at HEAD, or None when HEAD can't be read (new file, no git)."""
    text = head_text(rel)
    if text is None:
        return None
    return max(0, sum(1 for _ in csv.reader(text.splitlines())) - 1)


def main() -> int:
    failures: list[str] = []
    for label, (prefix, legacy) in FAMILIES.items():
        files = [p for p in sorted(DATA.glob(f"{prefix}*.csv")) if p.name != legacy]
        legacy_path = DATA / legacy
        if legacy_path.exists():
            files.append(legacy_path)

        now = sum(count_rows(p) for p in files)
        known = [head_rows(str(p.relative_to(REPO))) for p in files]
        untracked = any(k is None for k in known) and not all(k is None for k in known)
        before = sum(k for k in known if k is not None)

        if all(k is None for k in known):
            print(f"[skip] {label}: no committed state to compare ({now} rows on disk)")
        else:
            status = "ok" if now >= before else "LOST"
            note = " (some files new this run)" if untracked else ""
            print(f"[{status}] {label}: {before} -> {now} rows{note}")
            if now < before:
                failures.append(f"{label}: {before} -> {now} rows (lost {before - now})")

        current = DATA / f"{prefix}{CURRENT_YEAR}.csv"
        if not current.exists():
            failures.append(f"{label}: {current.name} missing")
        elif count_rows(current) == 0:
            failures.append(f"{label}: {current.name} is empty")

    if failures:
        print("\nDataset guard failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("\nDataset guard passed: all three families held or grew.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
