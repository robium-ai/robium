# Robium Plugin — MVP Design

**Date:** 2026-07-10
**Status:** Approved
**Scope:** The robium plugin repo only. The companion `robium-applications` repo gets its own design cycle later; the MVP trial apps seed it.

## Context

Robium is an AI-agent-first robotics dev toolchain, delivered as a skills-heavy Claude Code plugin. The north star: when anyone builds a robotics application with a coding agent, they enable Robium and the agent gets a large capability boost — it knows which libraries/frameworks/tools fit, how to glue them together, which patterns actually work, how to test, and where to get data. Robium ships knowledge and curation, not a framework: natural language skills + example snippets + Dockerfiles + config samples + a few genuinely reusable helper scripts. No invented syntax or DSL.

Source material: `notes/raw-drafts.md` (original notes), `notes/brainstorm-seed.md` (brainstorm seed). Key precedent: `huggingface/skills` — HuggingFace's production implementation of the Agent Skills convention (agentskills.io), researched in detail for this design.

## Decisions log

| Decision | Choice |
|---|---|
| MVP audience | The author first; structure stays public-ready, but no onboarding/marketplace polish yet |
| Verticals | ROS mobile-robot navigation + LeRobot/physical-AI manipulation, developed in parallel |
| Spec scope | Plugin repo only; `robium-applications` designed later |
| Definition of done | Two trial runs (one per vertical) reach running results in a fresh session with the plugin enabled, plus one learnings-absorption cycle |
| Skill granularity | Umbrella (decision-level) + per-tool skills, across the whole catalog |
| Authoring machinery | `skill-author` meta-skill inside the plugin |
| Platforms | Claude Code only for MVP; format stays agentskills.io-compliant so Cursor/others are additive later |
| CLI | None; uv-run helper scripts inside skills |
| Upstream delegation | Hybrid by domain: delegate where good upstream skills exist (HF), embed where none do (ROS, NVIDIA) |
| Samples provenance | Curate upstream examples now, mark verified/unverified, verify through trial runs |
| Subagents | One `robium-architect` subagent |
| Catalog strategy | Full catalog thin-to-thick: all ~18 skills exist from day one; trial-critical ones get full depth |
| Naming | Bare domain nouns for umbrellas (`architect`, not `robium-architect` — the plugin namespace provides branding); tool names for per-tool skills (`nav2`, `lerobot`) |

## 1. Repo structure

```
robium/
├── .claude-plugin/
│   ├── plugin.json          # name, description, version, author, license, keywords
│   └── marketplace.json     # single "robium" plugin entry exposing all skills
├── skills/
│   ├── _TEMPLATE/           # fill-in skeleton enforcing the skill format
│   ├── architect/
│   │   ├── SKILL.md
│   │   ├── references/      # single-topic .md files, 5–10 KB each
│   │   ├── scripts/         # uv-runnable helpers (only where genuinely reusable)
│   │   └── examples/        # curated sample snippets, configs, Dockerfiles
│   ├── ros2/
│   ├── nav2/
│   └── ... (~18 skills, see catalog)
├── agents/
│   └── robium-architect.md  # the one subagent definition
├── docs/
│   └── superpowers/specs/   # design docs (this file)
├── notes/                   # raw-drafts.md, brainstorm-seed.md
├── README.md                # short; hand-maintained skills table for now
└── LICENSE
```

- **Single plugin, not a per-skill marketplace.** HF registers one plugin per skill for granular installs; Robium's pitch is "enable this plugin, get the boost," so `marketplace.json` has one `robium` entry with `skills: "./skills"`. HF-style machinery (per-skill entries, curated/internal manifest split, generator scripts, AGENTS.md fallback, Cursor manifests) is additive later — nothing in this layout blocks it.
- **agentskills.io compliance:** skill `name` equals its directory name; each skill is `SKILL.md` plus optional `references/`, `scripts/`, `examples/`; file references stay one level deep from SKILL.md (no chained references).
- **Install story (dev phase):** local path install, or `/plugin marketplace add robium-ai/robium-docs` → `/plugin install robium@robium`. No version-sync tooling until going public.

## 2. Skill format

### Frontmatter

Minimal, following HF practice:

```yaml
---
name: nav2                      # must equal directory name
description: >
  <capability summary>. Use when: <explicit trigger phrases>;
  <literal keywords users type>. <workflow-position marker, e.g.
  "Load after architect selects the nav stack.">
  Not for: <negative scope to prevent misfires>.
---
```

