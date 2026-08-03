#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Evidence ledger (spec §4.2) — per-skill evidence.yaml, engine-written only.

helpful++ on ✓/attributed successes; harmful++ on wrong-guidance,
user-corrections, misfires. Counters carry sources — every increment is
auditable back to a dated learning entry or observation.
"""
import argparse
import datetime
import os
import sys

import yaml

_HEADER = ("# evidence ledger — maintained by the learning engine; "
           "do not hand-edit (spec §4.2)\n")
FILENAME = "evidence.yaml"


def _path(skill_dir):
    return os.path.join(skill_dir, FILENAME)


def load(skill_dir):
    p = _path(skill_dir)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save(skill_dir, data):
    with open(_path(skill_dir), "w", encoding="utf-8") as f:
        f.write(_HEADER)
        yaml.safe_dump(data, f, sort_keys=True, allow_unicode=True)


def increment(skill_dir, anchor, kind, source, date=None):
    if kind not in ("helpful", "harmful"):
        raise ValueError(f"kind must be helpful|harmful, got {kind!r}")
    date = date or datetime.date.today().isoformat()
    data = load(skill_dir)
    entry = data.setdefault(anchor, {"helpful": 0, "harmful": 0, "sources": []})
    entry[kind] = int(entry.get(kind, 0)) + 1
    if kind == "helpful":
        entry["last_verified"] = date
    sources = entry.setdefault("sources", [])
    if source and source not in sources:
        sources.append(source)
    save(skill_dir, data)
    return entry


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--anchor", required=True)
    ap.add_argument("--kind", required=True, choices=["helpful", "harmful"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--date")
    args = ap.parse_args(argv)
    entry = increment(args.skill, args.anchor, args.kind, args.source, args.date)
    print(f"{args.anchor}: helpful={entry['helpful']} harmful={entry['harmful']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
