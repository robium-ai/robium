import json
from pathlib import Path

import mine_transcripts as mt


def _write_transcript(tmp_path, events):
    p = tmp_path / "proj__sess1.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return p


def _user(text, uuid="u1", sidechain=False):
    return {"type": "user", "uuid": uuid, "isSidechain": sidechain,
            "message": {"role": "user", "content": text}}


def _meta_user(text, uuid="u1"):
    return {"type": "user", "uuid": uuid, "isSidechain": False, "isMeta": True,
            "message": {"role": "user", "content": text}}


def _assistant_tooluse(tool_id, name, cmd, uuid="a1"):
    return {"type": "assistant", "uuid": uuid, "isSidechain": False,
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": tool_id, "name": name,
                 "input": {"command": cmd} if name == "Bash" else {"skill": cmd}}]}}


def _tool_result(tool_id, text, uuid="r1"):
    return {"type": "user", "uuid": uuid, "isSidechain": False,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": text}]}}


def test_mines_rejection_as_user_correction(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "rm -rf build/"),
        _tool_result("t1", "The user doesn't want to proceed with this tool use."),
        _user("don't delete build, just clean the one package", uuid="u9"),
    ])
    flags = mt.mine_file(str(p))
    rej = [f for f in flags if f["type"] == "user-correction"]
    assert rej and "clean the one package" in rej[0]["excerpt"]
    assert rej[0]["source"].startswith("transcript proj__sess1.jsonl#")


def test_mines_repeated_errors_with_count(tmp_path):
    err = "CMake Error at CMakeLists.txt:14"
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "colcon build", uuid="a1"),
        _tool_result("t1", err, uuid="r1"),
        _assistant_tooluse("t2", "Bash", "colcon build", uuid="a2"),
        _tool_result("t2", err, uuid="r2"),
    ])
    flags = mt.mine_file(str(p))
    errors = [f for f in flags if f["type"] == "error"]
    assert len(errors) == 1 and errors[0]["seen"] == 2


def test_single_error_not_flagged(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "colcon build"),
        _tool_result("t1", "CMake Error at CMakeLists.txt:14"),
    ])
    assert [f for f in mt.mine_file(str(p)) if f["type"] == "error"] == []


def test_no_skill_fired_detection(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("how do I tune the nav2 costmap so the robot stops hugging walls?"),
    ])
    flags = mt.mine_file(str(p))
    ns = [f for f in flags if f["type"] == "no-skill-fired"]
    assert ns and "costmap" in ns[0]["excerpt"]


def test_skill_loaded_suppresses_no_skill_fired(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Skill", "nav2"),
        _tool_result("t1", "Launching skill: nav2"),
        _user("how do I tune the nav2 costmap here?", uuid="u2"),
    ])
    assert [f for f in mt.mine_file(str(p)) if f["type"] == "no-skill-fired"] == []


def test_sidechain_messages_ignored(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("no, that's wrong — use BEST_EFFORT", sidechain=True),
    ])
    assert mt.mine_file(str(p)) == []


def test_meta_messages_ignored(tmp_path):
    """isMeta user turns (skill-load boilerplate etc.) must not be classified,
    even when their text happens to look correction-shaped."""
    p = _write_transcript(tmp_path, [
        _meta_user("no, use X not Y"),
    ])
    assert mt.mine_file(str(p)) == []


def test_miner_scrubs_before_truncation(tmp_path):
    """A secret straddling the excerpt's 400-char cut must still be scrubbed.

    Old ordering `scrub(text[:400])` truncates the RAW user-correction
    text to 400 chars first. This layout is sized so the cut lands mid-way
    through "API_KEY=supersecretvalue123" (only "API_KEY=supe" survives),
    which cannot match the KEY=value pattern's 6-char-value minimum in a
    way that redacts the true boundary — the fragment "API_KEY=sup" leaks
    verbatim. New ordering `scrub(text)[:400]` scrubs the full text first
    (matching the complete secret), then truncates the redacted output.
    """
    prefix = "no, use this approach instead: "
    secret = "API_KEY=supersecretvalue123"
    text = (prefix + "x" * 356 + " " + secret + " more trailing content after secret")
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "deploy.sh"),
        _tool_result("t1", "The user doesn't want to proceed with this tool use."),
        _user(text, uuid="u9"),
    ])
    flags = mt.mine_file(str(p))
    rej = [f for f in flags if f["type"] == "user-correction"]
    assert rej
    assert "API_KEY=sup" not in rej[0]["excerpt"]
    assert "supersecretvalue123" not in rej[0]["excerpt"]


def test_cli_writes_queue_and_report(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("no, use the humble image not jazzy"),
    ])
    queue = tmp_path / "queue.jsonl"
    report = tmp_path / "report.md"
    mt.main([str(p), "--queue", str(queue), "--report", str(report)])
    assert len(queue.read_text().splitlines()) == 1
    assert "user-correction" in report.read_text()


def test_block_list_user_text_classified(tmp_path):
    """Plain user text encoded as content block list should be classified."""
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "rm -rf build/"),
        _tool_result("t1", "The user doesn't want to proceed with this tool use."),
        {"type": "user", "uuid": "u2", "isSidechain": False,
         "message": {"role": "user", "content": [
             {"type": "text", "text": "no, use rclcpp not rclpy"}
         ]}},
    ])
    flags = mt.mine_file(str(p))
    rej = [f for f in flags if f["type"] == "user-correction"]
    assert rej and "rclcpp" in rej[0]["excerpt"]


def test_rejection_pairs_with_block_list_followup(tmp_path):
    """Rejection followed by block-list user text should pair correctly."""
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "colcon build --cmake-args -DCMAKE_CXX_STANDARD=20"),
        _tool_result("t1", "The user doesn't want to proceed with this tool use."),
        {"type": "user", "uuid": "u2", "isSidechain": False,
         "message": {"role": "user", "content": [
             {"type": "text", "text": "try the standard C++17 instead"}
         ]}},
        _user("what's the weather like tomorrow?", uuid="u3"),
    ])
    flags = mt.mine_file(str(p))
    corrections = [f for f in flags if f["type"] == "user-correction"]
    assert len(corrections) == 1
    assert "C++17" in corrections[0]["excerpt"]
    assert "weather" not in corrections[0]["excerpt"]


def test_report_dir_created(tmp_path):
    """CLI --report into nonexistent nested dir should succeed and create it."""
    p = _write_transcript(tmp_path, [
        _user("no, use the humble image not jazzy"),
    ])
    nested_report = tmp_path / "reports" / "deep" / "nested" / "report.md"
    queue = tmp_path / "queue.jsonl"
    mt.main([str(p), "--queue", str(queue), "--report", str(nested_report)])
    assert nested_report.exists()
    assert "user-correction" in nested_report.read_text()
