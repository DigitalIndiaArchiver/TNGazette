#!/usr/bin/env bash
# Daily TN Gazette update — delta-only pipeline.
#
# Checks the TN gazette site for NEW rows only (since what is already in the
# canonical CSVs), fetches just the new PDFs via ocitwo (Indian vantage),
# merges them, distills only new PDFs to markdown, rebuilds stats + weekly
# pages, then commits/pushes to main. No bulk transfers: ocitwo keeps no
# repo clone and only ever holds one small state file + new PDFs.
#
#   scripts/daily_update.sh              # full run
#   PUSH=0 scripts/daily_update.sh       # do everything except git push
#   KEEP=1 scripts/daily_update.sh       # keep /tmp artifacts for debugging
#
# Exit codes: 0 ok (change or no-change) | 1 failure | 2 site unreachable.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
YEAR="$(date -u +%Y)"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
WORK="$(mktemp -d /tmp/tngazette-daily.XXXXXX)"
PUSH="${PUSH:-1}"
KEEP="${KEEP:-0}"
OCITWO="${OCITWO:-/home/workspace/Skills/ocitwo-access/scripts/ocitwo.sh}"
cleanup() { [ "$KEEP" = "1" ] || rm -rf "$WORK"; }
trap cleanup EXIT INT TERM

fail() { echo "DAILY_RESULT: failure reason=$1"; exit "${2:-1}"; }

echo "== 1. state: known URLs from canonical CSVs =="
python3 - "$WORK/state.json" "$YEAR" <<'PYEOF'
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from tn_lib import read_rows, GAZATTES_COLUMNS, ISSUES_COLUMNS, EXTRAORDINARY_COLUMNS

year = sys.argv[2]
def urls(path, col, columns):
    return [r[col].strip() for r in read_rows(Path(path), columns) if r.get(col, "").strip()]

state = {
    "ordinary_parts": urls(f"data/Gazattes_{year}.csv", "URL", GAZATTES_COLUMNS),
    "ordinary_issues": urls(f"data/GazatteIssues_{year}.csv", "URL", ISSUES_COLUMNS),
    "extraordinary": urls(f"data/ExtraOrdinaryGazattes_{year}.csv", "PDF Link", EXTRAORDINARY_COLUMNS),
}
Path(sys.argv[1]).write_text(json.dumps(state))
print("  known: %d parts, %d issues, %d extraordinary" % (
    len(state["ordinary_parts"]), len(state["ordinary_issues"]), len(state["extraordinary"])))
PYEOF
[ -s "$WORK/state.json" ] || fail "state-generation"

echo "== 2. push fetcher + state to ocitwo =="
$OCITWO exec "mkdir -p ~/tn-latest/out" || fail "ocitwo-unreachable" 2
$OCITWO put tn_lib.py "tn-latest/tn_lib.py" || fail "ocitwo-put" 2
$OCITWO put scripts/vantage_latest.py "tn-latest/vantage_latest.py" || fail "ocitwo-put" 2
$OCITWO put "$WORK/state.json" "tn-latest/state.json" || fail "ocitwo-put" 2

echo "== 3. delta fetch on ocitwo (Indian vantage) =="
REMOTE_OUT="$($OCITWO exec "cd ~/tn-latest && python3 vantage_latest.py --state state.json --out out --year $YEAR --delay 0.7 2>&1; echo REMOTE_EXIT:\$?")" || true
echo "$REMOTE_OUT" | tail -8
REMOTE_EXIT="$(echo "$REMOTE_OUT" | grep -o 'REMOTE_EXIT:[0-9]*' | tail -1 | cut -d: -f2)"
case "$REMOTE_EXIT" in
  0) : ;;
  2) fail "gazette-site-unreachable" 2 ;;
  3) fail "gazette-site-parse" ;;
  *) fail "ocitwo-run-exit-$REMOTE_EXIT" ;;
esac

$OCITWO get "tn-latest/out/delta.json" "$WORK/delta.json" || fail "ocitwo-get-delta" 2

