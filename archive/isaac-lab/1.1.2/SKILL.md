---
name: isaac-lab
version: 1.1.2
description: >
  NVIDIA Isaac Lab: reinforcement-learning and imitation-learning workflows on
  top of Isaac Sim: prebuilt environments and tasks, training runs, and
  exporting policies. Use when: 'isaac lab', 'GPU RL for robots', 'train in
  isaac', sim-to-real policy training in the NVIDIA stack. Load after
  isaac-sim basics are settled (same GPU requirements apply: RTX-class
  NVIDIA GPU, no macOS). Alternative ML path to lerobot; the architect skill
  decides between them. Not for: Isaac Sim setup itself (isaac-sim) or
  imitation learning on real-robot datasets (lerobot).
---

# isaac-lab

The GPU-parallel RL/IL training layer of robium's NVIDIA stack, built on top
of an already-running Isaac Sim: prebuilt environments and tasks
(`isaaclab_tasks`), training entry points for several RL libraries, an
imitation-learning path for generating and training on simulated
demonstrations, and exporting a trained policy. Isaac Lab
(`isaac-sim/IsaacLab`, current release **v3.0.0-beta2.patch1**, published
2026-07-02, verified via direct fetch of the GitHub releases API this
session) is NVIDIA's own framework layered on Isaac Sim, not a separate
product to install independently. Its main branch's own installation docs
state support for Isaac Sim 4.5/5.0/5.1 and recommend the latest 5.1.0
release specifically (verified via direct fetch of the installation docs
on 2026-07-10); that may trail the newest Isaac Sim release the `isaac-sim`
skill cites, so confirm the current supported-version pairing before
installing rather than assuming the two always track together.

## When to use this skill

- Running a prebuilt Isaac Lab task, training a policy with an RL library on
  top of a working Isaac Sim install, generating/training on simulated
  demonstrations, or exporting a trained policy for deployment.
- The trigger phrases in the description: 'isaac lab', 'GPU RL for robots',
  'train in isaac', sim-to-real policy training in the NVIDIA stack.
- Cross-references: go to the sibling skill instead when the question is:
  - **Isaac Sim itself is not installed/working yet** (GPU floor, container,
    USD scene, robot/sensor import, ROS 2 bridge) → `isaac-sim`. This skill
    assumes Isaac Sim is already running; it only adds the training layer on
    top.
  - **Imitation learning on datasets recorded from a real robot** (the
    LeRobotDataset format, `lerobot-train`/`lerobot-record`) → `lerobot`.
    This skill's own imitation-learning path (see Usage patterns) starts
    from demonstrations recorded *inside Isaac Sim*, not real hardware;
    that distinction is the actual boundary, not "imitation learning" as a
    category.
  - **Whether to use the NVIDIA stack (Isaac Sim/Lab) at all vs. LeRobot's
    own sim/eval tooling** → `architect` decides this, gated on the GPU
    floor (see Platform gotchas).
  - **Which simulator to use in general**, before Isaac Sim is chosen →
    `simulation`.
  - **Deciding data-sourcing strategy** (how much sim-generated vs. real
    data a project needs) → the `data` umbrella skill. This skill only
    covers the mechanics of Isaac Lab's own demonstration-generation and
    training tools, not the sourcing decision.

## Key directives

- **Delegation posture: embed + links.** The install-on-top-of-Isaac-Sim
  sequence, task-ID convention, and the RL/IL/export commands below are
  embedded because no single upstream page walks a new robium project
  through all three together, but every command is sourced from
  `isaac-sim.github.io/IsaacLab`'s own docs or the `isaac-sim/IsaacLab`
  GitHub repo, fetched directly on 2026-07-10, rather than retyped from an
  older Isaac Lab release's memory. See References.
