#!/usr/bin/env python3
"""Verify external-observation citations against pinned clones (spec §6a.3).

Anti-hallucination rule, deterministic: every cited quote must exist at
repo@sha path#lines — a citation that doesn't grep is a discarded candidate.
stdlib only.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SOURCE_RE = re.compile(
    r"^(?P<org>[\w.-]+)/(?P<repo>[\w.-]+)@(?P<sha>[0-9a-f]{7,40})"
    r"\s+(?P<path>\S+)#L(?P<a>\d+)(?:-L(?P<b>\d+))?$")


def _norm(text):
    return " ".join((text or "").split())


def verify_entry(entry, repos_root):
    fields = entry.get("fields", {})
    if fields.get("origin") != "external":
        return None
    eid = entry.get("id", "?")
    m = _SOURCE_RE.match(fields.get("source", ""))
    if not m:
        return f"{eid}: unparseable source '{fields.get('source', '')}'"
    clone = os.path.join(repos_root, m.group("repo"))
    if not os.path.isdir(clone):
        return f"{eid}: clone not found at {clone}"
    try:
        blob = subprocess.run(
            ["git", "-C", clone, "show", f"{m.group('sha')}:{m.group('path')}"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as exc:
        return f"{eid}: git show failed: {(exc.stderr or '').strip()[:160]}"
    a = int(m.group("a"))
    b = int(m.group("b") or m.group("a"))
    region = "\n".join(blob.splitlines()[a - 1:b])
    if not fields.get("quote"):
        return f"{eid}: external entry has no quote"
    if _norm(fields["quote"]) not in _norm(region):
        return (f"{eid}: quote not found at {m.group('path')}"
                f"#L{a}-L{b} @ {m.group('sha')}")
    return None


def main(argv=None):
    from observations import parse_file

    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", required=True)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args(argv)
    checked, errs = 0, []
    for path in args.files:
        if os.path.basename(path) == "README.md":
            continue
        for entry in parse_file(path):
            if entry.get("fields", {}).get("origin") != "external":
                continue
            checked += 1
            err = verify_entry(entry, args.repos)
            if err:
                errs.append(err)
                print(f"FAIL: {err}")
            else:
                print(f"PASS: {entry['id']} — {entry['fields'].get('source', '')}")
    print(f"Verified {checked} external citation(s): {'FAIL' if errs else 'PASS'}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