- The **description is the trigger surface** — written long (up to the 1024-char spec cap) with: capability summary, explicit "Use when" triggers, literal user keywords, workflow-position markers for skill chaining, and negative scoping. This mirrors HF's most effective convention.
- No `allowed-tools` (unused even by HF). `license`, `metadata`, `compatibility` only where meaningful (e.g. `isaac-sim` notes GPU requirements in `compatibility`).

### Body pattern

Target under 500 lines (~5000 tokens); depth goes to `references/`. Section order:

1. **When to use this skill** — expanded triggers; cross-references to sibling skills by name
2. **Key directives** — the guardrails ("never X", "always uv", "verify sensor rates before…")
3. **Quick start** — exact commands/snippets for the common path
4. **Decision guidance** (umbrellas) or **usage patterns** (tool skills)
5. **Platform gotchas** — macOS/Linux/GPU/remote-server notes
6. **Customization** — how to adapt the examples/configs
7. **References index** — one line per `references/*.md` and `scripts/*`, plus curated upstream links (official docs, example repos, existing plugins/skills)

### Conventions

- **Scripts:** run via `uv run scripts/foo.py`, self-contained with PEP 723 inline dependencies, helpful errors. A script exists only when genuinely reusable and repetitive; otherwise a snippet suffices.
- **References:** single-topic files, 5–10 KB, one level deep, never chained.
- **Delegation posture stated explicitly per skill:** e.g. `huggingface` says "install `hf-cli@huggingface/skills` and defer to it; robium adds only the robotics glue," while `ros2` embeds knowledge because no good upstream skill exists.
- **Examples:** curated from upstream (trimmed, with source links), each marked **verified** or **unverified**; trial runs and app iterations promote them to verified.
- **Changelog section:** skills modified by the learnings loop get a one-line dated note recording what battle-testing changed.
- `skills/_TEMPLATE/` captures all of this as a fill-in skeleton used by `skill-author`.

## 3. Skill catalog (18 skills)

Depth tiers per the thin-to-thick strategy: **deep** = full references/scripts/examples treatment now; **thin** = solid SKILL.md + curated upstream links now, deepened during iterations.

### Umbrellas (8)

| Skill | Depth | Role |
|---|---|---|
| `architect` | deep | Entry point: requirements → stack selection → scaffold plan; routes to all other skills; playbook for the architect subagent |
| `integration` | deep | Module boundaries, comms choices (topics/services/zenoh/gRPC), Dockerfiles, compose patterns |
| `environments` | deep | Virtual-env-first logic: uv/venv vs Docker decision, identical local/remote repro, GPU passthrough |
| `data` | thin | Sourcing strategy: offline datasets vs sim generation vs teleop collection |
| `visualization` | thin | Tool selection (rviz2 vs foxglove vs rerun) + visualization best practices |
| `simulation` | thin | Simulator selection (gazebo vs isaac-sim) + sensor simulation correctness |
| `testing` | thin | Test-driven robotics: smoke tests, sim-based regression, launch testing |
| `skill-author` | deep | Meta-skill: authoring/improving robium skills (Section 5) |

### Per-tool (10)

| Skill | Depth | Delegation posture |
|---|---|---|
| `ros2` | deep | Embed — no good upstream skill exists; core ROS 2 usage and package gluing |
| `nav2` | deep | Embed + link official docs/demos |
| `gazebo` | deep | Embed + link modern gz (Harmonic/Ionic) tutorials |
| `rviz2` | thin | Embed (small domain) |
| `foxglove` | thin | Embed + link Foxglove docs; key for the remote-server story |
| `rerun` | thin | Point heavily to Rerun's own examples/docs |
| `lerobot` | deep | Embed robotics glue + point to HF ecosystem |
| `isaac-sim` | deep | Embed + link NVIDIA docs (no upstream skill) |
| `isaac-lab` | thin | Embed + link |
| `huggingface` | thin | **Delegate** — install `hf-cli@huggingface/skills`; robium adds only robotics context |

### Routing rules

- Only `architect` knows the whole catalog; every other skill cross-references just its direct collaborators (`nav2` ↔ `gazebo`, `ros2`, `visualization`).
- Descriptions carry enough trigger surface that narrow questions fire the right skill directly without going through `architect` ("my costmap isn't updating" → `nav2`).

## 4. The architect subagent

One subagent definition: `agents/robium-architect.md`.

