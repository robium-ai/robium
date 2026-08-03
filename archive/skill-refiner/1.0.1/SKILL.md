---
name: skill-refiner
version: 1.0.1
description: >
  Curation pass over the robium skill catalog: measure bloat against token
  budgets, find cross-skill duplication and overlap worth merging, sweep
  dated version/status facts for staleness, and review which skills never
  fire so their trigger surface or existence gets questioned. Use when:
  'refine the skills', 'check skill bloat', 'are the skills bloated',
  'prune the skills', 'dedupe the skills', 'stale skill facts', at the end
  of a skill-updater absorption run (skill-updater routes here), or
  periodically (~monthly or after every 2-3 app builds). Report-first:
  produces a findings report, then applies only user-approved edits under
  skill-author's rules. Developer workflow — runs in the robium source
  checkout. Not for: absorbing session learnings (skill-updater) or
  authoring new skills (skill-author).
---

# skill-refiner

The catalog's weeding pass. Absorption (skill-updater, skill-author
hardening) makes the catalog *grow* by default; this skill is the
counterweight that keeps it lean: it measures bloat instead of feeling it,
hunts duplication across skills rather than within one, re-verifies dated
facts before they rot, and asks the question no addition-focused session
asks — "which of these skills earned its context cost?" The research this
skill distills from (MUSE-Autoskill's merge-on-overlap + prune-on-disuse,
Claude Code's least-invoked-first description dropping, Anthropic's
"smallest set of high-signal tokens" principle) all converges on the same
posture: a knowledge base that only ever adds is degrading, just slowly.

## When to use this skill

- End of a skill-updater absorption run — skill-updater invokes a scoped
  refine over the skills it just touched (its final step routes here).
- Periodically over the whole catalog: roughly monthly, or after every 2-3
  app builds, or when the skills list feels heavy — 'refine the skills',
  'check skill bloat', 'prune the skills'.
- Before a plugin release/tag, as the release-readiness sweep.
- When a specific smell appears: two skills answering the same question,
  a skill that never fires, a version fact that reads stale.
- Cross-references — go to the sibling skill instead when the task is:
  - Folding a session's learnings into skills → `skill-updater` (it feeds
    this skill, not the reverse).
  - Writing a new skill, or deep single-skill hardening from learnings
    files → `skill-author` (this skill finds the work; skill-author's
    rules govern how edits are made).
  - Description trigger-accuracy evals → skill-author wraps Claude's
    skill-creator tooling; this skill only flags the candidates.

## Key directives

- **Delegation posture: embed + links.** The four refinement passes and
  their decision rules live here; the *editing* rules (archive-then-bump,
  changelog, quality bar, validator) live in `skill-author`'s references
  and are followed, never forked. Metrics come from
  `scripts/skill_metrics.py` in this skill.
- **Report first, edit second — the same two gates as skill-updater.**
  A refine run's first output is a findings report (one line per finding:
  `[skill] finding → smallest intended edit`), never direct edits. Gate 1:
  the user selects findings. Gate 2: per-skill change summary before any
  commit. Deletions and merges are *more* dangerous than additions —
  a wrongly-pruned fact fails silently in some future session — so the
  human gate is not relaxed here; it's the point.
- **Measure, don't vibe.** Every bloat claim in the report cites a number
  from `scripts/skill_metrics.py` (body lines vs the 500 cap, description
  chars vs the 1024 bar, reference/example bytes, stale dated facts).
  "This skill feels long" is not a finding; "body 470/500 lines and 40%
  of Quick start duplicates references/setup.md" is.
- **Every deletion is paired with its evidence.** Prune a line only when
  the report can say why it's safe: duplicated at the owning skill (link
  it), superseded by a newer verified fact (cite it), or unused trigger
  surface (name the builds where it never fired). Keep the archive
  snapshot honest — it is the undo button for over-pruning.
- **Staleness is a first-class defect.** A version number, EOL date, GA
  claim, or issue reference carries an implicit expiry. Any dated fact
  older than the staleness window (default 90 days) gets re-verified
  against the live source during a full refine — the fix for a stale fact
  is re-verification (update the date), not deletion.
- **Merge duplicates to the lowest owner.** When the same fact lives in
  two skills, keep it at the lowest skill that can hold it (skill-author's
  placement rule) and replace the other copy with a one-line cross-ref.
  When two whole skills overlap heavily, propose a merge into the more
  general one — but skill merges are major restructures: flag for a
  dedicated session, don't do them inside a routine refine.

## Quick start

1. Run the metrics script from the robium checkout root:
   `python3 skills/skill-refiner/scripts/skill_metrics.py` (add
   `--stale-days 90` to tune the staleness window). It prints a per-skill
   table plus a warnings list — that list seeds the report. Two companion
   modes feed the other passes: `--dupes` (identical non-trivial lines in
   2+ skills) and `--history` (per-skill growth across `archive/`
   snapshots).
2. Walk the five passes below (scoped refine: only passes 1-2 on the
   skills just touched; full refine: all five over the catalog).
3. Present the findings report; the user selects (Gate 1).
4. Apply approved edits per skill-author's rules: archive snapshot →
   version bump (prunes/merges are typically build or minor; skill merges
   are major) → edit → changelog line.
5. Run `uv run skills/skill-author/scripts/validate_skills.py` — must PASS.
6. Present the per-skill change summary (Gate 2); commit only on explicit
   approval. Mark any learnings entries this run acted on.

## Decision guidance

The five passes, in the order they pay off:

**Pass 1 — Bloat audit (metrics).** From `skill_metrics.py`: flag bodies
over ~400 lines (the 500 cap is a wall, not a target), descriptions over
1024 chars, reference files that grew past their point, SKILL.md sections
that restate a reference file. Fix direction: push depth into references,
collapse prose to tables, delete restatements. The platform context is
unforgiving: every installed skill's description competes for one shared
listing budget (~1% of the context window), so description bytes are the
most expensive bytes in the repo.

