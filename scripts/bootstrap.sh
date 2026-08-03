#!/usr/bin/env bash
# robium dev bootstrap — run from a clone:  ./scripts/bootstrap.sh
#
# DEFAULT (anyone, incl. public contributors — NO secrets, NO Doppler needed):
#   installs uv + npm deps and runs the skill validator. That's all you need to
#   author skills and work on the CLI locally.
#     ./scripts/bootstrap.sh
#
# MAINTAINER / OPERATOR (adds Doppler-managed secrets — only for publishing the
# CLI, deploying the site, RunPod/NGC/GCP work):
#     ./scripts/bootstrap.sh --secrets          # laptop (after `doppler login`)
#     DOPPLER_TOKEN=dp.st.dev.… ./scripts/bootstrap.sh   # server (auto-enables)
set -euo pipefail
say() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }

# run from the repo (the script lives in scripts/, so root is one level up)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -f skills/skill-author/scripts/validate_skills.py ] || {
  echo "Run this from a robium clone (./scripts/bootstrap.sh)." >&2; exit 1; }

# secrets are OPT-IN: --secrets flag, or DOPPLER_TOKEN present (server case)
WITH_SECRETS=0
[ "${1:-}" = "--secrets" ] && WITH_SECRETS=1
[ -n "${DOPPLER_TOKEN:-}" ] && WITH_SECRETS=1

# 1) Toolchain + deps (no secrets involved) ----------------------------------
command -v uv >/dev/null 2>&1 || { say "Installing uv…"; curl -LsSf https://astral.sh/uv/install.sh | sh; }
if command -v npm >/dev/null 2>&1; then
  [ -d cli ]     && { say "npm deps: cli/";     (cd cli && npm ci --silent 2>/dev/null || npm install --silent); }
fi

# 2) Sanity check the core dev loop works (no secrets) -----------------------
if command -v uv >/dev/null 2>&1; then
  say "Validating skills…"; uv run skills/skill-author/scripts/validate_skills.py || true
fi
say "Checking .agents/skills farm…"; python3 scripts/check_agents_farm.py || true

# 3) Secrets (maintainer-only, opt-in) ---------------------------------------
if [ "$WITH_SECRETS" = "1" ]; then
  say "Secrets: setting up Doppler…"
  if ! command -v doppler >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then brew install dopplerhq/cli/doppler
    else curl -Ls https://cli.doppler.com/install.sh | sh; fi
  fi
  if [ -z "${DOPPLER_TOKEN:-}" ] && ! doppler whoami >/dev/null 2>&1; then
    echo "  Need Doppler auth: run 'doppler login' or set DOPPLER_TOKEN, then re-run with --secrets." >&2
  else
    [ -z "${DOPPLER_TOKEN:-}" ] && doppler setup --no-interactive -p robium -c dev >/dev/null
    if doppler run --project robium --config dev -- sh -c 'test -n "${NPM_TOKEN:-}"' >/dev/null 2>&1; then
      say "Doppler secrets reachable ✓  — run privileged tasks with: doppler run -- <cmd>"
    else
      echo "  Could not read secrets — check DOPPLER_TOKEN / login." >&2
    fi
  fi
else
  say "Secrets skipped (maintainer-only: CLI publish, site deploy, RunPod/NGC/GCP)."
  echo "  Need them? re-run:  ./scripts/bootstrap.sh --secrets   (see docs/secrets.md)"
fi

cat <<DONE

▸ robium ready.
  Contribute (no secrets):  uv run skills/skill-author/scripts/validate_skills.py
  Privileged tasks:         doppler run -- <command>   (after --secrets setup)
DONE
