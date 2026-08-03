---
name: architect
version: 1.6.1
description: >
  Entry-point skill for designing robotics applications with AI agents. Turns requirements (robot type, task, hardware, sim-vs-real, GPU/budget) into a full stack decision — middleware, simulation, data, visualization, training frameworks — plus a scaffold plan and a written architecture brief. Use when: starting any new robotics app; 'build a robot app', 'which robotics stack', 'scaffold a robotics project', 'mobile robot', 'robot arm', 'manipulation policy', 'navigation stack', backlog-driven kickoffs like 'let's do demo 1', 'do demo N', 'build the next demo'; or when requirements exist but the stack is unchosen. This is the entry-point skill of the robium plugin: load it first; it routes to every other robium skill per build phase. Not for: debugging an existing stack (use the matching tool skill) or authoring robium skills (skill-author).
---

# architect

The entry point to robium. Given a robotics application idea, this skill turns
requirements into a concrete stack decision — middleware, simulation, data,
visualization, and training frameworks — plus a scaffold plan and a written
**architecture brief**. It is the only skill that knows the whole robium
catalog; everything else is reached by routing from here. Load it first on any
new robotics app, then hand off to the domain skills for the actual build.

## When to use this skill

- Starting a brand-new robotics application from a rough idea ("build a mobile
  robot that navigates a warehouse", "train a manipulation policy on an arm").
- The requirements exist but the stack is unchosen, or half-chosen and you want
  a sanity check before committing.
- You need a durable, written architecture record the whole project builds from.
- You want the routing map: "which robium skill do I load for phase X?"
- Open-ended or backlog-driven kickoffs ("let's do demo 1", a vague feature
  idea) start with `brainstorming@superpowers` — it owns requirements-gathering.
  Architect takes over once requirements are settled (robot type, task,
  hardware, sim-vs-real, GPU) to make the stack decision itself, rather than
  brainstorming's own research improvising it.
- Cross-references — go straight to the tool skill, skipping architect, when the
  stack is already chosen and the question is narrow:
  - Debugging or configuring an existing stack → the matching tool skill
    (`nav2`, `ros2`, `gazebo`, `lerobot`, …). "My costmap isn't updating" is a
    `nav2` question, not an architect question.
  - Authoring or improving robium skills themselves → `skill-author`.
  - Deep-diving one decision (uv vs Docker, which visualizer) → the umbrella
    that owns it (`environments`, `visualization`); architect points you there.

## Key directives

- **Delegation posture: route + embed the decision logic.** The *decisions*
  (which stack, why) live here; the *how-to* lives in the skill each decision
  routes to. Never duplicate a tool skill's content — link to it.
- **Always produce or update `docs/architecture-brief.md` in the app repo.** <!-- id: always-produce-brief --> It
  is the living architecture contract — every later build step reads from it,
  and refinements edit it in place. No brief, not done. Use
  `references/brief-template.md` for its required sections.
- **Virtual-environment-first.** <!-- id: env-first-route-environments --> Reproducibility is decided before code: route
  the env question to the `environments` skill (uv/venv vs Docker) and record
  the choice in the brief. Do not let a project start with an ad-hoc setup.
- **Never invent syntax or tools.** <!-- id: never-invent-tools-verify-versions --> Recommend only real, current tools at
  versions you have verified — robium ships curation, not a framework. When a
  version fact matters (ROS 2 distro, Gazebo pairing, GPU floor), confirm it
  against current docs (e.g. [docs.ros.org](https://docs.ros.org/) for ROS 2
  distro/EOL status) rather than memory. See `references/stack-selection.md`
  for the verified defaults this skill ships with.
- **State open risks explicitly in the brief.** <!-- id: state-open-risks-explicitly --> Unverified assumptions (GPU
  availability, hardware you can't see, sim-to-real gaps) go in the brief's
  open-risks section, not silently into a decision.

## Quick start

**1. Collect the requirement checklist** (ask for anything missing; if a
critical item is still unknown, record the assumption in the brief rather than
guessing silently):

- **Robot type** — mobile base, arm/manipulator, humanoid, drone, custom?
- **Task** — navigate, manipulate/grasp, inspect, learn a policy, teleop?
- **Hardware** — real robot (which?), sim only, or sim-first then real?
- **Sim vs real** — where does the MVP need to run?
- **GPU** — is an NVIDIA RTX GPU available? VRAM? (gates Isaac Sim / Lab.)
- **Local vs remote** — laptop, workstation, or headless remote server?
  (drives the visualization choice — remote favors `foxglove`.)

**2. Pick a golden path.** The two MVP verticals:

- **Navigation** <!-- id: golden-path-navigation --> (mobile robot, autonomous nav in sim):
  `ros2` + `nav2` + `gazebo` + `visualization`
  → ROS 2 Jazzy (LTS) middleware, Nav2 for the nav stack, Gazebo Harmonic as
  the paired simulator, an RViz2 or Foxglove view. Dockerized env via
  `environments`. This is the classic, well-supported path — favor it when the
  task is "get from A to B autonomously."

- **Manipulation** <!-- id: golden-path-manipulation --> (arm, learned policy):
  `lerobot` (+ `isaac-sim` / `isaac-lab` *if a capable GPU is available*) +
  `huggingface` + `data`
  → LeRobot for policy training/eval (ACT, Diffusion, SmolVLA, π0), datasets
  and models sourced through the `huggingface` delegation, `data` for the
  sourcing strategy. Add `isaac-sim`/`isaac-lab` only when the GPU floor is
  met (see Platform gotchas); otherwise stay in LeRobot's own sim/eval tools
  and a CPU/uv env. Favor this when the task is "learn to grasp / manipulate."

**3. Write the brief.** Fill `docs/architecture-brief.md` from
`references/brief-template.md` — chosen stack + reasoning, module breakdown,
comms plan, env strategy, data plan, robium skills per phase, open risks.

**4. Scaffold — bootstrap-first.** <!-- id: bootstrap-first-scaffold --> Before laying anything out from scratch,
check the battle-tested sample registry: `REGISTRY.md` at the root of the
companion robium-applications repo
([github.com/robium-ai/robium-applications](https://github.com/robium-ai/robium-applications);
locally a sibling checkout when present). Each card names the stack an app
proves, what it can bootstrap, and its encoded battle scars. If an existing
app resembles the target (same vertical, overlapping stack), **bootstrap
from it** — copy its structure, env shape, and test shape, then diverge —
and note the donor app in the brief. Only when no card is close, lay out
the repo fresh per `references/scaffold-patterns.md` (ROS 2 app layout or
LeRobot app layout). Then hand each phase to its skill.

For the heavy version of step 2 (a full stack-comparison research burst that
keeps the noise out of the main conversation), launch the `robium-architect`
subagent; it runs this skill as its playbook and writes the brief.

## Decision guidance

The routing map. Architect is the only skill that sees the whole catalog; it
hands each build phase to the skill below. Grouped by phase.

### Design / architecture

| Skill | Hand off when… |
|---|---|
| `architect` | You are here — requirements → stack → brief → scaffold, and routing to everything below. |
| `integration` | Module boundaries and comms are the question: topics/services vs zenoh/gRPC, Dockerfiles, compose wiring across nodes. |
| `environments` | Deciding reproducibility: uv/venv vs Docker, identical local/remote repro, GPU passthrough. Resolve this early, per the env-first directive. |

### Middleware & motion

| Skill | Hand off when… |
|---|---|
| `ros2` | The app uses ROS 2 — core usage, packages, nodes, launch files, message/topic wiring. The substrate for the nav vertical. |
| `nav2` | Autonomous navigation for a mobile base — costmaps, planners, controllers, behavior trees, localization. |

### Simulation

| Skill | Hand off when… |
|---|---|
| `simulation` | Choosing a simulator or getting sensor simulation right, before committing to a specific engine. |
| `gazebo` | Simulating a ROS 2 robot — the paired sim for the nav vertical (Gazebo Harmonic ↔ ROS 2 Jazzy). |
| `isaac-sim` | Photoreal / GPU-accelerated sim or synthetic data — **only when the NVIDIA RTX GPU floor is met**. |
| `isaac-lab` | GPU-parallel reinforcement-learning environments on top of Isaac Sim — same GPU gate. |
| `mujoco` | Lightweight, contact-rich manipulation sim **without ROS** — a single-arm grasp / pick-and-place task (e.g. the SO-101), headless offscreen render, hand-rolled IK. The non-ROS, non-GPU-photoreal alternative to gazebo/isaac-sim; runs natively on Apple Silicon. |

### Learning & data

| Skill | Hand off when… |
|---|---|
| `lerobot` | Training or running a manipulation/imitation policy — the substrate for the manipulation vertical. |
| `huggingface` | Pulling datasets/models or pushing artifacts to the Hub — **delegate** to `hf-cli@huggingface-skills`; robium adds only the robotics glue. |
| `data` | Deciding where data comes from: offline datasets vs sim generation vs teleop collection. |

### Visualization

| Skill | Hand off when… |
|---|---|
| `visualization` | Choosing a viz tool or applying viz best practices, before picking a specific one. |
| `rviz2` | Classic ROS 2 visualization on a local Linux machine with a display. |
| `foxglove` | Web-based viz — the go-to for a **headless remote server** or cross-platform team viewing. |
| `rerun` | Timeline/multimodal logging for ML and perception debugging (heavy pointer to Rerun's own docs). |

### Verification & meta

| Skill | Hand off when… |
|---|---|
| `testing` | Standing up smoke tests, sim-based regression, or launch testing — plan this into the brief, don't bolt it on later. |
| `test-assets` | Sourcing the data tests run against — canonical worlds/models/datasets, fixture layout, goldens. Load with `testing` when planning the test setup. |
| `live-demo` | Publishing a finished app as a public interactive web demo — mission-control demo page, per-visitor Cloud Run sim instances, viewer handoff. Entry bar: the app's smoke test is green. |
| `cloud-run` | Deploying a headless robotics/sim/demo container to Google Cloud Run — build → Artifact Registry → `gcloud run deploy`, and the sim-on-Cloud-Run gotchas (no multicast, CPU-on-request, session affinity, ws timeout). The CPU deploy target live-demo builds on. |
| `skill-author` | Editing robium's own skills (fresh authoring, mining, hardening from learnings). Not an app-building skill. |
| `skill-updater` | End-of-session absorption: folding the current session's gotchas back into the robium skills. Not an app-building skill. |

See `references/stack-selection.md` for the decision trees behind these
hand-offs (middleware yes/no, simulator gazebo-vs-isaac, training framework).

## Platform gotchas

- **Isaac Sim / Isaac Lab are GPU-gated.** <!-- id: isaac-gpu-gate --> Per NVIDIA's current requirements
  ([docs.isaacsim.omniverse.nvidia.com](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)),
  the floor is an **RTX 4080 with 16 GB VRAM** (minimum), an RTX 5080 or
  better recommended (16 GB+ VRAM), and 32 GB+ system RAM (64 GB recommended;
  Isaac Lab RL training wants more of both). Linux (Ubuntu) is the primary
  target; **there is no macOS support**. If the GPU floor isn't met, do not
  route to Isaac — keep the manipulation path in LeRobot's own sim/eval
  tooling. Verify the current floor in `isaac-sim` before committing; treat
  GPU availability as an open risk if unconfirmed.
- **macOS / Apple Silicon** <!-- id: macos-no-native-ros2-gazebo --> cannot run the native ROS 2 + Gazebo desktop stack
  cleanly — plan for Docker (route to `environments`) or a Linux remote.
- **Remote / headless servers** <!-- id: headless-default-foxglove --> have no display for RViz2 — default the viz
  choice to `foxglove` (web UI) in that case, and note it in the brief.
- **ROS 2 distro choice:** <!-- id: ros2-distro-default-lyrical-jazzy-exception --> **Lyrical Luth** (LTS, GA 2026-05-22, supported to
  May 2031) is the current newest LTS — default new apps to it unless a
  dependency forces otherwise. Exception: the ROS 2 + Nav2 + Gazebo navigation
  vertical still defaults to **Jazzy Jalisco** (LTS, supported to May 2029) for
  now, because Nav2 has not yet shipped binary packages for Lyrical (tracked in
  `ros-navigation/navigation2#6123` as of 2026-07) — re-check before picking
  Lyrical for that path. Kilted Kaiju is non-LTS and nearing its own EOL
  (~Dec 2026); don't pick it as a new default. Record the chosen distro in the
  brief.

## Customization

- **Different robot/task:** re-run the requirement checklist and the decision
  trees in `references/stack-selection.md`. The two golden paths are starting
  points, not the only shapes — a drone-inspection app is still ROS 2 + a sim +
  viz, just with different nodes; a real-hardware manipulation app is LeRobot
  with the sim swapped for a hardware driver.
- **Adapt the scaffold:** `references/scaffold-patterns.md` gives a ROS 2 layout
  and a LeRobot layout; rename packages and prune directories your app doesn't
  need, but keep the `docs/architecture-brief.md` location fixed — tooling and
  every later phase expect it there.
- **Adapt the brief:** every section in `references/brief-template.md` is
  required, but its depth scales with the project — a one-robot sim demo needs a
  short comms plan; a multi-robot fleet needs a real one.

## References

- `references/stack-selection.md` — the decision trees: middleware (ROS 2
  yes/no), simulator (Gazebo vs Isaac), and training framework, with the
  verified version defaults this skill ships.
- `references/scaffold-patterns.md` — repo layouts for a ROS 2 app and a
  LeRobot app: directory trees plus what each directory holds.
- `references/brief-template.md` — the required sections of
  `docs/architecture-brief.md` (chosen stack + reasoning, module breakdown,
  comms plan, env strategy, data plan, robium skills per phase, open risks).
- `examples/architecture-brief-example.md` — a filled brief for a hypothetical
  diff-drive warehouse robot (status: unverified).
- Battle-tested sample apps + registry:
  [robium-applications](https://github.com/robium-ai/robium-applications) —
  `REGISTRY.md` indexes every app (stack, pass bar, bootstrap-for, battle
  scars); the bootstrap-first source for Quick start step 4.
- Upstream: [ROS 2 docs](https://docs.ros.org/), [Nav2 docs](https://docs.nav2.org/),
  [Gazebo docs](https://gazebosim.org/docs/), [LeRobot](https://github.com/huggingface/lerobot),
  [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/),
  [Isaac Lab](https://isaac-sim.github.io/IsaacLab/). The `robium-architect`
  subagent (`agents/robium-architect.md`) runs this skill as its playbook.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.6.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.6.0 (2026-08-01): routing table (Verification & meta) gains the new
  cloud-run skill — the Cloud Run deploy target for headless robotics/demo
  containers that live-demo builds on (issue #67).
- 1.5.0 (2026-07-31): route MuJoCo / non-ROS manipulation-sim tasks to the new mujoco skill.
- 1.4.0 (2026-07-18): routing table gains the new test-assets skill
  (test-data sourcing, paired with testing).
- 1.3.1 (2026-07-18): stale-fact refresh — robium-applications GitHub links
  repointed to the robium-ai org after the repo transfer (two occurrences;
  old URLs redirect).
- 1.3.0 (2026-07-15): description gains backlog-driven kickoff phrasing
  ('let's do demo 1', 'do demo N', 'build the next demo') after a real session
  missed the trigger; added a brainstorming↔architect handoff bullet to When
  to use this skill (brainstorming owns requirements-gathering, architect takes
  over for stack selection) after the two collided on being 'the' entry point
  and stack-selection research got duplicated by hand.

- 1.2.0 (2026-07-13): routing map gains the new `live-demo` skill
  (publish a finished app as a public web demo — born from the nav-trial
  demo deployment).

- 1.1.1 (2026-07-12): skill-refiner run 1 — present-tense 'this session' phrasing reworded (no meaning change) so the refiner's undated-provenance warning stays noise-free.

- 1.1.0 (2026-07-12): scaffold step made bootstrap-first — check
  robium-applications' REGISTRY.md for a resembling battle-tested app
  before scaffolding fresh; registry link added to References.
