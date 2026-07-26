#!/usr/bin/env bash
# Standard server entrypoint for Horizon News.
# Runs: collect -> static HTML build -> commit public docs -> push for Cloudflare Pages.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
RUN_DIR="${PROJECT_DIR}/.run"
LOCK_DIR="${RUN_DIR}/horizon-news.lock"
DATE_STAMP="$(date '+%Y-%m-%d')"
TIME_STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_FILE="${LOG_DIR}/horizon-${DATE_STAMP}.log"

mkdir -p "${LOG_DIR}" "${RUN_DIR}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

fail() {
  log "FAILED: $*"
  exit 1
}

cleanup() {
  rmdir "${LOCK_DIR}" 2>/dev/null || true
}

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  fail "Another Horizon News run is already active. Lock: ${LOCK_DIR}"
fi
trap cleanup EXIT

exec > >(tee -a "${LOG_FILE}") 2>&1

cd "${PROJECT_DIR}"

log "Starting Horizon News server run at ${TIME_STAMP}"
log "Project: ${PROJECT_DIR}"
log "Log: ${LOG_FILE}"

if [[ -f "${PROJECT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env"
  set +a
  log "Loaded environment from .env"
else
  log "No .env found; using process environment only"
fi

export UV_CACHE_DIR="${UV_CACHE_DIR:-${PROJECT_DIR}/.uv-cache}"

HOURS="${HORIZON_PUBLISH_HOURS:-24}"
EXTRA_ARGS=("--hours" "${HOURS}")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hours)
      shift
      [[ $# -gt 0 ]] || fail "--hours requires a value"
      HOURS="$1"
      EXTRA_ARGS=("--hours" "${HOURS}")
      ;;
    --no-push|--skip-collect|--skip-build)
      EXTRA_ARGS+=("$1")
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
  shift
done

command -v git >/dev/null 2>&1 || fail "git is not installed or not in PATH"
command -v uv >/dev/null 2>&1 || fail "uv is not installed or not in PATH"

if [[ "${HORIZON_AUTO_PULL:-0}" == "1" ]]; then
  log "Pulling latest code with git pull --ff-only"
  git pull --ff-only
fi

if [[ "${HORIZON_UV_SYNC:-1}" == "1" ]]; then
  log "Syncing Python dependencies with uv"
  uv sync --quiet
fi

log "Running publish workflow for the last ${HOURS} hours"
uv run python scripts/publish_daily.py "${EXTRA_ARGS[@]}"

log "Horizon News server run complete"
