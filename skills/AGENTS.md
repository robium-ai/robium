# Skill authoring guidance

This file applies only under `skills/`. Load the `skill-author` skill before
editing skill content; use `learning-loop` for evidence absorption/refining.

## Catalog boundaries

- Only `architect` knows the full catalog. Other skills reference direct
  collaborators and keep ownership bidirectional.
- Put knowledge in the lowest skill that owns the decision. Keep common-path
  guidance in `SKILL.md`; put optional depth in one-level `references/` files.
- Robium documents real upstream syntax and examples. Never invent a command,
  flag, API, configuration format, version fact, or DSL.

## Required mechanics

Before editing a skill, copy its current directory to
`archive/<name>/<old-version>/`. Never edit an archive.

- Build bump: correction, stale fact, typo, or trigger keyword.
- Minor bump: new pattern/reference or trigger-surface expansion.
- Major bump: restructure, ownership change, or description rewrite.

Add a dated changelog line for the new version. Regenerate `cli/src/catalog.json`
after any skill version/description change, then run:

```bash
uv run skills/skill-author/scripts/validate_skills.py
uv run scripts/engine/run_trigger_evals.py --skills <changed-skills>
```

## Format and review bar

- Frontmatter is `name`, `version`, `description` only, except the existing
  `isaac-sim` compatibility field. Description is a concise trigger surface:
  capability, realistic “Use when” phrases/keywords, workflow position, and
  negative scope.
- Required body order: When to use, Key directives, Quick start, Decision
  guidance or Usage patterns, Platform gotchas, Customization, References,
  Changelog. Body stays under 500 lines.
- The first Key-directives bullet states the delegation posture: embed,
  embed+links, or delegate.
- Local backticked paths must exist inside the same skill. Refer to another
  skill's files in prose rather than as a local path.
- State how current/versioned facts were verified. If direct documentation was
  unavailable, label search synthesis honestly and request re-verification.
- Examples remain `status: unverified` until a real fixture/run passes.

Direct-to-main is allowed only when the maintainer explicitly authorizes it in
the current conversation. Otherwise skill changes end in a human-reviewed PR.
