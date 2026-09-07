"""Shared validation for evals.yaml task-check fixtures."""

import os
import re
from pathlib import Path


TASK_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TaskSchemaError(ValueError):
    """Raised when an evals.yaml tasks list cannot be executed safely."""


def _relative_path(value, field, index):
    if not isinstance(value, str) or not value.strip():
        raise TaskSchemaError(f"tasks[{index}].{field} must be a non-empty string")
    normalized = os.path.normpath(value)
    if os.path.isabs(value) or normalized == ".." or normalized.startswith(f"..{os.sep}"):
        scope = "repo-root-relative" if field == "app" else "skill-relative"
        raise TaskSchemaError(f"tasks[{index}].{field} must be {scope} without '..'")


def _contained_path(value, base, field, index, *, must_be_dir):
    base = Path(base).resolve()
    resolved = (base / value).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise TaskSchemaError(f"tasks[{index}].{field} escapes its allowed root") from exc
    if not resolved.exists():
        raise TaskSchemaError(f"tasks[{index}].{field} does not exist: {value}")
    if must_be_dir and not resolved.is_dir():
        raise TaskSchemaError(f"tasks[{index}].{field} must name a directory")
    if not must_be_dir and not resolved.is_file():
        raise TaskSchemaError(f"tasks[{index}].{field} must name a file")
    return resolved


def validate_tasks(tasks, *, repo_root=None, skill_dir=None):
    """Validate and return a task list using the runner's canonical schema."""
    if not isinstance(tasks, list):
        raise TaskSchemaError("tasks must be a list")

    seen = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise TaskSchemaError(f"tasks[{index}] must be a mapping")
        for field in ("name", "command", "pass_criteria"):
            value = task.get(field)
            if not isinstance(value, str) or not value.strip():
                raise TaskSchemaError(f"tasks[{index}] missing required '{field}'")

        name = task["name"]
        if not TASK_NAME_RE.fullmatch(name):
            raise TaskSchemaError(f"tasks[{index}] name '{name}' is not kebab-case")
        if name in seen:
            raise TaskSchemaError(f"tasks[{index}] duplicate task name '{name}'")
        seen.add(name)

        try:
            re.compile(task["pass_criteria"])
        except re.error as exc:
            raise TaskSchemaError(
                f"tasks[{index}] pass_criteria is not a valid regex: {exc}"
            ) from exc

        if "timeout" in task:
            timeout = task["timeout"]
            if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
                raise TaskSchemaError(f"tasks[{index}].timeout must be a positive integer")
        if "app" in task:
            _relative_path(task["app"], "app", index)
            if repo_root is not None:
                resolved = _contained_path(
                    task["app"], repo_root, "app", index, must_be_dir=True
                )
                skills_root = (Path(repo_root).resolve() / "skills").resolve()
                try:
                    resolved.relative_to(skills_root)
                except ValueError:
                    pass
                else:
                    raise TaskSchemaError(
                        f"tasks[{index}].app cannot run inside the skills tree"
                    )
        if "example" in task:
            _relative_path(task["example"], "example", index)
            if skill_dir is not None:
                _contained_path(
                    task["example"], skill_dir, "example", index, must_be_dir=False
                )

    return tasks
