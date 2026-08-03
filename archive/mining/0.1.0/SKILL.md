---
name: mining
version: 0.1.0
description: >
  Registry-driven mining of external example repos — the learning engine's
  second experience source. Surveys, deep-reads, and comparatively analyzes
  approved repos (vendor demos, framework samples, community robot apps) into
  evidence-cited observations (origin: external) that harden robium skills or
  propose new ones; maintains crawl records for drift re-checks. Use when:
  'mine repo X', 'survey this repo', 'run a comparative run', 'learn from
  external repos', 'distill patterns from a repo', 'crawl SOURCES.md',
  triaging or re-crawling entries in learnings/SOURCES.md. Discovery is
  autonomous; mining spends only on human-approved registry entries. Output
  is observations plus registry updates — never direct skill edits. Not for:
  absorbing robium's own session learnings (skill-author hardening, until the
  learning-loop skill lands) or fresh skill authoring mechanics (skill-author).
---

# Mining — learning from external examples

Working external repos encode more accumulated judgment than our own sessions
can generate. This skill turns approved example repos into evidence-cited
observations in the learnings observations tier, sharing one pipeline with
session learning (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §6a).

## When to use this skill

- A repo in learnings/SOURCES.md is approved for exploration (status flip or
  the user says "mine repo X" — a direct naming is itself approval).
