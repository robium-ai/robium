# Robium Reference Applications Design Specification v2

**Status:** Revised draft (v1 by a Codex agent, 2026-08-05; v2 adapted to the real robium system same day)
**Audience:** Robium maintainers, contributors, and implementation agents
**Purpose:** Define a lightweight, repeatable standard for building reference applications that demonstrate Robium clearly and credibly.

v2 keeps v1's direction and principles and reconciles them with what already
exists: the `robium-ai` CLI (npm, `cli/` in the robium monorepo), the five
shipped apps in robium-internal-apps, REGISTRY.md, the learnings loop, the
promotion model, and the demo-gateway/orchestrator/bundled-viewer hosting
pattern proven by indoor-navigation.

## 1. Vision and principles

Robium reference applications are small, runnable examples that show how
Robium-equipped agents solve realistic robotics and embodied-AI problems.
Each application works as both a product demo and an engineering case study:
visitors understand the outcome quickly; developers can inspect, reproduce,
and adapt it.

1. **Useful before impressive.** Start with a recognizable problem and a measurable outcome.
2. **Runnable by default.** One documented command launches the default experience.
3. **Progressive disclosure.** Result first, then architecture, code, and depth.
4. **Realistic but bounded.** A complete vertical slice beats a broad, unfinished showcase.
5. **Portable.** Local first, then containers and hosted execution where appropriate.
6. **Observable.** Make state, decisions, sensor data, and failures visible.
7. **Framework-flexible.** Standardize the experience and contracts, not the UI framework.
8. **Honest.** Clearly distinguish live behavior, simulation, prerecorded data, and mocked components.
9. **(robium) Two hats.** Apps are built USING robium skills by an agent; every
   friction becomes a learnings entry (robium repo `learnings/`), and the skill
   pack hardens through the loop. An app that taught the skills nothing was
   built wrong.

## 2. Where apps live and how they are structured

Apps live one-per-directory in **robium-internal-apps** (private proving
ground). Polished apps are **promoted** to the public **robium-apps** showcase
as single clean commits; promotion is a copy, so every app is written
promotion-ready (README and paths make sense standalone). `REGISTRY.md` at the
internal repo root is the human catalog: quick-index row + card per app,
updated in the SAME commit as the app change.

Required files per app (merge of v1's tree and the shipped apps' shape):

```text
<app-id>/
├── README.md              # 5-minute quick start first; troubleshooting; cleanup
├── robium-app.yaml        # machine-readable contract (section 5)
├── Makefile               # the per-app command surface (section 4)
├── docs/architecture-brief.md   # written by the robium-architect agent at kickoff
├── src/                   # app code (colcon pkg, python pkg, ...)
├── tests/                 # smoke test = the pass bar
├── scenarios or profiles  # reproducible configurations (compose profiles,
│                          # config presets, or scripts; shape is app-specific)
└── docker/ or Dockerfile  # when the runtime rule (section 3) requires it
```

Optional: `ui/`, `assets/`, `docs/case-study.md`. Never commit large models,
recordings, or datasets; provide a download script or documented source with
version and checksum.

## 3. Runtime and execution strategy

**Decision rule, not a blanket default.** Pick the runtime by what the app
touches, following the robium environments skill:

- **ROS 2 / Gazebo / sim-heavy apps: Docker-first.** macOS cannot run these
  natively; one image, compose profiles as scenarios, all nodes of a scenario
  in one container (DDS multicast does not cross containers on macOS).
  Example: indoor-navigation.
- **Python/ML apps (LeRobot, MuJoCo, training/eval): uv-first.**
  `uv sync` + `uv run ...`, Python pinned, `uv.lock` committed. Docker is a
  documented exception when it would cost the accelerator (containers lose
  MPS on Apple Silicon). Example: imitation-manipulation, vla-language-learning.
- **GPU-cloud apps: remote-first.** The local machine is a thin client; the
  smoke test runs on the remote GPU and must not fake-pass off it.
  Example: quadruped-locomotion (RunPod).
- **Real-hardware apps: robot-first.** Setup steps live in the README;
  the smoke test is hardware-in-the-loop. Example: robot-teleoperation.

Whatever the runtime, the invariants are: reproducible from a clean clone,
config via environment variables (never embedded credentials), hardware
requirements documented, and a health/ready signal when the app runs as a
service.

