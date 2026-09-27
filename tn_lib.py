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
