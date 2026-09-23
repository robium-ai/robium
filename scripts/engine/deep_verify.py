#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Deep-verify lane — fixture-run unverified examples and report suggestions.

A `status: unverified` marker (spec §8 layer 4: examples/references content
shipped with an upstream-source link until a trial run verifies it) can be
promoted mechanically when the skill's evals.yaml carries a `tasks:`
fixture whose `example:` field names the file (skill-relative path, e.g.
`examples/load-dataset-snippet.py`). This module is the scheduled lane
that does that: `inventory` finds every unverified file and says whether
it has a fixture; `run_for_skill` actually runs the fixture (via
`run_task_checks.run_task` — no subprocess handling is reimplemented here)
and, on PASS, suggests the exact marker replacement.

This module never writes to `skills/**`. Review passing evidence and apply the
suggested status change with the normal repository editor. `--out` optionally
writes the same suggestions as YAML; there is no delta-application pipeline.

Scheduled-lane semantics: this is a periodic sweep, not a per-PR gate — a
failing example is a *finding* to report and fix later, not a fatal error.
The CLI always exits 0; failures show up in the printed report and in the
`failed` list, never as a nonzero exit or a raised exception.
"""
import argparse
import datetime
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_task_checks  # noqa: E402

_STATUS_UNVERIFIED = "status: unverified"
_ARTIFACT_DIRS = ("examples", "references")


class UnknownSkillError(ValueError):
    """Raised when deep verification names a skill outside the catalog."""


def _require_skill(skill, skills_dir):
    skill_dir = os.path.join(skills_dir, skill)
    if not os.path.isdir(skill_dir):
        available = ", ".join(_list_skills(skills_dir)) or "none"
        raise UnknownSkillError(
            f"unknown skill '{skill}' in {skills_dir} (available: {available})"
        )
    return skill_dir


def _list_skills(skills_dir):
    if not os.path.isdir(skills_dir):
        return []
    return sorted(
        name for name in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, name))
    )


def _unverified_files(skill_dir):
    """Skill-relative paths (sorted) of every file under examples/ or
    references/ containing the literal marker `status: unverified`."""
    found = []
    for sub in _ARTIFACT_DIRS:
        base = os.path.join(skill_dir, sub)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fname in files:
                path = os.path.join(root, fname)
                try:
                    text = open(path, encoding="utf-8").read()
                except (UnicodeDecodeError, OSError):
                    continue
                if _STATUS_UNVERIFIED in text:
                    found.append(os.path.relpath(path, skill_dir))
    return sorted(found)


def _fixture_map(skill, skills_dir):
    """example-relpath -> task dict, for every evals.yaml task carrying a
    non-empty `example:` field. Last task wins on a duplicate example
    (not expected in practice; the validator doesn't currently forbid
    it, so this stays a deterministic, not a raising, choice)."""
    tasks = run_task_checks.load_tasks(skill, skills_dir)
    return {t["example"]: t for t in tasks if t.get("example")}


def inventory(skills_dir):
    """Every unverified example/reference file across all skills under
    skills_dir. Each item: {"skill", "file", "fixture": task-name|None}."""
    items = []
    for skill in _list_skills(skills_dir):
        skill_dir = os.path.join(skills_dir, skill)
        fixtures = _fixture_map(skill, skills_dir)
        for rel in _unverified_files(skill_dir):
            task = fixtures.get(rel)
            items.append({
                "skill": skill,
                "file": rel,
                "fixture": task["name"] if task else None,
            })
    return items


def run_for_skill(skill, skills_dir, repo_root, date):
    """Run every unverified example's fixture (if it has one) for one
    skill. Returns {"suggestions", "passed", "failed", "unfixtured"}:

    - suggestions: exact status replacements for examples whose fixture passed.
    - passed: [{"skill", "file", "task"}] — mirrors suggestions 1:1.
    - failed: [{"skill", "file", "task", "tail"}] — no suggestion emitted.
    - unfixtured: [{"skill", "file"}] — no evals.yaml task's `example:`
      matches this file.
    """
    skill_dir = _require_skill(skill, skills_dir)
    fixtures = _fixture_map(skill, skills_dir)
    suggestions, passed, failed, unfixtured = [], [], [], []

    for rel in _unverified_files(skill_dir):
        task = fixtures.get(rel)
        if task is None:
            unfixtured.append({"skill": skill, "file": rel})
            continue

        task_name = task["name"]
        res = run_task_checks.run_task(task, repo_root)
        if res["pass"] is True:
            replace = f"status: verified {date} (deep-verify: {task_name})"
            suggestions.append({
                "skill": skill,
                "file": rel,
                "find": _STATUS_UNVERIFIED,
                "replace": replace,
                "task": task_name,
            })
            passed.append({"skill": skill, "file": rel, "task": task_name})
        else:
            failed.append({
                "skill": skill, "file": rel, "task": task_name,
                "tail": res["tail"],
            })

    return {"suggestions": suggestions, "passed": passed, "failed": failed,
            "unfixtured": unfixtured}


def _print_inventory(skills_dir):
    items = inventory(skills_dir)
    print("| skill | file | fixture |")
    print("|---|---|---|")
    unfixtured = 0
    for item in items:
        if item["fixture"] is None:
            unfixtured += 1
        print(f"| {item['skill']} | {item['file']} | {item['fixture'] or '—'} |")
    print(f"\nunfixtured: {unfixtured} (of {len(items)} unverified files — no silent caps)")


def _print_run_report(agg):
    print("| skill | file | task | result |")
    print("|---|---|---|---|")
    for p in agg["passed"]:
        print(f"| {p['skill']} | {p['file']} | {p['task']} | PASS |")
    for f in agg["failed"]:
        print(f"| {f['skill']} | {f['file']} | {f['task']} | FAIL — {f['tail']} |")
    for u in agg["unfixtured"]:
        print(f"| {u['skill']} | {u['file']} | — | unfixtured |")
    print(f"\ndeep-verify: {len(agg['passed'])} passed, {len(agg['failed'])} failed, "
          f"{len(agg['unfixtured'])} unfixtured")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true",
                    help="list every unverified example/reference and its fixture status")
    ap.add_argument("--run", action="store_true",
                    help="run fixtures for --skills and report review suggestions")
    ap.add_argument("--skills", nargs="+", default=None)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default=None,
                    help="optional YAML path for review suggestions")
    args = ap.parse_args(argv)

    if args.inventory:
        _print_inventory(args.skills_dir)
        return 0

    if args.run:
        if not args.skills:
            ap.error("--run requires --skills <names...>")
        date = args.date or datetime.date.today().isoformat()

        try:
            for skill in args.skills:
                _require_skill(skill, args.skills_dir)
                run_task_checks.load_tasks(skill, args.skills_dir)
        except (UnknownSkillError, run_task_checks.TaskSchemaError) as exc:
            print(f"deep-verify: error: {exc}", file=sys.stderr)
            return 2

        agg = {"suggestions": [], "passed": [], "failed": [], "unfixtured": []}
        for skill in args.skills:
            res = run_for_skill(skill, args.skills_dir, args.repo_root, date)
            for key in agg:
                agg[key].extend(res[key])

        _print_run_report(agg)

        if args.out:
            out_dir = os.path.dirname(args.out)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    {"date": date, "suggestions": agg["suggestions"]},
                    f,
                    sort_keys=False,
                )
            print(f"\nwrote review suggestions: {args.out} "
                  f"({len(agg['suggestions'])} suggestion(s)) — never applied")

        # Scheduled-lane semantics: a failing example is a finding for the
        # report above, not a fatal error for the CLI invocation itself.
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