### Hosted demos (cloud)

Optional, and appropriate for browser-accessible simulations and workloads
that need no local hardware. Use the proven robium pattern rather than
inventing per app:

- **Session gateway** in the container (single port: WebSocket tunnel with
  claim/hijack guard, `/start`, `/status` with boot log + RTF + countdown,
  `/shutdown`).
- **Orchestrator** (robium-website `demo-orchestrator/`) owns lifecycle and
  budgets; it is never in the data path. One `demos/<id>.json` per app.
- **Bundled viewer** when the app is viewer-centric: bake the Lichtblick web
  build into the image and serve it from the gateway, so the hosted iframe and
  the local `make demo` show the identical, self-contained experience
  (indoor-navigation two-flavor pattern).
- Resource limits, scale-to-zero, a reset mechanism, and a fallback
  screenshot/video are mandatory. Never imply prerecorded or simulated output
  is live hardware output.

## 4. CLI philosophy

Two layers, both already grounded in shipped code:

### 4a. The umbrella CLI: `robium-ai` (exists; grows an `app` noun)

`robium-ai` (npm, zero runtime deps) today does `setup`, `doctor`, `skills`.
Reference apps add an **`app`** command group; the noun is the app, and
scenarios are a flag:

```text
robium-ai app list                       # catalog from robium-app.yaml files
robium-ai app describe <id> [--json]     # metadata for humans and tooling
robium-ai app check <id>                 # preflight: doctor facts + app requirements
robium-ai app run <id> [--scenario NAME] # resolve and exec the app's verb/scenario
robium-ai app new <id> [--from <app>]    # scaffold by copying the closest existing app
```

`app run` and `app check` do not reimplement anything: they read
`robium-app.yaml` and exec the mapped command in the app directory, streaming
output. The apps repo is resolved by rule, never hardcoded: `--dir <path>`,
else `$ROBIUM_APPS_DIR`, else walk up from the current directory to the first
repo containing REGISTRY.md plus robium-app.yaml files.

Files stay within a small YAML subset so the zero-dependency CLI can parse
them: 2-space-indented nested maps, scalars, inline arrays, `{}`, quoted
strings, and comments. No anchors, no multi-line strings, no inline maps. `app check` layers `robium-ai doctor` facts (Docker, GPU, disk,
Python/uv) against the app's declared `requirements`. `app new` follows the
registry's bootstrap rule: copy the closest shipped app and diverge, instead
of abstract templates. Every command supports non-interactive use and `--json`
where output is data.

### 4b. The per-app surface: Make verbs (exists in all five apps)

The stable, agent- and human-facing entry point per app is its Makefile.
Standard verbs (an app may add more):

```text
make build   # one-time environment/image build (omit when nothing to build)
make demo    # the default showable end-to-end experience
make smoke   # the pass bar; exits nonzero on failure
make check   # preflight: deps, files, ports, credentials, hardware
make down    # teardown/cleanup
```

