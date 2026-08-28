import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "hooks" / "scripts" / "gemini_hook.mjs"


def run_gemini(action: str, event: dict):
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
        "session_id": "gemini-session",
        "transcript_path": str(project / "session.json"),
        "cwd": str(project),
        "hook_event_name": name,
        "timestamp": "2026-08-27T12:00:00Z",
    }


def test_session_and_prompt_subprocess_capture_without_blocking(tmp_path):
    start = run_gemini("session-start", {
        **base_event(tmp_path, "SessionStart"), "source": "startup",
    })
    assert start.returncode == 0
    assert json.loads(start.stdout) == {}
    assert (tmp_path / ".robium" / "transcripts").is_dir()

    prompt = run_gemini("user-prompt-submit", {
        **base_event(tmp_path, "BeforeAgent"),
        "prompt": "no, use uv not pip for this environment",
    })
    assert prompt.returncode == 0
    assert json.loads(prompt.stdout) == {}
    assert queue(tmp_path)[0]["type"] == "user-correction"
    assert queue(tmp_path)[0]["session"] == "gemini-session"


def test_after_tool_maps_gemini_shell_payload(tmp_path):
    result = run_gemini("post-tool-use", {
        **base_event(tmp_path, "AfterTool"),
        "tool_name": "run_shell_command",
        "tool_input": {"command": "colcon build"},
        "tool_response": {
            "llmContent": "CMake Error at CMakeLists.txt:14",
            "returnDisplay": "build failed",
            "error": {"message": "command exited with code 1"},
        },
    })
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}
    flags = queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "error"
    assert flags[0]["command"] == "colcon build"


def test_session_end_archives_gemini_transcript_and_clears_seen(tmp_path):
    transcript = tmp_path / "session.json"
    transcript.write_text('{"role":"user","content":"hello"}\n', encoding="utf-8")
    seen = tmp_path / ".robium" / ".seen-gemini-session"
    seen.parent.mkdir(parents=True)
    seen.write_text("abc\n", encoding="utf-8")

    result = run_gemini("session-end", {
        **base_event(tmp_path, "SessionEnd"), "reason": "exit",
    })
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}
    archived = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__gemini-session.jsonl"
    assert archived.read_text(encoding="utf-8") == transcript.read_text(encoding="utf-8")
    assert not seen.exists()


def test_adapter_is_fail_open_for_malformed_input():
    result = subprocess.run(
        ["node", str(ADAPTER), "session-start"],
        input="not-json",
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_gemini_extension_layout_and_portable_hook_commands():
    manifest = json.loads((ROOT / "gemini-extension.json").read_text())
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
    assert manifest["name"] == "robium"
    assert (ROOT / "skills" / "architect" / "SKILL.md").is_file()
    agent = (ROOT / "agents" / "robium-architect.md").read_text()
    assert "name: robium-architect" in agent
    assert "tools: Read" not in agent
    for event in ("BeforeAgent", "AfterTool", "SessionStart", "SessionEnd"):
        assert event in hooks
    gemini_commands = [
        hook["command"]
        for event in hooks.values()
        for definition in event
        for hook in definition["hooks"]
        if hook.get("name", "").startswith("robium-gemini")
        or hook.get("name", "").startswith("robium-capture")
    ]
    assert len(gemini_commands) == 4
    assert all("${extensionPath}" in command and "${/}" in command for command in gemini_commands)
