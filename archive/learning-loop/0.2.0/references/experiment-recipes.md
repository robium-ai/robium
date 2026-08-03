# Experiment recipes — variant A/B and contrastive rollouts

Two ways to resolve a contested or structural edit when a single draft
isn't obviously right (spec §9): variant A/B (default — cheap, mechanical,
run whenever the trigger fires) and contrastive rollouts (expensive —
reserved for high-stakes questions). Both end the same way: the engine
scores and recommends, a human picks by merging. The SKILL.md's Decision
guidance states the trigger and the posture; this file is the how.

## Worked walkthrough: variant A/B

Say an absorb pass has a contested description rewrite for nav2 — two
plausible ways to fold in a new observation about costmap inflation, and
it's not obvious which reads better without losing trigger coverage. Draft
2–3 feedback-conditioned DELTA variants against the observation (never
full-file rewrites, per variants-are-deltas), each its own deltas file in a
scratch location (throwaway drafts while iterating don't need the
dated-topic naming the delta-format reference describes for committed
deltas):

```yaml
# spec.yaml
skill: nav2
observation: obs-nav2-007
date: 2026-08-05        # optional — --archive-losers date fallback if --date is omitted
variants:
  - name: A
    deltas: variant-a.yaml
  - name: B
    deltas: variant-b.yaml
  - name: C
    deltas: variant-c.yaml
```

Each deltas: path is copied as-is (shutil.copy, no join against spec.yaml's
own location) — it resolves against the invoking shell's cwd, not against
spec.yaml's directory, so a bare filename like variant-a.yaml only resolves
when the command is run from the directory holding it; get the cwd wrong
and the harness fails with a plain FileNotFoundError, not a harness-level
message. Each variant file is an ordinary deltas file (same schema as any
absorb batch — see the delta-format reference) touching just the contested
anchor or section. Run the harness:

```bash
uv run scripts/engine/run_variants.py spec.yaml --skills-dir skills \
  --with-tasks --workdir /tmp/nav2-experiment
```

The harness copies the whole skills tree once per candidate into the
workdir, applies that candidate's deltas to the copy via the same
apply_deltas machinery absorb uses, and scores what comes out
deterministically — no LLM required unless the blind judge runs too. A
candidate never reaches scoring, and is reported as a build failure rather
than a contender with a bad score, in either of two cases: apply_deltas
refuses one of its ops outright (dropped anchor id, an already-taken
archive slot, a cap breach) — "variant 'A' refused by apply_deltas:
[...]"; or every op in the deltas file is a no-op (e.g. an add op naming a
section that doesn't exist — missing-section is a no-op, not a refusal)
and nothing gets applied at all — "variant 'A' applied zero ops (noop-only
deltas — not a scored candidate)". An implicit baseline row — the skill
exactly as it stands now — is always scored too, so the table always
answers whether any variant beat doing nothing.

--with-tasks opts into running the skill's evals.yaml task-check fixtures
too (real subprocess runs, never triggered silently by default — reach for
it when the observation is about behavior a task check exercises, not just
trigger phrasing). No evals.yaml tasks: means the tasks column reads "—"
even with --with-tasks on — no fixtures to run, not a skip.

### Reading the score table

The command prints an already-valid markdown table straight to stdout,
unpadded (single space around each pipe, no column alignment) — paste it
into the PR body as printed, don't hand-realign the columns:

```
| variant | triggers | flips | tasks | ~tokens | judge pick |
|---|---|---|---|---|---|
| baseline | 4/4 | 0 | 2/2 | 210 |  |
| A | 4/4 | 0 | 2/2 | 195 | yes |
| B | 3/4 | 1 | 2/2 | 180 |  |

recommendation: A (engine ranks; the human picks by merging)
```

- **triggers** — passed/total positive+negative trigger-eval cases (or
  "skipped" if the eval suite is empty).
- **flips** — previously-passing trigger cases the variant now fails,
  relative to the pre-experiment baseline. Non-zero is a real regression
  signal — read it before trusting a good trigger rate alone.
- **tasks** — passed/total task-check fixtures, populated only with
  --with-tasks and only when the skill has them; "—" otherwise (no
  fixtures ran, not "not applicable").
- **~tokens** — SKILL.md's character count divided by four, the runtime
  stand-in for the fitness formula's leanness term.
- **judge pick** — "yes" on the row the blind judge favored, if it ran
  (below); blank means not picked, not failed.