- **Role:** the "blank page" persona. Takes application requirements (robot type, task, hardware, sim-vs-real, budget/GPU constraints), runs the heavy research burst — comparing stacks, reading upstream docs, weighing trade-offs — in its own isolated context, using the `architect` skill as its playbook.
- **Output contract:** a structured **architecture brief**, which it MUST write to `docs/architecture-brief.md` in the application repo. Contents: chosen stack with reasoning, module breakdown, comms plan, env strategy (uv vs Docker), data plan, which robium skills to load per build phase, and open risks.
- **Lifecycle:** the subagent is one-shot. After it returns, the user talks to the main agent, which executes from the brief. **The brief file is the durable, living architecture contract:** all subsequent refinement happens in the main agent with the `architect` skill loaded, editing that same file. The subagent is relaunched only for genuine re-architecture pivots, producing a fresh brief version.
- **Boundaries:** research + brief only; it writes no scaffolding or project code. This keeps it side-effect-free and the noisy exploration out of the main conversation context.

No other personas for MVP — building, integrating, and debugging happen in the main agent with skills.

## 5. Authoring workflow (`skill-author`)

The machinery for how skills get born and improve — a first-class concern.

### Three authoring modes

1. **Fresh authoring** — new skill from `_TEMPLATE`: research upstream docs/examples, distill into the Section 2 format. Wraps Claude's own `skill-creator` (evals, description tuning) rather than reinventing it.
2. **Mining** — extract skills from existing code: point at repos (official demos, apps built *without* robium) and distill reusable patterns into new or existing skills.
3. **Hardening** — post-trial-run upgrades: consume learnings, promote thin skills to deep, mark examples verified once they've actually run.

### The learnings loop

- During any app-building session, friction is captured immediately in the app repo as dated notes: `learnings/YYYY-MM-DD.md` — wrong/missing guidance, stale samples, gaps where no skill fired, places the agent had to figure something out from scratch.
- Periodic hardening sessions (in the robium repo, `skill-author` loaded) consume those notes → skill edits → learnings marked absorbed. Edited skills get a changelog line.
- **Placement rule:** knowledge goes to the lowest skill that can hold it (a Nav2 costmap gotcha → `nav2`, not `architect`).
- **Recurrence rule:** anything appearing twice in learnings becomes a skill edit, not a third occurrence.

### Quality bar (enforced on every skill)

Template compliance; description-as-trigger-surface quality; under-500-line bodies; delegation posture stated; upstream links present; no invented syntax.

## 6. Validation & definition of done

### Repo-level checks (cheap, run any time)

- Every skill passes `skills-ref validate` (agentskills.io reference validator): name==dirname, frontmatter constraints, description length. `_TEMPLATE` is excluded — it is a skeleton, not a skill.
- Manifests parse; the plugin installs into Claude Code from a local path.
- Template drift check: required sections present in every SKILL.md.

### Trial runs (the real gate)

Both run in a fresh Claude Code session with the robium plugin enabled, inside a new `robium-applications` repo — rough is fine; these become its first proving-ground apps.

1. **Nav vertical:** "Build a mobile robot that navigates autonomously in simulation." Expected path: `architect` subagent → brief → ROS 2 + Nav2 + Gazebo scaffold, dockerized env, robot navigating between goals in sim, at least one viz tool live, a smoke test passing.
2. **Manipulation vertical:** "Train and run a manipulation policy on a simulated arm." Expected path: LeRobot (dataset selected/loaded via HF delegation, policy trained or fine-tuned small-scale, evaluated in sim), env repro via uv.

**Pass bar:** the agent reaches a running result with skills doing the heavy routing — no invented syntax, no getting stuck where a skill should have guided it. Rough edges are expected: every stumble goes into `learnings/` (that is the loop working, not the trial failing). Failures don't restart the trial — fix the skill via `skill-author`, resume the app.

**MVP done =** both trials reached a running result + one full learnings-absorption cycle back into the skills.

## Out of scope (deferred)

- `robium-applications` repo design (own brainstorm/spec cycle; seeded by the trial apps)
- Public release machinery: per-skill marketplace entries, curated/internal manifest split, generator scripts, README table generation, AGENTS.md fallback, Cursor/Gemini manifests, version-sync tooling
- A robium CLI
- Additional subagents (integrator, data, sim-runner) — only if iterations show need
- MuJoCo/Google-robotics per-tool skills — revisit after MVP
