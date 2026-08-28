import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "engine" / "prune_transcripts.py"


def transcript(root, name, *, age_days=0):
    path = root / ".robium" / "transcripts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    stamp = time.time() - age_days * 86400
    os.utime(path, (stamp, stamp))
    return path


def run_cleanup(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def seed_learning(root, transcript_name, learning_id="lrn-0101-01"):
    learnings = root / "learnings"
    learnings.mkdir(parents=True, exist_ok=True)
    (learnings / "2026-01-01.md").write_text(
        f"- [none] wrong-guidance <!-- id: {learning_id} -->\n"
        f"  source: transcript {transcript_name}#turn-1\n",
        encoding="utf-8",
    )


def seed_observation(root, status, learning_id="lrn-0101-01"):
    observations = root / "learnings" / "observations"
    observations.mkdir(parents=True, exist_ok=True)
    (observations / "testing.md").write_text(
        "## finding <!-- id: obs-testing-001 -->\n"
        f"status: {status}\nproof: 1\nsignal: wrong-guidance\n"
        f"sources: [{learning_id}]\ntarget: testing#x (update) - fix\n"
        "evidence: symptom\n",
        encoding="utf-8",
    )


def test_pending_queue_session_is_never_deleted(tmp_path):
    path = transcript(tmp_path, "robium__session-1.jsonl", age_days=30)
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.write_text('{"type":"error","session":"session-1"}\n', encoding="utf-8")
    result = run_cleanup(tmp_path, "--apply")
    assert result.returncode == 0
    assert "KEEP robium__session-1.jsonl pending-queue" in result.stdout
    assert path.exists()


def test_unconsolidated_or_tentative_evidence_is_never_deleted(tmp_path):
    name = "robium__evidence.jsonl"
    path = transcript(tmp_path, name, age_days=30)
    seed_learning(tmp_path, name)
    result = run_cleanup(tmp_path, "--apply")
    assert "KEEP robium__evidence.jsonl pending-evidence" in result.stdout
    assert path.exists()

    seed_observation(tmp_path, "tentative")
    result = run_cleanup(tmp_path, "--apply")
    assert "KEEP robium__evidence.jsonl pending-evidence" in result.stdout
    assert path.exists()


def test_all_linked_terminal_observations_allow_deletion(tmp_path):
    name = "robium__terminal.jsonl"
    path = transcript(tmp_path, name)
    seed_learning(tmp_path, name)
    seed_observation(tmp_path, "absorbed 2026-01-02")

    dry = run_cleanup(tmp_path)
    assert "DELETE robium__terminal.jsonl linked-terminal" in dry.stdout
    assert path.exists()

    applied = run_cleanup(tmp_path, "--apply")
    assert applied.returncode == 0
    assert "1 deleted" in applied.stdout
    assert not path.exists()


def test_rejected_observation_is_terminal(tmp_path):
    name = "robium__rejected.jsonl"
    path = transcript(tmp_path, name)
    seed_learning(tmp_path, name)
    seed_observation(tmp_path, "rejected (noise)")
    result = run_cleanup(tmp_path, "--apply")
    assert result.returncode == 0
    assert not path.exists()


def test_unreferenced_transcripts_expire_after_fourteen_days(tmp_path):
    old = transcript(tmp_path, "robium__old.jsonl", age_days=15)
    recent = transcript(tmp_path, "robium__recent.jsonl", age_days=13)
    result = run_cleanup(tmp_path, "--apply")
    assert result.returncode == 0
    assert "DELETE robium__old.jsonl expired-unreferenced" in result.stdout
    assert "KEEP robium__recent.jsonl recent-unreferenced" in result.stdout
    assert not old.exists()
    assert recent.exists()


def test_symlinks_are_ignored(tmp_path):
    outside = tmp_path / "outside.jsonl"
    outside.write_text("{}\n", encoding="utf-8")
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    (tdir / "robium__link.jsonl").symlink_to(outside)
    result = run_cleanup(tmp_path, "--apply", "--max-age-days", "0")
    assert result.returncode == 0
    assert outside.exists()
