# Go2 locomotion: a verified RL workflow

An end-to-end, battle-tested RSL-RL run on the Unitree Go2, exercised on a
RunPod L4 pod with the prebuilt Isaac Lab image (3.0.0-beta2-post1),
2026-07-26..28. Facts marked "verified against 3.0.0 source" were read out
of the Isaac Lab 3.0.0 source/docs in that session, not recalled.

## The verified pipeline (✓)

- **Task IDs:** `Isaac-Velocity-Flat-Unitree-Go2-v0` (train), plus
  `Isaac-Velocity-Flat-Unitree-Go2-Play-v0` and a `Rough` variant. Confirm
  the current names with `list_envs.py` (SKILL.md Quick start) rather than
  assuming these across releases.
- **Train script:** `scripts/reinforcement_learning/rsl_rl/train.py`.
  Default RL library is `rsl_rl` (PPO).
- **Smoke run:** `--num_envs 32 --max_iterations 10` → exit code 0,
  checkpoints written as `model_<iter>.pt`.
- **Benign headless warnings** to ignore on a clean run: OmniHub, X Server,
  materialx, usdrt.

## Critical: checkpoints land under the EXPERIMENT NAME, not the task ID

Checkpoints go to `logs/rsl_rl/unitree_go2_flat/<timestamp>/` — the subdir
is the **experiment name** `unitree_go2_flat`, **not** the task ID
`Isaac-Velocity-Flat-Unitree-Go2-v0`. A smoke test that asserts on a
task-ID-shaped log path will fail even though training succeeded. Assert on
the experiment-name path.

## Full training profile

- **4096 envs converges by ~iteration 300** (reward climbs from ≈ −0.5 to a
  ≈ +36 plateau; episode length saturates at the 1000-step max). The
  1000–2000-iteration defaults are refinement, not required for a walking
  policy — stop early once the plateau holds.
- **`save_interval` is a Hydra override**, not a CLI flag:
  `agent.save_interval=N` on the train command.
- **Render videos post-hoc**, not during training: run
  `play.py --checkpoint <path> --video --enable_cameras` (~2 min per
  checkpoint). This is preferred over in-training `--video`, which slows the
  run for footage you usually only want from a few checkpoints.

## Reward and cost live in CONFIG, not code

Reward and cost share a single `RewardsCfg` — a **cost is just a term with a
negative weight**. The per-step reward is `Σ weight · term() · dt`. Relevant
files (verified against 3.0.0 source):

- `locomotion/velocity/velocity_env_cfg.py` — the base `RewardsCfg`.
- `locomotion/velocity/mdp/rewards.py` — task-specific reward term
  functions.
- `isaaclab/envs/mdp/rewards.py` — the generic reward term library.

Weights override down a **3-layer chain**:
`velocity_env_cfg` → `config/go2/rough_env_cfg` → `config/go2/flat_env_cfg`,
with the flat config winning for the flat task. Kernels: reward terms use
`exp(-err²/std²)`; penalty terms use `sum(square(x))`.

## Custom robot / new task = EXTERNAL project, not a fork

To add a robot or task, scaffold an **isolated external project** with
`./isaaclab.sh --new`. It creates a standalone repo that pip-installs Isaac
Lab as a dependency and `gym.register`s the new task — you do not fork or
edit the Isaac Lab repo. The "internal task" path (editing the Isaac Lab
repo in place) is only for upstreaming, and it is **auto-disabled when Isaac
Lab is pip-installed** — which is exactly the case inside the prebuilt NGC
container. So on the prebuilt image, external-project is the only path.
(Verified vs the 3.0.0 doc: overview / own-project / template.rst.)

## Checkpoint portability across patch releases (✓)

An RSL-RL checkpoint (`model_1999.pt`, 984 KB) trained on Isaac Lab
3.0.0-beta2 loaded cleanly into 3.0.0-beta2-post1: same task → identical
observation/action dims and MLP shape, no size mismatch. This skips a
20–30-minute retrain when moving between patch images.

## Running custom scripts on a fresh pod

- **`/workspace` can be read-only for the `ubuntu` user** on a fresh pod →
  write your scripts and logs to `/data` (the non-`/workspace` volume path
  from the prebuilt-image-runpod reference) instead.
- **`play.py` imports a sibling `cli_args` module**, so launching it from
  `/data` throws `ModuleNotFoundError: cli_args`. Fix: set `PYTHONPATH` to
  the rsl_rl scripts directory (where `cli_args.py` lives) before running a
  copied/relocated `play.py`.
