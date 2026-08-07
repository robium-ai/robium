#!/usr/bin/env python3
"""SessionStart hook — init .robium/ workspace; summarize pending flags."""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from robium_hooks import emit_context, read_event, read_flags, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    robium_dir(cwd)
    flags = read_flags(cwd)
    if not flags:
        return
    by_type = {}
    for f in flags:
        by_type[f.get("type", "?")] = by_type.get(f.get("type", "?"), 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(by_type.items(), key=lambda x: -x[1]))
    emit_context("SessionStart",
                 f"robium learning engine: {len(flags)} pending flag(s) in "
                 f".robium/queue.jsonl ({summary}). Promote to learnings/ at the "
                 "next natural break; see learnings/README.md (schema) or the "
                 "capture section of AGENTS.md.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
