import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "hooks" / "scripts"


def run_hook(event):
    return subprocess.run([sys.executable, str(SCRIPTS / "session_end.py")],
                          input=json.dumps(event), capture_output=True, text=True, timeout=10)


def test_archives_transcript(tmp_path):
    src = tmp_path / "fake-transcript.jsonl"
    src.write_text('{"type":"user","message":{"role":"user","content":"hi"}}\n')
    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "abc123",
                  "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"})
    assert r.returncode == 0
    dest = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__abc123.jsonl"
    assert dest.exists() and dest.read_text() == src.read_text()


def test_rearchive_overwrites(tmp_path):
    src = tmp_path / "t.jsonl"
    src.write_text("v1\n")
    ev = {"hook_event_name": "SessionEnd", "session_id": "abc123",
          "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"}
    run_hook(ev)
    src.write_text("v1\nv2\n")
    run_hook(ev)
    dest = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__abc123.jsonl"
    assert dest.read_text() == "v1\nv2\n"


def test_missing_or_empty_transcript_is_noop(tmp_path):
    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "x",
                  "cwd": str(tmp_path), "transcript_path": str(tmp_path / "nope.jsonl"),
                  "reason": "exit"})
    assert r.returncode == 0
    tdir = tmp_path / ".robium" / "transcripts"
    assert not tdir.exists() or list(tdir.iterdir()) == []


def test_prunes_oldest_over_budget(tmp_path, monkeypatch):
    import session_end
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    old = tdir / "proj__old.jsonl"
    new = tdir / "proj__new.jsonl"
    old.write_bytes(b"x" * 1024)
    new.write_bytes(b"y" * 1024)
    import os, time
    os.utime(old, (time.time() - 9999, time.time() - 9999))
    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0015)  # ~1.5KB budget
    session_end.prune_archive(str(tmp_path))
    assert not old.exists() and new.exists()


def test_just_archived_survives_prune(tmp_path, monkeypatch):
    """Verify a just-archived old-mtime transcript survives pruning.

    Previously, copy2 preserved source mtime, so an old session could be
    pruned immediately. Now, archival stamps dest with current time, ensuring
    it's always the newest candidate.
    """
    import session_end
    import os
    import time

    # Create two pre-existing archives with old mtimes and ~1KB each.
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    pre_old = tdir / "proj__pre_old.jsonl"
    pre_new = tdir / "proj__pre_new.jsonl"
    pre_old.write_bytes(b"a" * 1024)
    pre_new.write_bytes(b"b" * 1024)
    now = time.time()
    os.utime(pre_old, (now - 200, now - 200))  # Oldest
    os.utime(pre_new, (now - 100, now - 100))  # Middle

    # Create a source transcript with ancient mtime (older than pre-existing).
    src = tmp_path / "old_session.jsonl"
    src.write_bytes(b"x" * 1024)  # Same size as pre-existing files
    os.utime(src, (now - 9999, now - 9999))  # Very old

    # Monkeypatch budget to ~2.5KB (forces pruning; total will be ~3KB).
    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0025)

    # Archive the ancient-mtime transcript and prune.
    event = {"hook_event_name": "SessionEnd", "session_id": "old_archive",
             "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"}
    session_end.archive_and_prune(event, str(tmp_path), lambda cwd: str(tdir.parent))

    # The just-archived file (now stamped with current time) should survive.
    # The oldest pre-existing (pre_old) should be pruned (oldest mtime).
    just_archived = tdir / f"{tmp_path.name}__old_archive.jsonl"
    assert just_archived.exists(), "Just-archived transcript should survive pruning"
    assert not pre_old.exists(), "Oldest pre-existing archive should be pruned"
    assert pre_new.exists(), "Newer pre-existing archive should survive"


def test_atomic_no_tmp_leftover(tmp_path):
    """Verify no .tmp file remains after successful archive."""
    src = tmp_path / "transcript.jsonl"
    src.write_text("content\n")
    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "test_atomic",
                  "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"})
    assert r.returncode == 0
    tdir = tmp_path / ".robium" / "transcripts"
    tmp_files = list(tdir.glob("*.tmp")) if tdir.exists() else []
    assert tmp_files == [], f"No .tmp files should remain, but found: {tmp_files}"


def test_prunes_ended_and_stale_seen_files_but_preserves_fresh_concurrent(tmp_path):
    import os
    import session_end

    d = tmp_path / ".robium"
    d.mkdir()
    ended = d / ".seen-ended"
    stale = d / ".seen-abandoned"
    concurrent = d / ".seen-concurrent"
    unrelated = d / "queue.jsonl"
    for path in (ended, stale, concurrent, unrelated):
        path.write_text("marker\n")

    now = 2_000_000_000.0
    os.utime(stale, (now - 8 * 86400, now - 8 * 86400))
    os.utime(concurrent, (now - 6 * 86400, now - 6 * 86400))
    session_end.prune_seen_files(str(tmp_path), "ended", now=now)

    assert not ended.exists()
    assert not stale.exists()
    assert concurrent.exists()
    assert unrelated.exists()


def test_session_end_prunes_seen_file_without_transcript(tmp_path):
    d = tmp_path / ".robium"
    d.mkdir()
    seen = d / ".seen-no-transcript"
    seen.write_text("signature\n")

    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "no-transcript",
                  "cwd": str(tmp_path), "reason": "exit"})

    assert r.returncode == 0
    assert not seen.exists()
