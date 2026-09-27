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
import io
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


KEY_COLUMN = {
    "ordinary gazettes": "URL",
    "weekly issues": "URL",
    "extraordinary gazettes": "PDF Link",
}


def _rows(text: str) -> list[list[str]]:
    """Parse CSV text into non-blank rows.

    Must go through a single reader: gazette Subjects legitimately contain
    newlines inside quoted cells, so splitting on lines first would invent
    rows that the real file does not have. NUL bytes are stripped first:
    current CPython's csv reader raises on them mid-parse.
    """
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]


def count_rows(path: Path) -> tuple[int, int]:
    """(data rows, unique documents) for a dataset file.

    Uniqueness is the measure that matters: a merge dedupes on the document
    key, so row count alone can fall while coverage does not. Counting keys
    also means a shrunken listing window cannot hide behind duplicates.
    """
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = _rows(f.read())
    if not rows:
        return 0, 0
    header, body = rows[0], _rows_data(rows[1:])
    key = _key_index(header, path.name)
    keys = {r[key] for r in body if len(r) > key and r[key].strip()}
    return len(body), len(keys)


def _rows_data(rows: list[list[str]]) -> list[list[str]]:
    return rows


def _key_index(header: list[str], name: str) -> int:
    """Column index of the document key, tolerating legacy file shapes.

    Legacy files (pre-2024) share the dataset folder but use older column
    sets, so fall back to the first URL-ish column actually present.
    """
    for candidate in ("URL", "PDF Link", "Link"):
        if candidate in header:
            return header.index(candidate)
    for i, col in enumerate(header):
        if "url" in col.lower() or "link" in col.lower():
            return i
    return len(header) - 1


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


def head_counts(rel: str) -> tuple[int, int] | None:
    """(rows, unique docs) committed at HEAD, or None when unreadable."""
    text = head_text(rel)
    if text is None:
        return None
    rows = _rows(text)
    if not rows:
        return 0, 0
    header, body = rows[0], rows[1:]
    key = _key_index(header, rel)
    keys = {r[key] for r in body if len(r) > key and r[key].strip()}
    return len(body), len(keys)


def main() -> int:
    failures: list[str] = []
    for label, (prefix, legacy) in FAMILIES.items():
        files = [p for p in sorted(DATA.glob(f"{prefix}*.csv")) if p.name != legacy]
        legacy_path = DATA / legacy
        if legacy_path.exists():
            files.append(legacy_path)

        counts = [count_rows(p) for p in files]
        now, now_keys = (sum(c[0] for c in counts), sum(c[1] for c in counts))
        known = [head_counts(str(p.relative_to(REPO))) for p in files]
        untracked = any(k is None for k in known) and not all(k is None for k in known)
        before = sum(k[0] for k in known if k is not None)
        before_keys = sum(k[1] for k in known if k is not None)

        if all(k is None for k in known):
            print(f"[skip] {label}: no committed state to compare ({now} rows on disk)")
        else:
            status = "ok" if now_keys >= before_keys else "LOST"
            note = " (some files new this run)" if untracked else ""
            print(
                f"[{status}] {label}: {before_keys} -> {now_keys} documents "
                f"({before} -> {now} rows){note}"
            )
            if now_keys < before_keys:
                failures.append(
                    f"{label}: {before_keys} -> {now_keys} documents "
                    f"(lost {before_keys - now_keys})"
                )

        current = DATA / f"{prefix}{CURRENT_YEAR}.csv"
        if not current.exists():
            failures.append(f"{label}: {current.name} missing")
        elif count_rows(current)[0] == 0:
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
