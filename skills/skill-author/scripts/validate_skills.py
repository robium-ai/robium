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

ANCHOR_RE = re.compile(r"<!-- id: ([a-z0-9][a-z0-9-]*) -->")
ANCHOR_ANY_RE = re.compile(r"(?i)<!--\s*id\s*:")


def check_anchors(name: str, text: str) -> tuple[list[str], set[str]]:
    errs: list[str] = []
    anchors = ANCHOR_RE.findall(text)
    if len(ANCHOR_ANY_RE.findall(text)) != len(anchors):
        errs.append(f"{name}: malformed anchor comment (must be '<!-- id: kebab-case -->')")
    seen: set[str] = set()
    for a in anchors:
        if a in seen:
            errs.append(f"{name}: duplicate anchor id '{a}'")
        seen.add(a)
    return errs, seen


def check_sidecars(skill_dir: Path, anchors: set[str]) -> list[str]:
    errs: list[str] = []
    name = skill_dir.name

    ev_path = skill_dir / "evidence.yaml"
    if ev_path.exists():
        try:
            data = yaml.safe_load(ev_path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError("top level must be a mapping of anchor -> entry")
            for key, entry in data.items():
                if key not in anchors:
                    errs.append(f"{name}: evidence.yaml unknown anchor '{key}'")
                if not isinstance(entry, dict):
                    raise ValueError(f"entry '{key}' must be a mapping")
                for fld in ("helpful", "harmful"):
                    if not isinstance(entry.get(fld, 0), int) or entry.get(fld, 0) < 0:
                        raise ValueError(f"entry '{key}.{fld}' must be a non-negative int")
                if not isinstance(entry.get("sources", []), list):
                    raise ValueError(f"entry '{key}.sources' must be a list")
        except Exception as exc:
            errs.append(f"{name}: evidence.yaml invalid: {exc}")

    evals_path = skill_dir / "evals.yaml"
    if evals_path.exists():
        try:
            data = yaml.safe_load(evals_path.read_text(encoding="utf-8")) or {}
            trig = data.get("triggers", {})
            if not isinstance(trig, dict):
                raise ValueError("'triggers' must be a mapping")
            for side in ("positive", "negative"):
                for case in trig.get(side) or []:
                    if not isinstance(case, dict) or not case.get("phrase"):
                        raise ValueError(f"each triggers.{side} case needs a 'phrase'")
            tasks = data.get("tasks", [])
            if not isinstance(tasks, list):
                raise ValueError("'tasks' must be a list")
            seen_task_names: set[str] = set()
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    raise ValueError(f"tasks[{i}] must be a mapping")
                for field in ("name", "command", "pass_criteria"):
                    val = task.get(field)
                    if not isinstance(val, str) or not val.strip():
                        raise ValueError(f"tasks[{i}] missing required '{field}'")
                try:
                    re.compile(task["pass_criteria"])
                except re.error as exc:
                    raise ValueError(
                        f"tasks[{i}] pass_criteria is not a valid regex: {exc}"
                    )
                task_name = task["name"]
                if not NAME_RE.match(task_name):
                    raise ValueError(
                        f"tasks[{i}] name '{task_name}' is not kebab-case"
                    )
                if task_name in seen_task_names:
                    raise ValueError(
                        f"tasks[{i}] duplicate task name '{task_name}'"
                    )
                seen_task_names.add(task_name)
                if "timeout" in task and not isinstance(task["timeout"], int):
                    raise ValueError(f"tasks[{i}].timeout must be an int")
        except Exception as exc:
            errs.append(f"{name}: evals.yaml invalid: {exc}")

    return errs


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

    anchor_errs, anchors = check_anchors(skill_dir.name, body)
    errs.extend(anchor_errs)
    for ref_file in skill_dir.glob("references/*.md"):
        ref_errs, ref_anchors = check_anchors(f"{skill_dir.name}/{ref_file.name}",
                                              ref_file.read_text(encoding="utf-8"))
        errs.extend(ref_errs)
        dup = anchors & ref_anchors
        for a in dup:
            errs.append(f"{skill_dir.name}: anchor '{a}' duplicated in {ref_file.name}")
        anchors |= ref_anchors
    errs.extend(check_sidecars(skill_dir, anchors))
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
