#!/usr/bin/env python3
"""SessionEnd hook — archive the agent transcript before host retention prunes
it (spec §4.0: transcripts are Tier −1, the engine's raw record)."""
import importlib.util
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAX_ARCHIVE_MB = 500
SEEN_MAX_AGE_DAYS = 7


def prune_seen_files(cwd: str, session_id: str, now: "float | None" = None) -> None:
    """Remove the ended session marker and abandoned markers older than 7 days."""
    root = os.path.abspath(cwd or os.getcwd())
    d = os.path.join(root, ".robium")
    if not os.path.isdir(d):
        return

    current_name = f".seen-{session_id}" if session_id else ""
    cutoff = (time.time() if now is None else now) - SEEN_MAX_AGE_DAYS * 86400
    for name in os.listdir(d):
        if not name.startswith(".seen-"):
            continue
        path = os.path.join(d, name)
        try:
            if name == current_name or os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def protected_archive_names(cwd: str) -> set[str]:
    """Return pending-evidence archive names; fail closed if classifier is absent."""
    tdir = Path(cwd) / ".robium" / "transcripts"
    candidates = {path.name for path in tdir.glob("*.jsonl") if path.is_file()}
    engine = Path(__file__).resolve().parents[2] / "scripts" / "engine" / "prune_transcripts.py"
    if not engine.is_file():
        return candidates
    try:
        spec = importlib.util.spec_from_file_location("robium_prune_transcripts", engine)
        if spec is None or spec.loader is None:
            return candidates
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        decisions = module.classify(Path(cwd))
        return {
            decision.path.name
            for decision in decisions
            if decision.reason in {"pending-queue", "pending-evidence"}
        }
    except Exception:
        return candidates


def prune_archive(cwd: str) -> None:
    """Enforce the size ceiling without deleting pending queue/observation evidence."""
    tdir = os.path.join(cwd, ".robium", "transcripts")
    if not os.path.isdir(tdir):
        return
    files = [os.path.join(tdir, f) for f in os.listdir(tdir) if f.endswith(".jsonl")]
    total = sum(os.path.getsize(f) for f in files)
    budget = MAX_ARCHIVE_MB * 1024 * 1024
    protected = protected_archive_names(cwd)
    for f in sorted(files, key=os.path.getmtime):
        if total <= budget:
            break
        if os.path.basename(f) in protected:
            continue
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
    prune_seen_files(cwd, event.get("session_id") or "")
    archive_and_prune(event, cwd, robium_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
