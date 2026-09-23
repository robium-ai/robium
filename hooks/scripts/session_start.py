#!/usr/bin/env python3
"""SessionStart hook: initialize capture and emit a sparse learning reminder."""
import collections
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


DIRECT_SIGNALS = frozenset({
    "user-correction", "remember", "guardrail", "no-skill-fired",
})
REMINDER_FILE = "learning-reminder.json"


def substantial_flags(flags: list[dict]) -> list[dict]:
    """Return unprocessed signals worth interrupting a future session for."""
    pending = [
        flag for flag in flags
        if isinstance(flag, dict) and not flag.get("observation")
    ]
    repeated_errors = collections.Counter(
        flag.get("signature") for flag in pending
        if flag.get("type") == "error" and flag.get("signature")
    )
    return [
        flag for flag in pending
        if flag.get("type") in DIRECT_SIGNALS
        or (
            flag.get("type") == "error"
            and repeated_errors[flag.get("signature")] >= 2
        )
    ]


def _today() -> str:
    return datetime.date.today().isoformat()


def _already_reminded(directory: str, day: str) -> bool:
    path = os.path.join(directory, REMINDER_FILE)
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle).get("date") == day
    except Exception:
        return False


def _mark_reminded(directory: str, day: str, count: int) -> None:
    path = os.path.join(directory, REMINDER_FILE)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump({"date": day, "count": count}, handle)
        handle.write("\n")
    os.replace(tmp, path)


def _reminder_text(flags: list[dict]) -> str:
    counts = collections.Counter(str(flag.get("type") or "unknown") for flag in flags)
    summary = ", ".join(f"{kind}: {count}" for kind, count in sorted(counts.items()))
    return (
        f"Robium has {len(flags)} substantial unprocessed learning signal(s) "
        f"queued ({summary}). Briefly ask the user in commentary whether to run "
        "the Robium learning cycle in a background subagent, then continue the "
        "current task without waiting. Do not start the learning cycle without "
        "approval. If approved, delegate the learning-loop work to a subagent: "
        "review the evidence, absorb any ready reusable guidance into the owning "
        "skill or its references, delete absorbed/rejected observations, and leave "
        "only unresolved observations as local untracked files."
    )


def main() -> None:
    from robium_hooks import emit_context, read_event, read_flags, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    directory = robium_dir(cwd)
    # Compaction is not a new user session and must not create a mid-turn nudge.
    if event.get("source") == "compact" or event.get("is_background_agent"):
        return
    flags = substantial_flags(read_flags(cwd))
    day = _today()
    if not flags or _already_reminded(directory, day):
        return
    _mark_reminded(directory, day, len(flags))
    emit_context("SessionStart", _reminder_text(flags))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
