#!/usr/bin/env python3
"""UserPromptSubmit hook: capture candidate signals without prompt injection.

Silent and fail-open. It may append a scrubbed queue flag; it never recalls,
renders, or injects observations, memory, reminders, or prior transcripts.
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
