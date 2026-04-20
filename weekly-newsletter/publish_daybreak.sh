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

# If $1 looks like a flag (starts with --), treat as no date provided
if [[ "${1:-}" == --* ]]; then
  DATE_STR="$(date +%Y-%m-%d)"
  FLAG_ARGS=("$@")
else
  DATE_STR="${1:-$(date +%Y-%m-%d)}"
  FLAG_ARGS=("${@:2}")
fi

# Parse flags
PUBLISH=""
SEND_EMAIL=""
POLISH=""
for arg in "${FLAG_ARGS[@]+"${FLAG_ARGS[@]}"}"; do
  case "$arg" in
    --publish)    PUBLISH="--publish" ;;
    --send-email) SEND_EMAIL="--send-email" ;;
    --polish)     POLISH="--polish" ;;
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

# Phase 1: Generate Markdown only (no PDF or social posts yet)
# Skipped entirely when --publish is set — approved MD must already exist.
FIXTURE_PATH="$SCRIPT_DIR/fixtures/daybreak_${DATE_STR}.json"

if [[ "$PUBLISH" == "--publish" ]]; then
  # Publishing to website — approved MD is the ONLY content source.
  # Never call the Claude API here; never regenerate narrative.
  if [[ ! -f "$MD_PATH" ]]; then
    echo "ERROR: Cannot publish — approved markdown not found:"
    echo "  $MD_PATH"
    echo ""
    echo "Run without --publish first to generate and review the content:"
    echo "  bash weekly-newsletter/publish_daybreak.sh $DATE_STR"
    exit 1
  fi
  echo "==> Approved newsletter found for $DATE_STR — proceeding to publish."
else
  # Generate-only mode: write the draft MD (calls Claude API once).
  DEFAULT_DIGEST_DIR="$HOME/Documents/ContentRepo/07-Reading/news-digest"
  DIGEST_DIR="${DIGEST_DIR:-$DEFAULT_DIGEST_DIR}"
  DIGEST_FLAG=""
  if [[ -n "${DIGEST_DIR:-}" && -d "$DIGEST_DIR" ]]; then
    DIGEST_FLAG="--digest-dir $DIGEST_DIR"
  fi

  if [[ ! -f "$MD_PATH" ]]; then
    if [[ -f "$FIXTURE_PATH" ]]; then
      echo "==> Fixture found — generating from verified Perplexity fixture ..."
      python generate_market_day_break.py --date "$DATE_STR" --md-only $DIGEST_FLAG
    else
      echo "==> No fixture found — fetching live data ..."
      python generate_market_day_break.py --date "$DATE_STR" --live --md-only $DIGEST_FLAG
    fi
  else
    echo "==> Using existing newsletter for $DATE_STR (skipping regeneration)"
  fi

  echo ""
  echo "Newsletter ready for review:"
  echo "  $MD_PATH"

  # Optional headless polish pass
  if [[ "$POLISH" == "--polish" ]]; then
    echo ""
    echo "==> Running headless polish pass ..."
    PROMPT_FILE="$REPO_ROOT/.claude/commands/headless-daybreak-polish.md"
    if [[ ! -f "$PROMPT_FILE" ]]; then
      echo "  [WARN] Polish prompt not found at $PROMPT_FILE — skipping polish step."
    elif ! command -v claude &>/dev/null; then
      echo "  [WARN] 'claude' CLI not found in PATH — skipping polish step."
    else
      PROMPT=$(sed "s|\\\$DAYBREAK_FILE|${MD_PATH}|g" "$PROMPT_FILE")
      claude -p "$PROMPT" \
        --allowedTools Read,Edit \
        --dangerously-skip-permissions \
        --model claude-sonnet-4-6
      echo "  Polish pass complete."
    fi
  fi

  if [[ "$SEND_EMAIL" == "--send-email" ]]; then
    echo ""
    echo "==> Sending email to subscribers ..."
    python "$SCRIPT_DIR/send_email.py" --edition daybreak --date "$DATE_STR"
    exit 0
  fi

  echo ""
  echo "Review the Markdown above, then run with --publish to generate social posts and deploy:"
  echo "  bash weekly-newsletter/publish_daybreak.sh $DATE_STR --publish"
  exit 0
fi

# Phase 2 (on --publish): Generate social posts from the approved MD
echo ""
echo "==> Generating social posts from approved content ..."
python generate_market_day_break.py --date "$DATE_STR" --no-rewrite-md

echo ""
echo "==> Rebuilding site ..."
python build_combined_site.py

echo ""
echo "==> Verifying site HTML matches approved MD ..."
python verify_site_content.py "$DATE_STR" --no-pdf

echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

# Stage each output — suppress errors for files that may not exist
_add() { git add "$@" 2>/dev/null || true; }
_add "weekly-newsletter/fixtures/daybreak_${DATE_STR}.json"
_add "weekly-newsletter/output/market_day_break_${DATE_STR}.md"
_add "weekly-newsletter/output/title_${DATE_STR}.txt"
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
echo "==> Generating email preview (review before sending) ..."
python "$SCRIPT_DIR/send_email.py" --edition daybreak --date "$DATE_STR" --save-preview

if [[ "$SEND_EMAIL" != "--send-email" ]]; then
  echo ""
  echo "Open output/email_preview_${DATE_STR}.html in a browser to review the email."
  echo "When ready to send, run:"
  echo "  bash weekly-newsletter/publish_daybreak.sh $DATE_STR --send-email"
  exit 0
fi

echo ""
echo "==> Sending email to subscribers ..."
python "$SCRIPT_DIR/send_email.py" --edition daybreak --date "$DATE_STR"
