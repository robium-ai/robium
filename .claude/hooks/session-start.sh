#!/usr/bin/env bash
# SessionStart hook — prepare a Claude Code on the web container so the repo's
# tests and validators run without any further setup.
#
# Mirrors the no-secrets half of scripts/bootstrap.sh (secrets stay opt-in and
# Doppler-managed; a web session never needs them). Deliberately does NOT
# install the heavy apps — see the note above the app section.
set -euo pipefail

# Web sessions only; local clones use ./scripts/bootstrap.sh.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$ROOT"

say() { printf '▸ %s\n' "$*"; }

# 1) uv — runs the skill validator (a PEP 723 script) and the app test envs.
if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
  fi
fi

# 2) Warm the validator's inline-dependency env (pyyaml) and confirm the core
#    dev loop works. Never fail the hook on a red validator — that is a code
#    finding for the session to act on, not a broken container.
say "Skill validator…"
uv run skills/skill-author/scripts/validate_skills.py || true

# 3) npm is NOT needed here: cli/ has zero dependencies and its `node --test`
#    suite runs without node_modules; installing there only litters an
#    untracked lockfile. (website/ and apps/ live in their own repos now —
#    robium-ai/robium-website and robium-ai/robium-apps.)

say "robium web session ready."
