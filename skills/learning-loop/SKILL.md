---
name: learning-loop
version: 1.0.0
description: >
  Robium's explicit learning engine: consolidate capture-only queue flags and
  transcript evidence into observations; absorb ready observations through
  deterministic anchor-targeted skill deltas; refine, A/B contested edits,
  deep-verify examples, prune landed transcript evidence, and report loop
  health. Use when: "consolidate", "absorb", "run the loop", "update my
  skills", "refine the skills", "learning loop status", "A/B this edit",
  "deep verify", or "clean transcripts". Never recalls or injects observations
  into new prompts. Not for external-repo mining, fresh skill authoring, or app
  implementation.
---

# Learning loop: capture, consolidate, absorb, retain

Robium captures possible signals silently and preserves enough transcript
evidence to evaluate them later. Consolidation and absorption happen only when
invoked or at a natural milestone; nothing from memory, observations, or the
queue is inserted into a new prompt automatically.

## When to use this skill

- Consolidating the .robium queue, archived transcript windows, and dated
  learnings into evidence-counted observations.
- Absorbing `status: ready` observations into versioned skill deltas.
- Refining skill content for duplication, staleness, harmful guidance, or
  growth through the same deterministic pipeline.
- Running blind delta variants for a genuinely contested edit, or deep-verifying
  a pinned example fixture.
- Reporting queue/backlog/eval/ledger health or pruning transcript evidence
  after linked changes have landed.
- Route external repository research to `mining`; route fresh skill creation
  and direct-edit quality mechanics to `skill-author`.

## Key directives

- **Delegation posture: embed.** This skill owns the workflows; deterministic
  mechanics live in the repository's scripts/engine directory and capture
  hooks live under the repository's hooks directory.
- **Capture only, never recall.** `UserPromptSubmit` may append a flag and
  `SessionEnd` may archive a transcript; `SessionStart` is silent. Hooks must
  never inject queue reminders, observations, memory, or recall text into a
  prompt.
- **Batch bookkeeping at natural milestones.** Do not interrupt implementation
  for a manual learning entry or mandatory per-skill retro. Hooks quarantine
  candidates; consolidation promotes useful signals and discards noise in one
  batch.
- **Consolidation never touches skill content.** Its write surface is
  the repository's learnings tree, observations tier, and evidence/eval
  sidecars.
- **Scripts hold the pen during absorb/refine.** Draft anchor-targeted deltas;
  use `apply_deltas.py` for archive, version, content, and changelog mechanics.
  Never bypass a refusal. A separately requested direct skill edit still uses
  the same archive/version/changelog/validation quality bar.
- **Absorb consumes `status: ready` only.** Read the source transcript window,
  apply the promotion bar, deduplicate against tentative/ready/absorbed/rejected
  observations, and perform one attribution/evidence self-check.
- **Review route depends on current authority.** External contributors,
  unattended automation, and unrequested absorption use a branch, PR, and human
  merge. A maintainer may explicitly authorize local direct-main work in the
  current conversation; that removes only the branch/PR ceremony, never the
  archive, evidence, version, changelog, eval, or validation requirements.
- **Preserve evidence until it is no longer needed.** A transcript linked by a
  pending queue flag or tentative/ready observation cannot be pruned. Once all
  linked observations are absorbed or rejected and the corresponding change
  has landed, prune it deterministically. Unreferenced transcripts expire after
  14 days; the archive size ceiling is only the final safeguard.
- **Variants are deltas, never full-file rewrites.** A candidate refused by
  `apply_deltas.py` is broken, not a contender.

## Quick start

Inspect loop health without changing anything:

```bash
wc -l .robium/queue.jsonl
rg -l '^status: ready' learnings/observations
uv run scripts/engine/skill_metrics.py
uv run scripts/engine/prune_transcripts.py --dry-run
```

After batched consolidation, absorb ready observations:

```bash
uv run scripts/engine/apply_deltas.py learnings/deltas/<file>.yaml --dry-run
uv run scripts/engine/apply_deltas.py learnings/deltas/<file>.yaml
uv run skills/skill-author/scripts/validate_skills.py
uv run scripts/engine/run_trigger_evals.py --skills <touched...> \
  --flip-gate-baseline archive/<skill>/<old-version> --flip-skill <skill>
```

For the default reviewed route, create the branch before applying and open a PR
with the evidence table. Under an explicit maintainer direct-main instruction,
apply and verify on local `main`, then commit there. Neither route authorizes a
push, merge, deployment, publication, or paid action that was not requested.

After the absorb/refine change has landed and observation statuses are terminal:

