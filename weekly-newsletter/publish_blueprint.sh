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

CONTENT_REPO="C:/Users/Akhil/Documents/ContentRepo"
ISSUES_DIR="$CONTENT_REPO/wednesday-series/Issues"

# Resolve slug + issue number from ContentRepo article for this date
SLUG=$(python -c "
import sys
from pathlib import Path
issues = Path('$ISSUES_DIR')
for f in issues.glob('*.md'):
    text = f.read_text(encoding='utf-8')
    if not text.startswith('---'): continue
    end = text.find('\n---', 3)
    if end == -1: continue
    for line in text[3:end].splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            if k.strip() == 'date' and v.strip().strip('\"') == '$DATE_STR':
                for l2 in text[3:end].splitlines():
                    if ':' in l2:
                        k2, _, v2 = l2.partition(':')
                        if k2.strip() == 'slug':
                            print(v2.strip().strip('\"'))
                            sys.exit(0)
print(''); sys.exit(1)
")

if [[ -z "$SLUG" ]]; then
  echo "ERROR: No Blueprint article found for date $DATE_STR in $ISSUES_DIR" >&2
  exit 1
fi

ISSUE_NUM=$(python -c "
import sys
from pathlib import Path
issues = Path('$ISSUES_DIR')
for f in issues.glob('*.md'):
    text = f.read_text(encoding='utf-8')
    if not text.startswith('---'): continue
    end = text.find('\n---', 3)
    if end == -1: continue
    for line in text[3:end].splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            if k.strip() == 'date' and v.strip().strip('\"') == '$DATE_STR':
                for l2 in text[3:end].splitlines():
                    if ':' in l2:
                        k2, _, v2 = l2.partition(':')
                        if k2.strip() == 'issue':
                            print(v2.strip().strip('\"'))
                            sys.exit(0)
print(''); sys.exit(0)
")

# Handle --send-email only (no publish)
if [[ "$SEND_EMAIL" == "--send-email" && "$PUBLISH" != "--publish" ]]; then
  echo "==> Sending Blueprint email for $DATE_STR ..."
  python "$SCRIPT_DIR/send_email.py" --edition blueprint --date "$DATE_STR"
  exit 0
fi

# Phase 1: Sync article from ContentRepo → content/articles/
echo "==> Syncing article from ContentRepo ..."
ARTICLE_SRC=$(find "$ISSUES_DIR" -name "*.md" -exec grep -l "date: $DATE_STR" {} \; | head -1)
if [[ -z "$ARTICLE_SRC" ]]; then
  echo "ERROR: No article file found for date $DATE_STR" >&2
  exit 1
fi
cp "$ARTICLE_SRC" "$SCRIPT_DIR/content/articles/investing-101-${SLUG}.md"
echo "  $ARTICLE_SRC -> content/articles/investing-101-${SLUG}.md"

# Phase 2: Generate email markdown
echo ""
echo "==> Generating email markdown ..."
python generate_blueprint.py --date "$DATE_STR"

echo ""
echo "Article ready for review. Run with --publish to deploy:"
echo "  bash weekly-newsletter/publish_blueprint.sh $DATE_STR --publish"

if [[ "$PUBLISH" != "--publish" ]]; then
  exit 0
fi

# Phase 3: Rebuild combined site (generates article page + updates main index)
echo ""
echo "==> Rebuilding combined site ..."
python build_combined_site.py

# Phase 4: Stage and commit
echo ""
echo "==> Staging changes ..."
cd "$REPO_ROOT"

_add() { git add "$@" 2>/dev/null || true; }
_add "weekly-newsletter/content/articles/investing-101-${SLUG}.md"
_add "weekly-newsletter/site/investing-101/${SLUG}/"
_add "weekly-newsletter/site/index.html"

if git diff --cached --quiet; then
  echo "Nothing new to publish — site is already up to date."
  exit 0
fi

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
