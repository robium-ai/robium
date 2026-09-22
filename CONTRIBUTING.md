# Contributing to robium

Thanks for wanting to help. **The contribution unit is deliberately small: one
skill, no build system.** If you know a robotics tool, you already know enough
to contribute: pick it, copy the template, fill it in, pass the validator,
open a PR. That's the whole loop.

## The two halves of the repo

robium has two halves that feed each other (see
[`AGENTS.md`](./AGENTS.md) for the full picture):

- **The knowledge layer** (`skills/`, `agents/`, agent manifests): robotics
  expertise packaged for supported coding agents. Each skill is a
  natural-language `SKILL.md` file plus (optionally) curated references and
  examples. **No build step, no invented DSL**: the deliverable is knowledge
  and real example files.
- **The applications** ([robium-ai/robium-apps](https://github.com/robium-ai/robium-apps),
  plus `learnings/observations/` here): reference apps built *using* the skills,
  which harden the catalog through a learnings loop.

Most contributions land in the first half: **a new or improved skill**. That's
what this guide walks through. App and infrastructure work follows the mode
rules in `AGENTS.md`; open an issue first so we can point you at the right
starting app.

If you installed Robium with `npx robium-ai setup`, you already have a Git
checkout and do not need to clone again:

```bash
cd ~/robium                       # or the path supplied with --dir
./scripts/bootstrap.sh
git switch -c my-skill-fix
```

Reference applications live in a separate sibling checkout. A typical
workspace looks like this:

```text
~/repos/
├── robium/          # plugin, CLI, skills, and learning engine
└── robium-apps/     # reference robotics applications
```

```bash
git clone https://github.com/robium-ai/robium ~/repos/robium
git clone https://github.com/robium-ai/robium-apps ~/repos/robium-apps
```

Keep application code in `robium-apps` (or your own application repository)
and reusable guidance in `robium`. Cross-reference evidence rather than
copying application trees, transcripts, or project data between repositories.

## Contribute a skill in five steps

### 1. Pick a tool you know

Pick one robotics library, framework, or tool you have real hands-on
experience with: ROS 2, Nav2, a simulator, a viz tool, a policy framework,
whatever you know well. One skill covers the mechanics of **one** tool (a
"tool skill") or one cross-cutting decision (an "umbrella skill"). Keep the
scope to a single tool; small is the point.

Browse [`skills/`](./skills) first to see what already exists and how the
existing skills are shaped. `skills/mujoco/SKILL.md` is a good example of a
lean tool skill.

Looking for an on-ramp? Issues labeled
[`good-first-skill`](https://github.com/robium-ai/robium/labels/good-first-skill)
are the contributor-funnel wishlist: skills we want that are a good first
contribution.

### 2. Copy the skill skeleton

```bash
cp -r templates/skill skills/<your-skill-name>
mv skills/<your-skill-name>/SKILL.template.md skills/<your-skill-name>/SKILL.md
```

The skeleton at `templates/skill/SKILL.template.md` demonstrates the lean
shape. Its sections are prompts to replace, not a required template. It is
intentionally not named `SKILL.md` so plugin discovery does not load it.

The directory name is the skill's identity: `<your-skill-name>` must equal the
`name:` field in the frontmatter.

### 3. Fill it in

Write the SKILL.md following the
[quality bar](./skills/skill-author/QUALITY.md). The rules that
reviews enforce:

- **Frontmatter is exactly `name` + `description`**, nothing else.
  (`name` must equal the directory name.)
- **Keep the description short and discriminating.** Say what the skill helps
  accomplish and separate it from its nearest neighbor without a keyword
  inventory.
- **Keep `SKILL.md` under 120 body lines.** This is a ceiling, not a target.
  Give it one organizing idea and move conditional commands, failures, tuning,
  platform evidence, schemas, and substantial examples into focused files.
- **Use natural sections.** There is no required heading list or delegation
  declaration.
- **No invented syntax.** Every command, flag, and config key must be
  traceable to the real tool's own docs. robium ships knowledge, not a
  made-up DSL.
- **Verify volatile facts against current official docs.** Keep exact observed
  values tied to their robot, platform, version, workload, and check.
- **Route depth conditionally.** Link a support file where it becomes useful;
  do not make every task load every reference.
- **Use evals selectively.** Preserve routing ambiguity or a meaningful
  executable regression, not headings or exact prose.

### 4. Run the checks

One command validates the skills, plugin manifests, and CLI tests:

```bash
./scripts/check.sh
```

Expected output:

```
Checked 26 skills: PASS
```

(The count goes up by one when you add a skill.) The validator checks the
lightweight contract: frontmatter, entrypoint size, local links, and optional
eval structure. Whether the guidance is genuinely useful is checked by a human
with realistic requests.

### 5. Open a PR

Push your branch and open a pull request. The
[PR template](./.github/PULL_REQUEST_TEMPLATE.md) has a short checklist. Keep
the PR to one skill where you can; small, reviewable units merge faster.

## Improving an existing skill

Fixing a stale fact or adding a hard-won gotcha to an existing skill is just as
welcome. Make the smallest useful edit, remove superseded guidance, and rely on
Git history rather than adding a skill version or changelog.

Learning-engine absorption still opens a reviewable PR rather than merging a
skill change automatically. See
`skills/learning-loop/PROMOTION.md` for the evidence and ownership process
maintainers use.

## Contributing a sanitized build finding

External users do not need to share a session transcript to improve Robium.
Open a [wrong or stale guidance issue](https://github.com/robium-ai/robium/issues/new/choose)
with the smallest reproducible finding:

1. Name the affected skill and public tool or application.
2. Describe the symptom, root cause, working fix, and the check that passed.
3. Include useful dead ends when they explain why the fix matters.
4. Link public upstream documentation or a minimal public reproduction when
   one is available.

Before posting, apply this privacy checklist:

- Do not attach raw agent transcripts, prompts, `.robium/transcripts/`, or
  unfiltered terminal logs.
- Remove credentials, tokens, cookies, private URLs, hostnames, IP addresses,
  account identifiers, and environment-variable values.
- Remove customer names and data, proprietary code or datasets, and internal
  project details that are not required to understand the finding.
- Replace local paths and private resource names with neutral placeholders.
- Re-read snippets and screenshots for secrets and identifying metadata.
- Share only facts and excerpts needed to reproduce and verify the guidance.

If the finding warrants a skill edit, make that change on a branch and open a
focused pull request using the lightweight validation and evidence steps
above. An agent may prepare the patch, but a human review and merge is still
required; a learning report never writes directly to the published skill
catalog.

## Reporting bugs and requesting skills

Use the [issue templates](https://github.com/robium-ai/robium/issues/new/choose):

- **New skill request**: a tool you want covered (label `skill`).
- **Wrong or stale guidance**: something in a skill or app is inaccurate,
  outdated, or misleading (label `quality`).
- **Idea / feature**: a broader improvement (label `idea`).

Open-ended questions and design discussion belong in
[GitHub Discussions](https://github.com/robium-ai/robium/discussions) or the
[Discord](https://robium.ai/join/discord), not the issue tracker.

## Ground rules

- Match the repo's tone and factual claims; don't contradict `AGENTS.md` or
  invent facts. When unsure about a volatile fact, verify against live docs.
- One logical change per PR. A new skill, or one skill's fix, is the ideal
  size.
- By contributing, you agree your work is licensed under the repo's
  [MIT license](./LICENSE).

Welcome aboard.
