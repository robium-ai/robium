import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "hooks" / "scripts" / "run_hook.sh"
MANIFEST = ROOT / "hooks" / "hooks.json"


def _shell():
    return shutil.which("sh") or shutil.which("bash")


def test_launcher_selects_interpreters_in_preference_order(tmp_path):
    shell = _shell()
    assert shell, "A POSIX shell is required for plugin hooks"

    def run_with(names):
        bindir = tmp_path / "bin"
        if bindir.exists():
            for child in bindir.iterdir():
                child.unlink()
        else:
            bindir.mkdir()
        for name in names:
            executable = bindir / name
            executable.write_text(f'#!/bin/sh\nprintf "%s:%s\\n" "{name}" "$*"\n')
            executable.chmod(0o755)
        posix_bindir = subprocess.run(
            [shell, "-c", "pwd"], cwd=bindir,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        env = os.environ.copy()
        env["PATH"] = posix_bindir
        return subprocess.run(
            [shell, str(RUNNER), str(ROOT / "hooks" / "scripts" / "session_start.py")],
            input="{}", capture_output=True, text=True, timeout=10, env=env,
        )

    assert run_with(("python3", "python", "py")).stdout.startswith("python3:")
    assert run_with(("python", "py")).stdout.startswith("python:")
    py = run_with(("py",))
    assert py.returncode == 0
    assert py.stdout.startswith("py:-3 ")


def test_launcher_is_silent_and_fail_open_without_interpreter(tmp_path):
    shell = _shell()
    assert shell, "A POSIX shell is required for plugin hooks"
    env = os.environ.copy()
    env["PATH"] = ""
    result = subprocess.run(
        [shell, str(RUNNER), str(ROOT / "hooks" / "scripts" / "session_start.py")],
        input="{}", capture_output=True, text=True, timeout=10, env=env,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_launcher_runs_real_hook(tmp_path):
    shell = _shell()
    assert shell, "A POSIX shell is required for plugin hooks"
    event = {"hook_event_name": "SessionStart", "session_id": "launcher",
             "cwd": str(tmp_path), "source": "startup"}
    result = subprocess.run(
        [shell, str(RUNNER), str(ROOT / "hooks" / "scripts" / "session_start.py")],
        input=json.dumps(event), capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert (tmp_path / ".robium" / "transcripts").is_dir()


def test_manifest_session_reminder_runs_for_codex_and_claude_roots(tmp_path):
    shell = _shell()
    assert shell, "A POSIX shell is required for plugin hooks"
    hooks = json.loads(MANIFEST.read_text())["hooks"]
    prompt_command = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
    start_command = hooks["SessionStart"][0]["hooks"][0]["command"]

    for variable in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        project = tmp_path / variable.lower()
        project.mkdir()
        env = os.environ.copy()
        env.pop("PLUGIN_ROOT", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env[variable] = str(ROOT)
        base = {"session_id": variable.lower(), "cwd": str(project)}

        prompt = subprocess.run(
            [shell, "-c", prompt_command],
            input=json.dumps({**base, "hook_event_name": "UserPromptSubmit",
                              "prompt": "no, use uv not pip"}),
            capture_output=True, text=True, timeout=10, env=env,
        )
        reminder = subprocess.run(
            [shell, "-c", start_command],
            input=json.dumps({**base, "hook_event_name": "SessionStart",
                              "source": "resume"}),
            capture_output=True, text=True, timeout=10, env=env,
        )

        assert prompt.returncode == 0 and prompt.stdout == ""
        context = json.loads(reminder.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "background subagent" in context
