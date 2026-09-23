#!/usr/bin/env python3
"""UserPromptSubmit hook: silently capture candidate learning signals.

It never recalls or injects prior material. The separate SessionStart hook may
emit a once-daily count-only reminder when substantial signals have accumulated.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    from classify import classify_prompt, is_remember
    from robium_hooks import append_flag, excerpt, read_event
    from scrub import scrub

    event = read_event()
    prompt = event.get("prompt") or ""
    cwd = event.get("cwd") or ""
    if len(prompt) <= 500 or is_remember(prompt):
        hit = classify_prompt(prompt)
        if hit:
            append_flag(cwd, {
                "type": hit["type"],
                "confidence": hit["confidence"],
                "session": event.get("session_id", ""),
                "excerpt": excerpt(scrub(prompt)),
            })

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
