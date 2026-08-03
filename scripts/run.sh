#!/usr/bin/env bash
# Run a command with robium maintainer secrets injected — from whichever source
# this machine has configured, so you don't hard-code "doppler run" everywhere:
#
#   1) Doppler   — if the CLI is set up (DOPPLER_TOKEN env, or `doppler login`)
#   2) .env      — else if a local ./.env exists (gitignored), source it
#   3) neither   — run the command as-is (fine for non-privileged / public dev)
#
# Usage:
#   ./scripts/run.sh <command> [args…]
#     e.g.  ./scripts/run.sh npm --prefix cli publish
#           ./scripts/run.sh uv run skills/skill-author/scripts/validate_skills.py
#
# Populate a .env (maintainer, if you don't use Doppler interactively):
#   doppler secrets download --no-file --format env > .env    # from Doppler, or
#   cp .env.template .env && edit in your values              # by hand
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
[ $# -gt 0 ] || { echo "usage: scripts/run.sh <command> [args…]" >&2; exit 2; }

if command -v doppler >/dev/null 2>&1 && { [ -n "${DOPPLER_TOKEN:-}" ] || doppler whoami >/dev/null 2>&1; }; then
  exec doppler run --project robium --config dev -- "$@"     # source 1: Doppler
elif [ -f .env ]; then
  set -a; . ./.env; set +a                                    # source 2: local .env
  exec "$@"
else
  exec "$@"                                                   # source 3: no secrets
fi
