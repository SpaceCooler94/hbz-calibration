#!/usr/bin/env bash
# render_run.sh — one runner for both Render cron jobs.
#
#   bash render_run.sh daily        grade yesterday, snapshot today
#   bash render_run.sh calibrate    backfill the season, recalibrate
#
# A Render cron job is a fresh, diskless container, so this clones the repo
# with a push-capable token, does the work in that clone, and commits the
# results back. State that must survive (agg/, snapshots/, ledger.csv,
# calibration.json, report.md) is versioned in git; data/raw is not, so it
# re-fetches each run — cheap for daily, ~10-15 min for the weekly backfill.
set -euo pipefail

MODE="${1:?usage: render_run.sh daily|calibrate}"
: "${GH_PAT:?set GH_PAT in the Render dashboard}"
: "${GH_REPO:?set GH_REPO (e.g. yourname/hbz-calibration)}"
BRANCH="${GH_BRANCH:-main}"
SEASON_START="${SEASON_START:-2026-03-26}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --quiet --branch "$BRANCH" \
  "https://x-access-token:${GH_PAT}@github.com/${GH_REPO}.git" "$WORK"
cd "$WORK"
git config user.name  "hbz-bot"
git config user.email "hbz-bot@users.noreply.github.com"

case "$MODE" in
  daily)
    python3 join_outcomes.py
    python3 collect_daily.py --season-start "$SEASON_START"
    git add agg snapshots ledger.csv 2>/dev/null || true
    MSG="daily: $(date -u +%F)"
    ;;
  calibrate)
    python3 test_leakage.py                       # leakage guard before grading
    END="${END_DATE:-$(date -u -d 'yesterday' +%F)}"
    python3 backfill.py --start "$SEASON_START" --end "$END"
    python3 calibrate.py
    git add calibration.json report.md
    MSG="calibrate: $(date -u +%F)"
    ;;
  *)
    echo "unknown mode: $MODE" >&2; exit 2 ;;
esac

if git diff --staged --quiet; then
  echo "nothing to commit"
else
  git commit --quiet -m "$MSG"
  git push --quiet origin "$BRANCH"
  echo "pushed: $MSG"
fi
