#!/usr/bin/env bash
# Weekly scrape from an Indian vantage point.
#
# GitHub-hosted runners cannot reach stationeryprinting.tn.gov.in (non-India
# IPs are refused), so the CI workflow preflights, skips and warns. This script
# is the out-of-band replacement: run it from a machine with an Indian egress
# (or through a SOCKS tunnel to one), and it does the whole weekly job locally
# - scrape, guard, extract, stats, tests - then tells you what to commit.
#
# Usage:
#   scripts/weekly_from_vantage.sh                 # direct connection (must be in India)
#   PROXY=socks5h://127.0.0.1:31080 scripts/weekly_from_vantage.sh
#   PUSH=1 scripts/weekly_from_vantage.sh          # commit + push to a dated branch
#
# Tunnel from a foreign machine to an Indian host:
#   ssh -f -N -D 127.0.0.1:31080 -i ~/.ssh/<key> \
#       -o ProxyCommand="tailscale nc <india-host> 22" ubuntu@<india-host>
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
PROXY="${PROXY:-}"
PUSH="${PUSH:-0}"
SITE="https://www.stationeryprinting.tn.gov.in/gazette.php?id=MjAyNg=="
CURL=(curl -sS -o /dev/null -w '%{http_code}' --max-time 30)
# Both scrapers honour the proxy: scrape_ordinary.py takes an explicit flag,
# scrape_gazettes.py reads the standard requests env vars.
SCRAPE_ARGS=()
if [ -n "$PROXY" ]; then
  SCRAPE_ARGS+=(--proxy "$PROXY")
  export ALL_PROXY="$PROXY" HTTPS_PROXY="$PROXY" HTTP_PROXY="$PROXY"
fi

echo "== preflight =="
code=$("${CURL[@]}" "$SITE" || echo "000")
echo "   direct: HTTP $code"
if [ "$code" != "200" ]; then
  if [ -z "$PROXY" ]; then
    echo "   FAIL: site unreachable and no PROXY set." >&2
    echo "   Re-run through an Indian vantage, e.g." >&2
    echo "     PROXY=socks5h://127.0.0.1:31080 $0" >&2
    exit 1
  fi
  pcode=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 --proxy "$PROXY" "$SITE" || echo "000")
  echo "   via proxy: HTTP $pcode"
  [ "$pcode" = "200" ] || { echo "   FAIL: proxy does not reach the site either." >&2; exit 1; }
fi

echo "== extraordinary (current years) =="
python3 scrape_gazettes.py || exit 1

echo "== ordinary (latest weekly issues) =="
python3 scrape_ordinary.py "${SCRAPE_ARGS[@]}" || exit 1

echo "== dataset guard =="
python3 scripts/assert_datasets.py || exit 1

echo "== markdown extraction (new PDFs only) =="
python3 scripts/extract_pdfs.py --gazette ordinary --years "$(date -u +%Y)" 2>/dev/null || \
  echo "   (extraction skipped - see #17 for wiring it into the weekly run)"

echo "== tests =="
python3 -m pytest tests/ -q || exit 1

echo "== site stats =="
python3 scripts/build_site_stats.py || exit 1

echo "== result =="
if git diff --quiet && git diff --cached --quiet; then
  echo "   no data changes this run"
  exit 0
fi
git --no-pager diff --stat
if [ "$PUSH" = "1" ]; then
  branch="data/$(date -u +%Y-%m-%d)"
  git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
  git add -A && git commit -q -m "Weekly scrape and Wayback archival ($(date -u +%Y-%m-%d)) from Indian vantage" && \
  git push -u origin "$branch" && echo "   pushed $branch - open a PR to run guards on main"
else
  echo "   commit and push when ready (re-run with PUSH=1 to do it automatically)"
fi