- A comparative question needs settling across sibling repos ("how do TB3 and
  TB4 sims differ on bringup?") — run a comparative set.
- A distilled repo drifted (status recheck, or a major upstream release) — re-crawl.
- Candidate repos need triage into the registry (discovery — filing rows is
  autonomous; mining them is not).
- For absorbing robium's own session learnings, use skill-author hardening
  (learning-loop supersedes it in Phase 2b). For authoring mechanics and the
  quality bar, use skill-author.

## Key directives

- Delegation posture: **embed** — the mining workflow lives here; it consumes
  the engine tools at scripts/engine/ (observations.py, verify_citations.py,
  placement.py) and the registry at learnings/SOURCES.md.
- **Spend only on approval.** <!-- id: spend-gated-registry --> Discovery
  (filing candidate rows with a one-line why) is autonomous; survey and deep
  passes run only on rows the human approved or repos the user named directly.
- **Every citation must grep.** <!-- id: citation-must-grep --> External
  observations carry source (repo@short-sha path#lines) and a verbatim quote;
  run the citation verifier before committing — a citation that fails is a
  discarded candidate, never a "close enough".
- **Observations, never skill edits.** <!-- id: observations-not-edits -->
  Mining output lands in learnings/observations/ and the registry. Skill
  content changes go through the absorb pipeline (Phase 2b) with its human
  merge gate — even for obviously-right findings.
- **Generic distills, specific doesn't.** <!-- id: generic-vs-specific -->
  Transferable patterns (idioms, orderings, workarounds, config shapes, how
  large apps are structured) become observations; project-local choices
  (names, ports, one-off tunings) are noise — drop them.
- **License gates vendoring.** <!-- id: permissive-license-only --> Check the
  repo license during survey. Pointer-first always (cite repo + path + commit);
  vendor a snippet only if short and adapted or materially modified, only from
  Apache/BSD/MIT (attribution header + upstream link + commit), never GPL into
  the plugin. Vendored files enter status unverified.
- **Code only.** <!-- id: code-only-no-history --> No issue-tracker crawling;
  commit-history mining (reverts, fix-chains) is considered-and-deferred
  (spec §6a.2) — do not re-litigate it mid-run.

## Quick start

Single-repo run, end to end (repo already approved in learnings/SOURCES.md):

```bash
# 1. pin a clone (shallow is fine — the recorded SHA is the clone's HEAD)
git clone --depth 1 https://github.com/ros2/examples .robium/mining/examples
git -C .robium/mining/examples rev-parse --short=7 HEAD   # record this SHA

# 2. survey: map the tree, check LICENSE, inventory candidate areas →
#    write .robium/mining/examples-survey.md proposing which areas earn deep reads

# 3. deep pass (approved areas only): read, triage generic-vs-specific,
#    place each candidate:
python3 scripts/engine/placement.py --text "composition via NodeOptions idiom"

# 4. draft observations in learnings/observations/<skill>.md
#    (origin: external, source: repo@sha path#lines, quote: verbatim)

# 5. verify — both must PASS before commit:
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/*.md

# 6. update the SOURCES.md row: status → distilled, add the crawl record:
#    crawled: YYYY-MM-DD @ <sha> → fed: <obs ids>
```

Flip the row to exploring when the survey starts; survey report stays in
.robium/mining/ (gitignored) as the audit trail.

## Decision guidance

**Run type.**

| Situation | Run |
|---|---|
| One approved repo, unknown value | Survey first; deep pass only on areas the survey report proposes (or pre-authorized survey+deep in the registry row) |
| Sibling repos answering the same need (e.g. TB3 sim vs TB4 sim) | Comparative: readers fan out across all members; distill the **common/divergent split** — commons arrive pre-verified (convergence bar met by construction), divergences become decision-surface candidates for umbrella skills |
| Distilled repo with upstream drift | Re-crawl: diff against the recorded SHA, re-mine only what changed, flag distillations whose source lines changed as recheck |

Every comparative run also diffs against **our own catalog and learnings** —
where the ecosystem contradicts a skill, route it as wrong-guidance or
better-method, not as a silent overwrite.

**Evidence bar by source authority** (spec §6a.4):

| Source | Bar |
|---|---|
| Official/vendor repo, consistent with the tool's current docs | ready outright — evidence line says "official" + how docs were checked (direct fetch vs search synthesis) + date; enters the 90-day staleness sweep like any dated claim |
| Community repos, same pattern in ≥2 independent reputable ones | ready via convergence (a comparative common-split satisfies this by construction) |
| Single community repo | tentative — stays until a second witness or a robium trial |
| Extracted example files | status unverified regardless of source; promoted only by a robium trial or the deep-verify lane (Phase 3) |

**Signal mapping for mined findings:** new transferable pattern →
better-method; confirms existing skill content → verified; contradicts skill
content → wrong-guidance; domain no skill owns → no-skill-fired (route to the
new-skills observations file).

**Conflicts — record both, field-tested leads.** <!-- id: field-tested-leads -->
When mined guidance contradicts session-verified knowledge, the observation
carries both with provenance: our field-tested guidance leads, the official
idiom is noted alongside with why it bit us, and the divergence is flagged
for re-verification (upstream may have fixed the original reason).

**New-skill path** (spec §6a.6): when mining surfaces a domain no skill owns,
file a proposal in the new-skills observations file — overlap analysis (run
the placement tool over the finding set), trigger-surface sketch, evidence
inventory. The human approves the *concept* before any authoring starts;
authoring then follows skill-author. Two gates, because new skills change
catalog shape.

## Platform gotchas

- Shallow clones (`--depth 1`) satisfy citation verification for the HEAD
  commit only. For a re-crawl diff, fetch the recorded SHA first:
  `git -C <clone> fetch --depth 1 origin <sha>`.
- Big repos (navigation2, IsaacLab): use a blobless clone to survey cheaply —
  `git clone --filter=blob:none <url>` — blobs download lazily on read.
- Prefer git clones over the GitHub API for reading (no rate-limit surprises;
  the clone is also what the citation verifier needs).
- Licenses live in LICENSE/LICENSE.md at the repo root but subdirectories can
  carry their own (vendored third-party dirs) — check the directory you are
  actually citing from.

## Customization

- Comparison sets are defined in the registry: list the member repos in one
  row's Notes (or a dedicated subsection) and mine them in a single run.
- User tier (Phase 4 preview): the same flow with a private registry at
  .robium/sources.md, observations in the user's repo, and overlay skills as
  the absorb destination — mined-from-private content gets an extra provenance
  review before any upstream contribution.

## References

- Registry: learnings/SOURCES.md — statuses, crawl records, discovery inbox.
- Observations contract: the README in learnings/observations/ (schema, ready
  bar, external-entry fields).
- Engine tools (repo root): scripts/engine/observations.py (lint),
  scripts/engine/verify_citations.py (citation check),
  scripts/engine/placement.py (target/overlap report).
- Pattern-recognition heuristics: the skill-author skill's mining-guide
  reference (what makes a pattern worth distilling) — still the judgment core.
- Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §6a.

## Changelog

- 0.1.0 (2026-08-02): initial skill — registry-driven survey→deep and
  comparative runs, extraction contract, source-authority evidence bar,
  conflict policy, new-skill proposal path (learning-engine Phase 2a, spec §6a).
