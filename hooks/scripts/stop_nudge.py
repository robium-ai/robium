#!/usr/bin/env python3
"""Stop hook — throttled one-line nudge when flags are pending. Never blocks."""
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])

THROTTLE_S = 900


def main() -> None:
    from robium_hooks import count_flags, read_event, robium_dir

    event = read_event()
    if event.get("stop_hook_active"):
        return
    cwd = event.get("cwd") or ""
    n = count_flags(cwd)
    if n == 0:
        return
    marker = os.path.join(robium_dir(cwd), ".last-nudge")
    now = time.time()
    try:
        last = os.path.getmtime(marker)
    except OSError:
        last = 0.0
    if now - last < THROTTLE_S:
        return
    with open(marker, "w") as f:
        f.write(str(now))
    print(f"robium: {n} pending learning flag(s) — run a retro/promotion when convenient.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
