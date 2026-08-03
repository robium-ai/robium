# Robium v2 — Vision & MVP Plan

*Converged 2026-07-08/09 after brainstorming sessions. Supersedes all legacy
PRDs (see `legacy-memory/` for what came before and why it changed).*

## Thesis

**Agents are already good at writing robotics code; they are terrible at producing
working robotics environments.** Version hell, sim assets, bridges, QoS, launch
files — that's where every AI-assisted robotics session dies.

Robium is an **AI-agent-first robotics dev toolchain**: an MCP server backed by a
catalog of **tested, working stacks and human-readable modules** that glue together
the open-source robotics ecosystem (ROS 2, simulators, visualization, perception
stacks, models like GR00T, frameworks like LeRobot). The user talks to their agent
(Claude Code, etc.); the agent calls Robium to scaffold, boot, and manage real
robotics environments; the user watches and iterates.

We do **not** write algorithms. We curate, pin, glue, and continuously verify.
The tested stacks + captured know-how are the moat.

## Positioning in one line

"One command between your AI agent and a running, visualized robot."

## Terminology

- **Stack** — a runnable, tested environment: pinned docker-compose + scripts
  + test. What users scaffold and boot. (Native term in both Docker —
  "compose stack" — and robotics — "nav stack".)
- **Module** — the integration knowledge package for one ecosystem tool/
  library/model: a SKILL.md (usage, gotchas, upstream links), runnable
  examples, proven config snippets. Continuity with v1's vocabulary, minus
  v1's machine-readable contract machinery.
- The knowledge file is named `SKILL.md` because it's the standard Claude
  skill format, installed into scaffolded projects' `.claude/skills/`.

## Core product principles

1. **The run moment is the product.** Every milestone ends with something
   executing and visible. (Chief lesson from v1 — see legacy-memory/06.)
2. **One golden path that never fails** beats a hub of 100 flaky integrations.
3. **No invented syntax.** Only formats that already exist: docker-compose,
   Markdown, minimal skill frontmatter (name/description). No custom DSLs,
   no schemas of our own to maintain. Avoid speculative machinery.
4. **The agent is the composition engine.** Intelligence lives in the agent
   reading human-readable modules — not in validation engines, dependency
   resolvers, or capability graphs. Deterministic code only where exactness
   is required: compose stacks known to boot, and MCP tools that copy/run them.
5. **Design for the agent as the user.** Structured tool outputs; every error
   says what's wrong *and what to call next*.
