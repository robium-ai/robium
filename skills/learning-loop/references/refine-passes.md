# The five refine passes: evidence-armed

skill-refiner's five-pass curation survives into the engine unchanged in
structure and posture (report-first, measure-don't-vibe, every deletion
paired with evidence) but each pass is now armed with a richer, engine-
maintained evidence source instead of a one-off metrics run. Refine still
produces a findings report first; approved findings become retire/move/
annotate deltas that go through the same apply_deltas.py and validation path as
absorb, rather than ad-hoc edits. The default landing route is PR and human
merge; the explicit maintainer direct-main exception in the parent skill also
applies. Scoped refine (passes
1–2) runs after every absorb, over just the skills that absorb touched;
fresh absorption is where duplication enters the catalog. Full refine (all
five passes) runs on its own cadence, roughly monthly or every 2–3 app
builds.

## Pass 1: Prune (ledger-driven) + bloat audit

This pass leads with the ledger predicate, per spec §10: prune candidates
are anchors with `harmful > 0 ∧ helpful == 0` in their skill's
evidence.yaml: proven friction, zero offsetting evidence of value. Every
anchor that clears that predicate becomes a `retire` delta carrying its
evidence trail (the sources list from the ledger entry) as the delta's
justification; the archive snapshot stays the undo button if a prune turns
out to be wrong. Be honest about current tooling here: no aggregate script
walks every skill's evidence.yaml and reports the harmful>0/helpful=0 set
in one pass yet (skill_metrics.py doesn't read the ledger at all), so
today this is a per-skill grep/manual read (evidence.yaml per touched
skill during a scoped refine; all of them during a full refine) rather than
a single command. A metrics-script extension that aggregates this
mechanically is the obvious next tooling gap, not yet closed.

The second half of the pass is skill-refiner's original bloat audit,
unchanged: flag bodies over ~400 lines (the 500 cap is a wall, not a
target), descriptions over 1024 chars, reference files that grew past
their point, SKILL.md sections that just restate a reference file.
skill_metrics.py still supplies these numbers: every bloat claim in the
report cites one ("body 470/500 lines", not "this skill feels long"). Fix
direction is unchanged too: push depth into references, collapse prose to
tables, delete restatements. One difference under the engine: a fix that
would push a skill's final body (content plus the new changelog line) past
the cap is refused by apply_deltas itself, not just flagged in review; the
500-line check now happens mechanically at apply time, so a bloat fix that
doesn't fit gets surfaced as a refusal (split to references/) rather than
discovered after the fact.

## Pass 2: Duplication / overlap

Seeded the same way (skill_metrics.py --dupes for identical non-trivial
lines across two or more skills), but the evidence arm is richer now:
anchor-level similarity across skills (two anchors making the same claim in
different words) is visible directly, because every claim-bearing item
already carries a stable anchor id. Where skill-refiner could only propose
"keep at the owning skill, cross-ref elsewhere" as a manual edit, the
engine expresses the same fix as a concrete delta pair: a `move` op
relocating the duplicated anchor to its lowest owning skill, plus (where
useful) an `add` op leaving a one-line cross-reference behind at the
skill that lost it. Skill-level duplication (two descriptions answering the
same phrasings) is still a judgment call for the report, not something
apply_deltas can resolve mechanically: propose tightening the "Not for:"
scoping of each, or flag a merge for a dedicated session.

## Pass 3: Staleness sweep

Unchanged: the metrics script lists every dated fact (YYYY-MM-DD, "as of",
version pins, issue refs) older than the staleness window (default 90
days, tunable per domain). Each gets re-verified against its live source
and either updated in place or explicitly flagged as needing a check at use
time. This remains the pass the wider ecosystem lacks (usage signals catch
dead content, only re-verification catches confidently wrong content), and
the engine changes nothing about how it runs, only how its fix lands: as an
`update` or `annotate` delta carrying the re-verified fact and a fresh date,
applied and reviewed exactly like any other absorb-style edit.

## Pass 4: Usage / retirement review

This pass combines evidence that exists without interrupting implementation:
hook captures, promoted observations, trigger evals, and non-trivial verified
examples. Mandatory per-skill end-of-block retros are no longer an input; a
consolidation may record a compact milestone result when it adds real evidence.
Combine these signals with the negative-eval side of each skill's evals.yaml
(misfires: phrasings that wrongly selected a skill). The
same three verdicts apply to a skill that never fires when it should: widen
its description (a trigger bug, drafted as an `annotate` or `update` delta
against the description and re-verified with skill-author's description
evals), merge it into its umbrella (a `move` of its durable content plus
retirement of the shell), or retire it outright (archived, recoverable). A
skill that fires and scores clean needs nothing; refinement is not churn.

## Pass 5: History / growth review

Unchanged in intent (read archive/<name>/<version>/ across bumps, flag a
skill that has only ever grown (absorption without pruning, the catalog's
default failure mode) and any single bump that added a large amount of body
content that should have landed in a reference file instead), but the
archive itself is richer now: every apply_deltas snapshot carries the
observation id(s) that motivated the change in its changelog line, so a
growth-review diff no longer has to guess why a bump happened. Where
Phase 3's experimentation engine has run, the archive also carries scored
variants and parent metadata for contested edits, which turns "did this
edit actually improve things" from a re-read judgment call into a
citable score. Findings from this pass feed straight back into passes 1
and 2 as concrete prune/merge candidates for the next refine cycle.

## What stayed exactly the same

- **Report first, edit second, same evidence and authority gates.**
  Findings are presented (`[skill] finding → smallest intended edit`) before
  any delta is drafted. External/unattended/unrequested changes require human
  PR merge; an explicitly authorized maintainer direct-main run keeps the same
  concrete diff, evidence, and validation requirements. Refine's deletions and
  moves need especially careful target verification.
- **Every deletion is paired with its evidence.** A prune's evidence is now
  literally the ledger counters that justified it (harmful>0, helpful=0);
  the report cites the counter values, not a feeling.
- **Merge duplicates to the lowest owner, flag whole-skill merges for a
  dedicated session** rather than folding them into a routine refine;
  skill merges are major restructures regardless of which pass surfaced
  them.

Adapted from skill-updater 1.1.1 / skill-refiner 1.0.1 at retirement (2026-08-02).