Scenario-shaped targets (like indoor-navigation's `sim` / `slam` / `nav`) are
declared in `robium-app.yaml` so `robium-ai app run <id> --scenario slam`
resolves them. Commands fail with actionable messages; interactive prompts are
allowed only where a non-interactive path also exists.

## 5. Application metadata: `robium-app.yaml`

The machine-readable contract used by the umbrella CLI, the website catalog,
and validation. REGISTRY.md remains the human map (battle scars, bootstrap
notes); the yaml carries what tools need, and a future validator keeps the two
consistent.

```yaml
schema_version: "1"
id: indoor-navigation
name: Indoor navigation (TurtleBot 3 + Nav2)
summary: SLAM builds a map, Nav2 drives clicked goals, fully in sim, viewer bundled.
version: 1.0.0
status: stable             # experimental | stable | archived
license: Apache-2.0
tags: [navigation, ros2, nav2, gazebo, foxglove]

runtime:
  kind: docker             # docker | uv | remote-gpu | hardware
  entrypoint: make demo

verbs:                     # standard verbs -> actual commands (section 4b)
  build: make build
  demo: make demo
  smoke: make smoke
  check: make check
  down: make down

scenarios:                 # optional; name -> command + one-line description
  slam:
    command: make slam
    summary: drive the mapping route and save the map
  nav:
    command: make nav
    summary: navigation on the saved map, manual init pose

requirements:
  hardware: []             # e.g. [turtlebot4] for real-robot apps
  gpu: none                # none | optional | required | remote
  network: optional

demo:
  default_scenario: demo
  hosted: true             # has an orchestrator config in robium-website
  estimated_startup_seconds: 45

artifacts:
  thumbnail: assets/thumbnail.png
  case_study: docs/case-study.md   # optional in v1 of the schema
```

Required: `schema_version`, `id` (== directory name), `name`, `summary`,
`version`, `status`, `license`, `runtime`, `verbs.smoke`, `requirements`,
`demo`. Unknown fields are tolerated for forward compatibility.

## 6. Application lifecycle (mapped to existing practice)

1. **Proposal:** the app brief (section 11) plus a kickoff run of the
   robium-architect agent, which writes `docs/architecture-brief.md`.
2. **Prototype:** prove the end-to-end path with one reproducible scenario;
   milestones from the brief.
3. **Reference-ready:** `make smoke` green from a clean clone, metadata and
   docs complete, REGISTRY.md card landed in the same commit, learnings
   captured throughout.
4. **Published:** promoted to the public robium-apps showcase; website card
   live; hosted demo (if any) verified.
5. **Maintained or archived:** registry `verified` dates on re-verification;
   archived apps stay runnable with a shelved note (pattern:
   indoor-navigation-workspace) rather than silently rotting.

## 7. UX and visualization guidelines

No single framework. Match the tool to the task: Gradio (model I/O demos),
Streamlit (data dashboards), NiceGUI (Python-led UIs), React (polished custom
pages), Foxglove/Lichtblick (robotics telemetry; prefer the bundled-viewer
pattern for zero-setup), Rerun (spatial/multimodal timelines), RViz (native
ROS debugging, local only).

Whatever the framework, four things must be easy to find: the scenario/input,
the live or recorded output, system status, and an explanation of what is
happening. Clear start/stop/reset; visible progress for slow operations; never
hide failures; usable empty state. Visualizations answer a question: label
units and frames, distinguish measured from predicted, make time alignment
clear, and expose why the system decided what it did (paths, costmaps,
confidence, events). Accessibility basics apply everywhere.

## 8. Interactive demo architecture

Keep the pipeline independent from the UI:

```text
scenario/input -> app pipeline -> structured events/results -> UI or viewer
                          \-> logs, metrics, recordings
```

Adapters isolate cameras, robots, simulators, storage, and third-party APIs.
The same scenario runs from the CLI and the UI. Prefer structured events over
UI-specific callbacks so a second frontend needs no rewrite. Every
hardware-dependent app offers a fallback: simulation, recorded input, or a
clearly labeled guided walkthrough.

## 9. Website integration and documentation

The website generates catalog cards and detail pages from `robium-app.yaml`
plus repository content; the orchestrator's `demos/<id>.json` should
eventually be derived from the yaml's `demo` section rather than maintained by
hand (v1.1). Each card: name, one-sentence outcome, tags, maturity, hardware
needs, live-demo availability. Each detail page: visual preview, quick-start
command, architecture summary, expected result, repository link, case study.

Every app ships: a README (prerequisites, five-minute quick start,
configuration, expected output, troubleshooting, cleanup), one architecture
diagram or data-flow explanation, an article (below), at least one current
screenshot or recording, and explicit labels for simulated/recorded/mocked/
live components. Documented commands are tested exactly as written (the
clean-clone honesty check). Performance claims state hardware, data, scenario,
and measurement method.

### The article (case study as a living, portable document)

`docs/case-study.md` IS the app's public article. One markdown file is the
single source for the website's article pages, the frontpage feature slots,
and cross-posting to other mediums (Medium, dev.to): the body is pure
portable markdown, and everything the site needs is frontmatter it strips
when cross-posting:

```markdown
---
title: The article headline
summary: One or two sentences shown on cards and list pages.
app: indoor-navigation        # must equal the app id
date: 2026-08-05              # last substantive revision (living document)
hero: assets/trailer.gif      # app-relative short clip (or image); optional
featured: true                # frontpage candidates; the site shows up to 3
---

Article body: problem, constraints, approach, Robium components used,
major decisions, results, limitations, next steps.
```

Rules: the hero is a short clip (roughly 20 s or less, GIF/MP4) or a still
image, honestly labeled (sim footage reads as sim); date moves when the
content substantively changes - it is a living document, revised as the app
evolves; the website lists ALL articles on its articles page and shows up
to three featured ones on the frontpage. Ingestion follows the catalog
pattern: generated from the apps checkout at build time with a committed
fallback.

## 10. Growth, scaffolding, and roadmap

A curated portfolio, not an unbounded examples folder. The current five apps
already span navigation, imitation learning, language-conditioned VLA, real
hardware, and GPU-cloud RL; extend coverage deliberately (perception and
observability are the thinnest axes). Each app has a maintainer and maturity
status. Community contributions come through the proposal template, starter
issues, and review criteria.

Scaffolding is `robium-ai app new <id> --from <closest-app>`: copy a shipped,
battle-tested app and diverge (the REGISTRY.md "Bootstrap for" rule), rather
than generating from abstract templates.

Roadmap (status as of 2026-08-05):

- **v1 — shipped:** `robium-app.yaml` schema agreed; yaml files on all five
  shipped apps plus the archived workspace flavor; `robium-ai app
  list|describe|run|check`; `make check` per app, honestly scoped for
  hardware/remote-GPU apps. (robium#67, robium-internal-apps#2)
- **v1.1 — shipped:** `app validate` (per-field errors, --json) run by apps
  CI on every push/PR; `app new <id> --from <app>` scaffold-by-copy;
  website catalog ingestion from yaml (fetch-apps.mjs, /apps page);
  orchestrator configs derived from the yamls' demo.orchestrator sections
  (sync-demos.mjs, drift check in site smoke). (robium#67,
  robium-internal-apps#2, robium-website#11)
- **v1.2 — shipped:** hosted-demo contract extracted to the vendorable
  shared/demo-gateway package (env-configured, stdlib contract test in CI);
  compatibility badges machine-derived from the metadata; the LiveDemo
  island reusable by any gateway-contract demo. (robium-internal-apps#2,
  robium-website#11)
- **Later:** scenario registry, benchmark datasets, community galleries,
  cross-app composition, only after the core is reliable.

## 11. New reference app brief (unchanged from v1)

```markdown
# [Application name]

## Outcome
[What can a user accomplish or observe?]

## Audience and problem
[Who is it for, and what real problem does it demonstrate?]

## Robium value
[Which Robium capability is essential, and why?]

## Default scenario
[Exact input, expected behavior, and visible result.]

## Execution modes
- Local:
- Docker:
- Hosted:
- Hardware-free fallback:

## Success criteria
- [Reproducible functional outcome]
- [Usability or startup target]
- [Quality or performance measure, if relevant]

## Known limitations
[Hardware, environment, safety, accuracy, or scale constraints.]
```

### Release checklist

- [ ] `robium-app.yaml` complete and valid; `id` matches the directory.
- [ ] Clean clone runs the documented quick start exactly as written.
- [ ] `make smoke` green; `make check` catches the likely setup failures.
- [ ] Default scenario deterministic enough to review.
- [ ] No-hardware fallback available when the app targets hardware.
- [ ] Secrets and large assets not committed.
- [ ] REGISTRY.md row + card landed in the same commit as the app change.
- [ ] Learnings captured; end-of-block retro written.
- [ ] Docker or hosted execution included when justified; hosted demos use
      the gateway/orchestrator pattern.
- [ ] UI exposes input, output, status, reset, and failures clearly.
- [ ] Visualizations include units, frames, time, and provenance.
- [ ] README, architecture brief, and current media present.
- [ ] Article (docs/case-study.md) present with frontmatter (title, summary,
      app, date; hero + featured where applicable); body reads standalone.
- [ ] Claims identify their measurement conditions.
- [ ] License, maintainer, maturity, and support expectations clear.

## 12. Definition of success

Different contributors (human or agent) build recognizably consistent
applications without being forced into one technology stack. A visitor
understands each application in under a minute; a developer launches its
default or fallback scenario in about five minutes; a maintainer validates,
publishes, and eventually archives it through predictable contracts
(`robium-app.yaml`, Make verbs, REGISTRY.md, the smoke bar). And every build
feeds the loop: the skills that built the app come out sharper than they went
in.
