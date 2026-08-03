#!/usr/bin/env python3
"""Verify .agents/skills/ mirrors skills/ exactly (committed symlink farm).

The farm gives Codex / Gemini CLI / Cursor / OpenCode / Antigravity automatic
workspace-scope discovery of every robium skill for anyone working inside the
clone. Drift (missing, extra, broken, or non-relative links) fails the check.
Run alongside the skill validator; deliberately lives outside skills/ (that
tree is policy-gated).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
FARM = os.path.join(ROOT, ".agents", "skills")


def main() -> int:
    expected = sorted(
        e for e in os.listdir(SKILLS)
        if os.path.isdir(os.path.join(SKILLS, e))
        and not e.startswith(("_", "."))
        and os.path.isfile(os.path.join(SKILLS, e, "SKILL.md"))
    )
    if not os.path.isdir(FARM):
        print(f"FAIL: {FARM} missing — create the symlink farm")
        return 1

    actual = sorted(e for e in os.listdir(FARM) if not e.startswith("."))
    errors = []
    for name in expected:
        link = os.path.join(FARM, name)
        if name not in actual:
            errors.append(f"missing link: .agents/skills/{name}")
            continue
        if not os.path.islink(link):
            errors.append(f"not a symlink: .agents/skills/{name}")
            continue
        target = os.readlink(link)
        if os.path.isabs(target):
            errors.append(f"absolute link (must be relative): .agents/skills/{name} -> {target}")
        if not os.path.isfile(os.path.join(link, "SKILL.md")):
            errors.append(f"broken link: .agents/skills/{name} -> {target}")
    for name in actual:
        if name not in expected:
            errors.append(f"extra entry (no matching skill): .agents/skills/{name}")

    if errors:
        print("\n".join(f"FAIL: {e}" for e in errors))
        return 1
    print(f"Checked farm: {len(expected)} links match skills/ — PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
