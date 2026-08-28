---
name: architect
version: 2.0.0
description: >
  Entry-point skill for shaping new robotics applications: lightweight
  brainstorming, project ideation, requirement/risk discovery, stack selection,
  comparing or choosing simulators/models/visualization, a first
  user-visible slice, and a concise architecture decision record. Use when:
  starting a new robotics app; 'brainstorm a robot app', 'build a robot app',
  'which robotics stack', 'choose between simulators', 'decide the simulator,
  model, robot, and visualization', 'what robotics project can we build',
  'cheapest useful demo', 'rethink the architecture', genuine re-architecture,
  'scaffold a robotics project', 'mobile robot',
  'robot arm', 'manipulation policy', 'navigation stack', 'let's do demo 1',
  or when requirements exist but the stack is unchosen. Load first for a new
  app, then route to domain skills. Excludes narrow maintenance work after stack
  selection and skill authoring (skill-author).
---

# architect

The entry point for a new Robium application. It combines a lean design
conversation with robotics stack selection, chooses the cheapest meaningful
proof, records decisions without freezing provisional assumptions, and routes
implementation to the skills that own each layer.

## When to use this skill

- Starting a new robotics application from a rough idea.
- Choosing or reconsidering the stack, simulator, embodiment, environment,
  data path, visualization, or compute target.
- Decomposing a multi-subsystem robotics idea into a first buildable slice.
- Writing a durable decision record for a new app or genuine re-architecture.
- Skip architect for a bounded change in an existing flow. Read the affected
  code and use the matching tool skill directly.

## Key directives

- **Delegation posture: route + embed decision logic.** Architect owns the
  product/stack choices and routing. Tool mechanics stay in the skill that owns
  them.
- **Brainstorm only where a real decision exists.** <!-- id: lean-brainstorming --> Inspect the repository and
  `robium-apps` registry first. Ask only questions whose answers materially
  change the first slice. For a genuine choice, offer 2–3 approaches with
  trade-offs and recommend one. Never announce a process classification.
- **One direction gate, then build.** <!-- id: one-direction-gate --> A new app or material architecture
  gets one rough direction approval. After that, proceed through implementation
  and verification; pause only for a material pivot, scope expansion, paid or
  publishing action, deployment, or safety concern.
- **Prove the riskiest assumption cheaply.** <!-- id: risk-first-slice --> Before polishing infrastructure or
  scaling compute, run the smallest probe that can disprove the stack and
  deliver the first user-visible working slice. Label provisional choices and
  update them when evidence changes.
- **Use a decision record, not a contract.** <!-- id: architecture-decision-record --> Create or update
  `docs/architecture-brief.md` for a new application or genuine
  re-architecture. It records validated decisions, provisional assumptions,
  risks, and authorized pivots. Bounded feature/fix work does not require a new
  brief or approval cycle.
- **Environment first, syntax verified.** <!-- id: env-first-route-environments --> Route reproducibility to
  `environments` before substantial code. Verify volatile versions, commands,
  and platform constraints against current primary sources or installed CLI
  help; never rely on memory.

## Quick start

1. **Read before asking.** Inspect the app registry, closest reference app,
   current repository, and available hardware/compute facts.
2. **Frame the first outcome.** Establish robot/embodiment, user-visible task,
   sim-vs-real target, and the pass/fail signal for the first slice. Record a
   reasonable assumption instead of asking about low-impact details.
3. **Compare only meaningful alternatives.** Recommend one stack. If cost,
   hardware, or an unfamiliar integration is uncertain, define a cheap spike
   that resolves it before full implementation.
4. **Write the decision record when warranted.** Use
   `references/brief-template.md` for a new app or re-architecture. Keep the
   core concise; add optional detail only when the system needs it.
