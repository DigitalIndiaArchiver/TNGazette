#!/usr/bin/env bash
# Daily TN — underreported TN govt document feeds.
#
# Per scheduler tick:
#   1. push fetcher to ocitwo, run the ocitwo scrape stage, pull sources.json
#   2. merge + update CSVs + rebuild docs/daily pages (build_daily.py)
#   3. commit + push if anything changed (gated on PUSH=1)
#   4. Telegram digest — only when the digest is non-empty AND this tick is a
#      digest slot (11:00/17:00 IST; override with DTN_FORCE_DIGEST=1). Empty
#      digest stays silent at any time. --digest-now forces the send.
#
# Sources (all underreported-by-design, no press releases):
#   go        — tn.gov.in dept-wise Government Orders (38 depts)
#   whatsnew  — tn.gov.in What's New (audit reports, circulars, policy notes)
#   tnpcb_ph  — TNPCB public hearing notices (EIA executive summaries)
#   seco      — CEO Tamil Nadu notifications (election orders)
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
TAG="[dtn]"
OCITWO="${OCITWO:-/home/workspace/Skills/ocitwo-access/scripts/ocitwo.sh}"
CACHE="scripts/.dtn_cache"
LOG_DIR="$CACHE"
mkdir -p "$CACHE"

ist_now() { TZ=Asia/Calcutta date "$1"; }
today="$(ist_now '+%F')"

exec 9>"scripts/.dtn.lock"
if ! flock -n 9; then
  echo "$TAG another run in flight; skipping tick"
  exit 0
fi

# ---- stage 1: ocitwo fetch ------------------------------------------------
if ! command -v "$OCITWO" >/dev/null 2>&1; then
  echo "$TAG ocitwo.sh not found at $OCITWO; skip"
  exit 1
fi
"$OCITWO" put scripts/dailytn_fetch.py /tmp/dailytn_fetch.py >/dev/null || exit 1
"$OCITWO" put tn_lib.py /tmp/tn_lib.py >/dev/null || exit 1
"$OCITWO" exec 'mkdir -p /tmp/dtn && cd /tmp/dtn && cp /tmp/tn_lib.py . 2>/dev/null; python3 /tmp/dailytn_fetch.py --stage ocitwo > /tmp/dtn/sources.json 2>/tmp/dtn/progress.txt; grep -q SOURCES_JSON_BEGIN /tmp/dtn/sources.json' >/dev/null || {
  echo "$TAG ocitwo fetch failed; tail of progress:"
  "$OCITWO" exec 'tail -3 /tmp/dtn/progress.txt' 2>/dev/null | sed 's/^/  | /'
  exit 1
}
"$OCITWO" get /tmp/dtn/sources.json "$CACHE/sources.json" >/dev/null || exit 1
cp "$CACHE/sources.json" "$LOG_DIR/sources-$today.json" 2>/dev/null || true

# ---- stage 2: merge + pages ------------------------------------------------
OUT="$(python3 scripts/build_daily.py 2>&1)"; rc=$?
echo "$TAG $OUT"
[ $rc -eq 0 ] || exit $rc

# ---- stage 3: commit + push ------------------------------------------------
if [ "${PUSH:-0}" = "1" ] && ! git diff --quiet -- data/dailytn docs/daily state/dailytn-state.json 2>/dev/null ||
   [ -n "$(git status --porcelain -- data/dailytn docs/daily state/dailytn-state.json 2>/dev/null)" ]; then
  git add data/dailytn docs/daily state/dailytn-state.json 2>/dev/null
  if ! git diff --cached --quiet 2>/dev/null; then
    if git commit -q -m "Daily TN ($today): ${OUT#DTN_BUILD: }" && git push -q origin main 2>/dev/null; then
      echo "$TAG committed + pushed"
    else
      echo "$TAG commit/push failed (non-fatal)"
    fi
  fi
fi

# ---- stage 4: telegram digest ---------------------------------------------
digest_slot=0
case "$(ist_now '+%H')" in 11|17) digest_slot=1 ;; esac
if [ "${1:-}" = "--digest-now" ] || [ "${DTN_FORCE_DIGEST:-0}" = "1" ] || [ $digest_slot -eq 1 ]; then
  total="$(python3 -c "import json;d=json.load(open('data/dailytn/digest-latest.json'));print(sum(d['counts'].values()))")"
  if [ "$total" -gt 0 ]; then
    set -a; [ -f /etc/zo/tngazette.env ] && . /etc/zo/tngazette.env; set +a
    alert_out="$(python3 scripts/dailytn_alert.py 2>&1)"; alert_rc=$?
    printf '%s\n' "$alert_out" | sed 's/^/  | /'
    if [ "$alert_rc" -eq 0 ]; then
      echo "$TAG digest posted ($total items)"
    else
      echo "$TAG digest send failed rc=$alert_rc (non-fatal); state NOT advanced; retries next slot"
    fi
  else
    echo "$TAG digest slot: nothing new, silent"
  fi
else
  echo "$TAG not a digest slot; page updated only"
fi
exit 0
