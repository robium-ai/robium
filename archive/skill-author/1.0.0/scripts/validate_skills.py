# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Validate every skill in skills/ against the robium quality bar.

Checks (per spec section 6): name==dirname, name charset/length, description
present and <=1024 chars, version present in major.minor.build form, body
<500 lines, required sections present, referenced local files exist.
_TEMPLATE is excluded (skeleton, not a skill).
"""
import re
import sys
from pathlib import Path

import yaml

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_SECTIONS = [
    "## when to use this skill",
    "## key directives",
    "## quick start",
    "## platform gotchas",
    "## customization",
    "## references",
]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LOCAL_REF_RE = re.compile(r"`((?:references|scripts|examples)/[^`\s]+)`")


def check_skill(skill_dir: Path) -> list[str]:
    errs: list[str] = []
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return [f"{skill_dir.name}: missing or malformed frontmatter"]
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        return [f"{skill_dir.name}: frontmatter YAML error: {exc}"]
    body = m.group(2)

    name = fm.get("name", "")
    desc = (fm.get("description") or "").strip()
    if name != skill_dir.name:
        errs.append(f"{skill_dir.name}: frontmatter name {name!r} != directory name")
    if not NAME_RE.match(name or "") or len(name) > 64:
        errs.append(f"{skill_dir.name}: name violates agentskills.io constraints")
    if not desc:
        errs.append(f"{skill_dir.name}: description missing")
    elif len(desc) > 1024:
        errs.append(f"{skill_dir.name}: description {len(desc)} chars (>1024)")
    version = str(fm.get("version") or "")
    if not VERSION_RE.match(version):
        errs.append(
            f"{skill_dir.name}: version {version!r} missing or not major.minor.build"
        )

    n_lines = body.count("\n") + 1
    if n_lines >= 500:
        errs.append(f"{skill_dir.name}: body {n_lines} lines (must be <500)")

    lower = body.lower()
    for section in REQUIRED_SECTIONS:
        if section not in lower:
            errs.append(f"{skill_dir.name}: missing required section '{section}'")

    for ref in LOCAL_REF_RE.findall(body):
        if not (skill_dir / ref).exists():
            errs.append(f"{skill_dir.name}: referenced file missing: {ref}")
    return errs


def main() -> None:
    skills_root = Path(__file__).resolve().parents[2]
    skill_dirs = sorted(
        p for p in skills_root.iterdir() if p.is_dir() and p.name != "_TEMPLATE"
    )
    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(check_skill(skill_dir))
    for err in errors:
        print(f"FAIL: {err}")
    print(f"Checked {len(skill_dirs)} skills: {'FAIL' if errors else 'PASS'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
