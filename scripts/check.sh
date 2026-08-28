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
    Path(".cursor-plugin/plugin.json"),
    Path(".agents/plugins/marketplace.json"),
    Path("gemini-extension.json"),
    Path("hooks/hooks.json"),
    Path("hooks/cursor-hooks.json"),
]
documents = {str(path): json.loads(path.read_text()) for path in paths}
versions = {
    documents[".claude-plugin/plugin.json"]["version"],
    documents[".claude-plugin/marketplace.json"]["metadata"]["version"],
    documents[".codex-plugin/plugin.json"]["version"],
    documents[".cursor-plugin/plugin.json"]["version"],
    documents["gemini-extension.json"]["version"],
    json.loads(Path("cli/package.json").read_text())["robiumPluginVersion"],
}
if len(versions) != 1:
    raise SystemExit(f"plugin version mismatch: {sorted(versions)}")
hooks = documents["hooks/hooks.json"]["hooks"]
for event in ("BeforeAgent", "AfterTool", "SessionStart", "SessionEnd"):
    if event not in hooks:
        raise SystemExit(f"Gemini hook event missing: {event}")
gemini_commands = [
    hook["command"]
    for event in hooks.values()
    for definition in event
    for hook in definition["hooks"]
    if hook.get("name", "").startswith(("robium-gemini", "robium-capture"))
]
if len(gemini_commands) != 4 or any(
    "${extensionPath}" not in command or "${/}" not in command
    for command in gemini_commands
):
    raise SystemExit("Gemini hook commands must use portable extension variables")
cursor_manifest = documents[".cursor-plugin/plugin.json"]
if cursor_manifest.get("skills") != "./skills/" or cursor_manifest.get("agents") != "./agents/robium-architect.md":
    raise SystemExit("Cursor manifest must package the skill catalog and architect agent")
if cursor_manifest.get("hooks") != "./hooks/cursor-hooks.json":
    raise SystemExit("Cursor manifest must select the dedicated Cursor hook schema")
cursor_hooks = documents["hooks/cursor-hooks.json"]
if cursor_hooks.get("version") != 1 or set(cursor_hooks.get("hooks", {})) != {
    "beforeSubmitPrompt", "afterShellExecution", "sessionStart", "sessionEnd"
}:
    raise SystemExit("Cursor hook config is incomplete or uses the wrong schema version")
if any(
    "cursor_hook.mjs" not in definition.get("command", "")
    for definitions in cursor_hooks["hooks"].values()
    for definition in definitions
):
    raise SystemExit("Cursor hook events must use the Cursor payload adapter")
agent = Path("agents/robium-architect.md").read_text()
if "name: robium-architect" not in agent or "tools: Read" in agent:
    raise SystemExit("Gemini architect agent is missing or uses host-specific tools")
print(f"Validated {len(paths)} manifests; plugin version {versions.pop()}")
'

printf '\nAll checks passed.\n'
