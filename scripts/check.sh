#!/usr/bin/env bash
# One local confidence check for skill, CLI, and package metadata changes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

printf '\n▸ Skills\n'
uv run skills/skill-author/scripts/validate_skills.py

printf '\n▸ CLI\n'
(cd cli && npm test)

printf '\n▸ Plugin manifests\n'
python3 -c '
import json
from pathlib import Path

paths = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".agents/plugins/marketplace.json"),
    Path("gemini-extension.json"),
    Path("hooks/hooks.json"),
]
documents = {str(path): json.loads(path.read_text()) for path in paths}
versions = {
    documents[".claude-plugin/plugin.json"]["version"],
    documents[".claude-plugin/marketplace.json"]["metadata"]["version"],
    documents[".codex-plugin/plugin.json"]["version"],
    documents["gemini-extension.json"]["version"],
    json.loads(Path("cli/package.json").read_text())["robiumPluginVersion"],
}
if len(versions) != 1:
    raise SystemExit(f"plugin version mismatch: {sorted(versions)}")
print(f"Validated {len(paths)} manifests; plugin version {versions.pop()}")
'

printf '\nAll checks passed.\n'