6. **Local-first.** MCP server runs on the user's machine, scaffolds into
   their cwd, drives their Docker. Artifacts belong to the user (git-init'd).
   Hosted catalog later; hosted GPU sim much later.
7. **Headless sim + browser visualization.** No X11, no GUI-in-Docker — makes
   macOS/Windows/Linux behave identically.
8. **Pin inside standard files.** Versions live where they naturally belong:
   image tags/digests in compose files, version notes in module text.
9. **A learning isn't captured until it's written down where it's used**:
   fix the stack/config, note the why in the relevant module — same commit.

## Locked decisions

| Decision | Choice | Notes |
|---|---|---|
| Runtime model | **Local-first** | uvx-installable MCP server; user's Docker |
| Visualization | **Foxglove** via foxglove_bridge | Not OSS anymore (Lichtblick = OSS fork, same protocol) — keep bridge generic |
| Server language | **Python + FastMCP** | Matches robotics community & contributors |
| ROS distro | **Jazzy only** | One distro, deep and tested |
| Flagship robot | **TurtleBot3** in Gazebo Harmonic, headless | Lightest assets, best Nav2 pairing |
| Simulation | Gazebo Harmonic, CPU, headless in Docker | Isaac/Cosmos deferred |
| Catalog format | **Modules (Markdown) + stacks (compose)** | No custom metadata format |
| Catalog naming | `catalog/stacks/` + `catalog/modules/` | Chosen 2026-07-09 over skills/recipes; alternatives considered: guides, handbook, environments, blueprints |
| Catalog hierarchy | **Flat by kind** | Domain taxonomy stays OUT of paths (v1 trap); lives in descriptions, later search. Alternatives considered: domain-first tree, stack-centric nesting, everything-is-a-skill |

## Catalog: modules + stacks

The catalog contains exactly two kinds of things. No module.yaml, no contract
schemas, no capability graphs — structured metadata can be extracted later
*if* scale ever demands it.

### Modules — the knowledge units

One folder per ecosystem tool/library/model, standard Claude skill format:

```
catalog/modules/<name>/
├── SKILL.md      # human-readable: what it is, LINK to upstream (GitHub
│                 # repo, model address, docs), which version/tag is known
│                 # to work, how to use it, inputs/outputs in prose,
│                 # gotchas we learned, best practices
├── examples/     # runnable scripts, referenced from SKILL.md
└── config/       # proven config snippets stacks copy (e.g., the foxglove
                  # bridge params with the QoS tricks)
```

Modules point outward to the ecosystem (LeRobot's GitHub, GR00T on NGC, Nav2
docs) rather than restating it — we curate and link, we don't fork or vendor.
A module is only created once knowledge actually exists (usually discovered
while building a stack) — never speculatively.

**Knowledge levels** (all just Markdown, authoring burden stays small):

- **Architect** (exactly 1): how to work with Robium — the process. Doubles
  as the MCP server's `instructions`. ~1 page. Lives at
  `catalog/modules/robium-architect/`.
- **Capability pages** (grow as needed, folder appears with the first real
  alternative): neutral comparisons ("SLAM: slam_toolbox vs RTAB-Map —
  pros/cons, when to pick which"). The agent consults these to choose;
  individual modules don't self-promote.
- **Module SKILL.md** (one per tool): the folders above.
- **Stack SKILL.md** (one per stack): what this project is, what's running,
  how to extend it. Mostly assembled at scaffold time.

**Scaffold-time skill installation (key feature):** `create_project` copies
the relevant modules' skills + the stack skill into the generated project's
`.claude/skills/` — the user's agent automatically carries exactly the
expertise for their stack. Post-scaffold, architect/capability knowledge
stays server-side, fetched via MCP if the user wants to swap modules.

**Anti-drift:** examples in modules are runnable and exercised by stack
tests where practical. When a trick is discovered: fix the config/stack,
note the why in the module — same commit.

**Security note for the community era:** SKILL.md files are instructions
injected into agents — community-contributed modules are a prompt-injection
surface and will need review before merging.

### Stacks — the working environments

```
catalog/stacks/<name>/
├── docker-compose.yml   # THE artifact: pinned images, known to boot
├── README.md            # for humans
├── SKILL.md             # for agents: project entry point
├── scripts/             # demo/starting-point scripts (e.g., goto.py)
├── config/              # copied-in snippets from modules, tuned here
└── test.sh              # boots the stack, asserts basic health
```

- **The stack is the tested unit.** CI = run every stack's test.sh (weekly +
  on change). That's the whole quality-control story at this scale.
- Reuse happens the boring way: shared robium base images, config snippets
  copied from modules, links between SKILL.md files. When a fix lands in a
  module's config snippet, stacks that copied it get updated by hand (or by
  an agent) — acceptable well past 20 stacks.
- Scaffolding = copy stack folder + install skills + git init. Idempotent,
  never overwrites.

## Repository layout

One repo, three zones. Catalog ships inside the pip package (uvx works
offline; catalog+server versioned together; `catalog/` can split into its
own repo later without restructuring).

```
robium/
├── pyproject.toml              # one package → `uvx robium`
├── src/robium/                 # ZONE 1: MCP server (deterministic code)
│   ├── server.py               # FastMCP entry, 7 tools
│   ├── doctor.py  scaffold.py  lifecycle.py  catalog.py
├── catalog/                    # ZONE 2: content — no code logic
│   ├── modules/<name>/{SKILL.md, config/, examples/}
│   │   └── robium-architect/   # process skill; served as MCP instructions
│   └── stacks/<name>/{docker-compose.yml, SKILL.md, README.md,
│                       scripts/, config/, test.sh}
├── docs/                       # ZONE 3: V2_VISION.md + legacy-memory/
├── tests/                      # server unit tests (stacks self-test via test.sh)
└── .github/workflows/ci.yml    # server tests + boot every stack
```

