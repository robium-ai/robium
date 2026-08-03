#!/usr/bin/env python3
"""Observations tier (Tier 2) — parse + lint learnings/observations/*.md.

Schema: learnings/observations/README.md (spec §4.5 + §6a.3). stdlib only.
Exit contract mirrors the skill validator: FAIL lines, summary line, exit 0/1.
"""
import argparse
import os
import re
import sys

SIGNALS = frozenset([
    "wrong-guidance", "no-skill-fired", "figured-out-from-scratch",
    "better-method", "noise", "verified", "user-correction",
])
_ID_RE = re.compile(r"<!-- id: (obs-[a-z0-9-]+-\d{3}) -->\s*$")
_HEAD_RE = re.compile(r"^## (.+?)\s*<!-- id: ")
_FIELD_RE = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")
_STATUS_RE = re.compile(r"^(tentative|ready|absorbed \d{4}-\d{2}-\d{2}|rejected \(.+\))$")
_SOURCE_RE = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{7,40}\s+\S+#L\d+(-L\d+)?$")


def parse_file(path):
    entries, current, open_field = [], None, None
    for lineno, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if line.startswith("## "):
            m_id = _ID_RE.search(line)
            m_head = _HEAD_RE.match(line)
            current = {
                "id": m_id.group(1) if m_id else None,
                "title": m_head.group(1) if m_head else line[3:].strip(),
                "line": lineno,
                "fields": {},
            }
            entries.append(current)
            open_field = None
            continue
        if current is None:
            continue
        m = _FIELD_RE.match(line)
        if m:
            current["fields"][m.group(1)] = m.group(2).strip()
            open_field = m.group(1)
            continue
        if not line.strip():
            # Blank line: keep the open field alive (real entries never put
            # a blank line inside a continuation block, so nothing to append).
            continue
        if line[:1] in (" ", "\t") and open_field is not None:
            # Indented continuation of a multi-line field value (e.g. quote:).
            current["fields"][open_field] += "\n" + line.strip()
        else:
            open_field = None
    return entries


def _sources_list(value):
    value = (value or "").strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [s.strip() for s in value[1:-1].split(",") if s.strip()]


def _ready_ok(fields):
    try:
        proof = int(fields.get("proof", "0"))
    except ValueError:
        proof = 0
    evidence = fields.get("evidence", "")
    return (
        proof >= 2
        or fields.get("signal") == "user-correction"
        or evidence.count("✓") >= 3
        or (fields.get("origin") == "external" and "official" in evidence.lower())
    )


def lint_file(path, known_skills=None):
    errs = []
    stem = os.path.splitext(os.path.basename(path))[0]
    if known_skills is not None and stem not in known_skills and stem != "new-skills":
        errs.append(f"{path}: filename stem '{stem}' is not a known skill (or new-skills)")
    seen = set()
    for e in parse_file(path):
        where = f"{path}:{e['line']}"
        if not e["id"]:
            errs.append(f"{where}: heading missing '<!-- id: obs-{stem}-NNN -->'")
            continue
        if e["id"] in seen:
            errs.append(f"{where}: duplicate id '{e['id']}'")
        seen.add(e["id"])
        if not e["id"].startswith(f"obs-{stem}-"):
            errs.append(f"{where}: id '{e['id']}' prefix must match filename stem '{stem}'")
        f = e["fields"]
        for req in ("status", "proof", "signal", "sources", "target", "evidence"):
            if not f.get(req):
                errs.append(f"{where}: missing field '{req}'")
        if f.get("status") and not _STATUS_RE.match(f["status"]):
            errs.append(f"{where}: bad status '{f['status']}'")
        if f.get("signal") and f["signal"] not in SIGNALS:
            errs.append(f"{where}: bad signal '{f['signal']}'")
        if f.get("proof") and not f["proof"].isdigit():
            errs.append(f"{where}: proof must be an integer")
        if f.get("sources") and not _sources_list(f["sources"]):
            errs.append(f"{where}: sources must be a non-empty [list]")
        if f.get("status") == "ready" and not _ready_ok(f):
            errs.append(f"{where}: status ready but no ready-bar met "
                        "(proof>=2 | user-correction | 3x ✓ | external+official)")
        if f.get("origin") == "external":
            if not f.get("source") or not _SOURCE_RE.match(f.get("source", "")):
                errs.append(f"{where}: external entry needs source "
                            "'<org>/<repo>@<sha> <path>#L<a>[-L<b>]'")
            if not f.get("quote"):
                errs.append(f"{where}: external entry needs a verbatim quote")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="+", required=True)
    ap.add_argument("--skills-dir", default="skills")
    args = ap.parse_args(argv)
    known = None
    if os.path.isdir(args.skills_dir):
        known = {d for d in os.listdir(args.skills_dir)
                 if not d.startswith("_")
                 and os.path.exists(os.path.join(args.skills_dir, d, "SKILL.md"))}
    all_errs = []
    for path in args.check:
        if os.path.basename(path) == "README.md":
            continue
        all_errs.extend(lint_file(path, known))
    for e in all_errs:
        print(f"FAIL: {e}")
    n = len([p for p in args.check if os.path.basename(p) != "README.md"])
    print(f"Checked {n} observation file(s): {'FAIL' if all_errs else 'PASS'}")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
