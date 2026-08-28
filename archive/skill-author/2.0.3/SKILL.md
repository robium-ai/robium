---
name: skill-author
version: 2.0.3
description: >
  Author new robium skills and enforce the catalog quality bar. Owns the
  authoring workflow from templates/skill, the quality bar
  (references/quality-bar.md: template compliance, trigger-surface
  descriptions, <500-line bodies, stated delegation posture, upstream links,
  no invented syntax), and scripts/validate_skills.py: run it after ANY
  skills/ change. Use when: 'write a new robium skill', 'new skill for X',
  template compliance questions, description/trigger-surface tuning, or
  validator failures. Wraps Claude's skill-creator skill for evals and
  description tuning instead of reinventing it. Not for: absorbing learnings
  or refining the catalog (learning-loop), mining example repos (mining),
  building robot applications (architect and the domain skills).
---

# skill-author

The meta-skill that governs how new robium skills get authored and how the
catalog's quality bar gets enforced. It is the repo's authoring machinery:
fresh authoring against the quality bar; absorption and refining live in the
learning-loop skill, mining in the mining skill.

## When to use this skill

- Creating a brand-new skill under `skills/<name>/` from the template.
- Auditing an existing skill against the quality bar, or running the
  validator before a commit.
- Tuning a skill's frontmatter `description` for better trigger accuracy, or
  evaluating whether a skill fires on the phrasing it should.
- Cross-reference: absorbing `learnings/` notes or refining the catalog
  (prune/dedup/staleness): use the `learning-loop` skill instead. Extracting
  reusable patterns out of example repos (this repo's own apps or external
  ones): use the `mining` skill instead.
- Cross-reference: for building an actual robotics application (choosing a
  stack, scaffolding a repo), use the `architect` skill and the domain skills
  it routes to instead; this skill only edits skills, never application code.

## Key directives

- **Delegation posture: embed.** This skill owns the authoring workflow
  outright; there is no good upstream skill for "how to write a robium
  skill," so the process lives here rather than being linked out.
- Knowledge goes to the **lowest skill that can hold it** <!-- id: knowledge-goes-to-lowest-skill-that-can-hold-it -->: a Nav2 costmap
  gotcha belongs in `nav2`, not `architect`; a ROS 2 launch-file quirk
  belongs in `ros2`, not a per-tool skill built on top of it. Never park
  knowledge one level higher than where it will actually be looked up.
- **Always run `scripts/validate_skills.py` before committing any skill
  change** <!-- id: always-run-validator-before-commit -->, whether the
  change came from fresh authoring here, a learning-loop absorb, or a mining
  distillation. A skill that fails the validator is not done.
- For eval design and description-wording tuning, **wrap Claude's own
  `skill-creator` skill** <!-- id: wrap-skill-creator-for-evals-not-reinvent --> rather than reinventing evals or trigger-testing
  machinery. skill-author supplies the robium-specific quality bar and
  workflow; skill-creator supplies the generic eval tooling.

## Quick start

**Fresh authoring** (new skill from scratch):

1. `cp -r templates/skill skills/<new-skill-name>`, rename the dir to
   match the intended `name:`, and rename `SKILL.template.md` to `SKILL.md` <!-- id: template-rename-not-skill-md -->
   (the template file is deliberately not named SKILL.md so plugin
   discovery never exposes the skeleton as an installable skill).
2. Research the upstream tool/library docs and examples for the domain the
   skill covers.
3. Fill every template section: frontmatter `description` (capability
   summary, `Use when:` triggers, literal keywords, workflow-position
   marker, `Not for:` negative scope), `## Key directives` (state the
   delegation posture explicitly), `## Quick start`, `## Decision guidance`
   or `## Usage patterns`, `## Platform gotchas`, `## Customization`,
   `## References` (local files plus upstream links).
4. Run `uv run skills/skill-author/scripts/validate_skills.py` and fix any
   `FAIL:` lines.
5. Commit.

## Decision guidance

