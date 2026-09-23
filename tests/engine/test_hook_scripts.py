import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "hooks" / "scripts"


def run_hook(name, event, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        input=json.dumps(event), capture_output=True, text=True, timeout=10,
    )


def read_queue(tmp_path):
    q = tmp_path / ".robium" / "queue.jsonl"
    if not q.exists():
        return []
    return [json.loads(l) for l in q.read_text().splitlines() if l.strip()]


def test_ups_captures_correction(tmp_path):
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
          "cwd": str(tmp_path), "prompt": "no, use the humble image not jazzy"}
    r = run_hook("user_prompt_submit.py", ev)
    assert r.returncode == 0 and r.stdout.strip() == ""
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "user-correction"
    assert flags[0]["session"] == "s1"
    assert "humble" in flags[0]["excerpt"]


def test_ups_ignores_plain_task_prompt(tmp_path):
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
          "cwd": str(tmp_path), "prompt": "please add a launch file for the lidar"}
    run_hook("user_prompt_submit.py", ev)
    assert read_queue(tmp_path) == []


def test_ups_only_long_explicit_remember_bypasses_length_gate(tmp_path):
    long_correction = "no, " + "x" * 600
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": long_correction})
    assert read_queue(tmp_path) == []

    pseudo_remember = "remember use uv, not pip " + "x" * 500
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": pseudo_remember})
    assert read_queue(tmp_path) == []

    explicit_remember = "remember: " + "x" * 600
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": explicit_remember})
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "remember"


def test_ups_scrubs_secrets(tmp_path):
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": "no, the token is HF_TOKEN=hf_abcdef123456 use that"})
    flags = read_queue(tmp_path)
    assert flags and "hf_abcdef123456" not in flags[0]["excerpt"]


def test_ups_fails_open_on_garbage_stdin():
    r = subprocess.run([sys.executable, str(SCRIPTS / "user_prompt_submit.py")],
                       input="{{{not json", capture_output=True, text=True, timeout=10)
    assert r.returncode == 0


def test_ups_boundary_straddling_secret_scrubbed(tmp_path):
    """Scrub the full prompt before taking its 400-character excerpt."""
    prefix = "no, use this instead: "
    secret = "API_KEY=supersecretvalue123"
    prompt = prefix + "x" * 366 + " " + secret + " trailing text after the secret value here"
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": prompt})
    flags = read_queue(tmp_path)
    assert flags
    assert "API_KEY=sup" not in flags[0]["excerpt"]
    assert "supersecretvalue123" not in flags[0]["excerpt"]


def test_ptu_boundary_straddling_secret_scrubbed(tmp_path):
    """Scrub the full output before taking its tail and excerpt windows."""
    marker = "[ERROR] deploy failed unexpectedly\n"
    secret = "API_KEY=supersecretvalue123"
    padding_before = "e" * 1979
    trailing = " trailing text " + "e" * 1970
    output = marker + padding_before + " " + secret + trailing
    ev = {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "deploy.sh"},
          "tool_response": output}
    r = run_hook("post_tool_use.py", ev)
    assert r.returncode == 0
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert "secretvalue123" not in flags[0]["excerpt"]
    assert "supersecretvalue123" not in flags[0]["excerpt"]


def test_ptu_captures_bash_error(tmp_path):
    ev = {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "colcon build --packages-select nav2_bringup"},
          "tool_response": {"stdout": "", "stderr": "CMake Error at CMakeLists.txt:14"}}
    r = run_hook("post_tool_use.py", ev)
    assert r.returncode == 0
    flags = read_queue(tmp_path)
    assert len(flags) == 1 and flags[0]["type"] == "error"
    assert flags[0]["command"].startswith("colcon build")
    assert "CMake Error" in flags[0]["excerpt"]


def test_ptu_captures_claude_failure_event(tmp_path):
    ev = {"hook_event_name": "PostToolUseFailure", "session_id": "s2",
          "cwd": str(tmp_path), "tool_name": "Bash",
          "tool_input": {"command": "colcon build"},
          "error": "CMake Error at CMakeLists.txt:14"}
    result = run_hook("post_tool_use.py", ev)
    assert result.returncode == 0 and result.stdout.strip() == ""
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "error"
    assert "CMake Error" in flags[0]["excerpt"]


def test_ptu_dedupes_same_error_in_session(tmp_path):
    ev = {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "colcon build"},
          "tool_response": "CMake Error at /a/CMakeLists.txt:14"}
    run_hook("post_tool_use.py", ev)
    run_hook("post_tool_use.py", ev)
    assert len(read_queue(tmp_path)) == 1


