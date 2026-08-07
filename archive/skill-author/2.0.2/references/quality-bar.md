# The robium quality bar

Every skill in `skills/` (except `_TEMPLATE`, which is a skeleton, not a
skill) must pass this checklist. `scripts/validate_skills.py` enforces the
mechanical items automatically; the rest are checked by hand during
authoring, mining, or hardening. Run the validator before every commit that
touches `skills/`; see `../SKILL.md`.

## 1. Template compliance

The skill was copied from the skills/_TEMPLATE skeleton and kept its section
structure: `## When to use this skill`, `## Key directives`,
`## Quick start`, `## Decision guidance` (umbrella skills) or
`## Usage patterns` (per-tool skills), `## Platform gotchas`,
`## Customization`, `## References`, `## Changelog`, in that order, as
level-2 headers.

- **How to check:** run the validator; it fails with
  `missing required section '<section>'` for anything absent. Header order
  and the umbrella-vs-tool choice of `## Decision guidance` vs
  `## Usage patterns` are not mechanically checked; verify by eye against
  `_TEMPLATE`.

## 2. Description is a trigger surface

The frontmatter `description` is not a summary for humans; it is the only
signal the agent uses to decide whether to load the skill. It must carry
five ingredients:

1. **Capability summary**: one sentence, what the skill covers.
2. **Explicit "Use when" triggers**: scenarios phrased the way a task would
   be framed, not just topic labels.
3. **Literal user keywords**: words/phrases a user might actually type,
   quoted (e.g. `'costmap not updating'`).
4. **Workflow-position marker**: where this skill sits relative to others,
   e.g. "Load after architect selects the nav stack."
5. **Negative scoping ("Not for")**: the adjacent skill(s) this one should
   NOT fire for, named explicitly, to prevent misfires.

- **How to check:** read the description with fresh eyes and ask "would
  this fire on the five or six most likely phrasings a user or agent would
  use for this domain, and stay silent on its neighbors' phrasings?" If any
  of the five ingredients is missing, it's not done. `skill-creator`'s eval
  tooling (wrapped, not reimplemented; see `../SKILL.md`) can be used to
  test trigger accuracy empirically.

## 3. Body under 500 lines

`SKILL.md` body (everything after the closing `---` of frontmatter) stays
under 500 lines. Depth beyond that goes to `references/`.

- **How to check:** the validator counts body lines and fails at `>=500`
  with `body <n> lines (must be <500)`. If a skill is approaching the cap,
  push the next addition into a new or existing `references/*.md` file
  instead of growing the body (see the Decision guidance section of
  `../SKILL.md`).

## 4. Delegation posture stated explicitly

`## Key directives` states, as its first bullet, one of: **embed**
(knowledge lives in this skill because no good upstream skill exists),
**embed + links** (embed the robium-specific glue, but point to upstream
docs for the rest), or **delegate to `<upstream skill/plugin>`** (install
and defer to an existing skill; robium adds only the domain-specific glue
on top).

- **How to check:** not mechanically validated; read `## Key directives`
  and confirm the very first bullet names one of the three postures and,
  for delegate/embed+links, names the upstream target concretely (a
  plugin/skill name or a docs URL, not "see upstream").

## 5. Upstream links present

`## References` lists at least one upstream link (official docs, an
examples repo, or a related plugin/skill) unless the skill's domain
genuinely has none (rare; note that explicitly if so, don't just omit the
line).

- **How to check:** open `## References` and confirm an "Upstream:" line
  with at least one real URL or named external skill/plugin, not a
  placeholder.

## 6. Examples carry status markers

Every file under a skill's `examples/` directory, and every reference to
one from `## References`, is marked **verified** (it has actually run
successfully, e.g. in a trial run) or **unverified** (curated from upstream
but not yet exercised in this repo).

- **How to check:** grep the skill's `## References` section and any
  `examples/` file headers for the literal words `verified` / `unverified`.
  A trial run or app iteration that exercises an example is what promotes
  it from unverified to verified; update the marker at that point, not
  before.

## 7. No invented syntax

Robium ships knowledge and curation (natural-language skills, example
snippets, Dockerfiles, config samples, and a few genuinely reusable helper
scripts), never a made-up DSL, config format, or command surface that
doesn't exist in the underlying tool.

- **How to check:** every command, flag, config key, or file format shown
  in a skill must be traceable to the real upstream tool's own docs or
  `--help` output. If you can't point to where the underlying tool defines
  it, it doesn't belong in the skill. Scripts are the one exception where
  robium can define its own interface (e.g. `validate_skills.py`'s own
  CLI), because the script itself is the source of truth for its syntax.

## 8. Referenced local files exist

Every backtick-quoted `references/...`, `scripts/...`, or `examples/...`
path mentioned in the body actually exists in the skill directory. Local
references stay one level deep from `SKILL.md`; never chain a reference
file into another reference file.

- **How to check:** the validator resolves every backtick-quoted
  `references/`, `scripts/`, or `examples/` path against the filesystem and
  fails with `referenced file missing: <path>` if absent. One-level-deep
  chaining is not mechanically checked; verify by eye that `references/`
  files don't themselves point deeper.

## 9. Versioned, with archived history

Every skill carries `version: MAJOR.MINOR.BUILD` in frontmatter. Bump
semantics: **build** = small corrections (typo, stale-fact refresh,
one-line fix, a keyword added to the description); **minor** = content
additions (new bullet/pattern, new reference or example file, description
trigger-surface expansion); **major** = restructure or re-scope (section
overhaul, ownership/boundary change, description rewrite). Before the
first edit of any bump, copy the skill's current directory to
`archive/<name>/<old-version>/` at the repo root; the archive is the
browsable evolution history and is committed, never edited, and never
loaded as a skill (plugin discovery only scans `skills/`). The new
version's `## Changelog` line starts with the version:
`- <new-version> (YYYY-MM-DD): <what changed and why>`.

- **How to check:** the validator fails on a missing or malformed
  `version`. The archive-before-bump step and changelog-version prefix are
  process rules; verify during review that any version bump in a diff is
  accompanied by the matching `archive/<name>/<old-version>/` snapshot.
