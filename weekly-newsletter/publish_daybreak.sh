#!/usr/bin/env bash
# publish_daybreak.sh — Generate and publish the Market Day Break daily brief.
#
# Usage:
#   bash publish_daybreak.sh              # today's date
#   bash publish_daybreak.sh 2026-03-04   # specific date

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATE_STR="${1:-$(date +%Y-%m-%d)}"

echo "==> Generating Market Day Break for $DATE_STR ..."
cd "$SCRIPT_DIR"
python generate_market_day_break.py --date "$DATE_STR" --live --pdf

echo ""
echo "==> Rebuilding site ..."
python build_combined_site.py

echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

# Stage each output — suppress errors for files that may not exist (e.g. PDF)
_add() { git add "$@" 2>/dev/null || true; }
_add "weekly-newsletter/fixtures/daybreak_${DATE_STR}.json"
_add "weekly-newsletter/output/market_day_break_${DATE_STR}.md"
_add "weekly-newsletter/output/market_day_break_${DATE_STR}.pdf"
_add "weekly-newsletter/site/daily/"
_add "weekly-newsletter/site/index.html"
_add "weekly-newsletter/site/downloads/"

if git diff --cached --quiet; then
  echo "Nothing new to publish — site is already up to date."
  exit 0
fi

git commit -m "Publish Market Day Break — $DATE_STR"
git push origin master

echo ""
echo "Done. Live at https://frameworkfoundry.info/daily/"
