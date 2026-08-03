#!/usr/bin/env python3
"""PreCompact hook — snapshot the queue before compaction (spec §12).

The queue file lives outside the context window, but a snapshot is cheap
insurance against any compaction-adjacent loss. Latest wins. Fail-open.
"""
import os
import shutil
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from robium_hooks import read_event

    event = read_event()
    cwd = event.get("cwd") or ""
    q = os.path.join(cwd, ".robium", "queue.jsonl")
    if os.path.exists(q) and os.path.getsize(q) > 0:
        shutil.copy2(q, os.path.join(cwd, ".robium", "queue-precompact.jsonl"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
