#!/usr/bin/env bash
# Minimal server bootstrap for Horizon News.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

command -v git >/dev/null 2>&1 || {
  echo "git is required. Install git first."
  exit 1
}

command -v uv >/dev/null 2>&1 || {
  echo "uv is required. Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
}

mkdir -p logs .run

if [[ ! -f .env ]]; then
  cp .env.server.example .env
  echo "Created .env from .env.server.example. Fill model keys before the first real run."
else
  echo ".env already exists; leaving it unchanged."
fi

uv sync

echo "Bootstrap complete."
echo "Test with: ./scripts/server_run.sh --no-push"
