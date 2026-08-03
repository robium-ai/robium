# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**robium** has two halves that feed each other:

- **The plugin** (`skills/`, `agents/`, `.claude-plugin/`) — a Claude Code plugin of robotics skills: natural-language SKILL.md files (agentskills.io format) plus curated references, examples, and one subagent. There is no application framework code, no build step, and deliberately **no invented syntax/DSL**: the deliverable is knowledge, real example files (Dockerfiles, YAML, SDF, Python snippets), and a few genuinely reusable scripts.
- **The applications** (the sibling repo [robium-ai/robium-apps](https://github.com/robium-ai/robium-apps), plus `learnings/` here) — the proving ground **and reference library** for the plugin. Apps are built *using* robium's skills, but the operator is robium's developer, not a client. Every app session wears two hats: build the app honestly, and treat every skill interaction as QA data. `learnings/` is a primary product; the apps themselves are the second — canonical, battle-tested samples that future applications reference or **bootstrap from**.

The halves were merged into one monorepo for the engine era, then re-split on 2026-08-03 ahead of the public release: the applications now live in `robium-ai/robium-apps` and the landing site + live-demo orchestrator in `robium-ai/robium-website`. This repo keeps the plugin, the CLI (`cli/`, the `robium-ai` npm package), the learning engine (`learnings/`, `scripts/engine/`), and the design docs (`docs/`). The hardening loop is unchanged — apps stumble → learnings captured (in this repo) → skills absorbed.

## Modes — anchor the work to the half that owns the output

Even in one repo, a session operates in one of a few modes, and the mode selects which rules bind:

- **Authoring skills** → you are producing new `skills/**` content with the `skill-author` skill (quality bar + validator). The engine-era update policy below governs how edits land.
- **Running the learning engine** → consolidate/absorb/refine with the `learning-loop` skill, mine external repos with `mining`. Everything up to a PR may run autonomously; nothing merges to `main` `skills/**` without a human.
- **Building or QA'ing an app** → the app code lives in a robium-apps checkout; learnings output still lands in THIS repo's `learnings/`. The two-hats rule applies: use skills as a client would, log learnings, and do **not** edit skills mid-build.
- **CLI work** → `cli/` (the `robium-ai` npm package; publish from that dir — see `cli/README.md`).
- **Site / live-demo infrastructure** → the robium-website repo (Astro site + demo orchestrator; has its own CLAUDE.md with the deploy pipeline and Cloud Run facts). Demo *backends* live in robium-apps.

The sibling repos are `robium-ai/robium-apps` (applications + REGISTRY.md) and `robium-ai/robium-website` (site + orchestrator, own CLAUDE.md); the engine-era skill-update policy below still governs any `skills/**` edit regardless of which repo you launch from.

## Repo layout

```
skills/            24 robium skills (the plugin's core deliverable)
agents/            robium-architect subagent
archive/           frozen snapshots of prior skill versions
.claude-plugin/    plugin.json + marketplace.json
learnings/         dated hardening notes (input to the skill-update loop)
cli/               robium-ai npm package (install/doctor CLI; publish from here)
docs/              CHANGELOG.md + superpowers/ (specs & plans) + V2_VISION.md, legacy-memory/
notes/             working notes
```

## Commands

```bash
# Dev setup (contributors — NO secrets needed): installs uv + npm deps, runs validator.
./scripts/bootstrap.sh

# Maintainer-only: API keys (publish/deploy/RunPod/NGC/GCP) live in Doppler (robium/dev),
# never in git. Opt in, then prefix privileged tasks with `doppler run --`. See docs/secrets.md.
./scripts/bootstrap.sh --secrets      # or: DOPPLER_TOKEN=… ./scripts/bootstrap.sh (server)
doppler run -- <command>

# The skill test suite. Run after ANY change under skills/. Must print "Checked 24 skills: PASS", exit 0.
uv run skills/skill-author/scripts/validate_skills.py

# Manifest sanity check
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); print('OK')"

# Local install smoke test (run inside a Claude Code session)
/plugin marketplace add /path/to/robium
/plugin install robium@robium
```

## Plugin architecture

- `skills/<name>/SKILL.md` — 24 skills. Two axes: **umbrellas** (selection + cross-cutting practice: architect, integration, environments, skill-author, learning-loop, mining, data, visualization, simulation, testing, test-assets, live-demo) vs **tool skills** (mechanics of one library: ros2, nav2, gazebo, mujoco, lerobot, isaac-sim, rviz2, foxglove, rerun, isaac-lab, huggingface, cloud-run); and **deep** (has `references/` and `examples/`) vs **thin** (SKILL.md only, deepened later via the learnings loop).
- Routing: only `architect` knows the whole catalog (its body has the routing table); every other skill cross-references just its direct collaborators. Cross-references must stay **bidirectional and consistent** — if you change what a skill owns, check both sides.
- `skills/_TEMPLATE/SKILL.template.md` — the authoring skeleton. It is deliberately **not** named SKILL.md: plugin discovery picks up any `skills/*/SKILL.md`, and the skeleton once shipped as an installable `robium:_TEMPLATE` skill. Never rename it back.
- `skills/skill-author/` — the meta-skill: authoring workflow, quality bar (`references/quality-bar.md`), and the validator script. The validator, template skeleton, and quality-bar doc must never drift apart — update all three together.
- `agents/robium-architect.md` — one-shot research subagent that writes `docs/architecture-brief.md` into an app directory. Refinement happens in the main agent with the `architect` skill; the subagent is only relaunched for genuine re-architecture.
- `.claude-plugin/` — `plugin.json` + `marketplace.json` (single `robium` entry, `source: "./"`). Skills and agents are auto-discovered; the manifests don't list them.
- `archive/<name>/<old-version>/` — frozen snapshots of prior skill versions (browsable evolution history). Committed, never edited, never loaded as skills (plugin discovery only scans `skills/`).
- `docs/superpowers/` — the approved design specs and implementation plans. Source of truth for catalog shape, skill format, and the done bar (trial runs under `apps/`).
- `docs/CHANGELOG.md` — dated record of shipped work. History only; nothing forward-looking goes here.

## Applications — proving ground + reference library

### Registry (mandatory)

`REGISTRY.md` at the root of the robium-apps repo is the index of every app — stack, pass bar, what it can bootstrap, battle scars. Two rules:

- **Read it first** when starting any new app: if an existing app resembles the target, bootstrap from it (copy its structure/env/test shape, then diverge) instead of scaffolding from scratch.
- **Keep it current**: an app is not done until its registry card is added/updated (quick-index row + card, `verified` date = last smoke pass), in the same commit as the app change.

### Building apps

- One app per `<name>/` directory in robium-apps: own env, own tests, own `docs/architecture-brief.md` (written by the `robium-architect` agent at kickoff; refined afterward with the `architect` skill in the main conversation).
- Test-driven: an app is not done until its smoke test passes (robium `testing` skill's bar).
- Environment-first: uv or Docker per the robium `environments` skill; local and remote runs must reproduce identically.

### Capture learnings as you work (mandatory)

Append a bullet to `learnings/YYYY-MM-DD.md` **at the moment an event happens** (create the file on first note; use today's real date; append `-<app>` to the filename if two apps run the same day). Details — exact command, exact error, exact phrasing — are the valuable part and they evaporate by end of session. Capture ALL of these signal types, tagged `[skill-name]` or `[none]`:

- **Wrong/stale guidance** — a skill's command/config/fact failed or is outdated.
- **No skill fired** — you asked something a skill should cover and nothing triggered. Record the exact phrasing you used; it becomes an eval case.
- **Figured out from scratch** — trial-and-error, source-reading, or web research that a skill should have spared you. Highest-value entries.
- **Better method found** — the skill's way worked, but you found a superior approach (simpler command, newer API, cleaner pattern). Robium's bar is best-known-method; capture upgrades even when nothing broke.
- **Noise/verbosity** — the answer existed but was buried; prose that should be a table; duplication. Feeds the hardening prune pass.
- **Worked as documented ✓** — a non-trivial snippet/example ran exactly as written. Name the file/section; ✓ entries are the only evidence that promotes `status: unverified` examples to verified.
- **User-corrected approach** — the user overrode or corrected a skill-guided approach mid-session. Record the exact correction and what the skill had suggested; a correction is the strongest single-observation signal that guidance and reality disagree.

**Schema v2 (learning engine Phase 1):** entries follow the template in
`learnings/README.md` — first line `[skill] signal-type (seen Nx) <!-- id: lrn-MMDD-NN -->`,
then optional `symptom:` / `root-cause:` / `fix: … (check: …)` / `dead-ends:` /
`anchors:` / `source:` fields. Only the first line is mandatory mid-session.
Capture hooks also flag corrections and errors automatically into the gitignored
`.robium/queue.jsonl`; promote flagged items into a dated entry at the next
natural break — or say 'consolidate' (learning-loop; the SessionStart summary lists what's pending).

Good entry: names the skill (or "none"), what was expected, what happened, and — if known — the fix. "nav2 was confusing" is useless; "nav2 Quick start costmap YAML omits the inflation_layer block → robot hugged obstacles" is actionable.

**Evidence bar (write entries that can be absorbed):** where they exist, capture (1) the passing check that verified the fix, (2) the exact error/symptom verbatim, and (3) the dead-ends ruled out and why — absorption holds new knowledge to this three-part bar; an entry missing a part waits in `learnings/` as tentative until the evidence shows up. Append a `(seen 2x)` count when the same friction re-hits — recurrence is the strongest promotion signal. Project-local facts (this app's port, this repo's path) go to the app's README/brief, not `learnings/`.

### End-of-block retro (mandatory)

At the end of each work block (milestone or session), add one line per robium skill that loaded during the block, scoring: **fired** (triggered when it should, quiet when it shouldn't), **accurate**, **complete**, **lean**. A clean score still gets a line — "no findings under real load" is evidence too.

### Two hats, one gate

- **During a build**: use the skills as a client would. Do NOT edit robium's skills mid-build and do NOT quietly substitute your own knowledge — capture the learning (hooks catch most of it; write the entry when it's nuanced), then proceed however the build needs. Same-session skill edits are forbidden even when the fix looks obvious.
- **Capture is automatic; consolidation is autonomous-safe.** The `learning-loop` skill's consolidate mode may run without asking: its write surface is `learnings/`, `learnings/observations/`, and the evidence/evals sidecars — never SKILL.md or references content.
- **Absorption runs to a PR, never to main.** "Absorb", "update my skills", "run the loop" → the learning-loop skill drafts anchor-targeted deltas, `scripts/engine/apply_deltas.py` applies them on a `loop/absorb-*` branch (archive snapshot + version bump + changelog, enforced by the script), verification gates run (validator, trigger evals, flip gate), and the result is a PR with an evidence table. Merging is the human gate — Gate 1 is the observation `status:` field (visible and editable in git), Gate 2 is PR review. If you prefer the old conversational gates, invoke the modes interactively and approve each step; the pipeline doesn't schedule itself.
- **Between builds**: full refine passes (`learning-loop` refine mode) and mining runs (`mining`) — same PR gate.

## Tracker

**GitHub Issues is the tracker for forward work** — `robium-ai/robium` issues for skills, quality, launch readiness, and demos; robium-website owns site + demo infra. File an item in the repo that owns the output, and cross-reference rather than duplicating. Labels: kind (`skill`, `quality`, `launch`, `ops`, `later`, `idea`, `epic`, `demo`) plus `good-first-skill` on the contributor-funnel wishlist. A deferred item becomes an issue — never a code comment or a checked-in TODO list.

## Skill update policy (engine era — merge is the gate)

1. **No agent merges to `main` `skills/**`. Ever.** The engine may capture, consolidate, and draft absorb/refine PRs autonomously; a human merges. Mid-build sessions never edit skills directly — they capture; the pipeline absorbs. This holds in fully autonomous runs: autonomy extends to the PR, never past it.
2. **Direct skill edits outside the pipeline** (hand-fixing a typo, restructuring a section in conversation) still require the user's explicit ask, and still follow the mechanics: archive snapshot to `archive/<name>/<old-version>/`, version bump, changelog line, same commit. When in doubt, route through the pipeline — apply_deltas does the mechanics for you.
3. **Version + archive on every change** — unchanged from day one, now script-enforced: apply_deltas refuses to run without a clean snapshot slot; bump semantics (build/minor/major) per the quality bar; a major bump requires re-confirming the skill's `evals.yaml` in the same PR (co-evolving evals).
4. The canonical process lives in the `learning-loop` skill (delta format, promotion bar, refine passes) and `skills/skill-author/references/quality-bar.md` item 9 (versioning). If any doc contradicts this policy, this policy wins — fix the doc.

## Skill format rules (validator-enforced and review-enforced)

- Frontmatter: `name` + `version` + `description`, nothing else (`name` == dirname; description ≤1024 chars — it is the trigger surface: capability + "Use when" phrases + literal keywords + workflow position + negative scope). Sole exception: `isaac-sim` also has `compatibility`.
- `version: MAJOR.MINOR.BUILD` (validator-enforced). Bump semantics: build = small correction (typo, stale-fact refresh, one-line fix, keyword added to description); minor = content addition (new bullet/pattern, new reference or example file, trigger-surface expansion); major = restructure/re-scope (section overhaul, ownership change, description rewrite).
- Body <500 lines. Required sections in order: `## When to use this skill`, `## Key directives`, `## Quick start`, then `## Decision guidance` (umbrellas) or `## Usage patterns` (tool skills), `## Platform gotchas`, `## Customization`, `## References`, `## Changelog`.
- `references/` files: single-topic, ~5–10 KB, one level deep. `examples/` files: `status: unverified` marker + upstream source links until a trial run verifies them.
- Every skill states its delegation posture (embed / embed+links / point-upstream / delegate) as the first Key-directives bullet.

## Rules that reviews repeatedly caught violations of

1. **No backticked non-local file tokens.** Backticks around a path or filename are only for files inside the same skill's directory. Another skill's file is prose: "the `environments` skill's Dockerfile.ros2 example" — no backticks on the filename. The validator only catches `references/|scripts/|examples/`-prefixed paths in SKILL.md; bare filenames and reference-file prose escape it, so grep all files manually.
2. **Citation honesty.** Every version/status/API claim states how it was actually verified (direct fetch vs search synthesis). If a fetch 404'd or was blocked (docs.ros.org is chronically bot-blocked) and you used search-snippet synthesis, the citation must say so with a re-verify prompt. Never write "verified via direct fetch" otherwise.
3. **Never write version facts from memory.** ROS/Gazebo/Isaac/LeRobot release names, LTS windows, pairings, GPU floors, and CLI shapes change; verify against live docs at authoring time. Shared facts (distro split, Gazebo pairings, Isaac GPU floor) are stated in the owning skill — other skills cite that skill rather than restating numbers, so facts can't drift.
4. **Stale cross-skill qualifiers.** When adding a skill, sweep the repo for now-false claims about it ("not yet written" etc.) — use a newline-flattened grep; one stale qualifier survived three line-based grep rounds because it spanned a line break.
