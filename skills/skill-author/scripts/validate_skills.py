# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Validate Robium's lightweight live-skill contract.

The validator protects discovery and obvious packaging mistakes. It does not
prescribe headings, prose, or a universal workflow; usefulness remains a human
review question.
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

ENGINE_DIR = Path(__file__).resolve().parents[3] / "scripts" / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from task_schema import TaskSchemaError, validate_tasks  # noqa: E402


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_KEYS = {"name", "description"}
MAX_DESCRIPTION_CHARS = 240
MAX_BODY_LINES = 120
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:references|scripts|examples)/[^`\s]+|[A-Z][A-Z0-9-]*\.md)`"
)
REMOTE_SCHEMES = ("http://", "https://", "mailto:")


def _without_fenced_code(text: str) -> str:
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = line.lstrip()[:3]
        if marker in {"```", "~~~"}:
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def _local_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        target = value[1:value.index(">")]
    else:
        target = value.split(maxsplit=1)[0]
    target = unquote(target)
    if not target or target.startswith("#") or target.startswith(REMOTE_SCHEMES):
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    return target


def _check_links(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    repo_root = skill_dir.parents[1].resolve()
    for source in sorted(skill_dir.rglob("*.md")):
        text = _without_fenced_code(source.read_text(encoding="utf-8"))
        targets = list(MARKDOWN_LINK_RE.findall(text))
        if source.name == "SKILL.md":
            targets.extend(BACKTICK_PATH_RE.findall(text))
        for raw in targets:
            target = _local_target(raw)
            if target is None:
                continue
            resolved = (source.parent / target).resolve()
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                errors.append(
                    f"{skill_dir.name}: {source.relative_to(skill_dir)} link escapes repository: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"{skill_dir.name}: {source.relative_to(skill_dir)} missing link target: {target}"
                )
    entrypoint = _without_fenced_code((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    linked = {
        (skill_dir / target).resolve()
        for raw in MARKDOWN_LINK_RE.findall(entrypoint) + BACKTICK_PATH_RE.findall(entrypoint)
        if (target := _local_target(raw)) is not None
    }
    for support in sorted(skill_dir.glob("*.md")):
        if support.name == "SKILL.md" or support.name.lower() == "readme.md":
            continue
        if support.resolve() not in linked:
            errors.append(
                f"{skill_dir.name}: support file {support.name} is not linked from SKILL.md"
            )
    return errors


def _check_evals(skill_dir: Path) -> list[str]:
    path = skill_dir / "evals.yaml"
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("top level must be a mapping")
        triggers = data.get("triggers", {})
        if not isinstance(triggers, dict):
            raise ValueError("'triggers' must be a mapping")
        for side in ("positive", "negative"):
            cases = triggers.get(side) or []
            if not isinstance(cases, list):
                raise ValueError(f"triggers.{side} must be a list")
            for case in cases:
                if not isinstance(case, dict) or not case.get("phrase"):
                    raise ValueError(f"each triggers.{side} case needs a 'phrase'")
                if side == "negative" and "expect" in case:
                    expected = case["expect"]
                    if not isinstance(expected, str) or not expected.strip():
                        raise ValueError("negative trigger 'expect' must be a skill name")
                    expected_dir = skill_dir.parent / expected
                    if expected == skill_dir.name or not (expected_dir / "SKILL.md").exists():
                        raise ValueError(
                            f"negative trigger 'expect' names unknown or current skill: {expected}"
                        )
        validate_tasks(
            data.get("tasks", []),
            repo_root=skill_dir.parents[1],
            skill_dir=skill_dir,
        )
    except TaskSchemaError as exc:
        return [f"{skill_dir.name}: evals.yaml invalid: {exc}"]
    except Exception as exc:
        return [f"{skill_dir.name}: evals.yaml invalid: {exc}"]
    return []


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    path = skill_dir / "SKILL.md"
    if not path.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]

    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, re.DOTALL)
    if not match:
        return [f"{skill_dir.name}: missing or malformed frontmatter"]
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return [f"{skill_dir.name}: frontmatter YAML error: {exc}"]
    if not isinstance(frontmatter, dict):
        return [f"{skill_dir.name}: frontmatter must be a mapping"]

    missing = FRONTMATTER_KEYS - set(frontmatter)
    extra = set(frontmatter) - FRONTMATTER_KEYS
    if missing:
        errors.append(f"{skill_dir.name}: frontmatter missing {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{skill_dir.name}: unsupported frontmatter fields: {', '.join(sorted(extra))}")

    name = frontmatter.get("name")
    if name != skill_dir.name:
        errors.append(f"{skill_dir.name}: frontmatter name {name!r} != directory name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append(f"{skill_dir.name}: name violates Agent Skills constraints")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_dir.name}: description missing")
    elif len(description.strip()) > MAX_DESCRIPTION_CHARS:
        errors.append(
            f"{skill_dir.name}: description {len(description.strip())} chars "
            f"(>{MAX_DESCRIPTION_CHARS})"
        )

    body = match.group(2)
    if not body.strip():
        errors.append(f"{skill_dir.name}: body is empty")
    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        errors.append(
            f"{skill_dir.name}: body {body_lines} lines (>{MAX_BODY_LINES}); move conditional depth to support files"
        )
    if re.search(r"^##\s+changelog\s*$", body, re.IGNORECASE | re.MULTILINE):
        errors.append(f"{skill_dir.name}: live skills do not carry changelogs")
    if any(path.name.lower() == "readme.md" for path in skill_dir.iterdir()):
        errors.append(f"{skill_dir.name}: use SKILL.md or a focused support file, not README.md")

    errors.extend(_check_links(skill_dir))
    errors.extend(_check_evals(skill_dir))
    return errors


def main() -> None:
    skills_root = Path(__file__).resolve().parents[2]
    skill_dirs = sorted(
        path for path in skills_root.iterdir()
        if path.is_dir() and path.name != "_TEMPLATE" and not path.name.startswith(".")
    )
    errors = [error for skill_dir in skill_dirs for error in check_skill(skill_dir)]
    for error in errors:
        print(f"FAIL: {error}")
    print(f"Checked {len(skill_dirs)} skills: {'FAIL' if errors else 'PASS'}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
