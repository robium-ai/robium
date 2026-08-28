#!/usr/bin/env python3
"""Deterministically report or prune archived transcript evidence.

Protection order:
1. a pending queue flag references the transcript/session;
2. a dated learning links the transcript and any linked observation is
   nonterminal, or the learning has not been consolidated into an observation;
3. all observations linked through every learning are absorbed/rejected;
4. otherwise, only an unreferenced transcript older than the retention window
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
_ENTRY_RE = re.compile(r"<!--\s*id:\s*(lrn-[a-z0-9-]+)\s*-->")
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


def learning_transcript_links(learnings_dir: Path) -> dict[str, set[str]]:
    """Map archived transcript filename to dated learning IDs."""
    links: dict[str, set[str]] = defaultdict(set)
    if not learnings_dir.is_dir():
        return links
    for path in sorted(learnings_dir.glob("*.md")):
        if path.name in {"README.md", "AGENTS.md", "CLAUDE.md", "SOURCES.md"}:
            continue
        current_id = None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = _ENTRY_RE.search(line)
            if match:
                current_id = match.group(1)
            if current_id:
                for name in _TRANSCRIPT_RE.findall(line):
                    links[name].add(current_id)
    return links


def observation_statuses(observations_dir: Path) -> dict[str, list[str]]:
    """Map each learning source ID to every observation status that cites it."""
    statuses: dict[str, list[str]] = defaultdict(list)
    if not observations_dir.is_dir():
        return statuses
    for path in sorted(observations_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        fields: dict[str, str] | None = None

        def record(current):
            if not current:
                return
            status = current.get("status", "")
            value = current.get("sources", "").strip()
            if not (value.startswith("[") and value.endswith("]")):
                return
            for source in (part.strip() for part in value[1:-1].split(",")):
                if source.startswith("lrn-"):
                    statuses[source].append(status)

        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if _OBS_HEADING_RE.match(line):
                record(fields)
                fields = {}
                continue
            if fields is not None:
                match = _FIELD_RE.match(line)
                if match:
                    fields[match.group(1)] = match.group(2).strip()
        record(fields)
    return statuses


def _terminal(status: str) -> bool:
    return status.startswith("absorbed ") or status.startswith("rejected (")


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
    links = learning_transcript_links(root / "learnings")
    statuses = observation_statuses(root / "learnings" / "observations")
    cutoff = (time.time() if now is None else now) - max_age_days * 86400
    decisions = []

    for path in sorted(transcripts_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.suffix != ".jsonl":
            continue
        session = path.stem.rsplit("__", 1)[-1] if "__" in path.stem else ""
        if path.name in queue_names or session in queue_sessions:
            decisions.append(Decision(path, "KEEP", "pending-queue"))
            continue

        learning_ids = links.get(path.name, set())
        if learning_ids:
            all_terminal = True
            for learning_id in learning_ids:
                linked_statuses = statuses.get(learning_id, [])
                if not linked_statuses or not all(_terminal(s) for s in linked_statuses):
                    all_terminal = False
                    break
            if all_terminal:
                decisions.append(Decision(path, "DELETE", "linked-terminal"))
            else:
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

    decisions = classify(Path(args.root), max_age_days=args.max_age_days)
    for decision in decisions:
        print(f"{decision.action} {decision.path.name} {decision.reason}")
    deleted = apply_decisions(decisions) if args.apply else 0
    eligible = sum(d.action == "DELETE" for d in decisions)
    kept = sum(d.action == "KEEP" for d in decisions)
    mode_name = "apply" if args.apply else "dry-run"
    print(f"Transcript cleanup ({mode_name}): {kept} kept, {eligible} eligible, {deleted} deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
