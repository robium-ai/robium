---
name: learning-loop
version: 0.1.0
description: >
  The session-side surface of robium's learning engine: consolidate captured
  flags and learnings into evidence-counted observations, absorb ready
  observations into anchor-targeted skill-edit PRs via the deterministic
  delta pipeline, refine (prune/dedup/staleness) through the same pipeline,
  and report loop health. Use when: 'consolidate', 'absorb', 'run the loop',
  'update my skills', 'absorb these learnings', 'refine the skills',
  'learning loop status', end-of-block retros, promoting .robium/queue.jsonl
  flags, or drafting an absorb/refine PR. Everything before git merge may run
  autonomously; nothing lands on main skills/** without a human merge. Not
  for: mining external repos (mining), fresh skill authoring or the quality
  bar (skill-author), building robot applications (architect).
---

# Learning loop — consolidate, absorb, refine

The engine's session-side pipeline (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md
§5–§8). Capture happens automatically (plugin hooks); this skill turns what
was captured into observations, and observations into reviewable skill-edit
PRs. The human gate is git merge.

## When to use this skill

- Promoting queue flags and completing dated learnings entries ("consolidate",
  a Stop-hook nudge, end of a work block).
- Drafting skill edits from ready observations ("absorb", "update my skills",
  "run the loop") — output is always a PR branch, never a direct edit.
- Catalog hygiene passes ("refine the skills") — prune/dedup/staleness through
  the same delta pipeline, report-first.
- Loop health ("learning loop status"): queue depth, unabsorbed backlog,
  eval-suite size, ledger totals.
- For distilling external repos, use the mining skill; for authoring a new
  skill from scratch, skill-author.

## Key directives

- Delegation posture: **embed** — the workflows live here; the deterministic
  tools live at scripts/engine/ (apply_deltas.py, run_trigger_evals.py,
  ledger.py, mine_transcripts.py, skill_metrics.py, observations.py,
  placement.py) and in the plugin hooks (recall).
- **Scripts hold the pen.** <!-- id: scripts-hold-the-pen --> LLM roles draft
  deltas and diagnose; apply_deltas.py applies them (snapshot, bump,
  changelog, sidecars). Never hand-edit a skill during absorb; never bypass
  the script's refusals — a refusal is a design signal, not an obstacle.
- **Consolidation never touches skills/ content.** <!-- id: consolidate-write-surface -->
  Its write surface is learnings/, learnings/observations/, and the
  evidence/evals sidecars — that boundary is what makes it autonomous-safe.
- **Absorb consumes status: ready only.** <!-- id: absorb-ready-only --> The
  ready bar (proof ≥ 2 | user-correction | three-part evidence | external
  official) is enforced by the observations lint; do not absorb around it.
- **Merge is the gate.** <!-- id: merge-is-the-gate --> Every absorb/refine
  run ends in a PR with the evidence table; no agent merges to main
  skills/**. Mid-build sessions capture; they never edit skills directly.
- **Dedup against everything seen** <!-- id: dedup-against-rejected --> —
  including absorbed and rejected observations — or judged-rejected findings
  reappear forever.
- **One self-check round** <!-- id: one-self-check-round --> on consolidator
  and absorber output: re-read the draft against the source transcript
  window for misattribution, missed dead-ends, wrong anchors, before writing.

## Quick start

Consolidate (autonomous-safe), then absorb to a PR:

```bash
# status: what's pending?
wc -l .robium/queue.jsonl                 # flags
grep -rc "status: ready" learnings/observations/*.md
uv run scripts/engine/skill_metrics.py    # catalog health

# consolidate: promote flags + complete entries + merge into observations
# (LLM workflow — see Decision guidance; writes learnings/ + sidecars only)

# absorb: draft deltas from ready observations, then:
uv run scripts/engine/apply_deltas.py deltas.yaml --dry-run   # review the report
git checkout -b loop/absorb-$(date +%F)
uv run scripts/engine/apply_deltas.py deltas.yaml
uv run skills/skill-author/scripts/validate_skills.py
uv run scripts/engine/run_trigger_evals.py --skills <touched...> \
  --flip-gate-baseline archive/<skill>/<old-version> --flip-skill <skill>
gh pr create --title "loop: absorb <topic>" --body-file report.md
```

## Decision guidance

**Consolidate** (spec §6) — inputs: queue flags, miner output
(scripts/engine/mine_transcripts.py over .robium/transcripts/), unconsolidated
learnings entries; each resolved to its archived-transcript window and read in
full context. Steps: promote flags that clear the noise bar into schema-v2
entries (verbatim text preserved); complete hand-written entries (evidence,
skill tags, recurrence); merge into observations per the schema README's
merge-on-same-finding and evolve-don't-overwrite rules; increment ledgers
(scripts/engine/ledger.py) with sources; harvest eval cases (no-skill-fired →
triggers.positive of the right skill, misfires → triggers.negative); draft
the end-of-block retro for human sign-off; attribute successes (green blocks
credit helpful to the anchors whose guidance shaped the actions — best-effort,
neutral by default). Then the self-check round.

**Absorb** (spec §7.1) — on ready observations: branch loop/absorb-YYYY-MM-DD;
draft deltas feedback-conditioned (current SKILL.md + observation's symptom/
fix/dead-ends + smallest-edit directive + placement rule — run
scripts/engine/placement.py per finding); apply via apply_deltas.py; verify
(validator → trigger evals → flip gate); scoped dup check over touched skills;
PR with the evidence table (per edit: skill, anchor, op, observation link,
sources, eval results). See the delta-format reference for op semantics.

**Refine** — the five passes (see the refine-passes reference) re-armed on
ledgers: prune harmful>0 ∧ helpful=0 first; dedup seeds from
skill_metrics.py --dupes; staleness (90-day windows) unchanged; usage reads
retro lines; growth review reads the archive. Output: retire/move/annotate
deltas through the same pipeline → PR. Scoped refine after every absorb; full
refine ~monthly.

**Recall** runs without invocation (UserPromptSubmit hook): ready
observations matching the prompt inject as [robium-recall] context, citing
ids. A wrong recall is capture signal — name the id and correct it; the
consolidator counts it harmful.

## Platform gotchas

- apply_deltas refuses an op whose archive dir already exists — that means a
  prior run bumped without merging. Rebase/merge the pending PR first.
- The trigger-eval judge shells to the claude CLI; offline or in CI without
  a key, pass --no-llm for the deterministic fallback (results are then
  keyword-based — good for gating, weaker for judging close calls).
- evidence.yaml and evals.yaml are engine-written; hand-edits will be
  overwritten and break increment audit trails.

## Customization

- User tier (Phase 4): same modes with observations under .robium/ and the
  absorb destination an overlay under .claude/skills/ — the workflows are
  path-parameterized, nothing else changes.
- Eval-case harvest thresholds and the recall budget are constants in the
  hook scripts; tune per install, not per session.

## References

- `references/delta-format.md` — op semantics, deltas.yaml schema, refusal rules.
- `references/promotion-bar.md` — queue→facts→observations promotion criteria.
- `references/refine-passes.md` — the five hygiene passes, evidence-armed.
- `references/learnings-loop.md` — the pre-engine hardening process (history + the manual fallback).
- Engine tools (repo root): scripts/engine/ — apply_deltas.py,
  run_trigger_evals.py, ledger.py, mine_transcripts.py, skill_metrics.py,
  observations.py, placement.py.
- Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §5–§8, §10.

## Changelog

- 0.1.0 (2026-08-02): initial skill — consolidate/absorb/refine/status modes
  over the Phase 2b delta pipeline; absorbs skill-updater's promotion bar and
  skill-refiner's five passes as references (learning-engine Phase 2b, §13).