```bash
uv run scripts/engine/prune_transcripts.py --dry-run
uv run scripts/engine/prune_transcripts.py --apply
```

## Decision guidance

### Consolidate

Read each queue candidate in its archived transcript window. Promote only flags
that name a real signal and have enough context to say what was expected and
what happened; discard shell noise, false positives, and context-free fragments.
Complete evidence fields where the transcript supports them, merge on the same
finding, preserve recurrence, and harvest trigger cases. Missing proof stays
tentative. A user correction is the strongest single-observation signal, but it
still needs accurate attribution and a useful proposed fix.

Consolidation is intentionally batched. A compact milestone summary is useful;
a ritual line for every skill that merely loaded is not required. Record a clean
result only when it adds evidence, such as a non-trivial example working exactly
as documented.

### Absorb

For each ready observation, choose the lowest owning skill and the smallest edit
that carries the knowledge. Prefer updating an existing anchor to adding a
bullet, and adding a bullet to creating a section. Draft a delta from the
observation's symptom, fix, dead ends, anchors, and source evidence; preview it;
apply through the engine; run validator, trigger evals, flip gate, task checks as
applicable, and a scoped duplicate check. The review artifact or direct-main
commit should include the same evidence table and verification results.

### Refine

Run the five evidence-armed hygiene passes from the refine reference: harmful
guidance first, duplication, staleness, usage/trigger fitness, then growth.
Produce deltas through the normal pipeline. A scoped pass follows absorption;
a catalog-wide pass is periodic, not an interruption to every build.

### Experiment

For a contested structural or trigger edit, draft two or three small DELTA
variants plus the baseline. `run_variants.py` applies each to an isolated
catalog, runs deterministic trigger/task/token scoring, and may ask a blind
judge when configured. The printed recommendation is evidence for the human,
not permission for unattended selection or merge.

### Deep-verify

`deep_verify.py --inventory` lists unverified examples and fixture coverage.
Running it executes only configured task fixtures; a pass emits an annotation
delta, while a failure remains a finding. Promotion still goes through the same
apply/validation/review route.

### Transcript retention

`prune_transcripts.py` reports every keep/delete decision and defaults to a dry
run. It protects queue-linked evidence and any transcript tied to a nonterminal
or not-yet-consolidated learning. It deletes terminal linked evidence only when
all linked observations are absorbed/rejected, and otherwise deletes only
unreferenced files older than 14 days. Review the report before `--apply`.

## Platform gotchas

- Capture flags are pointers, not conclusions. Command failures often contain
  expected probes or path misses and should be discarded when they teach
  nothing.
- `apply_deltas.py` refuses an existing archive slot; resolve the prior pending
  change rather than overwriting history.
- Trigger judging may use an external model. In offline CI, use the documented
  deterministic/no-LLM path and report that limitation.
- Transcript references must retain the exact archive filename and source ID;
  vague prose cannot be protected or cleaned deterministically.
- The archive size ceiling can remove old evidence under pressure. Normal
  operation should keep the archive below that point through status-aware
  cleanup rather than relying on the ceiling.

## Customization

- **Contributor/unattended mode:** always use the branch/PR/human-review route.
- **Explicit maintainer mode:** local direct-main is allowed only when the
  current conversation says so; do not persist that authority into future work.
- **User-local learning:** path-parameterize observations and deltas into a
  user overlay, but retain capture-only prompts and the same promotion bar.
- **Retention window:** keep 14 days as the default. A different window is an
  explicit repository policy choice and must never weaken pending-evidence
  protection.

## References

- `references/delta-format.md` - delta schema, operations, and refusals.
- `references/promotion-bar.md` - queue to learning to observation to delta.
- `references/refine-passes.md` - five evidence-armed hygiene passes.
- `references/learnings-loop.md` - historical/manual fallback context.
- `references/experiment-recipes.md` - small-variant evaluation recipes.
- Engine tools in the repository's scripts/engine directory: apply_deltas,
  run_trigger_evals, observations, placement, run_variants, deep_verify,
  run_task_checks, skill_metrics, mine_transcripts, and prune_transcripts.

## Changelog

- 1.0.0 (2026-08-27): remove recall and all prompt injection; make hooks
  capture-only and SessionStart silent; batch consolidation instead of immediate
  bookkeeping/mandatory retros; add evidence-aware transcript retention; and
  document the explicit maintainer direct-main exception while preserving all
  quality gates.
- 0.2.1 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 0.2.0 (2026-08-02): add experiment and deep-verify modes and their engine tools.
- 0.1.1 (2026-08-02): document the learnings/deltas location convention.
- 0.1.0 (2026-08-02): initial consolidate/absorb/refine/status pipeline.
