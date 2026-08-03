#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Variant A/B harness — contested-edit experiments (spec §9).

A "variant" is a candidate deltas file for one skill. This module builds a
whole-catalog scratch copy per candidate (`build_variant`), applies the
candidate's deltas to it via the existing `apply_deltas.apply_file`, and
scores the result deterministically against the trigger-eval and
task-check runners (`score_variant`). Scores are ranked by the spec's
fitness ordering (`rank`): trigger pass-rate desc, then task pass-rate
desc (treating an unrun `None` as a non-discriminating tie, so it never
raises and never distinguishes two `None`s from each other), then token
count asc (leanness, the runtime analogue of the fitness formula). An
optional blind content judge (`blind_judge`) shells out to `claude -p`
with shuffled candidate labels; ANY failure (nonzero exit, timeout,
missing binary, unparseable reply) collapses to `None` — the CLI reports
"content judge: skipped (<reason>)" rather than fabricate a pick.

The engine only ever recommends; a human merges the PR that adopts a
variant (`archive_losers` preserves the roads not taken as branch points
under `archive/<skill>/variants/<date>/<name>/`, never the winner).

Branch-guard note: `apply_deltas.apply_file`'s non-dry-run path refuses to
write on `main`/`master` by shelling out to `git -C <parent-of-skills-dir>
branch --show-current` and failing OPEN (proceeds) if that git call itself
fails — e.g. because the workdir isn't a git repo at all. Every variant
built by this module lives under a scratch `workdir` (a fresh tempdir by
default) that is NOT a git repository, so that guard harmlessly no-ops
here; this is expected and correct, not a gap — the real guard already ran
when the *source* deltas file was authored/reviewed, and archiving/PR
review is the actual gate for what lands in the real skills/ tree.
"""
import argparse
import datetime
import functools
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apply_deltas  # noqa: E402
import run_task_checks  # noqa: E402
import run_trigger_evals  # noqa: E402

BLIND_JUDGE_TIMEOUT_S = 45
_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# A valid reply is the WHOLE reply resolving to a single letter, once
# surrounding whitespace, markdown emphasis (*/**), and one trailing
# sentence punctuation mark are stripped -- not merely a letter appearing
# anywhere in the text (a reply like "Candidate B is the best
# integration." must never parse as "C", the first letter of "Candidate").
_JUDGE_REPLY_RE = re.compile(r"^\s*\**([A-Za-z])\**\s*[.!]?\s*$")


class VariantBuildError(RuntimeError):
    """Raised when a candidate deltas file doesn't produce a scorable variant:
    apply_deltas refused at least one op, or applied zero ops (a no-op-only
    deltas file is a broken/inert candidate, not a scored one)."""


def build_variant(name, deltas_path, skills_dir, workdir):
    """Copy the whole skills tree to <workdir>/<name>/skills, apply the
    candidate deltas file to that copy, and return the copy's skills dir.

    Raises VariantBuildError if apply_deltas refused any op or applied
    none. A copy of the deltas file is staged alongside (<workdir>/<name>/
    deltas.yaml) so archive_losers can package it later without needing
    the original path kept around.

    On failure, the entire <workdir>/<name>/ tree (skills copy + staged
    deltas + apply_deltas' own archive snapshot dir) is removed before the
    exception is raised. This is load-bearing, not cosmetic: archive_losers
    later walks every non-winner subdirectory of the workdir and archives
    whatever it finds there as a "scored loser" — a broken/refused variant
    that only failed to build must leave no directory behind at all, or it
    would get archived as if it were a legitimately scored candidate (see
    Task 4 review finding — a broken candidate is not a scored one).
    """
    variant_dir = os.path.join(workdir, name)
    variant_skills = os.path.join(variant_dir, "skills")
    # Remove the ENTIRE <workdir>/<name> dir, not just skills/, before
    # building: apply_deltas snapshots its OWN archive dir under
    # <variant_dir>/archive on every build, and a stale archive/ left over
    # from a prior build on a reused workdir trips apply_deltas' archive-
    # slot refusal ("archive .../archive/<skill>/<version> exists") since
    # the fresh skills copy starts back at the same baseline version.
    if os.path.exists(variant_dir):
        shutil.rmtree(variant_dir)
    os.makedirs(variant_dir, exist_ok=True)
    shutil.copytree(skills_dir, variant_skills)
    shutil.copy(deltas_path, os.path.join(variant_dir, "deltas.yaml"))

    archive_dir = os.path.join(variant_dir, "archive")
    report = apply_deltas.apply_file(deltas_path, skills_dir=variant_skills,
                                     archive_dir=archive_dir)

    if report["refused"] or not report["applied"]:
        refused = report["refused"]
        shutil.rmtree(variant_dir, ignore_errors=True)
        if refused:
            raise VariantBuildError(
                f"variant {name!r} refused by apply_deltas: {refused}")
        raise VariantBuildError(
            f"variant {name!r} applied zero ops (noop-only deltas — "
            "not a scored candidate)")
    return variant_skills


def score_variant(name, skill, variant_skills_dir, baseline_skills_dir, no_llm,
                  with_tasks=False, repo_root="."):
    """Score one variant's catalog deterministically.

    Returns {"name", "triggers": {passed, failed, skipped}, "flips": int,
    "tasks": {passed, failed, skipped}|None, "tokens": int}. `tasks` stays
    None unless with_tasks=True AND the skill actually has evals.yaml
    `tasks:` fixtures — they're expensive (real subprocess runs), so
    scoring never runs them silently.
    """
    trig = run_trigger_evals.run_skill(skill, variant_skills_dir, no_llm)
    passed = sum(1 for c in trig["cases"] if c["pass"])
    failed = sum(1 for c in trig["cases"] if not c["pass"])
    triggers = {"passed": passed, "failed": failed, "skipped": trig["skipped"]}

    # flip_gate's baseline_dir is the SKILL'S OWN directory (it reads
    # <baseline_dir>/SKILL.md directly), not a skills_dir root — see
    # test_trigger_evals.py's own fixture.
    flips = run_trigger_evals.flip_gate(
        skill, variant_skills_dir, os.path.join(baseline_skills_dir, skill), no_llm)

    tasks = None
    if with_tasks:
        task_defs = run_task_checks.load_tasks(skill, variant_skills_dir)
        if task_defs:
            t_passed = t_failed = 0
            for task in task_defs:
                res = run_task_checks.run_task(task, repo_root)
                if res["pass"]:
                    t_passed += 1
                else:
                    t_failed += 1
            tasks = {"passed": t_passed, "failed": t_failed, "skipped": 0}

    md_path = os.path.join(variant_skills_dir, skill, "SKILL.md")
    text = open(md_path, encoding="utf-8").read() if os.path.exists(md_path) else ""
    tokens = len(text) // 4

    return {"name": name, "triggers": triggers, "flips": len(flips),
            "tasks": tasks, "tokens": tokens}


def _trigger_rate(entry):
    t = entry["triggers"]
    total = t["passed"] + t["failed"]
    return t["passed"] / total if total else 1.0  # no cases -> neutral, not penalized


def _task_rate(entry):
    t = entry.get("tasks")
    if t is None:
        return None
    total = t["passed"] + t["failed"]
    return t["passed"] / total if total else 1.0


def _compare(a, b):
    ta, tb = _trigger_rate(a), _trigger_rate(b)
    if ta != tb:
        return -1 if ta > tb else 1  # desc
    ka, kb = _task_rate(a), _task_rate(b)
    # Only discriminate on task rate when BOTH sides ran tasks; an unrun
    # None never out- or under-ranks anything on this axis (falls through
    # to tokens), and two Nones are trivially equal to each other too.
    if ka is not None and kb is not None and ka != kb:
        return -1 if ka > kb else 1  # desc
    toka, tokb = a["tokens"], b["tokens"]
    if toka != tokb:
        return -1 if toka < tokb else 1  # asc (leaner wins)
    return 0


def rank(scores):
    """Fitness ordering (spec §9): trigger pass-rate desc, task pass-rate
    desc (None never discriminates), tokens asc. Returns a new list; input
    is not mutated."""
    return sorted(scores, key=functools.cmp_to_key(_compare))


def blind_judge(observation_text, variant_texts, timeout_s=BLIND_JUDGE_TIMEOUT_S):
    """Ask `claude -p` to pick the best candidate skill-text for a finding,
    with variant names hidden behind shuffled single-letter labels (the
    mapping is recorded in the return value so the caller can translate
    back). ANY failure — missing binary, nonzero exit, timeout, or a reply
    that doesn't resolve to one of the offered labels — returns None. The
    caller is expected to report that as "content judge: skipped (...)",
    never fabricate a ranking from a failed call.
    """
    names = list(variant_texts.keys())
    if not names:
        return None
    shuffled = names[:]
    random.shuffle(shuffled)
    mapping = dict(zip(_LABELS, shuffled))  # label -> variant name

    listing = "\n\n".join(
        f"Candidate {label}:\n{variant_texts[name]}" for label, name in mapping.items())
    prompt = (
        f"Given this finding: {observation_text}. Which candidate skill-text "
        "integrates it most accurately and leanly? Reply the single letter.\n\n"
        f"{listing}"
    )
    try:
        proc = subprocess.run(["claude", "-p", prompt], capture_output=True,
                              text=True, timeout=timeout_s)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    raw_reply = (proc.stdout or "").strip()
    m = _JUDGE_REPLY_RE.match(proc.stdout or "")
    if not m:
        # unparseable reply: <raw_reply> -- caller reports this as
        # "content judge: skipped (...)", never fabricates a pick.
        return None
    label = m.group(1).upper()
    if label not in mapping:
        return None
    return {"pick": mapping[label], "label": label, "mapping": mapping,
            "raw_reply": raw_reply}


def archive_losers(skill, date, winner, variants_workdir, archive_dir):
    """Copy every losing variant's applied skill dir + staged deltas.yaml +
    scores.md into archive/<skill>/variants/<date>/<name>/ — the road not
    taken, kept as a branch point, never garbage-collected. The winner is
    never touched (it graduates through the normal absorb/PR path, not
    the variants archive). Returns the list of archived variant names.
    """
    archived = []
    if not os.path.isdir(variants_workdir):
        return archived
    for name in sorted(os.listdir(variants_workdir)):
        if name == winner:
            continue
        variant_dir = os.path.join(variants_workdir, name)
        if not os.path.isdir(variant_dir):
            continue
        dest = os.path.join(archive_dir, skill, "variants", date, name)
        os.makedirs(dest, exist_ok=True)

        skill_src = os.path.join(variant_dir, "skills", skill)
        if os.path.isdir(skill_src):
            shutil.copytree(skill_src, os.path.join(dest, "skill"), dirs_exist_ok=True)

        deltas_src = os.path.join(variant_dir, "deltas.yaml")
        if os.path.exists(deltas_src):
            shutil.copy(deltas_src, os.path.join(dest, "deltas.yaml"))

        scores_src = os.path.join(variant_dir, "scores.md")
        if os.path.exists(scores_src):
            shutil.copy(scores_src, os.path.join(dest, "scores.md"))

        archived.append(name)
    return archived


def _fmt_triggers(t):
    if t["skipped"]:
        return "skipped"
    return f"{t['passed']}/{t['passed'] + t['failed']}"


def _fmt_tasks(t):
    if t is None:
        return "—"
    return f"{t['passed']}/{t['passed'] + t['failed']}"


def _write_scores_md(path, score):
    lines = [
        f"# scores: {score['name']}",
        "",
        f"- triggers: {_fmt_triggers(score['triggers'])}",
        f"- flips: {score['flips']}",
        f"- tasks: {_fmt_tasks(score['tasks'])}",
        f"- tokens: ~{score['tokens']}",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


_OBS_ID_RE = re.compile(r"^obs-(.+)-\d{3}$")


def _load_observation_text(observation_id, repo_root):
    """Best-effort lookup of the observation's actual text from
    learnings/observations/<stem>.md by anchor id; falls back to the raw
    observation id string (still a usable, if terse, judge prompt input)
    when the file/anchor can't be found."""
    m = _OBS_ID_RE.match(observation_id or "")
    if not m:
        return observation_id or ""
    path = os.path.join(repo_root, "learnings", "observations", f"{m.group(1)}.md")
    if not os.path.exists(path):
        return observation_id
    lines = open(path, encoding="utf-8").read().splitlines()
    marker = f"<!-- id: {observation_id} -->"
    for i, line in enumerate(lines):
        if marker in line:
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip():
                block.append(lines[j])
                j += 1
            return "\n".join(block)
    return observation_id


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--with-tasks", action="store_true")
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--archive-losers", action="store_true")
    ap.add_argument("--winner", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--archive-dir", default="archive")
    args = ap.parse_args(argv)

    with open(args.spec, encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}
    skill = spec["skill"]
    observation = spec.get("observation", "")
    variants_spec = spec.get("variants") or []

    workdir = args.workdir or tempfile.mkdtemp(prefix="robium-variants-")
    os.makedirs(workdir, exist_ok=True)

    scores = []
    variant_texts = {}
    build_errors = []

    baseline_score = score_variant("baseline", skill, args.skills_dir, args.skills_dir,
                                   args.no_llm, with_tasks=args.with_tasks,
                                   repo_root=args.repo_root)
    scores.append(baseline_score)
    # No scores.md staged for "baseline" — it's the current catalog, never
    # a candidate archive_losers would package.
    baseline_md = os.path.join(args.skills_dir, skill, "SKILL.md")
    if os.path.exists(baseline_md):
        variant_texts["baseline"] = open(baseline_md, encoding="utf-8").read()

    for v in variants_spec:
        name = v["name"]
        try:
            variant_dir = build_variant(name, v["deltas"], args.skills_dir, workdir)
        except VariantBuildError as exc:
            build_errors.append((name, str(exc)))
            continue
        sc = score_variant(name, skill, variant_dir, args.skills_dir, args.no_llm,
                           with_tasks=args.with_tasks, repo_root=args.repo_root)
        scores.append(sc)
        md_path = os.path.join(variant_dir, skill, "SKILL.md")
        if os.path.exists(md_path):
            variant_texts[name] = open(md_path, encoding="utf-8").read()
        _write_scores_md(os.path.join(workdir, name, "scores.md"), sc)

    ranked = rank(scores)

    judge_result = None
    judge_skip_reason = None
    if args.no_llm:
        judge_skip_reason = "--no-llm"
    elif len(variant_texts) < 2:
        judge_skip_reason = "fewer than two candidate texts to compare"
    else:
        obs_text = _load_observation_text(observation, args.repo_root)
        judge_result = blind_judge(obs_text, variant_texts)
        if judge_result is None:
            judge_skip_reason = "unavailable, timed out, or reply didn't resolve to a candidate"

    print("| variant | triggers | flips | tasks | ~tokens | judge pick |")
    print("|---|---|---|---|---|---|")
    for sc in scores:
        pick = "yes" if judge_result and judge_result["pick"] == sc["name"] else ""
        print(f"| {sc['name']} | {_fmt_triggers(sc['triggers'])} | {sc['flips']} "
              f"| {_fmt_tasks(sc['tasks'])} | {sc['tokens']} | {pick} |")

    if judge_result is not None:
        print(f"\ncontent judge: picked {judge_result['pick']} "
              f"(label {judge_result['label']}, raw reply: \"{judge_result['raw_reply']}\")")
    elif judge_skip_reason:
        print(f"\ncontent judge: skipped ({judge_skip_reason})")

    for name, msg in build_errors:
        print(f"\nvariant {name} build failed: {msg}")

    recommendation = ranked[0]["name"] if ranked else "baseline"
    print(f"\nrecommendation: {recommendation} (engine ranks; the human picks by merging)")

    if args.archive_losers:
        winner = args.winner or recommendation
        date = args.date or spec.get("date") or datetime.date.today().isoformat()
        archive_losers(skill, date, winner, workdir, args.archive_dir)

    return 0  # scores are information, not gates — always exit 0


if __name__ == "__main__":
    sys.exit(main())
