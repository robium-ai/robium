<!--
Thanks for contributing! Keep PRs small — ideally one skill, or one skill's fix.
See CONTRIBUTING.md for the full flow.
-->

## What & why

<!-- One or two sentences: what this changes and why. -->

## Checklist

- [ ] The validator passes: `uv run skills/skill-author/scripts/validate_skills.py` prints `Checked <n> skills: PASS` and exits 0.

**If this PR touches a skill (`skills/**`):**

- [ ] Frontmatter is exactly `name` + `version` + `description`; `name` equals the directory name.
- [ ] Body is under 500 lines; required sections are present and in order.
- [ ] **Version bumped** (`MAJOR.MINOR.BUILD`) per the semantics — build = small fix, minor = content addition, major = restructure/re-scope. New skills start at `1.0.0`.
- [ ] **Prior version archived** to `archive/<name>/<old-version>/` (for edits to an existing skill), in this same PR.
- [ ] A `## Changelog` line was added, starting with the new version: `- <version> (YYYY-MM-DD): …`.
- [ ] Version facts were verified against live upstream docs at authoring time (not written from memory); citations say how they were verified.
- [ ] Cross-references to sibling skills are bidirectional and consistent.

## Notes for reviewers

<!-- Anything reviewers should know: trade-offs, open questions, follow-ups. -->
