import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "hooks" / "scripts" / "cursor_hook.mjs"


def run_cursor(action: str, event: dict):
    return subprocess.run(
        ["node", str(ADAPTER), action],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def queue(project: Path):
    path = project / ".robium" / "queue.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def base_event(project: Path, name: str):
    return {
        "conversation_id": "cursor-session",
        "generation_id": "generation-1",
        "workspace_roots": [str(project)],
        "transcript_path": str(project / "session.jsonl"),
        "hook_event_name": name,
        "cursor_version": "1.7.0",
    }


def test_prompt_and_session_start_capture_without_blocking(tmp_path):
    start = run_cursor("session-start", {
        **base_event(tmp_path, "sessionStart"),
        "session_id": "cursor-session",
        "is_background_agent": False,
    })
    assert start.returncode == 0
    assert json.loads(start.stdout) == {}
    assert (tmp_path / ".robium" / "transcripts").is_dir()

    prompt = run_cursor("user-prompt-submit", {
        **base_event(tmp_path, "beforeSubmitPrompt"),
        "prompt": "no, use uv not pip for this environment",
        "attachments": [],
    })
    assert prompt.returncode == 0
    assert json.loads(prompt.stdout) == {"continue": True}
    assert queue(tmp_path)[0]["type"] == "user-correction"
    assert queue(tmp_path)[0]["session"] == "cursor-session"


def test_after_shell_execution_maps_cursor_payload(tmp_path):
    result = run_cursor("post-tool-use", {
        **base_event(tmp_path, "afterShellExecution"),
        "command": "colcon build",
        "cwd": str(tmp_path),
        "output": "CMake Error at CMakeLists.txt:14",
        "duration": 1234,
        "sandbox": False,
    })
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}
    flags = queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "error"
    assert flags[0]["command"] == "colcon build"


def test_session_end_archives_cursor_transcript(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text('{"role":"user","content":"hello"}\n', encoding="utf-8")
    result = run_cursor("session-end", {
        **base_event(tmp_path, "sessionEnd"),
        "session_id": "cursor-session",
        "reason": "completed",
    })
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}
    archived = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__cursor-session.jsonl"
    assert archived.read_text(encoding="utf-8") == transcript.read_text(encoding="utf-8")


def test_adapter_is_fail_open_for_malformed_input():
    result = subprocess.run(
        ["node", str(ADAPTER), "user-prompt-submit"],
        input="not-json",
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"continue": True}


def test_cursor_plugin_layout_uses_dedicated_native_hooks():
    manifest = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text())
    hooks = json.loads((ROOT / "hooks" / "cursor-hooks.json").read_text())
    assert manifest["name"] == "robium"
    assert manifest["skills"] == "./skills/"
    assert manifest["agents"] == "./agents/robium-architect.md"
    assert manifest["hooks"] == "./hooks/cursor-hooks.json"
    assert hooks["version"] == 1
    assert set(hooks["hooks"]) == {
        "beforeSubmitPrompt", "afterShellExecution", "sessionStart", "sessionEnd",
    }
    assert all(
        "cursor_hook.mjs" in definition["command"]
        for definitions in hooks["hooks"].values()
        for definition in definitions
    )
