# Contributing to robium

Thanks for wanting to help. **The contribution unit is deliberately small: one
skill, no build system.** If you know a robotics tool, you already know enough
to contribute — pick it, copy the template, fill it in, pass the validator,
open a PR. That's the whole loop.

## The two halves of the repo

robium has two halves that feed each other (see
[`CLAUDE.md`](./CLAUDE.md) for the full picture):

- **The knowledge layer** (`skills/`, `agents/`, agent manifests) — robotics
  expertise packaged for supported coding agents. Each skill is a
  natural-language `SKILL.md` file plus (optionally) curated references and
  examples. **No build step, no invented DSL** — the deliverable is knowledge
  and real example files.
- **The applications** ([robium-ai/robium-apps](https://github.com/robium-ai/robium-apps),
  plus `learnings/` here) — reference apps built *using* the skills, which
  harden the catalog through a learnings loop.

Most contributions land in the first half: **a new or improved skill**. That's
what this guide walks through. App and infrastructure work follows the mode
rules in `CLAUDE.md`; open an issue first so we can point you at the right
starting app.

## Contribute a skill in five steps

### 1. Pick a tool you know

Pick one robotics library, framework, or tool you have real hands-on
experience with — ROS 2, Nav2, a simulator, a viz tool, a policy framework,
whatever you know well. One skill covers the mechanics of **one** tool (a
"tool skill") or one cross-cutting decision (an "umbrella skill"). Keep the
scope to a single tool — small is the point.

Browse [`skills/`](./skills) first to see what already exists and how the
existing skills are shaped. `skills/mujoco/SKILL.md` is a good example of a
lean tool skill.

Looking for an on-ramp? Issues labeled
[`good-first-skill`](https://github.com/robium-ai/robium/labels/good-first-skill)
are the contributor-funnel wishlist — skills we want that are a good first
contribution.

### 2. Copy the `_TEMPLATE` skeleton

```bash
cp -r skills/_TEMPLATE skills/<your-skill-name>
mv skills/<your-skill-name>/SKILL.template.md skills/<your-skill-name>/SKILL.md
```

The skeleton at `skills/_TEMPLATE/SKILL.template.md` carries the required
section structure and inline guidance. (It is intentionally *not* named
`SKILL.md` so plugin discovery doesn't load the skeleton itself — don't rename
it in place.)

The directory name is the skill's identity: `<your-skill-name>` must equal the
`name:` field in the frontmatter.

### 3. Fill it in

Write the SKILL.md following the
[quality bar](./skills/skill-author/references/quality-bar.md). The rules that
reviews enforce:

- **Frontmatter is exactly `name` + `version` + `description`** — nothing else.
  (`name` must equal the directory name.)
- **The `description` is a trigger surface, not a summary.** It is the only
  signal an agent uses to decide whether to load your skill. Pack it with the
  capability, explicit "Use when" phrases, literal keywords a user might type,
  where the skill sits in the workflow, and a "Not for" negative-scope line
  naming the neighboring skills it should *not* fire for. (≤1024 chars.)
- **`version: MAJOR.MINOR.BUILD`** — start a brand-new skill at `1.0.0`.
- **Body under 500 lines.** Depth beyond that goes into `references/*.md`
  files (single-topic, ~5–10 KB, one level deep).
- **Required sections, in this order**, as level-2 (`##`) headers:
  `When to use this skill`, `Key directives`, `Quick start`, then
  `Decision guidance` (umbrella skills) **or** `Usage patterns` (tool skills),
  `Platform gotchas`, `Customization`, `References`, `Changelog`.
- **State the delegation posture** as the first bullet of `Key directives`:
  **embed** / **embed + links** / **delegate to `<upstream>`**.
- **No invented syntax.** Every command, flag, and config key must be
  traceable to the real tool's own docs. robium ships knowledge, not a
  made-up DSL.
- **Verify version facts against live docs at authoring time** — don't write
  release names, LTS windows, or CLI shapes from memory; they drift.
- **`examples/` files carry a `status:` marker** — `unverified` (curated from
  upstream, not yet run here) until a real run promotes them to `verified`.
- **Cross-references stay bidirectional.** If your skill points at a sibling,
  make sure the relationship reads consistently from both sides. Only the
  `architect` skill knows the whole catalog.
- **Backticks are for local files only.** Backtick a path only when the file
  lives inside your own skill's directory; another skill's file is prose.

### 4. Pass the validator

The validator is the pre-PR check. It must print a PASS line and exit 0:

```bash
uv run skills/skill-author/scripts/validate_skills.py
```

Expected output:

```
Checked 24 skills: PASS
```

(The count goes up by one when you add a skill.) The validator enforces the
mechanical rules — frontmatter fields, version format, section presence, body
line count, and that every backtick-quoted `references/`, `scripts/`, or
`examples/` path actually exists. The judgment items in the quality bar
(is the description a good trigger surface? is the delegation posture right?)
are checked by a human in review.

Manifest sanity check, if you touched anything under `.claude-plugin/`
(you usually won't — skills are auto-discovered and don't need manifest edits):

```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('OK')"
```

### 5. Open a PR

Push your branch and open a pull request. The
[PR template](./.github/PULL_REQUEST_TEMPLATE.md) has a short checklist. Keep
the PR to one skill where you can — small, reviewable units merge faster.

## Improving an existing skill

Fixing a stale fact or adding a hard-won gotcha to an existing skill is just as
welcome. A few extra rules apply because skills are versioned like software:

- **Bump the `version:`** per the semantics — **build** = small correction
  (typo, stale-fact refresh, one-line fix, a keyword added to the
  description); **minor** = content addition (new bullet/pattern, new reference
  or example file); **major** = restructure or re-scope.
- **Archive the prior version** before your first edit of a bump: copy the
  skill's current directory to `archive/<name>/<old-version>/`. The archive is
  the browsable history — committed, never edited, never loaded as a skill.
- **Add a `## Changelog` line** starting with the new version:
  `- <new-version> (YYYY-MM-DD): <what changed and why>`.

If you're working through Claude Code, note that the STRICT skill-update policy
in `CLAUDE.md` means skills are never edited automatically — a human always
selects and approves the change. See
`skills/skill-author/references/learnings-loop.md` for the full hardening
process maintainers use.

## Reporting bugs and requesting skills

Use the [issue templates](https://github.com/robium-ai/robium/issues/new/choose):

- **New skill request** — a tool you want covered (label `skill`).
- **Wrong or stale guidance** — something in a skill or app is inaccurate,
  outdated, or misleading (label `quality`).
- **Idea / feature** — a broader improvement (label `idea`).

Open-ended questions and design discussion belong in
[GitHub Discussions](https://github.com/robium-ai/robium/discussions) or the
[Discord](https://robium.ai/join/discord), not the issue tracker.

## Ground rules

- Match the repo's tone and factual claims — don't contradict `CLAUDE.md` or
  invent facts. When unsure about a versioned fact, verify against live docs.
- One logical change per PR. A new skill, or one skill's fix, is the ideal
  size.
- By contributing, you agree your work is licensed under the repo's
  [MIT license](./LICENSE).

Welcome aboard.
