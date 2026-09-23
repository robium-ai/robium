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


def test_archived_transcript_scrubs_nested_tool_output(tmp_path):
    src = tmp_path / "sensitive-transcript.jsonl"
    secret = "hf_abcdefghijklmnopqrstuvwxyz"
    capability = "0123456789abcdef0123456789abcdef"
    record = {
        "type": "tool_output",
        "AUTH_TOKEN": "direct-secret-value",
        "payload": {
            "text": json.dumps({
                "HF_TOKEN": secret,
                "VLA_CAPABILITY": capability,
                "cwd": "/Users/example/repos/robium",
                "owner": "person@example.com",
                "result": "useful evidence",
            })
        },
    }
    src.write_text(json.dumps(record) + "\n", encoding="utf-8")

    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "sensitive",
                  "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"})

    assert r.returncode == 0
    dest = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__sensitive.jsonl"
    archived = dest.read_text(encoding="utf-8")
    assert secret not in archived
    assert capability not in archived
    assert "direct-secret-value" not in archived
    assert "person@example.com" not in archived
    assert "/Users/example" not in archived
    assert "useful evidence" in archived
    assert json.loads(archived)


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


def test_size_ceiling_never_deletes_pending_queue_evidence(tmp_path, monkeypatch):
    import session_end
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    protected = tdir / "proj__pending.jsonl"
    disposable = tdir / "proj__disposable.jsonl"
    protected.write_bytes(b"p" * 1024)
    disposable.write_bytes(b"d" * 1024)
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.write_text('{"type":"error","session":"pending"}\n', encoding="utf-8")
    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0005)

    session_end.prune_archive(str(tmp_path))

    assert protected.exists()
    assert not disposable.exists()


def test_size_ceiling_never_deletes_tentative_observation_evidence(tmp_path, monkeypatch):
    import session_end
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    name = "proj__evidence.jsonl"
    protected = tdir / name
    protected.write_bytes(b"p" * 1024)
    observations = tmp_path / "learnings" / "observations"
    observations.mkdir(parents=True)
    (observations / "testing.md").write_text(
        "## finding <!-- id: obs-testing-001 -->\n"
        "status: tentative\nsignal: wrong-guidance\n"
        f"source: transcript {name}#turn-1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0005)

    session_end.prune_archive(str(tmp_path))

    assert protected.exists()


def test_just_archived_survives_prune(tmp_path, monkeypatch):
    """Pruning uses archive time rather than the source transcript's mtime."""
    import session_end
    import os
    import time

    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    pre_old = tdir / "proj__pre_old.jsonl"
    pre_new = tdir / "proj__pre_new.jsonl"
    pre_old.write_bytes(b"a" * 1024)
    pre_new.write_bytes(b"b" * 1024)
    now = time.time()
    os.utime(pre_old, (now - 200, now - 200))  # Oldest
    os.utime(pre_new, (now - 100, now - 100))  # Middle

    src = tmp_path / "old_session.jsonl"
    src.write_bytes(b"x" * 1024)
    os.utime(src, (now - 9999, now - 9999))

    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0025)

    event = {"hook_event_name": "SessionEnd", "session_id": "old_archive",
             "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"}
    session_end.archive_and_prune(event, str(tmp_path), lambda cwd: str(tdir.parent))

    just_archived = tdir / f"{tmp_path.name}__old_archive.jsonl"
    assert just_archived.exists(), "Just-archived transcript should survive pruning"
    assert not pre_old.exists(), "Oldest pre-existing archive should be pruned"
    assert pre_new.exists(), "Newer pre-existing archive should survive"


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
