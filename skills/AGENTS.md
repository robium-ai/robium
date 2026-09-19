# Skill guidance

This file applies under `skills/`. Load `skill-author` before changing skill
content and `learning-loop` when working from captured evidence.

## Keep discovery and context cheap

- Only `architect` needs the full catalog. Other skills name direct neighbors
  only where work crosses a real boundary.
- Live frontmatter contains only `name` and a short `description`.
- Give each entrypoint one strong organizing idea and keep it human-readable.
  There is no required section template.
- Assume ordinary coding competence. Include only guidance that changes a
  capable agent's decisions.
- Put conditional commands, failures, tuning, platform evidence, schemas, and
  substantial examples in focused support files. Link them where they become
  relevant instead of loading them by default.
- Keep official upstream documentation authoritative for volatile commands,
  APIs, packages, and configuration.
- Preserve exact Robium-observed values with their conditions; never present
  one application's workaround as a universal default.

## Change and review

- Git history is the normal record of live skill changes. Do not add per-skill
  versions, changelogs, README files, or routine archive snapshots.
- Existing files under `archive/` are immutable historical snapshots.
- Preserve useful examples and scripts only when they provide reusable value;
  validate changed executable artifacts proportionally.
- Run `uv run skills/skill-author/scripts/validate_skills.py` once after each
  coherent batch of live skill changes, not after every file or sentence.
- Use trigger or task evals only when they protect a meaningful routing or
  behavior regression. Do not test headings or exact prose.
- Regenerate `cli/src/catalog.json` after a skill name or description changes.

Robium ships practical robotics knowledge and real reusable examples, not an
application framework or invented DSL.
