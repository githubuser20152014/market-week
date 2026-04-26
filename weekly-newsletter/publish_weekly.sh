#!/usr/bin/env bash
# publish_weekly.sh — Generate and publish the Framework Foundry Weekly (US + intl + global editions).
#
# Usage:
#   bash publish_weekly.sh                              # generate all editions for today
#   bash publish_weekly.sh 2026-02-28                   # generate for specific date
#   bash publish_weekly.sh 2026-02-28 --publish         # build site + commit + push + email
#   bash publish_weekly.sh 2026-02-28 --global-only     # generate global edition only
#   bash publish_weekly.sh 2026-02-28 --global-only --publish

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATE_STR="${1:-$(date +%Y-%m-%d)}"

# Parse flags
PUBLISH=""
GLOBAL_ONLY=""
for arg in "${@:2}"; do
  case "$arg" in
    --publish)     PUBLISH="--publish" ;;
    --global-only) GLOBAL_ONLY="--global-only" ;;
  esac
done

# Helper: use fixture-aware generation (skip --live if fixture exists for this date)
_live_flag() {
  local fixture_path="$1"
  if [[ -f "$fixture_path" ]]; then
    echo ""          # fixture found — no --live needed
  else
    echo "--live"    # no fixture — fetch from yfinance
  fi
}

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

if [[ "$GLOBAL_ONLY" != "--global-only" ]]; then
  US_LIVE=$(_live_flag "$SCRIPT_DIR/fixtures/indices_${DATE_STR}.json")
  echo "==> Generating US edition for $DATE_STR ${US_LIVE:+(live)}..."
  python generate_newsletter.py --date "$DATE_STR" $US_LIVE

  echo ""
  INTL_LIVE=$(_live_flag "$SCRIPT_DIR/fixtures/intl_indices_${DATE_STR}.json")
  echo "==> Generating intl edition for $DATE_STR ${INTL_LIVE:+(live)}..."
  python generate_intl_newsletter.py --date "$DATE_STR" $INTL_LIVE
  echo ""
fi

DEFAULT_DIGEST_DIR="$HOME/Documents/ContentRepo/07-Reading/news-digest"
DIGEST_DIR="${DIGEST_DIR:-$DEFAULT_DIGEST_DIR}"
DIGEST_FLAG=""
if [[ -n "${DIGEST_DIR:-}" && -d "$DIGEST_DIR" ]]; then
  DIGEST_FLAG="--digest-dir $DIGEST_DIR"
fi

GLOBAL_EQ_LIVE=$(_live_flag "$SCRIPT_DIR/fixtures/global_equity_${DATE_STR}.json")
echo "==> Generating global edition for $DATE_STR ${GLOBAL_EQ_LIVE:+(live)}..."
python generate_global_newsletter.py --date "$DATE_STR" $GLOBAL_EQ_LIVE $DIGEST_FLAG

echo ""
echo "Newsletters ready for review:"
if [[ "$GLOBAL_ONLY" != "--global-only" ]]; then
  echo "  $SCRIPT_DIR/output/newsletter_${DATE_STR}.md"
  echo "  $SCRIPT_DIR/output/intl_newsletter_${DATE_STR}.md"
fi
echo "  $SCRIPT_DIR/output/global_newsletter_${DATE_STR}.md"

if [[ "$PUBLISH" != "--publish" ]]; then
  echo ""
  echo "Review the newsletters above, then run with --publish to deploy:"
  echo "  bash weekly-newsletter/publish_weekly.sh $DATE_STR --publish"
  exit 0
fi

echo ""
echo "==> Rebuilding site ..."
python build_combined_site.py

echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

_add() { git add "$@" 2>/dev/null || true; }

if [[ "$GLOBAL_ONLY" != "--global-only" ]]; then
  _add "weekly-newsletter/fixtures/indices_${DATE_STR}.json"
  _add "weekly-newsletter/fixtures/intl_indices_${DATE_STR}.json"
  _add "weekly-newsletter/output/newsletter_${DATE_STR}.md"
  _add "weekly-newsletter/output/intl_newsletter_${DATE_STR}.md"
fi

_add "weekly-newsletter/fixtures/global_equity_${DATE_STR}.json"
_add "weekly-newsletter/fixtures/global_fx_${DATE_STR}.json"
_add "weekly-newsletter/fixtures/global_commodity_${DATE_STR}.json"
_add "weekly-newsletter/output/global_newsletter_${DATE_STR}.md"
_add "weekly-newsletter/site/"
_add "weekly-newsletter/site/index.html"
_add "weekly-newsletter/site/downloads/"

if git diff --cached --quiet; then
  echo "Nothing new to publish — site is already up to date."
  exit 0
fi

git commit -m "Publish Framework Foundry Weekly — $DATE_STR"
git push origin master

echo ""
echo "Done. Live at https://frameworkfoundry.info/"

echo ""
echo "==> Sending email to subscribers ..."
cd "$SCRIPT_DIR"
if [[ "$GLOBAL_ONLY" != "--global-only" ]]; then
  python send_email.py --edition weekly --date "$DATE_STR"
  python send_email.py --edition intl   --date "$DATE_STR"
fi
python send_email.py --edition global  --date "$DATE_STR"
