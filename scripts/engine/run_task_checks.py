#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Task-check runner: executes evals.yaml `tasks:` fixtures (spec §4.3).

Each validated task is a shell command run with an explicit timeout, cwd scoped to
the named app directory (repo-root-relative) or the repo root — NEVER
inside skills/. PASS requires exit 0 AND a regex match against the
combined stdout+stderr. Never run as root; never alters state outside its
own cwd; a timeout terminates the full task process group rather than leaving
children behind.

`run_task` is the reusable primitive: the deep-verify lane (Task 5) will
import it directly to score fixture-verified examples without going
through this module's CLI.
"""
import argparse
import os
import re
import signal
import subprocess
import sys
import time

import yaml

from task_schema import TaskSchemaError, validate_tasks

DEFAULT_TIMEOUT_S = 300
TAIL_MAX_LINES = 5
TAIL_MAX_CHARS = 400


def load_tasks(skill, skills_dir):
    path = os.path.join(skills_dir, skill, "evals.yaml")
    if not os.path.exists(path):
        return []
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TaskSchemaError(f"{path}: top level must be a mapping")
    tasks = data.get("tasks", [])
    try:
        return list(validate_tasks(tasks))
    except TaskSchemaError as exc:
        raise TaskSchemaError(f"{path}: {exc}") from exc


def _tail(text):
    text = (text or "").strip()
    lines = text.splitlines()[-TAIL_MAX_LINES:]
    tail = "\n".join(lines)
    if len(tail) > TAIL_MAX_CHARS:
        tail = tail[-TAIL_MAX_CHARS:]
    return tail


def _stop_process_group(proc):
    """Terminate the task shell and every child it launched."""
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return proc.communicate()
    else:
        # /T is the Windows equivalent of killing the complete process tree.
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            timeout=5,
            check=False,
        )

    output = (None, None)
    try:
        output = proc.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        pass

    if os.name == "posix":
        # The group can outlive its leader when a child ignores SIGTERM, so
        # send the final signal even when communicate() already reaped the
        # shell process.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif proc.poll() is None:
        proc.kill()
    if proc.poll() is None:
        output = proc.communicate()
    return output


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
    popen_opts = {"start_new_session": True} if os.name == "posix" else {
        "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP,
    }
    proc = subprocess.Popen(
        command, shell=True, cwd=cwd, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, **popen_opts
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        seconds = time.time() - start
        combined = (stdout or "") + (stderr or "")
        matched = re.search(pass_criteria, combined) is not None
        ok = proc.returncode == 0 and matched
        return {"name": name, "pass": ok, "exit": proc.returncode,
                "matched": matched, "seconds": seconds, "tail": _tail(combined)}
    except subprocess.TimeoutExpired:
        stdout, stderr = _stop_process_group(proc)
        seconds = time.time() - start
        note = f"TIMEOUT after {timeout}s"
        combined = (stdout or "") + (stderr or "")
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
        try:
            all_tasks = load_tasks(skill, args.skills_dir)
        except TaskSchemaError as exc:
            failed += 1
            print(f"{skill}: invalid task schema: {exc}")
            continue
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