- **On a cloud GPU, prefer the prebuilt Isaac Lab image over a source
  install.** <!-- id: prefer-prebuilt-image --> `nvcr.io/nvidia/isaac-lab` (latest tag observed
  3.0.0-beta2-post1 on the NGC catalog 2026-07-26..28) bundles a matched
  Isaac Sim + Isaac Lab in one container, which sidesteps the version-
  pairing trap (below) and the multi-step source install. This is the
  battle-tested path from the go2-locomotion app on RunPod; the pip+source
  route in Quick start remains valid for a workstation you own. See
  `references/prebuilt-image-runpod.md` for the provisioning specifics
  (NGC auth, EULA env vars, the `/workspace` volume-shadow gotcha, and the
  entrypoint override), and the `environments` skill's GPU-and-remote
  reference for the general pod networking/SSH mechanics this builds on.
- **The GPU/driver floor is `isaac-sim`'s, not restated here.** <!-- id: gpu-floor-inherited-from-isaac-sim --> Isaac Lab
  runs inside Isaac Sim, so it inherits that skill's GPU requirement
  verbatim; check the exact minimum/recommended GPU and VRAM numbers there,
  don't re-derive or re-type them in this skill. Isaac Lab's own RL training
  workloads (many parallel environments) also want more VRAM headroom than a
  bare Isaac Sim scene; treat `isaac-sim`'s stated floor as a minimum, not a
  comfortable working point for large `--num_envs` runs.
- **Start from a prebuilt task before writing a custom environment.** <!-- id: start-from-prebuilt-task --> List
  and run an existing task first (see Quick start) to confirm the install
  works end to end with zero environment-authoring risk, the same
  "validate the pipeline before customizing" posture `lerobot` takes with a
  pretrained policy.
- **Never write task IDs, script paths, or CLI flags from memory.** <!-- id: no-task-id-facts-from-memory --> Isaac
  Lab's task registry and script layout change across releases (the top-level
  scripts directory was itself reorganized into `reinforcement_learning` and
  `imitation_learning` subdirectories); list the currently-registered
  tasks instead of assuming a task name from a prior release still exists,
  and re-verify script paths against `isaac-sim/IsaacLab`'s `main` branch
  before repeating one in a real project.

## Quick start

Source: `isaac-sim.github.io/IsaacLab`'s installation and quickstart docs,
and the `isaac-sim/IsaacLab` GitHub repo's scripts directory tree, fetched
directly on 2026-07-10.

**1. Confirm the GPU floor** <!-- id: confirm-gpu-floor --> : see the `isaac-sim` skill; do not proceed
until the target machine meets it.

**2a. Cloud GPU (preferred): pull the prebuilt Isaac Lab image.** <!-- id: cloud-gpu-prebuilt-image-step -->
`nvcr.io/nvidia/isaac-lab` bundles a matched Isaac Sim + Isaac Lab, so there
is no separate Isaac Sim install and no version-pairing to reconcile. See
`references/prebuilt-image-runpod.md` for the RunPod provisioning specifics
(NGC auth, EULA env vars, the `/workspace` volume-shadow gotcha, the
entrypoint override, and the observed image tag/driver/Python versions).

**2b. Workstation you own (alternative): install Isaac Sim via pip, then
Isaac Lab from source on top of it** <!-- id: workstation-pip-source-install --> (per-release version pins matter;
verify the current recommended Isaac Sim version against the installation
docs before pinning it):

```bash
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com
git clone https://github.com/isaac-sim/IsaacLab.git --branch main
cd IsaacLab
./isaaclab.sh --install
```

**3. List the registered tasks:** <!-- id: list-registered-tasks -->

```bash
python scripts/environments/list_envs.py
```

**4. Train on a prebuilt task** <!-- id: train-prebuilt-task-command --> with one of the shipped RL libraries
(`rsl_rl`, `skrl`, `rl_games`, `sb3`):

```bash
python scripts/reinforcement_learning/skrl/train.py --task=Isaac-Ant-v0 --headless
```

**5. Watch progress and evaluate/export**: see Usage patterns.

## Usage patterns

