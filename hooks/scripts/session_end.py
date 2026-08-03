#!/usr/bin/env python3
"""SessionEnd hook — archive the session transcript before Claude Code retention
prunes it (spec §4.0: transcripts are Tier −1, the engine's raw record)."""
import os
import shutil
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

MAX_ARCHIVE_MB = 500


def prune_archive(cwd: str) -> None:
    tdir = os.path.join(cwd, ".robium", "transcripts")
    if not os.path.isdir(tdir):
        return
    files = [os.path.join(tdir, f) for f in os.listdir(tdir) if f.endswith(".jsonl")]
    total = sum(os.path.getsize(f) for f in files)
    budget = MAX_ARCHIVE_MB * 1024 * 1024
    for f in sorted(files, key=os.path.getmtime):
        if total <= budget:
            break
        total -= os.path.getsize(f)
        os.remove(f)


def archive_and_prune(event: dict, cwd: str, robium_dir_fn) -> None:
    """Archive transcript atomically and prune by archived-at recency."""
    src = event.get("transcript_path") or ""
    if not (src and os.path.exists(src) and os.path.getsize(src) > 0):
        return
    d = robium_dir_fn(cwd)
    project = os.path.basename(os.path.abspath(cwd or os.getcwd()))
    session = event.get("session_id") or os.path.splitext(os.path.basename(src))[0]
    dest = os.path.join(d, "transcripts", f"{project}__{session}.jsonl")

    # Clean up any stale .tmp file before atomic write.
    tmp = dest + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)

    # Atomic write: copy to tmp, then replace dest.
    shutil.copy2(src, tmp)
    os.replace(tmp, dest)

    # Stamp dest with current time so pruning orders by archived-at recency,
    # not source-write time. This ensures a just-archived old-mtime transcript
    # survives immediate pruning.
    os.utime(dest)

    prune_archive(cwd)


def main() -> None:
    from robium_hooks import read_event, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    archive_and_prune(event, cwd, robium_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
