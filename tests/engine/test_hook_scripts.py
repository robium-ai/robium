import json
import os
import subprocess
import sys
import time
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


def test_ups_skips_long_prompt_unless_remember(tmp_path):
    long = "no, " + "x" * 600
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": long})
    assert read_queue(tmp_path) == []
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": "remember: " + "x" * 600})
    assert len(read_queue(tmp_path)) == 1


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


def test_ups_long_pseudo_remember_skipped(tmp_path):
    # "remember use uv, not pip" is not a real remember (no colon/comma after remember)
    # Even though it starts with "remember", it should NOT bypass the >500 char gate
    prompt = "remember use uv, not pip " + "x" * 500  # 525+ chars total
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": prompt})
    assert read_queue(tmp_path) == []


def test_ups_long_true_remember_captured(tmp_path):
    # "remember: " is a real remember and SHOULD bypass the >500 char gate
    prompt = "remember: " + "x" * 600  # 610+ chars total
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": prompt})
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "remember"


def test_ups_boundary_straddling_secret_scrubbed(tmp_path):
    """Secret straddling the 400-char excerpt boundary must still be scrubbed.

    Scrub must run on the FULL prompt before truncation. With the old
    `scrub(excerpt(prompt))` ordering, excerpt() cuts the raw prompt to
    400 chars first, landing mid-value inside "API_KEY=supersecretvalue123"
    (only "API_KEY=sup" survives the cut) — too short to match the
    KEY=value pattern's 6-char minimum, so the fragment "sup" leaks
    unredacted. The correct `excerpt(scrub(prompt))` ordering scrubs the
    full prompt (matching the complete secret) before any truncation.
    """
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
    """Secret straddling the output[-2000:] window boundary must be scrubbed.

    Old ordering `scrub(excerpt(output[-2000:], 400))` slices the RAW
    output to its last 2000 chars first. This layout is sized so that
    slice boundary lands mid-value inside "API_KEY=supersecretvalue123",
    leaving only the tail "...secretvalue123..." visible with no leading
    "API_KEY=" in the truncated slice — which cannot match the KEY=value
    pattern (no "=" in the visible fragment) and so the value leaks
    verbatim. New ordering `excerpt(scrub(output)[-2000:], 400)` scrubs
    the full output first (matching the complete secret) before any
    windowing, so nothing of the value survives into the excerpt.
    """
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


def test_ptu_commit_nudge_when_flags_pending(tmp_path):
    for i in range(3):
        run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
                 "session_id": "s2", "cwd": str(tmp_path),
                 "prompt": f"no, fix the {i} param not that one"})
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit -m 'feat: x'"},
                 "tool_response": "1 file changed"})
    out = json.loads(r.stdout)
    assert "pending learning" in out["hookSpecificOutput"]["additionalContext"]


def test_ptu_no_nudge_on_amend_or_empty_queue(tmp_path):
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit --amend"},
                 "tool_response": "ok"})
    assert r.stdout.strip() == ""


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


def test_ptu_no_nudge_on_empty_queue(tmp_path):
    """A non-amend git commit with clean output and empty queue should emit nothing."""
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s3",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit -m 'feat: y'"},
                 "tool_response": "1 file changed"})
    assert r.stdout.strip() == ""
    assert read_queue(tmp_path) == []


def test_session_start_initializes_and_summarizes(tmp_path):
    r = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                 "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    assert r.returncode == 0
    assert (tmp_path / ".robium" / "transcripts").is_dir()
    assert r.stdout.strip() == ""  # empty queue → silent
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s3", "cwd": str(tmp_path), "prompt": "no, wrong distro"})
    r2 = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                  "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    out = json.loads(r2.stdout)
    assert "1 pending" in out["hookSpecificOutput"]["additionalContext"]


def test_stop_nudge_throttles(tmp_path):
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s4", "cwd": str(tmp_path), "prompt": "no, wrong port"})
    r1 = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                  "cwd": str(tmp_path), "stop_hook_active": False})
    assert "pending" in r1.stdout
    r2 = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                  "cwd": str(tmp_path), "stop_hook_active": False})
    assert r2.stdout.strip() == ""  # throttled


def test_stop_nudge_respects_stop_hook_active(tmp_path):
    r = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                 "cwd": str(tmp_path), "stop_hook_active": True})
    assert r.stdout.strip() == "" and r.returncode == 0


def test_stop_nudge_window_pinned(tmp_path):
    # seed one flag so the nudge is eligible
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s5", "cwd": str(tmp_path), "prompt": "no, wrong topic name"})
    marker = tmp_path / ".robium" / ".last-nudge"
    ev = {"hook_event_name": "Stop", "session_id": "s5", "cwd": str(tmp_path),
          "stop_hook_active": False}
    # first nudge creates the marker
    assert "pending" in run_hook("stop_nudge.py", ev).stdout
    # inside the window (100s ago) → suppressed
    os.utime(marker, (time.time() - 100, time.time() - 100))
    assert run_hook("stop_nudge.py", ev).stdout.strip() == ""
    # outside the window (901s ago) → fires again
    os.utime(marker, (time.time() - 901, time.time() - 901))
    assert "pending" in run_hook("stop_nudge.py", ev).stdout


OBS_READY = """## costmap inflation missing <!-- id: obs-nav2-007 -->
status: ready
proof: 2
signal: wrong-guidance
sources: [lrn-1]
target: nav2#costmap-inflation (update) — robot hugs obstacles without inflation_layer
evidence: ✓ ✓ ✓
"""


def _seed_obs(tmp_path):
    d = tmp_path / "learnings" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(OBS_READY)


def test_ups_injects_recall_on_match(tmp_path):
    _seed_obs(tmp_path)
    r = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "why does the robot hug obstacles? costmap inflation maybe"})
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("[robium-recall]") and "obs-nav2-007" in ctx


def test_ups_capture_and_recall_coexist(tmp_path):
    _seed_obs(tmp_path)
    r = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "no, the costmap inflation obstacles fix was wrong"})
    assert read_queue(tmp_path)  # correction captured
    assert "obs-nav2-007" in r.stdout  # and recall injected


def test_ups_silent_when_no_match_or_marker(tmp_path):
    _seed_obs(tmp_path)
    r1 = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path), "prompt": "please write a launch file for the lidar"})
    assert r1.stdout.strip() == ""
    r2 = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "[robium-recall] costmap inflation obstacles"})
    assert r2.stdout.strip() == "" and read_queue(tmp_path) == []


def test_pre_compact_snapshots_queue(tmp_path):
    run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path), "prompt": "no, wrong distro again"})
    r = run_hook("pre_compact.py", {"hook_event_name": "PreCompact",
                 "session_id": "s9", "cwd": str(tmp_path), "trigger": "auto"})
    assert r.returncode == 0
    snap = tmp_path / ".robium" / "queue-precompact.jsonl"
    assert snap.exists()
    assert snap.read_text() == (tmp_path / ".robium" / "queue.jsonl").read_text()
