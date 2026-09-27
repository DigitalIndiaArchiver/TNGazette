#!/usr/bin/env python3
"""Shared helpers for TN Gazette scrapers (pure functions, unit-testable)."""
import base64

BASE = "https://www.stationeryprinting.tn.gov.in/"


def b64_year(year):
    """Base64-encode a year for the redesigned site's id params."""
    return base64.b64encode(str(year).encode()).decode()


def norm_href(href, base=BASE):
    """Normalize a scraped href to an absolute URL on the TN site.

    Handles: absolute URLs (passthrough), backslash path separators
    (the new site emits gazette\\2026\\file.pdf), and relative paths.
    """
    if not href:
        return ""
    href = href.replace("\\", "/").strip()
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return base + href.lstrip("/")


def split_issue_text(text):
    """Split an issue-cell string like '38 dated:23-09-2026' into
    (issue_no, date_str). Returns ('', '') when the pattern is absent.
    """
    if not text:
        return "", ""
    parts = text.split("dated:")
    issue_no = parts[0].strip() if parts else ""
    date_str = parts[1].strip() if len(parts) > 1 else ""
    return issue_no, date_str


GAZATTES_COLUMNS = [
    "Part", "Content", "URL", "Date", "Issue",
    "Deleted", "Archived URL", "Archived Date",
]
ISSUES_COLUMNS = ["Issue No", "Issue No and Date", "Date", "URL"]
EXTRAORDINARY_COLUMNS = [
    "Issue No", "Issue Date", "Extraordinary Part & Section", "PDF Link",
    "Extraordinary Type", "Subject", "Department", "G.O No",
]
