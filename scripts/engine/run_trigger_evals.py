#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Trigger evals + flip gate (spec §8 layers 2–3).

Judge: `claude -p` timeboxed at 30 s; ANY failure falls back to the
deterministic placement analyzer (spec §12). Blocking when eval cases
exist for a touched skill; skipped-and-said when none exist yet.

Note on flip_gate's determinism: The flip comparison uses _catalog_judge
(deterministic keyword-overlap scorer) for both the baseline and current
run. This avoids asymmetries in judge behavior (LLM timeouts, parsing
failures) that could cause flips to fire/clear based on judge availability
rather than description changes. Inside flip_gate, we re-score the current
run's cases against the baseline catalog to ensure both sides use the same
scoring method. This trades full judge fidelity in the gate for deterministic
regression detection.
"""
import argparse
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement  # noqa: E402

TIMEOUT_S = 30


def _load_cases(skill, skills_dir):
    path = os.path.join(skills_dir, skill, "evals.yaml")
    if not os.path.exists(path):
        return []
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    triggers = data.get("triggers") or {}
    cases = []
    for kind in ("positive", "negative"):
        for case in triggers.get(kind) or []:
            cases.append({"phrase": case["phrase"], "kind": kind,
                          "expected": case.get("expect", skill)})
    return cases


def judge(phrase, catalog, no_llm, timeout_s=TIMEOUT_S, skills_dir="skills"):
    if not no_llm:
        listing = "\n".join(f"{n}: {d['description'][:200]}"
                            for n, d in sorted(catalog.items()))
        prompt = ("You route user requests to exactly one skill. Skills "
                  f"(name: description):\n{listing}\nUser phrasing: "
                  f"'{phrase}'. Reply with ONLY the single best skill name.")
        try:
            out = subprocess.run(["claude", "-p", prompt],
                                 capture_output=True, text=True,
                                 timeout=timeout_s).stdout.lower()
            for name in sorted(catalog, key=len, reverse=True):
                if name in out:
                    return name
        except Exception:
            pass
    hits = placement.analyze(phrase, skills_dir)["skills"]
    return hits[0][0] if hits else ""


def run_skill(skill, skills_dir, no_llm, catalog_override=None):
    cases = _load_cases(skill, skills_dir)
    if not cases:
        return {"cases": [], "skipped": True}
    catalog = catalog_override or placement.load_catalog(skills_dir)
    out = []
    for c in cases:
        selected = judge(c["phrase"], catalog, no_llm, skills_dir=skills_dir)
        ok = (selected == skill) if c["kind"] == "positive" else (selected != skill)
        out.append({**c, "selected": selected, "pass": ok})
    return {"cases": out, "skipped": False}


def flip_gate(skill, skills_dir, baseline_dir, no_llm):
    cases = _load_cases(skill, skills_dir)
    if not cases:
        return []
    baseline_text = open(os.path.join(baseline_dir, "SKILL.md"),
                         encoding="utf-8").read()
    catalog = placement.load_catalog(skills_dir)
    baseline_catalog = dict(catalog)
    baseline_catalog[skill] = {
        "description": placement._frontmatter_description(baseline_text),
        "anchors": catalog.get(skill, {}).get("anchors", {}),
    }
    # Use _catalog_judge (deterministic keyword-overlap scorer) for both baseline
    # and current run. This avoids asymmetries in judge behavior (LLM timeouts,
    # parsing failures) that could cause flips to fire/clear based on judge
    # availability rather than description changes. No LLM calls in flip_gate.
    flips = []
    for case in cases:
        old_sel = _catalog_judge(case["phrase"], baseline_catalog)
        now_sel = _catalog_judge(case["phrase"], catalog)
        old_ok = (old_sel == skill) if case["kind"] == "positive" else (old_sel != skill)
        now_ok = (now_sel == skill) if case["kind"] == "positive" else (now_sel != skill)
        if old_ok and not now_ok:
            flips.append(case)
    return flips


def _catalog_judge(phrase, catalog):
    q = placement.tokens(phrase)
    best, best_s = "", 0.0
    for name, data in catalog.items():
        s = len(q & placement.tokens(data["description"]))
        s = s / (max(len(q), 1) ** 0.5)
        if s > best_s:
            best, best_s = name, s
    return best


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", nargs="+", required=True)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--flip-gate-baseline")
    ap.add_argument("--flip-skill")
    args = ap.parse_args(argv)

    # Validate flip gate flags: both required or neither
    if bool(args.flip_gate_baseline) != bool(args.flip_skill):
        print("flip gate NOT run: both --flip-gate-baseline and --flip-skill are required")
        return 1

    passed = failed = skipped = 0
    for skill in args.skills:
        res = run_skill(skill, args.skills_dir, args.no_llm)
        if res["skipped"]:
            skipped += 1
            print(f"{skill}: SKIPPED (no eval cases yet — say so in the PR)")
            continue
        for c in res["cases"]:
            ok = "PASS" if c["pass"] else "FAIL"
            print(f"{skill} [{c['kind']}] '{c['phrase']}' -> {c['selected']}: {ok}")
            passed, failed = passed + c["pass"], failed + (not c["pass"])
    flips = []
    if args.flip_gate_baseline and args.flip_skill:
        flips = flip_gate(args.flip_skill, args.skills_dir,
                          args.flip_gate_baseline, args.no_llm)
        for c in flips:
            print(f"FLIP: {args.flip_skill} [{c['kind']}] '{c['phrase']}' "
                  "passed on baseline, fails now — BLOCKING")
    print(f"Trigger evals: {passed} passed, {failed} failed, "
          f"{skipped} skipped-skills, {len(flips)} flips")
    return 1 if (failed or flips) else 0


if __name__ == "__main__":
    sys.exit(main())