**Pass 2 — Duplication / overlap.** Seed it mechanically with
`skill_metrics.py --dupes` (identical non-trivial lines in 2+ skills;
ignore template boilerplate like the cross-reference stanzas), then judge
semantically: the same command, fact, or gotcha appearing in 2+ skills →
keep at the owning skill, cross-ref elsewhere. Skill-level: two skills
whose descriptions answer the same phrasings (trigger-surface collision —
misfires in both directions) → tighten the "Not for:" scoping of each, or
propose a merge. New content absorbed by skill-updater is the usual source
of fresh duplication — that is why the scoped refine runs after every
absorption.

**Pass 3 — Staleness sweep (full refine only).** The metrics script lists
every dated fact (`YYYY-MM-DD`, "as of", version pins, issue refs) older
than the window. For each: re-verify against the live source (PyPI, docs,
the issue tracker), update fact + date, or mark the claim as needing a
check at use time. This is the pass the wider ecosystem lacks — usage
signals catch dead skills, but only re-verification catches confidently
wrong ones.

**Pass 4 — Usage / retirement review (full refine only).** The usage
signal is the end-of-block retro lines in the app repos' `learnings/`
files (one line per skill per build, with fired/quiet scoring). A skill
that never fired across 2+ builds that *should* have exercised it gets one
of three verdicts: widen its description (trigger bug — route to
skill-author's eval tooling), merge it into its umbrella (content fine,
standalone existence unjustified), or retire it (archive keeps it
recoverable). A skill that fired and scored clean needs nothing — leave
it alone; refinement is not churn.

**Pass 5 — History / growth review (full refine only).** The `archive/`
snapshots are the audit trail — read them. `skill_metrics.py --history`
prints each skill's body-line chain across versions with a growth trend
(`++` = grew every bump) and flags two smells: a skill that has *only
ever grown* across 2+ bumps (absorption without pruning — the catalog's
default failure mode), and a single bump that added ≥60 body lines
(review whether it should have landed in a reference file). For any
flagged skill, read the actual change:
`diff -ru archive/<name>/<prev-version>/ skills/<name>/` — look for
additions that restate what an earlier version already said (repeat
absorption of the same learning in different words), sections that get
edited back and forth across bumps (churn — the content never settled;
consider restructuring instead of a fourth rewording), and growth that
belongs in `references/` rather than the body. Findings feed passes 1-2
as concrete prune/merge candidates.

## Platform gotchas

- **The platform already prunes silently — beat it to the punch.** Claude
  Code truncates each skill's listed description (~1,536 chars) and, when
  the listing budget overflows, drops descriptions starting with the
  least-invoked skills. A bloated catalog doesn't fail loudly; marginal
  skills just quietly stop triggering. Keeping descriptions ≤1024 chars
  and the catalog small is what keeps triggering deterministic.
- **No invocation telemetry exists.** Claude Code exposes no per-skill
  usage counts; the retro lines in `learnings/` are the only usage record.
  If retros stop being written, Pass 4 goes blind — the refine report
  should say so rather than guessing.
- **Edits target the source checkout, never the plugin cache** — same rule
  as skill-updater. After a refine commit, push and reinstall/
  `/reload-plugins`, or the next session refines against stale copies.

## Customization

- **Staleness window:** default 90 days (`--stale-days`). Fast-moving
  domains (LeRobot, Isaac) deserve 60; slow ones (ROS 2 LTS facts) can
  stretch to 180.
- **Cadence:** the default (scoped after each absorption, full refine
  monthly / every 2-3 builds) suits an actively-built catalog. A dormant
  catalog needs only the staleness sweep before its next real use.
- **Thresholds:** the metrics script's warning thresholds (body 400,
  description 1024) are robium's bars; a fork with different quality-bar
  numbers should change them in one place — the script's constants.

## References

- `scripts/skill_metrics.py` — the metrics dashboard: per-skill body
  lines, description chars, reference/example sizes, unverified-example
  counts, stale dated facts, last-changelog date; `--dupes` for
  cross-skill duplicate lines, `--history` for growth trends across the
  `archive/` version snapshots. Stdlib-only; run from the repo root.
- skill-author's references are the canonical editing rules this skill
  applies: quality-bar (structure, description bar, version semantics)
  and learnings-loop (placement rule, prune step, absorbed markers).
- Upstream concepts distilled here: [Anthropic on context engineering]
  (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  ("smallest set of high-signal tokens"), [Claude Code skills docs]
  (https://code.claude.com/docs/en/skills) (listing budget + least-invoked
  dropping), MUSE-Autoskill (arXiv 2605.27366; merge-on-overlap,
  prune-on-disuse), Voyager (arXiv 2305.16291; verification-gated skill
  libraries). Sibling skills: `skill-updater` (routes here at the end of
  each absorption), `skill-author` (editing rules + eval tooling).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.1 (2026-07-12): run-1 self-improvement — metrics script gains an un-sweepable-provenance warning (undated phrasings like 'this session', 'at the time of writing') after the first full refine found 103 such claims the staleness sweep could never age.

- 1.0.0 (2026-07-12): created — five-pass curation (bloat metrics,
  dedup/overlap, staleness sweep, usage review, archive-history growth
  review) distilled from the 2026-07-12 ecosystem research (MUSE
  merge/prune, Claude Code listing budget, Anthropic context-engineering
  guidance), with skill-updater's double gate carried over unchanged.
  Metrics script verified live on the day-one catalog: bloat table,
  --dupes (6 boilerplate-only hits), --history (3 grew-every-bump flags).
