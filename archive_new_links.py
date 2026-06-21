#!/usr/bin/env python3
"""Archive unarchived TN Gazette PDF links to the Wayback Machine.

Reads all CSVs in data/ that have a URL-like column, finds rows missing
Wayback archival, saves the URLs, and writes the updated CSV back.

Usage:
  python archive_new_links.py                              # all eligible CSVs
  python archive_new_links.py --file data/Gazattes.csv     # single file
  python archive_new_links.py --dry-run                    # preview only, no saves
  python archive_new_links.py --delay 2                    # seconds between saves
"""
import argparse
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import waybackpy
from waybackpy.exceptions import NoCDXRecordFound

USER_AGENT = "TNGazette Archiver (github.com/DigitalIndiaArchiver/TNGazette)"
DATA_DIR = Path(__file__).parent / "data"

# Column name variants across different CSVs
URL_COLUMNS = {"URL", "PDF Link"}


class _Timeout(Exception):
    """Raised when a Wayback API call times out."""
    pass


def _timeout_handler(_signum, _frame):
    raise _Timeout()


def _archive_one(url: str, max_tries: int = 5, timeout: int = 30) -> tuple:
    """Archive one URL and return (archived_url, archived_date) or (None, None)."""
    # Set an alarm so stuck HTTP calls don't hang forever
    signal.signal(signal.SIGALRM, _timeout_handler)

    # 1. Check CDX for existing snapshot
    try:
        signal.alarm(timeout)
        cdx = waybackpy.WaybackMachineCDXServerAPI(url, USER_AGENT)
        oldest = cdx.oldest()
        signal.alarm(0)
        if oldest:
            return oldest.archive_url, pd.to_datetime(
                oldest.timestamp, format="%Y%m%d%H%M%S"
            )
    except _Timeout:
        signal.alarm(0)
        return None, None
    except NoCDXRecordFound:
        signal.alarm(0)
        pass
    except Exception:
        signal.alarm(0)
        pass  # network blip — fall through to try saving

    # 2. Save to Wayback
    try:
        signal.alarm(timeout)
        save_api = waybackpy.WaybackMachineSaveAPI(url, USER_AGENT, max_tries=max_tries)
        archive_url = save_api.save()
        signal.alarm(0)
        return archive_url, pd.Timestamp.utcnow().floor("s")
    except _Timeout:
        signal.alarm(0)
        return None, None
    except Exception:
        signal.alarm(0)
        return None, None


def process_csv(csv_path: Path, dry_run: bool = False, delay: float = 1.0) -> dict:
    """Process a single CSV: find unarchived URLs and archive them.
    Returns a summary dict.
    """
    df = pd.read_csv(csv_path)

    # Determine which column holds URLs
    url_col = next((c for c in df.columns if c in URL_COLUMNS), None)
    if url_col is None:
        return {"file": csv_path.name, "status": "skipped", "reason": "no URL column"}

    total = len(df)

    # Ensure Wayback columns exist
    has_archived_col = "Archived URL" in df.columns
    has_date_col = "Archived Date" in df.columns

    if not has_archived_col:
        df["Archived URL"] = pd.NA
    if not has_date_col:
        df["Archived Date"] = pd.NA

    # Rows missing archival — null or empty string
    missing_mask = df["Archived URL"].isna() | (df["Archived URL"] == "")
    to_archive = missing_mask.sum()

    if to_archive == 0:
        return {"file": csv_path.name, "status": "done", "total": total, "archived": 0}

    print(f"\n  {csv_path.name}: {to_archive}/{total} URLs need archival")

    if dry_run:
        print(f"  [DRY RUN] Would archive {to_archive} URLs")
        return {
            "file": csv_path.name,
            "status": "dry-run",
            "total": total,
            "would_archive": to_archive,
        }

    # Archive each missing URL
    archived_count = 0
    failed_count = 0

    for idx in df.index[missing_mask]:
        url = str(df.at[idx, url_col]).strip()
        if not url or url == "<NA>" or url == "nan":
            df.at[idx, "Archived URL"] = None
            df.at[idx, "Archived Date"] = None
            continue

        print(f"    Archiving [{idx + 1}/{total}]: {url[:80]}...", end=" ", flush=True)
        arch_url, arch_date = _archive_one(url)

        if arch_url:
            df.at[idx, "Archived URL"] = arch_url
            df.at[idx, "Archived Date"] = arch_date
            print("OK")
            archived_count += 1
        else:
            df.at[idx, "Archived URL"] = None
            df.at[idx, "Archived Date"] = None
            print("FAILED")
            failed_count += 1

        if delay > 0:
            time.sleep(delay)

    # Write updated CSV back
    df.to_csv(csv_path, index=False)
    return {
        "file": csv_path.name,
        "status": "done",
        "total": total,
        "archived": archived_count,
        "failed": failed_count,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Archive unarchived TN Gazette PDF links to Wayback Machine",
    )
    parser.add_argument(
        "--file", "-f", type=Path, action="append", dest="files",
        help="One or more CSV files (default: all with URL columns in data/)",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Scan and report what would be archived, but don't save",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Seconds to wait between Wayback saves (default: 1.0)",
    )
    args = parser.parse_args()

    files: list[Path] = args.files
    if not files:
        if not DATA_DIR.is_dir():
            print("No files given and data/ directory not found.")
            sys.exit(1)
        files = sorted(DATA_DIR.glob("*.csv"))

    results = [process_csv(f, dry_run=args.dry_run, delay=args.delay) for f in files]

    print("\n=== Summary ===")
    total_archived = 0
    total_failed = 0
    for r in results:
        if r["status"] == "skipped":
            print(f"  {r['file']:45s} skipped ({r['reason']})")
        elif r["status"] == "dry-run":
            print(f"  {r['file']:45s} {r['would_archive']:4d} would be archived")
        elif r["status"] == "done":
            ok = r.get("archived", 0)
            fail = r.get("failed", 0)
            total_archived += ok
            total_failed += fail
            if ok + fail == 0:
                print(f"  {r['file']:45s} all archived, nothing to do")
            else:
                print(f"  {r['file']:45s} {ok} archived, {fail} failed")
    if total_archived + total_failed > 0:
        print(f"\n  Total: {total_archived} archived, {total_failed} failed")


if __name__ == "__main__":
    main()
