<!--
Thanks for contributing! Keep PRs small — ideally one skill, or one skill's fix.
See CONTRIBUTING.md for the full flow.
-->

## What & why

<!-- One or two sentences: what this changes and why. -->

## Checklist

- [ ] The validator passes: `uv run skills/skill-author/scripts/validate_skills.py` prints `Checked <n> skills: PASS` and exits 0.

**If this PR touches a skill (`skills/**`):**

- [ ] Frontmatter is exactly `name` + `description`; `name` equals the directory name.
- [ ] The entrypoint is under 120 body lines, uses natural sections, and keeps conditional depth in focused support files.
- [ ] Volatile facts were verified against current official sources; observed values retain their measured conditions.
- [ ] Local links resolve and sibling skills are mentioned only at real subsystem boundaries.
- [ ] Tests protect meaningful routing or behavior, not headings or exact prose.

## Notes for reviewers

<!-- Anything reviewers should know: trade-offs, open questions, follow-ups. -->
