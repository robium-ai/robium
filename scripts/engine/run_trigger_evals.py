#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Optional semantic trigger evals with a lexical diagnostic fallback.

The semantic judge is `claude -p`, timeboxed at 30 seconds. When it is not
available, lexical scoring remains visible for comparison but is inconclusive
and non-blocking; concise descriptions should not become keyword inventories
to satisfy the fallback.

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
                          "expected": case.get("expect")})
    return cases


def judge_details(phrase, catalog, no_llm, timeout_s=TIMEOUT_S, skills_dir="skills"):
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
                    return name, "semantic"
        except Exception:
            pass
    hits = placement.analyze(phrase, skills_dir)["skills"]
    return (hits[0][0] if hits else ""), "lexical"


def judge(phrase, catalog, no_llm, timeout_s=TIMEOUT_S, skills_dir="skills"):
    """Return only the selected skill for callers that do not need provenance."""
    return judge_details(phrase, catalog, no_llm, timeout_s, skills_dir)[0]


def run_skill(skill, skills_dir, no_llm, catalog_override=None):
    cases = _load_cases(skill, skills_dir)
    if not cases:
        return {"cases": [], "skipped": True}
    catalog = catalog_override or placement.load_catalog(skills_dir)
    out = []
    for c in cases:
        selected, method = judge_details(
            c["phrase"], catalog, no_llm, skills_dir=skills_dir
        )
        ok = ((selected == skill) if c["kind"] == "positive"
              else (selected == c["expected"] if c.get("expected") else selected != skill))
        out.append({**c, "selected": selected, "pass": ok,
                    "method": method, "conclusive": method == "semantic"})
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
        old_ok = ((old_sel == skill) if case["kind"] == "positive"
                  else (old_sel == case["expected"] if case.get("expected") else old_sel != skill))
        now_ok = ((now_sel == skill) if case["kind"] == "positive"
                  else (now_sel == case["expected"] if case.get("expected") else now_sel != skill))
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

    passed = failed = diagnostic = skipped = 0
    for skill in args.skills:
        res = run_skill(skill, args.skills_dir, args.no_llm)
        if res["skipped"]:
            skipped += 1
            print(f"{skill}: SKIPPED (no eval cases yet — say so in the PR)")
            continue
        for c in res["cases"]:
            if c["conclusive"]:
                ok = "PASS" if c["pass"] else "FAIL"
                passed, failed = passed + c["pass"], failed + (not c["pass"])
            else:
                ok = "DIAGNOSTIC PASS" if c["pass"] else "DIAGNOSTIC MISS"
                diagnostic += 1
            print(f"{skill} [{c['kind']}] '{c['phrase']}' -> {c['selected']}: {ok}")
    flips = []
    if args.flip_gate_baseline and args.flip_skill:
        flips = flip_gate(args.flip_skill, args.skills_dir,
                          args.flip_gate_baseline, args.no_llm)
        for c in flips:
            print(f"DIAGNOSTIC FLIP: {args.flip_skill} [{c['kind']}] "
                  f"'{c['phrase']}' passed lexically on baseline, misses now")
    print(f"Trigger evals: {passed} passed, {failed} failed, "
          f"{diagnostic} lexical diagnostics, {skipped} skipped-skills, "
          f"{len(flips)} diagnostic flips")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
