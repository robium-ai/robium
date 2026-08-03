import json
import subprocess
import robium_hooks as rh


def test_robium_dir_creates_workspace(tmp_path):
    d = rh.robium_dir(str(tmp_path))
    assert (tmp_path / ".robium" / "transcripts").is_dir()
    assert d == str(tmp_path / ".robium")


def test_robium_dir_adds_git_exclude(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    rh.robium_dir(str(tmp_path))
    exclude = (tmp_path / ".git" / "info" / "exclude").read_text()
    assert ".robium/" in exclude
    # idempotent — second call must not duplicate the line
    rh.robium_dir(str(tmp_path))
    assert exclude.count(".robium/") == (tmp_path / ".git" / "info" / "exclude").read_text().count(".robium/")


def test_append_and_count_flags(tmp_path):
    rh.append_flag(str(tmp_path), {"type": "error", "excerpt": "boom"})
    rh.append_flag(str(tmp_path), {"type": "user-correction", "excerpt": "no, use X"})
    assert rh.count_flags(str(tmp_path)) == 2
    flags = rh.read_flags(str(tmp_path))
    assert flags[0]["type"] == "error"
    assert "ts" in flags[0] and "project" in flags[0]


def test_read_flags_skips_corrupt_lines(tmp_path):
    rh.append_flag(str(tmp_path), {"type": "error"})
    with open(tmp_path / ".robium" / "queue.jsonl", "a") as f:
        f.write("not json\n")
    assert rh.count_flags(str(tmp_path)) == 1


def test_excerpt_truncates():
    assert rh.excerpt("x" * 1000) == "x" * 400 + "…"
    assert rh.excerpt("short") == "short"


def test_emit_context_shape(capsys):
    rh.emit_context("SessionStart", "hello")
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert out["hookSpecificOutput"]["additionalContext"] == "hello"