Deliberately absent until needed: `catalog/capabilities/` (appears with the
first real alternative, e.g., second SLAM module), `images/` (custom base
images only when two stacks share a layer; MVP pulls pinned upstream images).

Scaffold output = normal user-owned repo: compose file + README + scripts/
+ config/ + `.claude/skills/` (stack + module skills) + git init.

## MVP scope (few days of dev)

An installable MCP server + two bulletproof stacks, demoable end-to-end in
Claude Code.

**Stacks:**
- **A — `ros2-workspace`**: Jazzy dev container + foxglove_bridge + demo node.
  "Hack on ROS 2 without installing ROS 2."
- **B — `nav-sim` (flagship)**: TurtleBot3 + Gazebo Harmonic (headless) + Nav2 +
  foxglove_bridge, with `scripts/goto.py` (Nav2 simple commander) as the
  agent's starting point for custom behavior.

**MCP tools (7):** `doctor`, `list_stacks`, `describe_stack`, `create_project`,
`start`, `status`/`logs`, `stop`.
- `start` is non-blocking; lifecycle observed via `status`/`logs`.
- `create_project` copies the stack, installs its skills into
  `.claude/skills/`, git-inits, never overwrites.
- `doctor` checks Docker daemon, disk, arch/platform, port conflicts.

**Modules in MVP:** robium-architect (1 page), foxglove-bridge, nav2,
turtlebot3 — plus the two stack SKILL.md files. All short, all real.

**The demo (launch asset):** user → Claude: "I want to experiment with robot
navigation" → agent scaffolds & boots via Robium → user opens Foxglove, sees
the robot → "make it patrol three waypoints" → agent (armed with the installed
nav2 skill) edits goto.py, runs it, robot moves. Record this; it answers
"why not just Claude?" visually.

**Build order (risk-first):**
1. **Day 1:** Hand-build stack B as plain docker-compose; prove it boots on
   macOS (Apple Silicon) with Foxglove connected. Zero Robium code. Highest risk.
2. **Day 2:** Python/FastMCP server wrapping scaffold + lifecycle tools.
3. **Day 3:** Stack A, `doctor`, module polish, README, demo recording.
   Cut stack A before cutting polish on B.

**Explicitly deferred:** web UI, auth, hosted anything, GitHub publishing,
catalog registry service, Isaac Sim / Cosmos / GR00T stacks (GPU), real
hardware profiles, Rerun bridge, multi-distro support, community contribution
pipeline, any machine-readable module metadata.

## Post-MVP direction (unordered candidate list)

- Weekly boot-test CI for all stacks (the moat industrialized).
- More stacks: manipulation (MoveIt 2), perception (camera + YOLO), SLAM,
  LeRobot data collection / imitation learning, rosbag record & replay.
- More modules: GR00T & Isaac ecosystem, Cosmos, popular drivers and sensors.
- Hardware profiles: tested real-robot bring-up (TurtleBot4, SO-ARM, …).
- Hosted catalog registry; cloud GPU sim streaming (the monetization story).
- Catalog as separate open repo (community contribution surface).
- Rerun/Lichtblick as alternative viz backends.
- `upgrade` tool to refresh existing scaffolds from updated stacks/modules.
- `search_catalog(query)` MCP tool once the catalog outgrows folder browsing
  (~20+ modules): plain full-text search first (SQLite FTS over modules +
  examples, return WHOLE runnable examples with context, never chunks);
  embeddings only if keyword search demonstrably fails — same tool signature,
  so retrieval can evolve grep → FTS → embeddings with no other changes.
- Long-term: verified example library as a moat — harvest real-world usage,
  CI-verify it boots, serve via search. "Runnable, tested robotics examples"
  is something docs and training data don't reliably provide.

## Open questions (to revisit, not blocking MVP)

- Name/branding of the MCP server binary (`robium` assumed).
- License (MIT vs Apache-2.0 — decide before publishing).
- Monorepo vs app+catalog split (start mono, split when community shows up).
- If/when the catalog gets large: extract structured metadata from modules
  (deliberately deferred — no invented formats until scale proves the need).
