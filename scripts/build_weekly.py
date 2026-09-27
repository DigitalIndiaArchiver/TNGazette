#!/usr/bin/env python3
"""Build the weekly-updates pages for the docs site.

Reads the current year's canonical CSVs, groups rows by ISO week of the
gazette date, and writes:
  docs/weekly/index.html            latest week + archive list
  docs/weekly/{isoYear}-W{ww}.html  one frozen page per week with data

Static HTML only (no JS), so archived pages never rot. Markdown links are
computed with the same slug rule as scripts/extract_utils.py - keep in sync.

Usage: python3 scripts/build_weekly.py [--year 2026]
"""
import argparse
import re
from datetime import datetime, date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tn_lib import read_rows, GAZATTES_COLUMNS, EXTRAORDINARY_COLUMNS

PROJECT = Path(__file__).resolve().parent.parent
DOCS = PROJECT / "docs"
WEEKLY = DOCS / "weekly"
MARKDOWN = PROJECT / "data" / "markdown"
REPO_BLOB = "https://github.com/DigitalIndiaArchiver/TNGazette/blob/main/data/markdown"
TRUNC = 360


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def slugify(text, max_len=80):
    # keep in sync with extract_utils.slugify
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:max_len].rstrip("-")


def parse_ord_date(s):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_extra_date(s):
    try:
        return datetime.strptime(s.strip(), "%d-%m-%Y").date()
    except ValueError:
        return None


def week_key(d):
    iso = d.isocalendar()
    return (iso[0], iso[1])


def week_range(d):
    iso = d.isocalendar()
    start = date.fromisocalendar(iso[0], iso[1], 1)
    end = date.fromisocalendar(iso[0], iso[1], 7)
    return start, end


def md_link(gaz_type, year, issue_no, part_label, label):
    fname = f"{issue_no}-{slugify(part_label)}.md"
    if (MARKDOWN / gaz_type / str(year) / fname).exists():
        url = f"{REPO_BLOB}/{gaz_type}/{year}/{fname}"
        return f' <a href="{url}">text ↗</a>'
    return ""


def pdf_cell(url, archived, deleted):
    out = []
    if url:
        out.append(f'<a href="{esc(url)}" title="Official site (India-only access)">PDF ↗</a>')
    if archived and str(archived).strip().lower() not in ("nan", "none", ""):
        out.append(f'<a href="{esc(archived)}">Wayback ↗</a>')
    if str(deleted).strip().lower() in ("true", "1"):
        out.append('<span class="flag">deleted on official site</span>')
    return " ".join(out) if out else "—"


def trunc(s):
    s = str(s or "").strip()
    if len(s) <= TRUNC:
        return esc(s)
    return esc(s[:TRUNC].rstrip()) + "…"


NAV = """<header class="site-header">
  <div class="container">
    <a class="site-title" href="../index.html">TN Gazette Archive<span class="ta">தமிழ்நாடு அரசிதழ்</span></a>
    <nav class="site-nav">
      <a href="../index.html">Overview</a>
      <a href="../data.html">The data</a>
      <a href="../years.html">Years</a>
      <a href="index.html" class="active">Weekly</a>
      <a href="../archives.html">Originals &amp; archives</a>
      <a href="../about.html">About</a>
    </nav>
  </div>
</header>"""