**Run a prebuilt task.** <!-- id: run-prebuilt-task-ids --> Task IDs follow `Isaac-<Name>-v0` (manager-based
workflow) or `Isaac-<Name>-Direct-v0` (direct workflow); `list_envs.py`
(Quick start) prints the full current table with entry points, rather than
guessing a name from a tutorial. `--num_envs=<n>` sets how many parallel
environments run (the GPU-parallel core of Isaac Lab's speed advantage);
drop `--headless` only for local interactive debugging on a machine with a
display, since it costs render throughput.

**Train + monitor.** <!-- id: train-monitor-tensorboard --> Each RL library ships its own `train.py` under its own
subdirectory of the reinforcement-learning scripts tree, with a matching
`play.py` for evaluation and checkpoint loading:

```bash
python scripts/reinforcement_learning/rsl_rl/train.py --task=Isaac-Cartpole-v0 --headless --num_envs=4096
```

Runs log to a timestamped directory under `logs/<library>/<task>/`; RSL-RL's
own agent config exposes a `logger` field (`tensorboard` by default, or
`wandb`/`neptune`, confirmed via direct fetch of `isaaclab_rl`'s RL-library
config on 2026-07-10); point `tensorboard --logdir logs/rsl_rl` at the run
directory to watch reward/loss curves live. `--max_iterations` overrides the
task's default training length for a short smoke run before committing to a
full one, the same small-scale-first posture `lerobot` uses for fine-tunes.

**Verified Go2 locomotion walkthrough.** <!-- id: go2-checkpoint-path-trap --> A battle-tested RSL-RL run on the
Unitree Go2 (task `Isaac-Velocity-Flat-Unitree-Go2-v0`, PPO), smoke,
full-training profile, reward/cost config, custom-robot scaffolding, and
checkpoint portability, lives in `references/go2-rl-workflow.md`. One trap
worth stating up front: RSL-RL writes checkpoints under the **experiment
name**, `logs/rsl_rl/unitree_go2_flat/<timestamp>/`, **not** the task ID, so
a smoke test asserting on a task-ID-shaped path fails even when training
succeeded. Reward and cost also live in config, not code (a cost is a reward
term with a negative weight); the reference names the exact files and the
3-layer weight-override chain.

**Evaluate and export a trained policy.** <!-- id: export-policy-jit-onnx --> `play.py` (same per-library
directory as `train.py`) loads a checkpoint and runs it in the environment;
for RSL-RL specifically, it also exports the policy to both TorchScript
(JIT) and ONNX under the checkpoint's `exported/` directory automatically,
confirmed by direct fetch of the RSL-RL `play.py` source on 2026-07-10, which
calls `export_policy_to_jit`/`export_policy_to_onnx` (or the older
`export_policy_as_jit`/`export_policy_as_onnx` helpers on RSL-RL < 4.0). This
exported artifact is the sim-to-real hand-off point; deploying it onto real
hardware is outside this skill's depth once exported.

**Imitation learning from simulated demonstrations.** <!-- id: sim-imitation-learning-path --> A separate
`imitation_learning/` script tree (`isaaclab_mimic`, `robomimic`, and a
`record_demos.py`/`replay_demos.py` pair under the tools scripts directory)
records teleoperated or scripted demonstrations *inside Isaac Sim* and trains a
policy on them; this is the sim-side imitation-learning path, distinct from
`lerobot`'s real-robot-dataset training (see When to use this skill). Treat
this as a pointer, not a full walkthrough; verify the current CLI against
the `imitation_learning/` and `tools/` directories before running it.

**Hand-off from LeRobot.** <!-- id: lerobot-isaaclab-arena-handoff --> `lerobot-eval --env.type=isaaclab_arena` loads
Isaac Lab Arena through LeRobot's EnvHub mechanism (`lerobot.envs.make_env`)
rather than this skill's own scripts; that's `lerobot`'s territory calling
into an Isaac Lab environment, not the reverse; see the `lerobot` skill's
eval-and-sim reference for that specific invocation.

## Platform gotchas

- **GPU floor is `isaac-sim`'s; don't re-derive it.** No macOS, RTX-class
  NVIDIA GPU required; see that skill for the exact minimum/recommended
  numbers and how they were verified.
- **Isaac Sim/Isaac Lab version pairing is narrower than "whatever's
  newest."** <!-- id: version-pairing-narrower --> Isaac Lab's `main` branch supports a specific Isaac Sim version
  window (4.5/5.0/5.1 as of 2026-07-10, recommending 5.1.0) rather than
  every Isaac Sim release; installing the two independently without
  checking this pairing is a common source of import-time failures. Re-check
  the installation docs' compatibility statement before pinning versions in
  a real project.
- **Headless is the default for real training runs, same as `isaac-sim`.** <!-- id: headless-default-training -->
  `--headless` avoids paying render cost for a GUI viewport during a
  training run with thousands of parallel environments; reserve the
  non-headless mode for short interactive checks on a machine with a
  display, per `isaac-sim`'s own headless-first guidance.

## Customization

- **Different task or robot:** `list_envs.py` (Quick start) is the source of
  truth for what's currently registered; pick an existing task close to the
  target robot/behavior before authoring a new one. When you do author one,
  a custom robot/task is an **external project, not a fork of Isaac Lab**:
  `./isaaclab.sh --new` scaffolds a standalone repo that pip-installs Isaac
  Lab and `gym.register`s the task. The in-repo "internal task" path is only
  for upstreaming and is auto-disabled whenever Isaac Lab is pip-installed
  (i.e. inside the prebuilt NGC container), so external-project is the only
  path there. See `references/go2-rl-workflow.md`; Isaac Lab's own tutorials
  (linked in References) cover task authoring in depth this skill does not
  duplicate.
- **Different RL library:** swap which library's subdirectory of the
  reinforcement-learning scripts tree you invoke (`rsl_rl`, `skrl`, `rl_games`,
  `sb3`); each wraps the same underlying Isaac Lab environment with that
  library's own agent config and CLI flags, so a task that works under one
  library isn't a guaranteed drop-in for another's config shape.
- **No local GPU meeting the floor:** don't try to run Isaac Lab without it;
  route to `lerobot`'s own sim/eval tooling (per `architect`'s
  manipulation-vertical guidance) or provision a remote GPU host meeting
  `isaac-sim`'s floor first.

