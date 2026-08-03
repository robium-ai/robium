#!/usr/bin/env python3
"""Offline transcript miner (spec §5): rejections, repeated errors, no-skill-fired.

Reads archived Claude Code session JSONL (.robium/transcripts/), emits queue
flags with transcript coordinates plus a human-readable report. stdlib only.
Usage: python3 scripts/engine/mine_transcripts.py FILES... [--queue Q] [--report R]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "hooks", "scripts"))

from classify import ROBOTICS_KEYWORDS, classify_prompt, error_signature, is_error_result  # noqa: E402
from scrub import scrub  # noqa: E402

REJECTION_MARKERS = ("doesn't want to proceed", "user rejected", "User rejected")
MIN_ERROR_COUNT = 2


def _iter_events(path):
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            yield json.loads(line)
        except Exception:
            continue


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if isinstance(block.get("content"), str):
                    parts.append(block["content"])
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
        return "\n".join(parts)
    return ""


def mine_file(path):
    base = os.path.basename(path)
    flags = []
    tool_uses = {}          # tool_use_id -> {"name", "input", "uuid"}
    error_counts = {}       # signature -> {"count", "command", "excerpt", "uuid"}
    skill_loaded = False
    pending_rejection = None

    for ev in _iter_events(path):
        if ev.get("isSidechain"):
            continue
        etype = ev.get("type")
        if etype == "user" and ev.get("isMeta"):
            continue
        msg = ev.get("message") or {}
        uuid = ev.get("uuid", "")

        if etype == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_uses[block.get("id")] = {"name": block.get("name"),
                                                  "input": block.get("input") or {},
                                                  "uuid": uuid}
                    if block.get("name") == "Skill":
                        skill_loaded = True

        elif etype == "user":
            content = msg.get("content")
            # tool results
            found_tool_result = False
            if isinstance(content, list):
                for block in content:
                    if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                        continue
                    found_tool_result = True
                    text = _text_of(block.get("content"))
                    tu = tool_uses.get(block.get("tool_use_id"), {})
                    if any(m in text for m in REJECTION_MARKERS):
                        pending_rejection = {"tool": tu.get("name", "?"),
                                             "command": (tu.get("input") or {}).get("command", ""),
                                             "uuid": uuid}
                    elif tu.get("name") == "Bash":
                        cmd = (tu.get("input") or {}).get("command", "")
                        if is_error_result(cmd, text):
                            sig = error_signature(cmd, text)
                            rec = error_counts.setdefault(
                                sig, {"count": 0, "command": cmd,
                                      "excerpt": text, "uuid": uuid})
                            rec["count"] += 1
                if found_tool_result:
                    continue
            # plain user prompt
            text = content if isinstance(content, str) else _text_of(content)
            if not text:
                continue
            if pending_rejection is not None:
                flags.append({
                    "type": "user-correction", "confidence": 0.9, "mined": True,
                    "excerpt": scrub(text)[:400],
                    "context": (f"rejected {pending_rejection['tool']}: "
                                + scrub(pending_rejection['command'])[:150]),
                    "source": f"transcript {base}#{uuid}",
                })
                pending_rejection = None
                continue
            hit = classify_prompt(text)
            if hit:
                flags.append({"type": hit["type"], "confidence": hit["confidence"],
                              "mined": True, "excerpt": scrub(text)[:400],
                              "source": f"transcript {base}#{uuid}"})
            elif not skill_loaded and any(k in text.lower() for k in ROBOTICS_KEYWORDS):
                flags.append({"type": "no-skill-fired", "confidence": 0.6, "mined": True,
                              "excerpt": scrub(text)[:400],
                              "source": f"transcript {base}#{uuid}"})

    for sig, rec in error_counts.items():
        if rec["count"] >= MIN_ERROR_COUNT:
            flags.append({"type": "error", "seen": rec["count"], "signature": sig,
                          "mined": True, "command": scrub(rec["command"])[:200],
                          "excerpt": scrub(rec["excerpt"])[-400:],
                          "source": f"transcript {base}#{rec['uuid']}"})
    return flags


def write_report(flags, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    by_type = {}
    for f in flags:
        by_type.setdefault(f["type"], []).append(f)
    lines = ["# Transcript mining report", ""]
    for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {t} ({len(items)})")
        for f in items:
            head = f.get("command") or f.get("excerpt", "")[:100]
            seen = f" (seen {f['seen']}x)" if f.get("seen") else ""
            lines.append(f"- {head}{seen} — {f['source']}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--queue", default=".robium/queue.jsonl")
    ap.add_argument("--report", default=".robium/mining-report.md")
    args = ap.parse_args(argv)

    all_flags = []
    for path in args.files:
        all_flags.extend(mine_file(path))
    os.makedirs(os.path.dirname(os.path.abspath(args.queue)), exist_ok=True)
    with open(args.queue, "a", encoding="utf-8") as q:
        for f in all_flags:
            q.write(json.dumps(f, ensure_ascii=False) + "\n")
    write_report(all_flags, args.report)
    print(f"mined {len(all_flags)} flags from {len(args.files)} transcript(s) "
          f"-> {args.queue}, report: {args.report}")


if __name__ == "__main__":
    main()