- **New skill vs. deepen an existing one vs. add a reference file**:
  ask in this order:
  1. Does an existing skill already own this domain (same tool, same
     decision point)? <!-- id: existing-skill-owns-domain-edit-not-new --> If yes, the content is an edit to that skill, not a
     new one.
  2. Within that skill, is the content core to the common path (belongs in
     `SKILL.md` itself, under `## Quick start`/`## Decision guidance`) or a
     deep dive only some callers need (belongs in a new or existing file
     under `references/`)? <!-- id: core-path-vs-references-split -->
  3. Only create a brand-new skill when the content is a genuinely distinct
     decision point or tool with its own trigger surface <!-- id: new-skill-only-for-distinct-decision-point -->, e.g. `nav2` vs
     `gazebo` are separate skills because they're separate tools with
     separate "when do I load this" questions, even though both feed the
     nav vertical.
  4. If the new content would push a skill's `SKILL.md` body toward the
     500-line cap, that's a signal to push the *next* addition into
     `references/` rather than growing the body further; don't wait until
     the validator fails. <!-- id: approaching-500-line-cap-push-to-references -->
- **Body snippet vs. `examples/` file** <!-- id: snippet-in-skill-md-vs-examples-file -->: a snippet belongs directly in
  `SKILL.md` (`## Quick start` or `## Decision guidance`) when it is short
  (a handful of lines), generic across the skill's common cases, and needed
  on the most common path. It belongs in `examples/` instead when it is a
  fuller file (a whole launch file, a multi-service Dockerfile/compose
  file, a full config) that callers copy and adapt rather than read inline;
  those get a one-line reference from `## References` plus a
  verified/unverified status marker (see `references/quality-bar.md`).

## Platform gotchas

- None specific to this skill; it edits Markdown and runs a `uv`-managed
  Python script, which behaves the same on macOS and Linux. Per-skill
  platform gotchas belong in the skill being authored, not here.

## Customization

- The authoring workflow is process, not code; there is nothing to template
  beyond the skeleton in templates/skill itself. When robium's quality bar
  changes (a new required section, a new constraint), update
  `REQUIRED_SECTIONS`/checks in `scripts/validate_skills.py`,
  the template skeleton, and `references/quality-bar.md` together;
  the three must never drift apart.
- If a project forks robium and wants a stricter or looser bar (e.g. a
  600-line cap, or an extra required `## Safety` section), edit the
  validator's constants and the checklist in lockstep, then re-run it
  against every skill in the catalog to see what breaks.

## References

- `references/quality-bar.md`: the full per-skill checklist enforced by
  the validator and by hand during review, with a one-line "how to check"
  per item.
- `references/mining-guide.md`: pattern-recognition heuristics (what makes
  a pattern worth distilling), consumed by the `mining` skill.
- `scripts/validate_skills.py`: the repo-level validator; run it before
  every commit that touches `skills/`.
- Upstream: Claude's built-in `skill-creator` skill (evals, description
  tuning), the [agentskills.io](https://agentskills.io) convention this
  format follows, `docs/superpowers/specs/2026-07-10-robium-plugin-design.md`
  section 5 (the design source for this skill). Sibling skills: `learning-loop`
  (absorption and catalog refining; successor to skill-updater and
  skill-refiner, both retired to `archive/`) and `mining` (external
  example-repo distillation).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 2.0.3 (2026-08-07): moved the authoring skeleton out of `skills/` so native
  Codex plugin validation sees only installable skill directories.
- 2.0.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 2.0.1 (2026-08-02): validator checks evals.yaml tasks: entry schema
  (name/command/pass_criteria required and pass_criteria a compilable
  regex; timeout int; name kebab-case and unique per skill)
- 2.0.0 (2026-08-02): restructure: Modes 2 (mining) and 3 (hardening) moved
  to the mining and learning-loop skills; skill-author is authoring + quality
  bar + validator custody only (learning-engine Phase 2b, spec §13).
- 1.1.3 (2026-08-02): description, intro, When-to-use + Mode 2 residual external-repo claims narrowed to in-repo apps (final-review fix; completes the 1.1.2 narrowing).
- 1.1.2 (2026-08-02): Mode 2 narrowed to in-repo apps; external-repo mining
  moved to the new mining skill (learning-engine Phase 2a).
- 1.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.1.0 (2026-07-12): ecosystem-research absorption: learnings-loop gains
  a seventh capture signal (user-corrected approach, from
  continuous-learning-v2's pattern-detection taxonomy), an evidence bar
  for entries (passing check + named failure pattern + ruled-out
  dead-ends, from self-learning-skills), recurrence-count annotation, and
  a prune-step route to the new skill-refiner; sibling cross-refs added.