Fitness ordering (spec §9, exactly what the ranking computes): trigger
pass-rate descending first, then task pass-rate descending as a tiebreaker
(an unrun None neither gains nor loses on this axis — it falls through to
the next one), then token count ascending last — the leanest surviving
candidate wins ties. The printed recommendation line is exactly that
ranking's top row: information, not a decision — nothing about it changes
a file. The human reads the table, picks the variant they trust (often but
not always the recommendation — flips and judge pick are legitimate
reasons to override it), and merges that variant's deltas file through the
normal absorb path (apply_deltas → validator → trigger evals → PR), as if
it had been drafted as a single observation from the start.

### The blind content judge

Two independent conditions each skip the judge before it ever shells out,
with their own printed reason: --no-llm on the command line ("content
judge: skipped (--no-llm)"), or fewer than two candidate texts to compare
("content judge: skipped (fewer than two candidate texts to compare)").
Only when neither applies does the harness shell out to the claude CLI
with every candidate's resulting SKILL.md text behind shuffled
single-letter labels (the observation text is looked up by matching
spec.yaml's observation: field, e.g. obs-nav2-007, against its anchor
comment in learnings/observations/nav2.md — the stem before the trailing
-NNN names the file — falling back to the raw id string if no match is
found). This is a genuine second opinion on content quality — does a
phrasing actually integrate the finding, or just avoid breaking triggers —
that the deterministic scores can't answer. A third, independent failure
mode collapses to the same no-pick outcome (missing claude binary, nonzero
exit, timeout, an unparseable reply); the CLI prints "content judge:
skipped (<reason>)" rather than fabricate a preference either way. A
skip means no opinion, not evidence against every candidate.

### Archiving the losers

Once a winner is picked and merged, run the harness again with
--archive-losers --winner A (name it explicitly — omitting --winner
defaults to the harness's own recommendation, which may not be the
variant actually merged, archiving the wrong set as losers). There's no
resume: this second invocation rebuilds and rescores every candidate from
scratch just like the first — reusing the same --workdir is safe (each
variant's subdirectory is fully cleared and rebuilt, not appended to) and
convenient for tidiness; add --no-llm too, since the content judge's
opinion already did its job the first time. Every non-winning variant's
applied skill directory, staged
deltas file, and score summary land under an archive path scoped to
skill/date/variant — branch points to revisit later (the archive is where
roads-not-taken live, not a trash can), never garbage-collected. The
winner itself is never copied there; it graduates through the ordinary
absorb archive snapshot apply_deltas takes on every version bump.

## Contrastive rollouts (reserved, recipe-only)

Variant A/B scores content — trigger phrasing, task-fixture pass/fail,
leanness. It never watches an agent use the guidance to build something.
Contrastive rollouts do: N parallel agents attempt the same scripted app
task, once with a candidate variant's guidance in place and once without
(or against a competing variant); the pass-vs-fail diff across those runs
is distilled into observations — findings about where the guidance
actually changed agent behavior, not a score table. Expensive (N full task
attempts per side, not one cheap harness run) and reserved for genuinely
high-stakes calls: standing up a new skill's structure from scratch, or a
disputed best-known-method where the eval suite and task checks come back
clean but the question is still whether the guidance helps in practice.
Most contested edits don't clear that bar — variant A/B is the default for
a reason.

**Breadth/depth model split** (OAE's ensemble pattern, spec §9): a
cheap/fast model drafts the competing variants and runs the scripted
rollouts — volume work, many attempts, low discrimination needed per
attempt. Reserve the strong model for judging the rollout transcripts and
distilling the diff into observations — one careful read per comparison,
not N reads. Spending the strong model on rollout volume instead of
judgment is the failure mode this split exists to prevent.

**Orchestration** — no dedicated script exists for this the way the
variant harness exists for variant A/B; run it through whatever
parallel-subagent fan-out the harness offers (dispatching N task
attempts, collecting transcripts, one distillation pass over the
results). Treat this as the recipe for structuring that fan-out, not a
CLI reference — there's no CLI yet.

## When not to experiment

Both recipes exist for edits where the right answer is genuinely
contested. Most absorb-ready observations are not that: a single obvious
fix — a stale fact corrected, a missing trigger keyword, a one-line
clarification — has one clearly-smallest edit, and running a variant
harness over it is pure overhead with no real uncertainty to resolve.
Default to plain absorb (one deltas file, apply, verify, PR) and reach for
variant A/B only when a genuine fork shows up — description rewrites,
section restructures, or two dead-end-ruled-out fixes that both look
reasonable. Reach for contrastive rollouts even more rarely, only when
variant A/B's content-level scores wouldn't settle the question because
the question is behavioral, not textual.

Adapted from scripts/engine/run_variants.py and
docs/superpowers/specs/2026-08-01-learning-engine-design.md §9 at Task 6
authoring (2026-08-02).
