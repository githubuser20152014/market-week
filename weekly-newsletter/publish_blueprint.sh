#!/usr/bin/env bash
# publish_blueprint.sh — Build and publish a Blueprint article.
#
# Usage:
#   bash publish_blueprint.sh                              # build only (today's date)
#   bash publish_blueprint.sh 2026-03-26                  # build only (specific date)
#   bash publish_blueprint.sh 2026-03-26 --publish        # build + commit + push
#   bash publish_blueprint.sh 2026-03-26 --send-email     # send email only (no publish)
#   bash publish_blueprint.sh 2026-03-26 --publish --send-email  # full flow

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
for arg in "${FLAG_ARGS[@]+"${FLAG_ARGS[@]}"}"; do
  case "$arg" in
    --publish)    PUBLISH="--publish" ;;
    --send-email) SEND_EMAIL="--send-email" ;;
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

# Handle --send-email only (no publish)
if [[ "$SEND_EMAIL" == "--send-email" && "$PUBLISH" != "--publish" ]]; then
  echo "==> Sending Blueprint email for $DATE_STR ..."
  python "$SCRIPT_DIR/send_email.py" --edition blueprint --date "$DATE_STR"
  exit 0
fi

# Phase 1: Build web page
echo "==> Building Blueprint web page for $DATE_STR ..."
python build_blueprint_site.py --date "$DATE_STR"

# Phase 2: Generate email markdown (for preview / future send)
echo ""
echo "==> Generating email markdown ..."
python generate_blueprint.py --date "$DATE_STR"

echo ""
echo "Article page ready for review."
echo "  Open site/investing-101/ to preview locally."

if [[ "$PUBLISH" != "--publish" ]]; then
  echo ""
  echo "Review, then run with --publish to deploy:"
  echo "  bash weekly-newsletter/publish_blueprint.sh $DATE_STR --publish"
  exit 0
fi

# Phase 3: Rebuild combined site (updates main index)
echo ""
echo "==> Rebuilding combined site ..."
python build_combined_site.py

# Phase 4: Resolve slug from the article for targeted staging
SLUG=$(python -c "
import sys; sys.path.insert(0, '.')
from build_blueprint_site import parse_frontmatter, find_article_by_date
from pathlib import Path
p = find_article_by_date('$DATE_STR')
if p is None: sys.exit(1)
meta, _ = parse_frontmatter(p.read_text(encoding='utf-8'))
print(meta.get('slug', ''))
")

if [[ -z "$SLUG" ]]; then
  echo "ERROR: Could not resolve slug for date $DATE_STR" >&2
  exit 1
fi

# Phase 5: Stage and commit
echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

_add() { git add "$@" 2>/dev/null || true; }
_add "weekly-newsletter/site/investing-101/${SLUG}/"
_add "weekly-newsletter/site/index.html"

if git diff --cached --quiet; then
  echo "Nothing new to publish — site is already up to date."
  exit 0
fi

ISSUE_NUM=$(python -c "
import sys; sys.path.insert(0, 'weekly-newsletter')
from build_blueprint_site import parse_frontmatter, find_article_by_date
from pathlib import Path
p = find_article_by_date('$DATE_STR')
if p is None: sys.exit(1)
meta, _ = parse_frontmatter(p.read_text(encoding='utf-8'))
print(meta.get('issue', ''))
")

COMMIT_MSG="Publish The Blueprint"
[[ -n "$ISSUE_NUM" ]] && COMMIT_MSG="$COMMIT_MSG — Issue #${ISSUE_NUM}"
COMMIT_MSG="$COMMIT_MSG — $DATE_STR"

git commit -m "$COMMIT_MSG"
git push origin master

echo ""
echo "Done. Live at https://frameworkfoundry.info/investing-101/${SLUG}/"

# Phase 6: Email preview
echo ""
echo "==> Generating email preview ..."
python "$SCRIPT_DIR/send_email.py" --edition blueprint --date "$DATE_STR" --save-preview

if [[ "$SEND_EMAIL" != "--send-email" ]]; then
  echo ""
  echo "Open output/email_preview_${DATE_STR}.html to review the email."
  echo "When ready to send:"
  echo "  bash weekly-newsletter/publish_blueprint.sh $DATE_STR --send-email"
  exit 0
fi

echo ""
echo "==> Sending Blueprint email to subscribers ..."
python "$SCRIPT_DIR/send_email.py" --edition blueprint --date "$DATE_STR"
