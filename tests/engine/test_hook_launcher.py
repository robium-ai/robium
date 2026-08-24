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


def test_manifest_routes_every_hook_through_launcher():
    data = json.loads(MANIFEST.read_text())
    commands = [hook["command"]
                for matchers in data["hooks"].values()
                for matcher in matchers
                for hook in matcher["hooks"]]

    assert len(commands) == 4
    assert all("run_hook.sh" in command for command in commands)
    assert all(not command.startswith("python3 ") for command in commands)
    for script in ("user_prompt_submit.py", "post_tool_use.py",
                   "session_start.py", "session_end.py"):
        assert sum(script in command for command in commands) == 1


def test_launcher_interpreter_preference_is_python3_python_then_py3():
    source = RUNNER.read_text()
    python3 = source.index("command -v python3")
    python = source.index("command -v python", python3 + 1)
    py = source.index("command -v py", python + 1)
    assert python3 < python < py
    assert 'exec py -3 "$script_path"' in source


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
