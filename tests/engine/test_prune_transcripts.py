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


def seed_observation(root, status, transcript_name):
    observations = root / "learnings" / "observations"
    observations.mkdir(parents=True, exist_ok=True)
    (observations / "testing.md").write_text(
        "## finding <!-- id: obs-testing-001 -->\n"
        f"status: {status}\nproof: 1\nsignal: wrong-guidance\n"
        "sources: [robium-apps/x]\ntarget: testing#x (update) - fix\n"
        "evidence: symptom\n"
        f"source: transcript {transcript_name}#turn-1\n",
        encoding="utf-8",
    )


def test_pending_queue_session_is_never_deleted(tmp_path):
    path = transcript(tmp_path, "robium__session-1.jsonl", age_days=30)
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.write_text('{"type":"error","session":"session-1"}\n', encoding="utf-8")
    result = run_cleanup(tmp_path, "--apply")
    assert "KEEP robium__session-1.jsonl pending-queue" in result.stdout
    assert path.exists()


def test_nonterminal_observation_keeps_its_transcript(tmp_path):
    name = "robium__evidence.jsonl"
    path = transcript(tmp_path, name, age_days=30)
    seed_observation(tmp_path, "tentative", name)
    result = run_cleanup(tmp_path, "--apply")
    assert "KEEP robium__evidence.jsonl pending-evidence" in result.stdout
    assert path.exists()


def test_removed_observation_allows_explicit_immediate_cleanup(tmp_path):
    name = "robium__done.jsonl"
    path = transcript(tmp_path, name, age_days=1)
    result = run_cleanup(tmp_path, "--max-age-days", "0", "--apply")
    assert "DELETE robium__done.jsonl expired-unreferenced" in result.stdout
    assert not path.exists()


def test_unreferenced_transcripts_expire_after_fourteen_days(tmp_path):
    fresh = transcript(tmp_path, "robium__fresh.jsonl", age_days=1)
    stale = transcript(tmp_path, "robium__stale.jsonl", age_days=30)
    result = run_cleanup(tmp_path, "--apply")
    assert "KEEP robium__fresh.jsonl recent-unreferenced" in result.stdout
    assert fresh.exists()
    assert not stale.exists()


def test_symlinks_are_ignored(tmp_path):
    real = tmp_path / "outside.jsonl"
    real.write_text("{}\n", encoding="utf-8")
    link = tmp_path / ".robium" / "transcripts" / "robium__link.jsonl"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(real)
    run_cleanup(tmp_path, "--apply")
    assert real.exists()
    assert link.exists()