def page(title, description, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="../style.css">
</head>
<body>
{NAV}
<main class="container">
{body}
</main>
<footer class="site-footer">
  <div class="container">
    An independent open-data project ·
    <a href="https://github.com/DigitalIndiaArchiver/TNGazette">source &amp; datasets on GitHub</a> ·
    data from the <a href="https://www.stationeryprinting.tn.gov.in/">TN Commissionerate of Printing and Stationery</a>
  </div>
</footer>
</body>
</html>
"""


def short(s, n=140):
    s = " ".join(str(s or "").split())
    if len(s) <= n:
        return esc(s)
    return esc(s[:n].rstrip()) + "…"


def tldr_section(rows_o, rows_x):
    """One line per distinct subject: ordinary part categories + each
    extraordinary notification."""
    items = []
    seen = {}
    for r in rows_o:
        key = " ".join(str(r.get("Content") or "").split()).lower()
        if not key:
            key = ("part:" + str(r.get("Part") or "")).lower()
        seen.setdefault(key, [r, 0])
        seen[key][1] += 1
    n_issues = len({str(r.get("Issue") or "") for r in rows_o})
    if rows_o:
        parts = sorted(seen.values(), key=lambda v: -v[1])
        for r, n in parts:
            note = f' <span class="stat-meta">({n} part{"s" if n > 1 else ""})</span>' if n > 1 else ""
            items.append(
                f'      <li><strong>Ordinary</strong> — {short(r.get("Content"))}{note} '
                f'<a href="#ordinary">parts →</a></li>')
    for r in sorted(rows_x, key=lambda r: str(r.get("Issue Date") or "")):
        no = str(r.get("Issue No") or "").strip() or "?"
        d = parse_extra_date(str(r.get("Issue Date") or ""))
        label = f"Ex. no. {no}" + (f" ({d.strftime('%d %b')})" if d else "")
        pieces = [f"<strong>{esc(label)}</strong>"]
        subject = " ".join(str(r.get("Subject") or "").split())
        dept = str(r.get("Department") or "").strip()
        if dept and len(subject) > len(dept):
            idx = subject.find(dept)
            if idx > 0:
                subject = subject[:idx].rstrip(" .-–—;")
        subj = short(subject)
        if subj:
            pieces.append(subj)
        dept = short(r.get("Department"), 60)
        if dept:
            pieces.append(dept)
        link = ""
        if (r.get("PDF Link") or "").strip():
            link = f' <a href="{esc(r["PDF Link"])}">PDF ↗</a>'
        items.append(f"      <li>{' — '.join(pieces)}{link}</li>")
    if not items:
        return ""
    lis = "\n".join(items)
    return f"""
  <section class="tldr">
    <h2>TL;DR — what the gazette covered this week</h2>
    <ul>
{lis}
    </ul>
  </section>"""


def ordinary_table(rows, year):
    if not rows:
        return ""
    trs = []
    for r in sorted(rows, key=lambda r: (r["Issue"], r["Part"])):
        trs.append(
            f"<tr><td>{esc(r['Issue'])}</td><td>{esc(r['Date'])}</td>"
            f"<td>{esc(r['Part'])}</td><td title=\"{trunc(r['Content'])}\">{trunc(r['Content'])}</td>"
            f"<td>{pdf_cell(r['URL'], r.get('Archived URL'), r.get('Deleted'))}"
            f"{md_link('ordinary', year, r['Issue'], r['Part'], 'text')}</td></tr>")
    return f"""
<table>
<thead><tr><th>Issue</th><th>Date</th><th>Part</th><th>Contents</th><th>Links</th></tr></thead>
<tbody>{''.join(trs)}</tbody>
</table>"""


def extra_table(rows, year):
    if not rows:
        return ""
    trs = []
    for r in sorted(rows, key=lambda r: r["Issue Date"]):
        part = r["Extraordinary Part & Section"]
        trs.append(
            f"<tr><td>{esc(r['Issue No'])}</td><td>{esc(r['Issue Date'])}</td>"
            f"<td>{esc(r['Extraordinary Type'])}</td>"
            f"<td title=\"{trunc(r['Subject'])}\">{trunc(r['Subject'])}</td>"
            f"<td>{esc(r['Department'])}</td><td>{esc(r['G.O No'])}</td>"
            f"<td>{pdf_cell(r['PDF Link'], '', '')}"
            f"{md_link('extraordinary', year, r['Issue No'], part, 'text')}</td></tr>")
    return f"""
<table>
<thead><tr><th>Issue No</th><th>Date</th><th>Type</th><th>Subject</th><th>Department</th><th>G.O No</th><th>Links</th></tr></thead>
<tbody>{''.join(trs)}</tbody>
</table>"""


def week_body(wk, weeks, current, lede=None, include_archive=True):
    (wy, ww) = wk
    rows_o = weeks[wk]["ordinary"]
    rows_x = weeks[wk]["extraordinary"]
    start, end = week_range(min(weeks[wk]["dates"]))
    n_issues = len({r["Issue"] for r in rows_o})
    stats = f"""
  <section class="stats">
    <div class="stat"><div class="stat-num">{n_issues}</div><div class="stat-label">weekly issues</div></div>
    <div class="stat"><div class="stat-num">{len(rows_o)}</div><div class="stat-label">ordinary parts</div></div>
    <div class="stat"><div class="stat-num">{len(rows_x)}</div><div class="stat-label">extraordinary notifications</div></div>
  </section>"""
    tldr = tldr_section(rows_o, rows_x)
    arch = [w for w in sorted(weeks, reverse=True) if w != wk]
    arch_items = "\n".join(
        f'      <li><a href="{week_file(w)}.html">{week_title(w)}</a></li>' for w in arch)
    arch_html = (f"\n  <section>\n    <h2>Older weeks</h2>\n    <ul>\n{arch_items}\n    </ul>\n  </section>"
                 if arch else "")
    heading = ("This week in the Gazette" if current else "Gazette updates")
    lede_html = (f'<p class="lede">{lede}</p>' if lede else f"""<p class="lede">ISO week {ww} of {wy}. Everything the archive picked up this week:
    ordinary weekly issues part by part, and extraordinary notifications, with links to the
    official PDF, its Wayback copy and the extracted full text. Frozen when the week closes —
    later corrections only re-add rows dated to this week.</p>""")
    return f"""
  <section class="hero">
    <h1>{heading}<br><span class="ta">{esc(start.strftime('%d %b'))} – {esc(end.strftime('%d %b %Y'))}</span></h1>
    {lede_html}
  </section>
{stats}
{tldr}
  <section>
    <h2 id="ordinary">Ordinary gazette parts</h2>
    {ordinary_table(rows_o, wy) or '<p class="stat-meta">No ordinary issues dated this week.</p>'}
  </section>
  <section>
    <h2 id="extraordinary">Extraordinary notifications</h2>
    {extra_table(rows_x, wy) or '<p class="stat-meta">No extraordinary notifications dated this week.</p>'}
  </section>
  <section class="usage">
    <h2>Where this comes from</h2>
    <p class="stat-meta">Rows are dated to their gazette date, not the scrape date: a page shows
    what the government published that week. PDFs on the official site are reachable only from
    Indian IPs — the Wayback copies are not. Full-text links go to the extracted markdown on
    GitHub. Older weeks: see the archive list below, or
    <a href="../data.html">the datasets</a> for everything at once.</p>
  </section>{arch_html if include_archive else ""}"""


def week_file(wk):
    return f"{wk[0]}-W{wk[1]:02d}"


def week_title(wk):
    return f"{wk[0]} week {wk[1]:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=date.today().year)
    args = ap.parse_args()
    year = args.year

    weeks = {}
    skipped = 0
    for r in read_rows(PROJECT / f"data/Gazattes_{year}.csv", GAZATTES_COLUMNS):
        d = parse_ord_date(r.get("Date", ""))
        if not d:
            skipped += 1
            continue
        wk = weeks.setdefault(week_key(d), {"ordinary": [], "extraordinary": [], "dates": []})
        wk["ordinary"].append(r)
        wk["dates"].append(d)
    for r in read_rows(PROJECT / f"data/ExtraOrdinaryGazattes_{year}.csv", EXTRAORDINARY_COLUMNS):
        d = parse_extra_date(r.get("Issue Date", ""))
        if not d:
            skipped += 1
            continue
        wk = weeks.setdefault(week_key(d), {"ordinary": [], "extraordinary": [], "dates": []})
        wk["extraordinary"].append(r)
        wk["dates"].append(d)

    if not weeks:
        print(f"No dated rows for {year}; nothing to build")
        return

    WEEKLY.mkdir(parents=True, exist_ok=True)
    current_wk = week_key(date.today())

    for wk, data in sorted(weeks.items()):
        start, end = week_range(min(data["dates"]))
        body = week_body(wk, weeks, current=(wk == current_wk))
        title = f"TN Gazette updates — {year} week {wk[1]:02d} ({start.strftime('%d %b')}–{end.strftime('%d %b %Y')})"
        (WEEKLY / f"{week_file(wk)}.html").write_text(
            page(title, "Weekly updates from the TN Gazette archive: ordinary parts and extraordinary notifications, with PDF, Wayback and full-text links.", body),
            encoding="utf-8")

    latest = max(weeks)
    listing = "\n".join(
        f'      <li><a href="{week_file(w)}.html">{week_title(w)}</a>'
        f' — {len(weeks[w]["ordinary"])} parts, {len(weeks[w]["extraordinary"])} extraordinary</li>'
        for w in sorted(weeks, reverse=True))
    index_lede = ("The latest updates from the Tamil Nadu Government Gazette, refreshed daily by "
                  "the archive's pipeline: new ordinary parts and extraordinary notifications, "
                  "each with the official PDF, a Wayback copy where one exists, and the extracted "
                  "full text. When the week closes, this page freezes into the archive below.")
    body = (week_body(latest, weeks, current=True, lede=index_lede, include_archive=False)
            + f"\n  <section>\n    <h2>Archive of past weeks</h2>\n    <ul>\n{listing}\n    </ul>\n  </section>")
    (WEEKLY / "index.html").write_text(
        page(f"TN Gazette updates — week {latest[1]:02d}, {latest[0]}",
             "The latest weekly updates from the TN Gazette archive, refreshed daily, plus the frozen archive of past weeks.",
             body),
        encoding="utf-8")

    print(f"Weekly pages: {len(weeks)} week pages + index for {year} "
          f"({skipped} rows without parsable dates skipped) -> {WEEKLY}")


if __name__ == "__main__":
    main()
