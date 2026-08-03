# Robium v2 — Design

**Status:** Approved design — **partially amended**, see plan
**Date:** 2026-07-09
**Supersedes:** `docs/V2_VISION.md`
**Amended by:** `docs/superpowers/plans/2026-07-09-robium-v2-implementation.md`, Part I

> **Amendments.** Verification of this document's external assumptions (2026-07-09)
> invalidated four of them. §3 (Docker contexts as remote targets), §4 (vendoring the
> `diffusion_pusht` model card), the visualization note in §3 (Foxglove Studio), and the
> Build Order's go/no-go gate are superseded by Part I of the implementation plan.
> Read the plan's amendments before acting on §3, §4, or Build Order.

## Context

Robium has no implementation. The repository holds only `docs/legacy-memory/` — a retrospective on a prior, separate `robium-old` codebase that began as an ambitious robotics IDE, shrank into an undifferentiated CRUD app, and stalled — and `docs/V2_VISION.md`, an earlier "converged" MVP plan (ROS 2 Jazzy only, custom MCP server, TurtleBot3 flagship).

This document is the output of a from-scratch brainstorm that treated `V2_VISION.md` as a prior conclusion to pressure-test rather than settled ground. It draws on research into three existing projects: `agenticros/agenticros` (an agent-to-ROS2 bridge), GitHub's `spec-kit` (spec-driven development tooling), and `huggingface/skills` (HuggingFace's real-world implementation of the Agent Skills / `SKILL.md` convention). The scope first broadened beyond ROS 2, then re-converged on a design leaner than the original vision.

The old project's own retrospective (`docs/legacy-memory/06-analysis-and-lessons.md`) identified two lessons it never acted on: *the run moment is the product*, and *the catalog is the moat*. This design is built to reach a working run moment quickly — a 1-2 week MVP — while keeping the catalog format compatible with the wider Agent Skills ecosystem instead of inventing proprietary schemas.

## Thesis

AI coding agents write robotics code well but produce working robotics *environments* poorly. That gap widens as the ecosystem fragments across classical ROS 2, NVIDIA's physical-AI stack (Isaac Sim/Lab, GR00T), and HuggingFace/LeRobot.

Robium is a curated catalog of tested, runnable environments — packaged as *skills* — that an AI coding agent scaffolds and boots on a developer's behalf, instead of hand-rolling brittle glue code each time.

**Pains addressed, in priority order:**

1. **Mixing ecosystems.** Getting classical ROS 2 and a modern ML policy (LeRobot, GR00T) to work together.
2. **Per-framework setup.** Each ecosystem's own bespoke, fragile installation.
3. **Discovery.** Not knowing which tested options exist across frameworks for a given task.

**Primary user:** an AI coding agent, principally Claude Code, with a human directing and observing. Robium is not a human-first CLI or UI product in this MVP.

## Design Decisions

### 1. Distribution: Claude Code plugin plus a thin CLI

The earlier vision specified a custom MCP server built on FastMCP with typed tools. Research into `huggingface/skills` — the closest real-world precedent — showed HuggingFace distributes primarily as a **Claude Code / Cursor plugin marketplace alongside a CLI (`hf`)**, which skill bodies invoke via Bash. Their MCP server, `hf-mcp`, came later as a secondary layer on that same foundation.

Robium follows the same sequence: a catalog of skills plus a thin `robium` CLI that `SKILL.md` bodies instruct the agent to shell out to. This surrenders typed tool-call schemas and server-side gating, which is acceptable for an MVP, in exchange for a far smaller build surface and a proven distribution model.

An MCP server exposing skills as `skill://` URIs — following the in-progress SEP-2640 "Skills Over MCP" proposal — is a natural post-MVP layer on the same foundation.

**CLI surface:**