5. **Bootstrap, then diverge.** Check `REGISTRY.md` in the sibling
   [robium-apps](https://github.com/robium-ai/robium-apps) repository. Copy the
   closest app's environment, test, and launch shape when one exists; otherwise
   use `references/scaffold-patterns.md`.
6. **Build the first slice.** Hand each phase to the lowest owning skill and
   update the decision record only when a decision or risk actually changes.

Use the Claude-only `robium-architect` agent only for an explicitly requested
or genuinely ambiguous heavy comparison that would otherwise flood the main
conversation. Normal new-app design stays in the main conversation.

## Decision guidance

### Choose the first vertical

- **Navigation:** `ros2` + `nav2` + `simulation` → `gazebo`, then
  `visualization` → `rviz2` or `foxglove`. Use `environments` before bring-up.
- **Learned manipulation:** `lerobot` + `data` + `huggingface`, with
  `simulation` selecting MuJoCo/Gazebo/Isaac as the task requires. Add
  `isaac-sim`/`isaac-lab` only after their NVIDIA GPU requirements are proven.
- **Hybrid or unfamiliar stack:** define module boundaries with `integration`,
  identify the costliest uncertainty, and spike that boundary before building
  the whole system.

### Route by build phase

| Decision or work | Owning skill |
|---|---|
| Environment/reproducibility | `environments` |
| Module boundaries, protocols, containers | `integration` |
| ROS 2 substrate | `ros2` |
| Mobile navigation/localization | `nav2` |
| Simulator selection/sensor fidelity | `simulation` |
| Modern ROS simulation | `gazebo` |
| Lightweight non-ROS manipulation sim | `mujoco` |
| NVIDIA photoreal simulation | `isaac-sim` |
| NVIDIA RL/IL training | `isaac-lab` |
| Manipulation policies/VLAs | `lerobot` |
| Dataset sourcing/collection strategy | `data` |
| Hub models, datasets, Jobs, Spaces | `huggingface` |
| Visualization selection | `visualization` |
| ROS desktop visualization | `rviz2` |
| Remote/web ROS visualization | `foxglove` |
| ML/data timelines | `rerun` |
| Test strategy and smoke bar | `testing` |
| Fixtures/worlds/datasets | `test-assets` |
| Public interactive demo | `live-demo` |
| Cloud Run deployment mechanics | `cloud-run` |
| RunPod GPU execution | `runpod` |
| External example mining | `mining` |
| Learning consolidation/absorption | `learning-loop` |
| Skill authoring/quality | `skill-author` |

## Platform gotchas

- Isaac Sim/Lab require a supported NVIDIA RTX-class GPU and do not run on
  macOS. Load `isaac-sim` and verify its current floor before selecting it.
- Native ROS 2/Gazebo development is Linux-centric. On macOS, choose a
  container or Linux remote through `environments`.
- Headless remote work needs web/recorded visualization (`foxglove` or
  `rerun`) rather than assuming RViz2/display forwarding.
- Cloud/GPU inventory, pricing, quotas, and framework versions are volatile.
  Verify them only when they affect the selected path; do not turn every design
  into a broad research pass.

## Customization

- Scale the decision record to the project. A small one-process demo may need
  only outcome, chosen stack, environment, pass bar, and risks. Add modules,
  communications, data, or rollout sections only when they contain decisions.
- A discovered constraint may change a provisional choice without invalidating
  the whole design. Record the evidence and pivot; request another direction
  decision only when the user-visible outcome or material scope changes.
- Decompose an idea with several independent products into ordered slices. Fully
  design only the first slice; record later slices as non-binding follow-ups.

## References

- `references/stack-selection.md`: simulator, middleware, and training decision
  trees; verify volatile defaults before use.
- `references/scaffold-patterns.md`: starting layouts for navigation and
  manipulation applications.
- `references/brief-template.md`: concise decision-record template with
  optional depth.
- `examples/architecture-brief-example.md`: filled hypothetical brief (status:
  unverified).
- Upstream: [ROS 2](https://docs.ros.org/), [Nav2](https://docs.nav2.org/),
  [Gazebo](https://gazebosim.org/docs/),
  [LeRobot](https://github.com/huggingface/lerobot),
  [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/), and the MIT-licensed
  [Superpowers brainstorming skill](https://github.com/obra/superpowers), whose
  useful exploration/alternatives/YAGNI principles were adapted here without
  its global classification and repeated-approval gates.

## Changelog

- 2.0.0 (2026-08-27): absorbed lightweight brainstorming into architect;
  replaced global classification/repeated approval with one direction gate;
  made the brief a scalable decision record; added risk-first/user-visible
  slicing; narrowed the heavy Claude architect agent; repointed bootstrapping
  to robium-apps.
- 1.9.0 (2026-08-24): route RunPod inventory, provisioning, diagnostics,
  validation, billing, and cleanup to the new generic `runpod` skill.
- 1.8.1 (2026-08-03): style pass; removed em dashes throughout.
- 1.8.0 (2026-08-02): routing: learning-loop added; retired skill-updater.
- 1.7.0 (2026-08-02): routing table gained mining; skill-author narrowed.
- 1.6.1 (2026-08-01): anchor IDs added to claim-bearing items.
- 1.6.0 (2026-08-01): routing table gained cloud-run.
- 1.5.0 (2026-07-31): routed MuJoCo manipulation simulation.
- 1.4.0 (2026-07-18): routing table gained test-assets.
- 1.3.1 (2026-07-18): refreshed transferred repository links.
- 1.3.0 (2026-07-15): added backlog kickoff triggers and prior brainstorming
  handoff.
- 1.2.0 (2026-07-13): routing map gained live-demo.
- 1.1.1 (2026-07-12): clarified dated provenance.
- 1.1.0 (2026-07-12): made scaffolding bootstrap-first.
