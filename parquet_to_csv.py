#!/usr/bin/env python3
"""Convert TN Gazette Parquet files to CSV.

Usage:
  python parquet_to_csv.py                                          # converts all .parquet in data/
  python parquet_to_csv.py data/ExtraOrdinaryGazattes_2026.parquet  # single file
  python parquet_to_csv.py --overwrite data/*.parquet               # force overwrite
"""
import argparse
import sys
from pathlib import Path

import pandas as pd


def convert(parquet_path: Path, overwrite: bool = False) -> Path | None:
    """Convert a .parquet file to .csv next to it. Returns the csv Path or None."""
    if parquet_path.suffix != ".parquet":
        print(f"  Skipping {parquet_path.name} — not a .parquet file")
        return None

    csv_path = parquet_path.with_suffix(".csv")
    if csv_path.exists() and not overwrite:
        print(f"  Skipping {csv_path.name} — already exists (use --overwrite to replace)")
        return None

    df = pd.read_parquet(parquet_path)
    df.to_csv(csv_path, index=False)
    print(f"  {parquet_path.name} → {csv_path.name}  ({len(df)} rows)")
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert TN Gazette Parquet files back to CSV.",
    )
    parser.add_argument(
        "files", nargs="*", type=Path,
        help="One or more .parquet files (default: all .parquet files in data/)",
    )
    parser.add_argument(
        "--overwrite", "-f", action="store_true",
        help="Overwrite existing CSV files",
    )
    args = parser.parse_args()

    files: list[Path] = args.files
    if not files:
        data_dir = Path(__file__).parent / "data"
        if not data_dir.is_dir():
            print("No files given and data/ directory not found.")
            sys.exit(1)
        files = sorted(data_dir.glob("*.parquet"))
        if not files:
            print("No .parquet files found in data/.")
            return

    results = [convert(f, overwrite=args.overwrite) for f in files]
    converted = [r for r in results if r is not None]
    print(f"\nDone. {len(converted)} file(s) converted.")


if __name__ == "__main__":
    main()