| Command | Purpose |
| --- | --- |
| `robium doctor` | Check the active target's capabilities (Docker, GPU/CUDA) |
| `robium target list` / `robium target set <name>` | Inspect and switch the active Docker context |
| `robium list` | List catalog skills, filtered by named facet flags (`--kind stack`, `--framework ros2`, `--requires-gpu`) |
| `robium create <skill> <dir>` | Scaffold a project from a skill, idempotently |
| `robium start` / `stop` / `status` / `logs` | Manage a scaffolded environment's lifecycle (`kind: stack` only) |

### 2. Catalog format: one unified "skill"

Every catalog entry is a single `SKILL.md`-based skill, compliant with the Agent Skills specification:

- `name` must equal its directory name; lowercase and hyphens only.
- `description` (≤1024 chars) is the only field loaded at discovery time, so it is written as an activation trigger — what the skill does, when to reach for it, and common wrong turns — not a summary.

All skills share one schema and one set of folder conventions. There is no second entry type, no separate manifest kind, and no dependency syntax between skills — HuggingFace has none either, and expresses composition in a skill's own description ("this skill coordinates X, Y, Z").

What differs between skills is *content*, recorded in `metadata.kind`:

| `kind` | Meaning | Additionally ships |
| --- | --- | --- |
| `stack` | A runnable environment | `docker-compose.yml`, `test.sh` |
| `module` | Integration knowledge, no environment of its own | — |
| `meta` | Knowledge about authoring robium itself | — |

This is a content distinction, not a structural one: `kind` drives filtering and tells robium whether `start`/`stop` apply, but every skill is read, validated, and installed identically. Of the MVP four, `nav-sim` and `manip-lerobot` are `stack`; `docker-patterns` is `module`; `robium-architect` is `meta`.

Robotics facets (`framework`, `robot`, `simulator`, `requires_gpu`, `use_case`) live inside the spec-legal `metadata:` map as a robium-defined schema, since the upstream specification deliberately leaves that map open.

**Progressive disclosure** governs the whole catalog, mirroring the Agent Skills model: `name` and `description` at discovery; the `SKILL.md` body on activation; bundled scripts and references only at execution. This lets the catalog grow without exhausting an agent's context.

**Per-skill layout:**

| Path | Required | Purpose |
| --- | --- | --- |
| `SKILL.md` | always | Frontmatter plus body, with inline snippets |
| `docker-compose.yml` | `kind: stack` | Base service definitions |
| `compose.<variant>.yml` | no | Compose override files, applied with `-f` — e.g. `compose.sim.yml`, `compose.gpu.yml` |
| `test.sh` | `kind: stack` | Headless smoke test |
| `scripts/` | no | Self-contained automation, e.g. PEP 723 `uv run` headers |
| `references/` | no | Vendored upstream docs (see §4) |
| `examples/` | no | Usage examples |
| `config/` | no | Robium-specific extra; not a spec convention |

`SKILL.md` bodies stay under roughly 500 lines and include inline code snippets directly. Deeper material moves into `references/`.

### 3. Execution: Docker contexts as targets

A *target* is a Docker context: the local socket by default, or a remote GPU box over SSH. `robium target set` switches the active context; `robium doctor` probes it for GPU and CUDA availability.

Skills declare `requires_gpu` in metadata, reconciled against the active target at two points. `robium create` **warns** when scaffolding a GPU-requiring skill onto a CPU-only target, since the user may intend to switch targets before running it. `robium start` **refuses** and exits non-zero, naming the unmet requirement, rather than failing deep in a container build.

This reuses a mechanism Docker already ships rather than building bespoke cloud orchestration. Auto-provisioning cloud GPU instances is out of scope: robium points at a machine the user already has. LeRobot's own documentation already covers running on NVIDIA Brev without a local GPU, which validates the pattern.

Every skill is **fully self-contained** — no shared base image, no `FROM` coupling, no dependency edges between skills. To keep authors from reinventing boilerplate without introducing that coupling, the `docker-patterns` skill holds annotated, copy-adaptable Dockerfile and Compose snippets: ROS 2 Jazzy base, GPU passthrough, Foxglove bridge, `rerun` wiring. Authors copy and adapt; they never inherit.