NEW="$(python3 -c "
import json
d = json.load(open('$WORK/delta.json'))
print(len(d.get('new_parts', [])), len(d.get('new_issues', [])), len(d.get('new_extraordinary', [])), len(d.get('downloads', [])))
")"
read -r N_PARTS N_ISSUES N_EXTRA N_PDFS <<EOF
$NEW
EOF
echo "  delta: +$N_PARTS parts, +$N_ISSUES issues, +$N_EXTRA extraordinary, $N_PDFS pdfs"

echo "== 4. pull new PDFs (if any) =="
if [ "$N_PDFS" != "0" ]; then
  $OCITWO exec "cd ~/tn-latest/out && tar czf pdfs.tgz pdfs" || fail "ocitwo-tar" 2
  $OCITWO get "tn-latest/out/pdfs.tgz" "$WORK/pdfs.tgz" || fail "ocitwo-get-pdfs" 2
fi
$OCITWO exec "rm -f ~/tn-latest/out/delta.json ~/tn-latest/out/pdfs.tgz && rm -rf ~/tn-latest/out/pdfs" >/dev/null || true

if [ "$N_PARTS" != "0" ] || [ "$N_EXTRA" != "0" ]; then
  echo "== 5. merge delta into canonical CSVs =="
  python3 - "$WORK/delta.json" "$YEAR" <<'PYEOF'
import csv, json, shutil, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from tn_lib import read_rows, merge_by_key, GAZATTES_COLUMNS, ISSUES_COLUMNS, EXTRAORDINARY_COLUMNS

delta = json.loads(Path(sys.argv[1]).read_text())
year = sys.argv[2]

def esc(val):
    s = str(val or "")
    if any(c in s for c in (",", '"', "\n")):
        return '"' + s.replace('"', '""') + '"'
    return s

def file_columns(path, fallback):
    # archive_new_links.py appends Archived columns to files it touches, so
    # always merge with whatever header the file already carries.
    if path.exists():
        with open(path, encoding="utf-8", errors="replace") as fh:
            first = fh.readline().strip()
        if first:
            return [c.strip() for c in next(csv.reader([first]))]
    return fallback

def merge_csv(path, fallback_cols, key, fresh):
    columns = file_columns(path, fallback_cols)
    rows = read_rows(path, columns)
    merged = merge_by_key(rows, fresh, key)
    added = len(merged) - len(rows)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write(",".join(columns) + "\n")
        for row in merged:
            fh.write(",".join(esc(row.get(c, "")) for c in columns) + "\n")
    print("  %s: +%d rows -> %d" % (path.name, added, len(merged)))
    return pd.DataFrame(merged, columns=columns)

gaz = merge_csv(Path(f"data/Gazattes_{year}.csv"), GAZATTES_COLUMNS, "URL", delta.get("new_parts", []))
iss = merge_csv(Path(f"data/GazatteIssues_{year}.csv"), ISSUES_COLUMNS, "URL", delta.get("new_issues", []))
ext = merge_csv(Path(f"data/ExtraOrdinaryGazattes_{year}.csv"), EXTRAORDINARY_COLUMNS, "PDF Link", delta.get("new_extraordinary", []))
gaz.to_parquet(f"data/Gazattes_{year}.parquet", index=False, engine="pyarrow")
iss.to_parquet(f"data/GazatteIssues_{year}.parquet", index=False, engine="pyarrow")
ext.to_parquet(f"data/ExtraOrdinaryGazattes_{year}.parquet", index=False, engine="pyarrow")
Path("/tmp/parquet_data").mkdir(exist_ok=True)
shutil.copy(f"data/ExtraOrdinaryGazattes_{year}.parquet", f"/tmp/parquet_data/ExtraOrdinaryGazattes_{year}.parquet")
PYEOF
  [ $? -eq 0 ] || fail "merge"
else
  echo "== 5. merge skipped (no new rows) =="
fi

if [ "$N_PARTS" != "0" ] || [ "$N_EXTRA" != "0" ]; then
  echo "== 5b. LLM citizen gist for the week =="
  timeout 300 python3 scripts/generate_gist.py 2>&1 | tail -1     || echo "  (gist generation failed - non-fatal, page omits it)"
