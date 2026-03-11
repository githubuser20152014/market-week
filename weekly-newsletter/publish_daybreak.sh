#!/usr/bin/env bash
# publish_daybreak.sh — Generate and publish the Market Day Break daily brief.
#
# Usage:
#   bash publish_daybreak.sh                        # generate only (today)
#   bash publish_daybreak.sh 2026-03-06             # generate only (specific date)
#   bash publish_daybreak.sh 2026-03-06 --publish   # build site + commit + push + email

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATE_STR="${1:-$(date +%Y-%m-%d)}"

# Parse flags
PUBLISH=""
for arg in "${@:2}"; do
  case "$arg" in
    --publish) PUBLISH="--publish" ;;
  esac
done

# Ensure we are on master before publishing
CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "master" ]]; then
  echo "ERROR: You are on branch '$CURRENT_BRANCH'. Switch to master before publishing."
  echo "  git checkout master"
  exit 1
fi

# Load API keys if present
ENV_FILE="$SCRIPT_DIR/config/api_keys.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

cd "$SCRIPT_DIR"
MD_PATH="$SCRIPT_DIR/output/market_day_break_${DATE_STR}.md"
PDF_PATH="$SCRIPT_DIR/output/market_day_break_${DATE_STR}.pdf"

# Only generate if not already present (preserves manual edits on --publish)
if [[ ! -f "$MD_PATH" ]]; then
  echo "==> Generating Market Day Break for $DATE_STR ..."
  python generate_market_day_break.py --date "$DATE_STR" --live --pdf
else
  echo "==> Using existing newsletter for $DATE_STR (skipping regeneration)"
fi

echo ""
echo "Newsletter ready for review:"
echo "  $MD_PATH"

if [[ "$PUBLISH" != "--publish" ]]; then
  echo ""
  echo "Review the newsletter above, then run with --publish to deploy:"
  echo "  bash weekly-newsletter/publish_daybreak.sh $DATE_STR --publish"
  exit 0
fi

echo ""
echo "==> Rebuilding site ..."
python build_combined_site.py

echo ""
echo "==> Regenerating PDF from verified site HTML ..."
python regen_daybreak_pdf.py "$DATE_STR"

echo ""
echo "==> Verifying HTML and PDF match approved MD ..."
python verify_site_content.py "$DATE_STR"

echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

# Stage each output — suppress errors for files that may not exist (e.g. PDF)
_add() { git add "$@" 2>/dev/null || true; }
_add "weekly-newsletter/fixtures/daybreak_${DATE_STR}.json"
_add "weekly-newsletter/output/market_day_break_${DATE_STR}.md"
_add "weekly-newsletter/output/market_day_break_${DATE_STR}.pdf"
_add "weekly-newsletter/output/linkedin_${DATE_STR}.txt"
_add "weekly-newsletter/output/x_${DATE_STR}.txt"
_add "weekly-newsletter/output/substack_${DATE_STR}.html"
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

echo ""
echo "==> Sending email to subscribers ..."
python "$SCRIPT_DIR/send_email.py" --edition daybreak --date "$DATE_STR"