Visualization is **framework-native per skill**: Foxglove for ROS-2-topic-based skills, `rerun` for LeRobot-based skills. Forcing one tool across both ecosystems would fight their native conventions.

### 4. No invented syntax, including at the skill layer

A skill wrapping a library is a thin pointer to that library's own configuration and CLI syntax, never a robium re-abstraction of it.

Where an upstream project already publishes agent-facing documentation — LeRobot ships an `AGENT_GUIDE.md` with real Docker and CLI recipes — the skill **vendors a pinned copy** into `references/`, recording `source_url` and `source_commit` in metadata for later re-sync. Rewriting those instructions would guarantee drift.

Live external `skill://` references, pointing outside robium's catalog, are a documented future option once SEP-2640 stabilizes. Vendoring preserves the offline-first guarantee described next.

### 5. Offline-first, generated and validated metadata

The catalog ships inside the robium package. No registry fetch is needed for `doctor`, `list`, or `create` to work, because robotics development often happens on constrained or air-gapped networks.

The guarantee covers discovery and scaffolding only, not runtime. `robium start` still pulls Docker images, and `manip-lerobot` fetches its pretrained policy from the HuggingFace Hub on first boot. Robium never fetches *its own catalog* over the network.

`SKILL.md` frontmatter is the single source of truth. Everything else is generated from it:

- `scripts/generate_marketplace.py` regenerates `.claude-plugin/marketplace.json` and `AGENTS.md`, a plain-text fallback catalog for agents without native skill support.
- `scripts/validate_skills.py` enforces hard gates before a skill is catalog-ready: `name` equals directory name, name matches the required pattern, `description` is non-empty and within limits, frontmatter parses as a YAML mapping.
- `scripts/publish.sh --check` fails CI when regeneration would produce a diff, catching drift between hand-edited frontmatter and generated artifacts.

### 6. Idempotent, non-destructive scaffolding

`robium create` and any subsequent update never clobber hand-edited files.

At scaffold time robium writes `.robium/manifest.json` into the target project, recording the source skill, its version, and a SHA-256 for each generated file. On a later `create` into the same directory, robium recomputes each file's hash: where it still matches the manifest the file is regenerated freely; where it diverges the user's edit wins, the file is left untouched, and robium reports the skipped path. A user who wants the catalog's version back deletes the file and re-runs.

## Repository Layout

```
robium/
├── pyproject.toml
├── skills/
│   ├── nav-sim/            # SKILL.md, docker-compose.yml (+overlays), scripts/,
│   │                       # references/, examples/, config/, test.sh
│   ├── manip-lerobot/      # same shape; references/ vendors LeRobot's AGENT_GUIDE.md
│   ├── docker-patterns/    # examples only: annotated Dockerfile/Compose snippets
│   └── robium-architect/   # meta-skill: how to author a robium skill
├── .claude-plugin/
│   └── marketplace.json    # generated
├── AGENTS.md               # generated fallback catalog
├── scripts/                # repo tooling — distinct from each skill's own scripts/
│   ├── generate_marketplace.py
│   ├── validate_skills.py
│   └── publish.sh
├── src/robium/             # the thin CLI
│   ├── cli.py
│   ├── doctor.py
│   ├── target.py
│   ├── catalog.py
│   ├── scaffold.py
│   └── lifecycle.py
├── docs/
├── tests/
└── .github/workflows/ci.yml
```

`robium-architect` is robium's equivalent of HuggingFace's `hf-cli` bootstrap skill: the first thing installed, teaching an agent how to author everything else.

## MVP Flagship Skills

Two skills, chosen to prove the catalog scales across both a classical-robotics and an ML-heavy vertical.

