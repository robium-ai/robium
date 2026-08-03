#!/usr/bin/env python3
"""Overlap/placement analyzer — which skill/anchor already covers this finding?

Deterministic keyword-overlap report over skill descriptions + anchored lines.
Used by mining (target selection, near-dup detection) and the Phase 2b
absorber/new-skill overlap analysis. stdlib only.
"""
import argparse
import math
import os
import re
import sys

_STOP = frozenset(
    "the a an and or of to in for with on is are be this that it as at by "
    "from use when not you your skill skills robium".split())
_ANCHOR_RE = re.compile(r"<!-- id: ([a-z0-9][a-z0-9-]*) -->")


def tokens(text):
    return {t for t in re.findall(r"[a-z0-9_]+", (text or "").lower())
            if len(t) > 2 and t not in _STOP}


def _frontmatter_description(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    out, in_desc = [], False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if re.match(r"^description:", line):
            in_desc = True
            out.append(line.split(":", 1)[1].strip().lstrip(">").strip())
        elif in_desc and (line.startswith(" ") or line.startswith("\t")):
            out.append(line.strip())
        elif in_desc:
            break
    return " ".join(x for x in out if x)


def load_catalog(skills_dir):
    catalog = {}
    for d in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, d, "SKILL.md")
        if d.startswith("_") or not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        anchors = {}
        for line in text.splitlines():
            m = _ANCHOR_RE.search(line)
            if m:
                anchors[m.group(1)] = line
        catalog[d] = {"description": _frontmatter_description(text),
                      "anchors": anchors}
    return catalog


def _score(q, t):
    if not q or not t:
        return 0.0
    return len(q & t) / (math.sqrt(len(q)) * math.sqrt(len(t)))


def analyze(text, skills_dir, top=5):
    q = tokens(text)
    catalog = load_catalog(skills_dir)
    skills, anchors = [], []
    for name, data in catalog.items():
        s = _score(q, tokens(data["description"]))
        if s > 0:
            skills.append((name, round(s, 3)))
        for aid, line in data["anchors"].items():
            a = _score(q, tokens(line))
            if a > 0:
                anchors.append((f"{name}#{aid}", round(a, 3)))
    skills.sort(key=lambda x: -x[1])
    anchors.sort(key=lambda x: -x[1])
    return {"skills": skills[:top], "anchors": anchors[:top]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--file")
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    text = args.text if args.text else open(args.file, encoding="utf-8").read()
    out = analyze(text, args.skills_dir, args.top)
    print("target skills:   " + (" · ".join(f"{n} {s}" for n, s in out["skills"]) or "(none)"))
    print("similar anchors: " + (" · ".join(f"{n} {s}" for n, s in out["anchors"]) or "(none)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
