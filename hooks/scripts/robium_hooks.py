"""Shared helpers for robium capture hooks.

stdlib only. Every consumer wraps main() in try/except and exits 0 —
capture must never break a session (spec §12: fail-open).
"""
import datetime
import json
import os
import sys

QUEUE = "queue.jsonl"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_event() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def _ensure_git_exclude(cwd: str) -> None:
    info = os.path.join(cwd, ".git", "info")
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return
    os.makedirs(info, exist_ok=True)
    exclude = os.path.join(info, "exclude")
    line = ".robium/"
    try:
        existing = open(exclude, encoding="utf-8").read() if os.path.exists(exclude) else ""
    except Exception:
        existing = ""
    if line not in existing.splitlines():
        with open(exclude, "a", encoding="utf-8") as f:
            f.write(("" if existing.endswith("\n") or not existing else "\n") + line + "\n")


def robium_dir(cwd: str) -> str:
    cwd = cwd or os.getcwd()
    d = os.path.join(cwd, ".robium")
    os.makedirs(os.path.join(d, "transcripts"), exist_ok=True)
    _ensure_git_exclude(cwd)
    return d


def append_flag(cwd: str, flag: dict) -> None:
    d = robium_dir(cwd)
    flag.setdefault("ts", now_iso())
    flag.setdefault("project", os.path.basename(os.path.abspath(cwd or os.getcwd())))
    with open(os.path.join(d, QUEUE), "a", encoding="utf-8") as f:
        f.write(json.dumps(flag, ensure_ascii=False) + "\n")


def read_flags(cwd: str) -> list:
    path = os.path.join(cwd or os.getcwd(), ".robium", QUEUE)
    flags = []
    if not os.path.exists(path):
        return flags
    for line in open(path, encoding="utf-8"):
        try:
            flags.append(json.loads(line))
        except Exception:
            continue
    return flags


def count_flags(cwd: str) -> int:
    return len(read_flags(cwd))


def excerpt(text: str, n: int = 400) -> str:
    text = text or ""
    return text if len(text) <= n else text[:n] + "…"


def emit_context(event_name: str, text: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    }))
