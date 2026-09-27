"""Shared helpers for TN Gazette scrapers. Pure functions, no network."""
import base64
from datetime import datetime

BASE_URL = "https://www.stationeryprinting.tn.gov.in/"

GAZATTES_COLUMNS = [
    "Part", "Content", "URL", "Date", "Issue", "Deleted",
    "Archived URL", "Archived Date",
]
ISSUES_COLUMNS = ["Issue No", "Issue No and Date", "Date", "URL"]
LEGACY_ISSUES_COLUMNS = ["", "Issue No and Date", "Particulars", "URL"]
EXTRAORDINARY_COLUMNS = [
    "Issue No", "Issue Date", "Extraordinary Part & Section", "PDF Link",
    "Extraordinary Type", "Subject", "Department", "G.O No",
]


def b64_year(year):
    """Encode a year the way the redesigned site does in ?id= params."""
    return base64.b64encode(str(year).encode()).decode()


def listing_url(year):
    """Ordinary gazette issue listing URL (latest ~38 issues, year-agnostic)."""
    return f"{BASE_URL}gazette.php?id={b64_year(year)}"


def norm_href(href):
    """Normalize a PDF/list link href from the redesigned site to an absolute URL.

    Handles backslash path separators ('gazette\\\\2026\\\\x.pdf'), leading-slash
    relative paths, absolute passthrough, and empty/None values.
    """
    if not href:
        return ""
    href = str(href).strip()
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    return BASE_URL + href.replace("\\", "/").lstrip("/")


def split_issue_text(text):
    """Split an issue cell like '38 dated:23-09-2026' into (issue_no, date_str).

    Returns (issue_no, '') when the 'dated:' marker is missing or the date
    does not parse as %d-%m-%Y. Returns ('', '') for empty/None input.
    """
    if not text:
        return "", ""
    s = str(text).strip()
    if "dated:" not in s:
        return s, ""
    issue_no, _, date_part = s.partition("dated:")
    issue_no = issue_no.strip().rstrip("-").strip()
    date_str = date_part.strip()
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return issue_no, ""
    return issue_no, date_str


def read_rows(path, columns):
    """Read a CSV into dicts safely: no field-size cap, no NUL/CR bytes.

    Government gazette rows carry very long Subject cells (some exceed 128 KB,
    which is csv's default per-field limit) and occasional NUL bytes from
    mangled PDF text extraction. Both break naive reads and pandas/parquet
    writes, so normalise here instead of at every call site.

    A leading row identical to ``columns`` is treated as the header and
    dropped, so callers get data rows only.
    """
    import csv

    try:
        csv.field_size_limit(1 << 30)
    except OverflowError:
        csv.field_size_limit(2 ** 31 - 1)

    if not path.exists():
        return []
    out = []
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for raw in csv.reader(fh):
            if not raw or not any(cell.strip() for cell in raw):
                continue
            values = [
                cell.replace("\x00", "").replace("\r", " ").strip()
                for cell in raw
            ]
            if not any(values):
                continue
            if values == list(columns):
                continue  # header row
            out.append(dict(zip(columns, values)))
    return out


def merge_by_key(existing, fresh, key):
    """Union two row lists on `key`, preferring rows already on disk.

    Scrapers that rewrite a year file must not lose history when the
    source's listing window shrinks (the redesigned TN site only exposes
    recent issues). On-disk rows win so accumulated metadata such as
    Wayback columns survives.
    """
    seen = set()
    merged = []
    for row in existing + fresh:
        k = (row.get(key) or "").strip()
        if not k:
            # Rows without a usable key must never collapse into one another.
            merged.append(row)
            continue
        if k in seen:
            continue
        seen.add(k)
        merged.append(row)
    return merged
