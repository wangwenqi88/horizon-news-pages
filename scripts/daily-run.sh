#!/usr/bin/env bash
# Backward-compatible entrypoint. The standard server runner lives in server_run.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/server_run.sh" "$@"
