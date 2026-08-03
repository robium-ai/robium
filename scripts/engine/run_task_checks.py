#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Task-check runner: executes evals.yaml `tasks:` fixtures (spec §4.3).

Each task is a shell command run with an explicit timeout, cwd scoped to
the named app directory (repo-root-relative) or the repo root — NEVER
inside skills/. PASS requires exit 0 AND a regex match against the
combined stdout+stderr. Never run as root; never alters state outside its
own cwd; a timeout aborts the subprocess rather than hanging the run.

`run_task` is the reusable primitive: the deep-verify lane (Task 5) will
import it directly to score fixture-verified examples without going
through this module's CLI.
"""
import argparse
import os
import re
import subprocess
import sys
import time

import yaml

DEFAULT_TIMEOUT_S = 300
TAIL_MAX_LINES = 5
TAIL_MAX_CHARS = 400


def load_tasks(skill, skills_dir):
    path = os.path.join(skills_dir, skill, "evals.yaml")
    if not os.path.exists(path):
        return []
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    return list(data.get("tasks") or [])


def _tail(text):
    text = (text or "").strip()
    lines = text.splitlines()[-TAIL_MAX_LINES:]
    tail = "\n".join(lines)
    if len(tail) > TAIL_MAX_CHARS:
        tail = tail[-TAIL_MAX_CHARS:]
    return tail


def run_task(task, repo_root, dry_run=False):
    name = task["name"]
    command = task["command"]
    pass_criteria = task["pass_criteria"]
    app = task.get("app")
    timeout = task.get("timeout", DEFAULT_TIMEOUT_S)
    cwd = os.path.join(repo_root, app) if app else repo_root

    if dry_run:
        print(f"[dry-run] {name}: {command} (cwd={cwd})")
        return {"name": name, "pass": None, "exit": None, "matched": False,
                "seconds": 0.0, "tail": "dry-run: not executed"}

    start = time.time()
    try:
        proc = subprocess.run(command, shell=True, cwd=cwd,
                               capture_output=True, text=True, timeout=timeout)
        seconds = time.time() - start
        combined = (proc.stdout or "") + (proc.stderr or "")
        matched = re.search(pass_criteria, combined) is not None
        ok = proc.returncode == 0 and matched
        return {"name": name, "pass": ok, "exit": proc.returncode,
                "matched": matched, "seconds": seconds, "tail": _tail(combined)}
    except subprocess.TimeoutExpired as exc:
        seconds = time.time() - start
        combined = (exc.stdout or "") + (exc.stderr or "")
        note = f"TIMEOUT after {timeout}s"
        if combined.strip():
            note += f" — {_tail(combined)}"
        return {"name": name, "pass": False, "exit": None, "matched": False,
                "seconds": seconds, "tail": note}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", nargs="+", required=True)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--task", default=None, help="run only this task name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)

    passed = failed = skipped = 0
    for skill in args.skills:
        all_tasks = load_tasks(skill, args.skills_dir)
        tasks = all_tasks
        if args.task:
            tasks = [t for t in all_tasks if t.get("name") == args.task]
            if not tasks and all_tasks:
                # The skill HAS tasks but none match --task: a CI-invocation
                # typo, not an honest skip. Fail loudly instead of falling
                # into the "no tasks at all" skip message below.
                failed += 1
                have = ", ".join(t.get("name", "?") for t in all_tasks)
                print(f"{skill}: no task named '{args.task}' (has: {have})")
                continue
        if not tasks:
            skipped += 1
            print(f"{skill}: SKIPPED (no tasks yet — say so in the PR)")
            continue
        for task in tasks:
            res = run_task(task, args.repo_root, dry_run=args.dry_run)
            if res["pass"] is True:
                status = "PASS"
                passed += 1
            elif res["pass"] is False:
                status = "FAIL"
                failed += 1
            else:
                status = "SKIPPED"
            print(f"{skill} {res['name']}: {status} ({res['seconds']:.2f}s) {res['tail']}")
    print(f"Task checks: {passed} passed, {failed} failed, {skipped} skipped-skills")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