**`nav-sim`** — the classical vertical. TurtleBot3, Nav2, Gazebo Harmonic headless, Foxglove. Carries over the earlier vision's already-vetted combination: CPU-friendly and local-first.

**`manip-lerobot`** — the ML vertical. LeRobot's `gym-pusht` simulated task driven by the pretrained public `lerobot/diffusion_pusht` policy, visualized with `rerun`. Requires no physical hardware, runs fully headless, and has a documented upstream Docker and cloud-GPU recipe. Its `references/` vendors LeRobot's `AGENT_GUIDE.md`.

`gym-pusht` was chosen over a real arm or an ALOHA/ACT setup because robium ships a reproducible container, not a hardware purchase, and because a pretrained public policy yields a working demo without a training run.

Real hardware (SO-100/101) and IsaacLab/LeIsaac training are explicit post-MVP catalog additions.

## Build Order

Risk-first, roughly 1-2 weeks.

1. **Days 1-3.** Hand-build `manip-lerobot` as plain docker-compose, with zero robium code. This is the largest unknown: LeRobot, `rerun`, and GPU target switching.

   **Go/no-go gate.** It must boot headless and render `rerun` output, on both a local target and a remote GPU context. If it cannot, stop: the CLI and tooling in later phases would be built on an unproven foundation, and the ML vertical — half the thesis — needs rethinking before anything else is written.

2. **Day 4.** Harden `nav-sim`, the lower-risk, already-vetted combination. Independent of phase 1 and parallelizable with it.
3. **Day 5.** Build the CLI — `doctor`, `target`, `list`, `create`, `start`/`stop`/`status`/`logs` — wired to Docker context switching and both flagship skills.
4. **Day 6.** Author `robium-architect` and `docker-patterns` from lessons learned building the two flagship skills. Write `generate_marketplace.py` and `validate_skills.py`.
5. **Days 7-10.** Buffer: CI, validation hardening, polish, demo recording.

Phases 1 and 2 are independent. Phases 3 and 4 depend on both, since the CLI is shaped by what the two flagship skills actually need, and the meta-skills document patterns discovered while building them.

## Verification

- Each skill ships a `test.sh`: a standalone headless smoke test proving the environment boots, runnable identically by a human or an agent.
- CI runs both flagship skills' `test.sh`. `nav-sim` runs on a standard runner. `manip-lerobot`'s GPU path runs on a GPU runner where available, otherwise it is skipped, exercising `doctor`'s graceful-degradation path.
- `scripts/validate_skills.py` runs in CI against every skill.
- `scripts/publish.sh --check` fails CI on any drift between frontmatter and generated artifacts.

## Non-Goals

Deferred deliberately, not overlooked:

- **MCP server and `skill://` exposure** (SEP-2640) — a post-MVP layer on the CLI and skills foundation.
- **Auto-provisioning cloud GPU instances** — the user brings their own machine and Docker context.
- **Web UI, hosted service, authentication.**
- **IsaacLab, GR00T, and real-hardware skills** — clear post-MVP catalog additions.
- **Live robot control.** Robium scaffolds and boots; visualization is the proof of life. An agent calling typed verbs against a running robot, as `agenticros` does, is a plausible later extension once environments run reliably.
- **Multi-agent ACP/A2A protocols.**
- **External or community skill registry** — the catalog ships inside the package.
- **Auto-upgrading skills** — installs stay version-pinned.

## Decisions Taken to Unblock Day One

- **License: Apache-2.0.** ROS 2, `agenticros`, and `huggingface/skills` all use it; its explicit patent grant matters in a robotics context. Reversible before any public release.
- **Package and binary name: `robium`.** Both the distribution and the CLI entry point.

## Open Questions

Does not block implementation.

- Whether robium's `metadata` facet schema should be formalized as JSON Schema now, or left informal until enough skills exist to generalize from. Deferring costs little: `validate_skills.py` can add facet validation later without changing any `SKILL.md`.
