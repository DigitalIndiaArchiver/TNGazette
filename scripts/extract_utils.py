"""
Shared utilities for PDF-to-markdown extraction pipeline.
"""
import os, re, time, logging
from pathlib import Path

import requests
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MARKDOWN_DIR = DATA_DIR / "markdown"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# ── Helpers ────────────────────────────────────────────────────────────────

def slugify(text, max_len=80):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:max_len].rstrip('-')


def make_frontmatter(metadata):
    parts = ["---"]
    for key, value in metadata.items():
        if value is None or (isinstance(value, float) and value != value):
            continue
        s = str(value).strip()
        if not s:
            continue
        escaped = s.replace('"', '\\"')
        parts.append(f'{key}: "{escaped}"')
    parts.append("---")
    return "\n".join(parts)


def sanitize_text(text):
    if not text:
        return ""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── PDF operations ─────────────────────────────────────────────────────────

def _encode_unicode_url(url):
    from urllib.parse import urlsplit, urlunsplit, quote
    parts = urlsplit(url)
    path = quote(parts.path, safe="/%@") if parts.path else ""
    query = quote(parts.query, safe="=&%+") if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def fetch_pdf(url, timeout=45):
    url = _encode_unicode_url(url)
    session = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=1)
    b = requests.adapters.HTTPAdapter(max_retries=1)
    session.mount("http://", a)
    session.mount("https://", b)
    try:
        resp = session.get(
            url, timeout=timeout,
            headers={"User-Agent": "TNGazette-Extractor/1.0"}
        )
        if resp.status_code != 200:
            logger.warning("HTTP %s for %s", resp.status_code, url[:80])
            return None
        ct = resp.headers.get("Content-Type", "")
        if "application/pdf" not in ct and not url.lower().endswith(".pdf"):
            if len(resp.content) < 200 or b"<html" in resp.content[:500].lower():
                logger.warning("Non-PDF content at %s (type: %s)", url[:80], ct)
                return None
        return resp.content
    except requests.exceptions.RequestException as exc:
        logger.warning("Fetch failed for %s: %s", url[:60], exc)
        return None


def extract_text(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        chunks = []
        for page in doc:
            chunks.append(page.get_text())
        doc.close()
        return "\n\n".join(chunks)
    except Exception as exc:
        logger.error("Text extraction failed: %s", exc)
        return None


def resolve_pdf_url(row):
    archived = row.get("Archived URL")
    original = row.get("URL") or row.get("PDF Link") or ""
    archive_val = str(archived).strip() if archived and not (isinstance(archived, float) and archived != archived) else ""
    orig_val = str(original).strip() if original and not (isinstance(original, float) and original != original) else ""
    if archive_val:
        return archive_val, "wayback"
    if orig_val:
        return orig_val, "original"
    return None, None


# ── Output paths ───────────────────────────────────────────────────────────

def output_path(gazette_type, year, issue_no, part_label):
    year_str = str(year)
    slug = slugify(f"{issue_no}-{part_label}")
    out_dir = MARKDOWN_DIR / gazette_type / year_str
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{slug}.md"


def build_metadata(row, gazette_type, year, url_source, pdf_url):
    md = {"source": url_source, "type": gazette_type, "year": year, "pdf_url": pdf_url}
    for col in row.index:
        if col in ("", "Unnamed: 0", "URL", "PDF Link", "Archived URL", "Archived Date", "Deleted"):
            continue
        val = row[col]
        if val is None or (isinstance(val, float) and val != val):
            continue
        s = str(val).strip()
        if not s:
            continue
        md[col] = s
    return md


# ── Rate limiting ──────────────────────────────────────────────────────────

class RateLimiter:
    def __init__(self, delay=1.0):
        self.delay = delay
        self._last = 0.0

    def wait(self):
        elapsed = time.time() - self._last
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last = time.time()
