#!/usr/bin/env python3
"""Deterministically report or prune archived transcript evidence.

Protection order:
1. a pending queue flag references the transcript/session;
2. any local observation cites the transcript;
3. otherwise, only an unreferenced transcript older than the retention window
   is eligible.

Dry-run is the default. The tool never follows symlinks and only deletes direct
`.jsonl` children of `<root>/.robium/transcripts`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_AGE_DAYS = 14
_TRANSCRIPT_RE = re.compile(r"([A-Za-z0-9._-]+__[A-Za-z0-9-]+\.jsonl)")
_OBS_HEADING_RE = re.compile(r"^## .+<!--\s*id:\s*(obs-[a-z0-9-]+)\s*-->\s*$")
_FIELD_RE = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")


@dataclass(frozen=True)
class Decision:
    path: Path
    action: str
    reason: str


def _json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _json_strings(item)


def pending_queue_refs(queue_path: Path) -> tuple[set[str], set[str]]:
    sessions: set[str] = set()
    names: set[str] = set()
    if not queue_path.is_file():
        return sessions, names
    for raw in queue_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(raw)
        except (TypeError, ValueError):
            continue
        session = item.get("session") if isinstance(item, dict) else None
        if isinstance(session, str) and session:
            sessions.add(session)
        for value in _json_strings(item):
            names.update(_TRANSCRIPT_RE.findall(value))
    return sessions, names


def observation_transcript_statuses(observations_dir: Path) -> dict[str, list[str]]:
    """Map each cited transcript filename to the statuses of entries citing it."""
    statuses: dict[str, list[str]] = defaultdict(list)
    if not observations_dir.is_dir():
        return statuses
    for path in sorted(observations_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        status = ""
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if _OBS_HEADING_RE.match(line):
                status = ""
                continue
            match = _FIELD_RE.match(line)
            if match and match.group(1) == "status":
                status = match.group(2).strip()
            for name in _TRANSCRIPT_RE.findall(line):
                statuses[name].append(status)
    return statuses


def classify(
    root: Path,
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
) -> list[Decision]:
    root = root.resolve()
    transcripts_dir = root / ".robium" / "transcripts"
    if not transcripts_dir.is_dir():
        return []

    queue_sessions, queue_names = pending_queue_refs(root / ".robium" / "queue.jsonl")
    statuses = observation_transcript_statuses(root / "learnings" / "observations")
    cutoff = (time.time() if now is None else now) - max_age_days * 86400
    decisions = []

    for path in sorted(transcripts_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.suffix != ".jsonl":
            continue
        session = path.stem.rsplit("__", 1)[-1] if "__" in path.stem else ""
        if path.name in queue_names or session in queue_sessions:
            decisions.append(Decision(path, "KEEP", "pending-queue"))
            continue

        cited = statuses.get(path.name, [])
        if cited:
            decisions.append(Decision(path, "KEEP", "pending-evidence"))
            continue

        if path.stat().st_mtime < cutoff:
            decisions.append(Decision(path, "DELETE", "expired-unreferenced"))
        else:
            decisions.append(Decision(path, "KEEP", "recent-unreferenced"))
    return decisions


def apply_decisions(decisions: list[Decision]) -> int:
    deleted = 0
    for decision in decisions:
        if decision.action != "DELETE":
            continue
        path = decision.path
        if path.is_symlink() or not path.is_file() or path.suffix != ".jsonl":
            continue
        path.unlink()
        deleted += 1
    return deleted


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Robium repository root")
    parser.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Delete eligible files")
    mode.add_argument("--dry-run", action="store_true", help="Report only (default)")
    args = parser.parse_args(argv)
    if args.max_age_days < 0:
        parser.error("--max-age-days must be non-negative")

    root = Path(args.root)
    mode_name = "apply" if args.apply else "dry-run"

    decisions = classify(root, max_age_days=args.max_age_days)
    for decision in decisions:
        print(f"{decision.action} {decision.path.name} {decision.reason}")
    deleted = apply_decisions(decisions) if args.apply else 0
    eligible = sum(d.action == "DELETE" for d in decisions)
    kept = sum(d.action == "KEEP" for d in decisions)
    print(f"Transcript cleanup ({mode_name}): {kept} kept, {eligible} eligible, {deleted} deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
