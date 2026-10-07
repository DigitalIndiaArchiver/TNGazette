#!/usr/bin/env bash
# TNGazette check scheduler — deterministic cadence loop, no LLM sessions.
#
# Cadence (IST): hourly on weekdays 09:00-20:00, every 4h otherwise.
# Each due check runs scripts/daily_update.sh (PUSH=1). The driver is
# delta-only, so a no-change check costs two ocitwo round-trips plus a
# listing scrape; the expensive steps (download/distill/wayback/telegram)
# fire only when new gazettes actually landed. The Telegram channel alert
# is driver step 10.5 — new items post to @tngazette automatically.
#
# Discord #ungalsoththu is notified only on delta>0 or failure; clean
# checks stay silent (log only).
#
# State: scripts/.last_check (epoch of last completed check, gitignored).
# Lost state (fresh boot) = one immediate check — safe.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
IST="Asia/Calcutta"
STATE="scripts/.last_check"
LOCK="scripts/.driver.lock"   # single-instance guard around driver runs
CHANNEL_ID="1551896270862417920"   # LogicPlay #ungalsoththu
TAG="[tgz-sched]"

now_epoch() { date +%s; }
ist_now() { TZ="$IST" date "$@"; }

notify_discord() {
  [ -n "${DISCORD_BOT_TOKEN:-}" ] || { echo "$TAG no DISCORD_BOT_TOKEN, skip notify"; return 0; }
  local payload
  payload="$(python3 -c 'import json,sys; print(json.dumps({"content": sys.argv[1]}))' "$1")"
  curl -s -o /dev/null --max-time 20 -X POST \
    "https://discord.com/api/v10/channels/$CHANNEL_ID/messages" \
    -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$payload" || echo "$TAG discord notify failed"
}

interval_for() {
  # hourly on weekdays 09:00-19:59 IST, else every 4h
  local dow hour
  dow="$(ist_now +%u)"    # 1=Mon .. 7=Sun
  hour="$((10#$(ist_now +%H)))"   # 00-23, forced decimal
  if [ "$dow" -le 5 ] && [ "$hour" -ge 9 ] && [ "$hour" -lt 20 ]; then
    echo 3600
  else
    echo 14400
  fi
}

last="$(cat "$STATE" 2>/dev/null || echo 0)"

while true; do
  iv="$(interval_for)"
  t="$(now_epoch)"
  if [ $((t - last)) -ge "$iv" ]; then
    echo "$TAG $(ist_now '+%F %T %Z') due (every ${iv}s; last check $((t - last))s ago)"
    LOG="$(mktemp /tmp/tngaz-sched.XXXXXX)"
    (
      flock -n 9 || { echo "$TAG another driver holds the lock; skipping this tick"; exit 97; }
      PUSH=1 bash scripts/daily_update.sh
    ) 9>"$LOCK" >"$LOG" 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then
      last="$(now_epoch)"; echo "$last" > "$STATE"
      result="$(grep -o 'DAILY_RESULT:.*' "$LOG" | tail -1)"
      echo "$TAG $result"
      case "$result" in
        *no-change*) : ;;  # clean check: silent
        "")
          echo "$TAG driver ok but no DAILY_RESULT line; tail:"
          tail -3 "$LOG" | sed "s/^/$TAG | /" ;;
        *)
          notify_discord "TNGazette check $(ist_now '+%d %b %H:%M IST'): ${result#DAILY_RESULT: } — https://digitalindiaarchiver.github.io/TNGazette/" ;;
      esac
      # Daily TN — independent feeds (G.O.s / What's New / TNPCB / SECO);
      # own lock, non-fatal: a dtn failure never fails the gazette tick
      if dtn_out="$(PUSH=1 bash scripts/dailytn_update.sh 2>&1)"; then
        echo "$TAG dtn: $(echo "$dtn_out" | grep -E 'DTN_BUILD|digest|committed' | tail -2 | tr '\n' ' ' | cut -c1-200)"
      else
        echo "$TAG dtn FAILED rc=$?; tail: $(echo "$dtn_out" | tail -2 | tr '\n' ' ' | cut -c1-200)"
      fi
      rm -f scripts/.dtn.lock
    elif [ "$rc" -eq 97 ]; then
      echo "$TAG skipped (lock held); watermark unchanged"
    else
      last="$(now_epoch)"; echo "$last" > "$STATE"  # a failed probe still counts; retry next due
      echo "$TAG driver FAILED rc=$rc; tail:"
      tail -5 "$LOG" | sed "s/^/$TAG | /"
      reason="$(tail -2 "$LOG" | tr '\n' ' ' | tr -s ' ' | cut -c1-250)"
      notify_discord "TNGazette check FAILED (rc=$rc) at $(ist_now '+%d %b %H:%M IST'): $reason"
    fi
    rm -f "$LOG"
  fi
  sleep 300
done
