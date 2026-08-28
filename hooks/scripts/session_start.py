#!/usr/bin/env python3
"""SessionStart hook: initialize `.robium/` silently and fail open."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    from robium_hooks import read_event, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    robium_dir(cwd)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
