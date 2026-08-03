#!/usr/bin/env python3
"""UserPromptSubmit hook — flag corrections/guardrails/remember/positive signals.

Silent: writes queue flags only, never stdout (spec §5). Fail-open.
Also injects recall context (spec §5) — the short loop.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from classify import classify_prompt, is_remember
    from recall import eligible, load_observations, match, render
    from robium_hooks import append_flag, emit_context, excerpt, read_event
    from scrub import scrub

    event = read_event()
    prompt = event.get("prompt") or ""
    cwd = event.get("cwd") or ""
    if prompt.startswith("[robium-recall]"):   # engine-injected content is never re-captured
        return

    if len(prompt) <= 500 or is_remember(prompt):
        hit = classify_prompt(prompt)
        if hit:
            append_flag(cwd, {
                "type": hit["type"],
                "confidence": hit["confidence"],
                "session": event.get("session_id", ""),
                "excerpt": excerpt(scrub(prompt)),
            })

    try:
        entries = [e for e in load_observations(cwd) if eligible(e)]
        text = render(match(prompt, entries))
        if text:
            emit_context("UserPromptSubmit", text)
    except Exception:
        pass  # recall is best-effort; capture must not be harmed by it


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
