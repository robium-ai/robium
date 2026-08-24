#!/usr/bin/env python3
"""PostToolUse(Bash) hook — flag error-bearing commands.

Capture only: the sole nudge channel is SessionStart, so this hook never
writes to stdout. Dedup: one flag per (command-head, error-signature) per
session. Fail-open.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _response_text(resp) -> str:
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        return "\n".join(str(resp.get(k) or "") for k in ("stdout", "stderr", "output", "error"))
    try:
        return json.dumps(resp)
    except Exception:
        return str(resp)


def main() -> None:
    from classify import error_signature, is_error_result
    from robium_hooks import append_flag, excerpt, read_event, robium_dir
    from scrub import scrub

    event = read_event()
    if event.get("tool_name") != "Bash":
        return
    cwd = event.get("cwd") or ""
    command = (event.get("tool_input") or {}).get("command", "")
    output = _response_text(event.get("tool_response"))

    if is_error_result(command, output):
        sig = error_signature(command, output)
        seen_path = os.path.join(robium_dir(cwd), f".seen-{event.get('session_id', 'na')}")
        seen = set()
        if os.path.exists(seen_path):
            seen = set(open(seen_path, encoding="utf-8").read().split())
        if sig not in seen:
            with open(seen_path, "a", encoding="utf-8") as f:
                f.write(sig + "\n")
            append_flag(cwd, {
                "type": "error",
                "session": event.get("session_id", ""),
                "command": excerpt(scrub(command), 200),
                "signature": sig,
                "excerpt": excerpt(scrub(output)[-2000:], 400),
            })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
