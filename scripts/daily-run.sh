#!/usr/bin/env bash
# Horizon daily collection + static HTML build + GitHub sync for Cloudflare Pages.
# Usage:
#   ./scripts/daily-run.sh
#   ./scripts/daily-run.sh --no-push

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"
REMOTE="${HORIZON_PUBLISH_REMOTE:-pages}"
BRANCH="${HORIZON_PUBLISH_BRANCH:-main}"
HOURS="${HORIZON_PUBLISH_HOURS:-24}"
PUSH=1

if [[ "${1:-}" == "--no-push" ]]; then
  PUSH=0
fi

cd "$PROJECT_DIR"

echo "$LOG_PREFIX Starting Horizon daily publish workflow..."

if ! git diff --cached --quiet; then
  echo "$LOG_PREFIX Git index already has staged changes. Commit, unstage, or review them before publishing."
  exit 1
fi

echo "$LOG_PREFIX Installing/updating dependencies..."
uv sync --quiet

echo "$LOG_PREFIX Collecting news for the last ${HOURS} hours..."
uv run horizon --hours "$HOURS"

echo "$LOG_PREFIX Building static HTML..."
uv run python scripts/build_static_pages.py

echo "$LOG_PREFIX Staging public artifacts..."
git add docs/index.html docs/daily docs/data docs/_posts

if git diff --cached --quiet; then
  echo "$LOG_PREFIX No public artifact changes to commit."
  exit 0
fi

DATE="$(date '+%Y-%m-%d')"
git commit -m "Daily HTML summary: ${DATE}"

if [[ "$PUSH" -eq 1 ]]; then
  echo "$LOG_PREFIX Pushing to ${REMOTE}/${BRANCH}..."
  git push "$REMOTE" "HEAD:${BRANCH}"
else
  echo "$LOG_PREFIX --no-push set; commit created locally only."
fi

echo "$LOG_PREFIX Done."