## References

- `references/prebuilt-image-runpod.md`: the prebuilt `nvcr.io/nvidia/
  isaac-lab` image (observed tag 3.0.0-beta2-post1) and its RunPod
  provisioning specifics: NGC auth, EULA env vars, the `/workspace`
  volume-shadow gotcha, and the entrypoint override + stop→start. Points to
  the `environments` skill for the general pod networking/SSH mechanics.
- `references/go2-rl-workflow.md`: the verified Unitree Go2 RSL-RL run:
  task IDs, smoke and full-training profile, the experiment-name log-path
  trap, reward/cost-in-config layout and 3-layer override chain, the
  external-project route for custom robots, and checkpoint/script
  portability on a fresh pod.
- Upstream: [Isaac Lab documentation](https://isaac-sim.github.io/IsaacLab/)
  (installation, quickstart, and task/training concepts; primary source for
  this skill, fetched directly on 2026-07-10), [isaac-sim/IsaacLab GitHub
  repo](https://github.com/isaac-sim/IsaacLab) (the reinforcement-learning,
  imitation-learning, tools, and environments scripts subdirectories, fetched
  directly via the GitHub Contents API and raw file URLs this
  session; source of the exact script paths, task-ID convention, and
  export-format claims above). Sibling skills: `isaac-sim` (GPU floor,
  install, and the Isaac Sim instance this skill runs on top of), `lerobot`
  (alternative manipulation ML path; owns real-robot-dataset imitation
  learning and the `isaaclab_arena` EnvHub hand-off), `data` (data-sourcing
  strategy, including how much this skill's own demo-generation tools should
  contribute), `simulation` (simulator selection before Isaac Sim is
  chosen), `architect` (routes here, GPU-gated, decides `isaac-lab` vs.
  `lerobot`).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.1.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 1.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.1.0 (2026-07-31): hardened from the go2-locomotion RunPod L4 run (2026-07-26..28): added the prebuilt-image-runpod and go2-rl-workflow references, made the prebuilt `nvcr.io/nvidia/isaac-lab` image the preferred cloud path, and surfaced the experiment-name log-path trap and external-project custom-robot route.
- 1.0.1 (2026-07-12): skill-refiner run 1: provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