fi

if [ "$N_PDFS" != "0" ]; then
  echo "== 6. cache new PDFs for distilling =="
  mkdir -p scripts/.pdf_cache
  python3 - "$WORK/delta.json" "$WORK/pdfs.tgz" "$WORK/pdfs-extract" <<'PYEOF'
import json, shutil, sys, tarfile
from pathlib import Path
import hashlib

delta = json.loads(Path(sys.argv[1]).read_text())
cache = Path("scripts/.pdf_cache")
extract = Path(sys.argv[3])
cache.mkdir(parents=True, exist_ok=True)
with tarfile.open(sys.argv[2]) as tar:
    extract.mkdir(parents=True, exist_ok=True)
    tar.extractall(extract, filter="data")
src = extract / "pdfs"
if not src.is_dir():
    hits = [h for h in extract.rglob("pdfs") if h.is_dir()]
    if not hits:
        print("  tarball contains no pdfs/ directory")
        sys.exit(4)
    src = hits[0]
n = 0
for item in delta.get("downloads", []):
    f = src / item["file"]
    if f.exists():
        (cache / (hashlib.md5(item["url"].encode()).hexdigest() + ".pdf")).write_bytes(f.read_bytes())
        n += 1
shutil.rmtree(extract, ignore_errors=True)
print(f"  cached {n} of {len(delta.get('downloads', []))} expected PDFs")
if n != len(delta.get("downloads", [])):
    sys.exit(3)
print("  cached %d PDFs" % n)
PYEOF
  [ $? -eq 0 ] || fail "pdf-cache"
fi

echo "== 7. distill new PDFs to markdown =="
timeout 600 python3 scripts/extract_pdfs.py --gazette ordinary --years "$YEAR" --only-cache 2>&1 | tail -2 \
  || echo "  (ordinary distill incomplete - non-fatal, backlog drains over runs)"
timeout 600 python3 scripts/extract_pdfs.py --gazette extraordinary --years "$YEAR" --only-cache 2>&1 | tail -2 \
  || echo "  (extraordinary distill incomplete - non-fatal, backlog drains over runs)"

echo "== 8. dataset guard + tests =="
python3 scripts/assert_datasets.py || fail "assert-datasets"
python3 -m pytest tests/ -q || fail "tests"

echo "== 9. Wayback archival of new links =="
timeout 480 python3 archive_new_links.py --delay 2 \
  --file "data/Gazattes_$YEAR.csv" --file "data/GazatteIssues_$YEAR.csv" \
  --file "data/ExtraOrdinaryGazattes_$YEAR.csv" 2>&1 | tail -3 \
  || echo "  (wayback step failed - non-fatal, retried next run)"

echo "== 10. stats + weekly pages =="
python3 scripts/build_site_stats.py || fail "site-stats"
python3 scripts/build_weekly.py || fail "weekly-pages"

echo "== 10.5 Telegram channel alert =="
TG_OUT="$(timeout 120 python3 scripts/telegram_alert.py 2>&1)"; TG_RC=$?
echo "$TG_OUT" | tail -3
[ "$TG_RC" -ne 0 ] && echo "  (telegram alert failed rc=$TG_RC - non-fatal; unsent items retry next run)"

echo "== 11. commit + push =="
git add -A
if git diff --cached --quiet; then
  echo "DAILY_RESULT: no-change parts=0 issues=0 extra=0 pushed=0"
  exit 0
fi
git diff --cached --stat | tail -3
git commit -q -m "Daily update ($STAMP): +$N_PARTS parts, +$N_ISSUES issues, +$N_EXTRA extraordinary" \
  || fail "commit"
if [ "$PUSH" = "1" ]; then
  git push -q origin main || fail "push"
  echo "DAILY_RESULT: pushed parts=$N_PARTS issues=$N_ISSUES extra=$N_EXTRA pushed=1"
else
  echo "DAILY_RESULT: staged parts=$N_PARTS issues=$N_ISSUES extra=$N_EXTRA pushed=0 (PUSH=0)"
fi