def test_ptu_ignores_clean_output_and_other_tools(tmp_path):
    run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
             "cwd": str(tmp_path), "tool_name": "Bash",
             "tool_input": {"command": "ls"}, "tool_response": "file.txt"})
    run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
             "cwd": str(tmp_path), "tool_name": "Read",
             "tool_input": {"file_path": "/x"}, "tool_response": "ERROR text in a file"})
    assert read_queue(tmp_path) == []


def test_ptu_failing_commit_captured_as_error(tmp_path):
    """A failing git commit (pre-commit hook rejection) should be captured as error."""
    ev = {"hook_event_name": "PostToolUse", "session_id": "s3", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "git commit -m 'feat: x'"},
          "tool_response": {"stdout": "", "stderr": "error: file.py:10: E501 line too long\npre-commit hook exited with code 1"}}
    r = run_hook("post_tool_use.py", ev)
    assert r.returncode == 0
    flags = read_queue(tmp_path)
    assert len(flags) == 1 and flags[0]["type"] == "error"
    assert "pre-commit hook" in flags[0]["excerpt"]


def test_ptu_command_mentioning_commit_not_swallowed(tmp_path):
    """A failing command that merely mentions 'git commit' should still be flagged."""
    ev = {"hook_event_name": "PostToolUse", "session_id": "s3", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "grep -rn 'git commit' CHANGELOG.md"},
          "tool_response": "grep: CHANGELOG.md: No such file or directory"}
    r = run_hook("post_tool_use.py", ev)
    assert r.returncode == 0
    flags = read_queue(tmp_path)
    assert len(flags) == 1 and flags[0]["type"] == "error"
    assert "No such file" in flags[0]["excerpt"]


def test_ptu_clean_commit_not_flagged(tmp_path):
    """A git commit with clean output produces no flag and no output."""
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s3",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit -m 'feat: y'"},
                 "tool_response": "1 file changed"})
    assert r.stdout.strip() == ""
    assert read_queue(tmp_path) == []


def test_session_start_initializes_and_ignores_one_ordinary_error(tmp_path):
    r = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                 "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    assert r.returncode == 0
    assert (tmp_path / ".robium" / "transcripts").is_dir()
    assert r.stdout.strip() == ""
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.write_text(
        '{"type":"error","session":"s3","signature":"only-once"}\n',
        encoding="utf-8",
    )
    r2 = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                  "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    assert r2.returncode == 0
    assert r2.stdout.strip() == ""


def test_session_start_reminds_once_per_day_for_correction(tmp_path):
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.parent.mkdir(parents=True)
    queue.write_text(
        '{"type":"user-correction","session":"older"}\n',
        encoding="utf-8",
    )
    event = {"hook_event_name": "SessionStart", "session_id": "s4",
             "cwd": str(tmp_path), "source": "startup"}

    first = run_hook("session_start.py", event)
    second = run_hook("session_start.py", event)

    payload = json.loads(first.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "1 substantial" in context
    assert "background subagent" in context
    assert second.stdout.strip() == ""


def test_session_start_repeated_error_is_substantial_but_linked_rows_are_not(tmp_path):
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.parent.mkdir(parents=True)
    queue.write_text(
        '{"type":"error","signature":"same","session":"a"}\n'
        '{"type":"error","signature":"same","session":"b"}\n'
        '{"type":"user-correction","session":"c","observation":"obs-x-001"}\n',
        encoding="utf-8",
    )
    result = run_hook("session_start.py", {
        "hook_event_name": "SessionStart", "session_id": "s5",
        "cwd": str(tmp_path), "source": "resume",
    })
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "2 substantial" in context
    assert "error: 2" in context
    assert "user-correction" not in context


def test_session_start_compaction_never_reminds(tmp_path):
    queue = tmp_path / ".robium" / "queue.jsonl"
    queue.parent.mkdir(parents=True)
    queue.write_text('{"type":"remember","session":"a"}\n', encoding="utf-8")
    result = run_hook("session_start.py", {
        "hook_event_name": "SessionStart", "session_id": "s6",
        "cwd": str(tmp_path), "source": "compact",
    })
    assert result.stdout.strip() == ""


def test_ups_only_captures_with_observations_present(tmp_path):
    d = tmp_path / "learnings" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(
        "## costmap inflation missing <!-- id: obs-nav2-007 -->\n"
        "status: ready\nproof: 2\nsignal: wrong-guidance\n"
        "sources: [lrn-1]\ntarget: nav2#costmap-inflation (update)\n"
        "evidence: ✓ ✓ ✓\n",
        encoding="utf-8",
    )
    plain = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "why does the robot hug obstacles? costmap inflation maybe"})
    assert plain.returncode == 0
    assert plain.stdout.strip() == ""
    assert read_queue(tmp_path) == []

    correction = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "no, the costmap inflation obstacles fix was wrong"})
    assert read_queue(tmp_path)
    assert correction.stdout.strip() == ""
