---
name: lerobot
version: 1.0.0
description: >
  HuggingFace LeRobot for physical-AI manipulation: the LeRobotDataset
  format, loading and recording episodes, training policies (ACT, diffusion,
  pi0), evaluating in simulation, and teleoperation. Use when: 'lerobot',
  'manipulation policy', 'imitation learning', 'train a robot arm policy',
  'ACT', 'diffusion policy', physical-AI dataset/training/eval tasks. Core
  skill of the manipulation vertical; pairs with huggingface (hub
  mechanics), environments (uv-first install), and data (sourcing
  strategy). Not for: classical motion planning or the NVIDIA RL stack
  (isaac-lab).
---

# lerobot

The manipulation-vertical core tool skill for robium: the LeRobotDataset
format, loading and recording episodes, training imitation-learning and
VLA policies (ACT, Diffusion, Pi0/Pi0.5/SmolVLA and others), evaluating in
simulation, and teleoperation. LeRobot (`huggingface/lerobot`, PyPI package
`lerobot`, version **0.6.1** as of this session, `requires-python >=3.12`)
is HuggingFace's end-to-end robot-learning library — this skill embeds the
robotics-specific glue (dataset shape, training/eval CLI, sim envs,
teleoperation) and delegates hub mechanics (auth, upload/download, model
cards) to the `huggingface` skill's territory. LeRobot moves fast; every
command below is either a direct upstream docstring/doc example fetched
this session or marked with how it was verified — re-check before relying
on exact flags in a real project.

## When to use this skill

- Any manipulation/imitation-learning task: loading or recording a
  LeRobotDataset, training a policy (ACT, Diffusion, Pi0-family, SmolVLA,
  ...), evaluating a policy in simulation, teleoperating a robot arm.
- The trigger phrases in the description: 'lerobot', 'manipulation policy',
  'imitation learning', 'train a robot arm policy', 'ACT', 'diffusion
  policy'.
- Cross-references — go to the sibling skill instead when the question is:
  - Hub auth, dataset/model upload-download, model cards, repo management →
    the `huggingface` skill's territory; LeRobot's own `hf auth login`/
    `hf upload` commands are shown here only where a lerobot workflow
    requires them inline.
  - Whether to use uv or Docker, GPU passthrough, headless/remote display →
    `environments` (load first if not already decided; see Key directives).
  - Deciding *which* dataset(s) to source or combine for a task → the
    `data` umbrella skill's territory.
  - Rendering/inspecting recorded episodes in depth → the `rerun` skill;
    LeRobot's own `--viz` extra and `lerobot-dataset-viz` script wrap Rerun
    directly — cross-referenced here by name, not re-taught.
  - Classical motion planning (no learned policy) → out of scope repo-wide;
    this skill and the manipulation vertical are learning-based only.
  - The NVIDIA Isaac Lab RL stack (GPU-parallel RL/IL training environments,
    prebuilt tasks, policy export) → `isaac-lab`.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: embed + links.** The manipulation-specific glue
  (LeRobotDataset shape, training/eval CLI, which policies exist, sim envs
  shipped) lives in this skill and its references, because no single
  upstream page ties it together for a new robium project — but hub
  mechanics (auth, push/pull, model cards) are explicitly *not*
  re-explained here; they belong to the `huggingface` skill once it
  exists, and LeRobot's own `hf auth login`/`hf upload` invocations are
  shown inline only as far as a lerobot workflow needs them.
- **uv-first, per `environments`.** LeRobot is a pure-Python ML package —
  `environments`' decision tree routes it to uv, not Docker, unless the
  project also needs ROS 2 or another system dependency. LeRobot's own
  installation docs default to conda but explicitly document a uv path
  (`uv python install 3.12`, `uv venv --python 3.12`, PyTorch >= 2.10
  only) — this skill's Quick start uses `environments`' `uv add`/`uv run`
  pattern instead, since a robium project depends on `lerobot` as a
  package rather than developing it from source. See Quick start and
  the `environments` skill's uv-patterns reference.
- **Start from a pretrained/hub policy or an official example config
  before training from scratch.** Evaluate an existing hub checkpoint
  (e.g. `lerobot/diffusion_pusht`) in sim first to validate the eval
  pipeline end to end with zero training risk, and when you do train, start
  from `--policy.type=act` (or another shipped policy type) against an
  existing dataset — an official example config — rather than hand-rolling
  a new policy config. Only reach for `--policy.path=<hub-id>` to fine-tune
  an existing checkpoint, or a fully custom config, once the standard path
  has been verified working. See Quick start and
  `references/policies-and-training.md`.
- **Small-scale fine-tune before a long run.** Run a short `--steps` smoke
  training (low thousands, not tens of thousands) against the target
  dataset/policy combination first, confirm the loss curve and an eval
  pass both look sane, *then* scale `--steps` up for the real run. See
  `examples/train-act-command.md` and `references/policies-and-training.md`
  for the compute-hardware guide this scales against.
- **Never write LeRobot CLI flags, dataset schema fields, or the shipped
  policy/env list from memory.** LeRobot ships new policies, environments,
  and CLI scripts frequently, and its own docs note the dataset format
  itself has changed major versions (v2.1 to v3.0) — flags and script names
  that were correct in an older tutorial or a training run's memory are not
  a safe default. Every command and claim in this skill is marked with
  how it was verified this session (direct fetch of the `huggingface/lerobot`
  GitHub repo's README/`docs/source`/`src/lerobot` at the `main` branch, or
  the HF Hub API for dataset/model existence) — re-verify against
  `github.com/huggingface/lerobot` or `huggingface.co/docs/lerobot` before
  repeating a claim in a real project.

## Quick start

This walks through the manipulation-vertical trial-run backbone: a uv
environment, evaluating a pretrained baseline in sim, then a small-scale
fine-tune and re-evaluation — all against the same dataset/env pair
(`lerobot/pusht` dataset, `pusht` sim env) so every step is internally
consistent. Source: `huggingface/lerobot`'s README, `docs/source/installation.mdx`,
and `src/lerobot/scripts/lerobot_eval.py`'s own docstring example, fetched
directly this session.

**1. Set up a uv environment** (see the `environments` skill's uv-patterns
reference for the general pattern):

```bash
uv python pin 3.12          # LeRobot requires Python >=3.12
uv add "lerobot[core_scripts,training,pusht]"
```

`core_scripts` pulls the dataset/hardware/viz extras `lerobot-record`,
`lerobot-replay`, and `lerobot-calibrate` need; `training` adds `accelerate`
and `wandb`; `pusht` adds the `gym-pusht` sim environment used below. Install
`ffmpeg` for video decoding — `sudo apt install ffmpeg` (Linux) or
`brew install ffmpeg` (Apple Silicon) if on PyTorch >= 2.10, otherwise
`conda install ffmpeg -c conda-forge`. See `references/datasets.md` and the
`environments` skill's GPU guidance for the CUDA-wheel variant if training on
an NVIDIA GPU.

**2. Sanity-check the install:**

```bash
uv run lerobot-info
```

**3. Evaluate an existing pretrained policy in sim first** (validates the
eval pipeline before any training — the "start from pretrained" directive).
This is `lerobot_eval.py`'s own docstring example, fetched directly:

```bash
uv run lerobot-eval \
  --policy.path=lerobot/diffusion_pusht \
  --env.type=pusht \
  --eval.batch_size=10 \
  --eval.n_episodes=10 \
  --policy.device=cuda   # or mps / cpu — see Platform gotchas
```

**4. Small-scale fine-tune** an ACT policy on the same dataset — see
`examples/train-act-command.md` for the full command (a short `--steps`
smoke run before scaling up).

**5. Re-run step 3's eval command** with `--policy.path` pointed at your new
checkpoint's `outputs/train/.../checkpoints/last/pretrained_model` directory
to confirm the trained policy improves on the baseline.

For loading/recording datasets, see the Usage patterns below and
`references/datasets.md`; for the full policy/training picture, see
`references/policies-and-training.md`; for sim envs beyond `pusht`, see
`references/eval-and-sim.md`.

## Usage patterns

**Browse/load a hub dataset.** `LeRobotDataset(repo_id)` downloads and
caches a dataset from the Hub (`~/.cache/huggingface/lerobot/{repo_id}`);
`StreamingLeRobotDataset(repo_id)` iterates it directly from the Hub with no
local copy. Browse candidate datasets via the hub's `LeRobot` tag or the
hosted [dataset visualizer](https://huggingface.co/spaces/lerobot/visualize_dataset)
before committing to one — actually pulling/searching the Hub beyond that is
the `huggingface` skill's territory. See `references/datasets.md` and
`examples/load-dataset-snippet.py`.

**Visualize episodes.** `lerobot-dataset-viz --repo-id=<id> --episode-index=0`
renders a recorded/loaded episode through Rerun, locally or streamed from a
headless machine (`--mode distant`) — the visualization mechanics themselves
belong to the `rerun` skill; this skill only owns invoking the LeRobot-side
command. See `references/datasets.md` and Platform gotchas.

**Train a policy on an existing dataset.** `lerobot-train --dataset.repo_id=<id>
--policy.type=act --output_dir=<dir> --policy.device=<cuda|mps|cpu>
--policy.repo_id=<hub-id>` trains a fresh policy shaped to the dataset's own
state/action/camera features; swap `--policy.type` for another shipped
policy or `--policy.path=<hub-id>` to fine-tune an existing checkpoint
instead. See `examples/train-act-command.md` and
`references/policies-and-training.md`.

**Evaluate in a sim env.** `lerobot-eval --policy.path=<id-or-dir>
--env.type=<pusht|aloha|libero|...> --eval.n_episodes=<n>` runs rollouts in
a gym-vectorized sim env and reports success/reward metrics; multi-task
suites like LIBERO accept a comma-separated `--env.task` list. See
`references/eval-and-sim.md`.

**Record new episodes.** `lerobot-record --robot.type=<id> --teleop.type=<id>
--dataset.repo_id=<id> --dataset.num_episodes=<n> --dataset.single_task=<desc>`
drives a real robot via teleoperation, saves a LeRobotDataset locally, and
pushes it to the Hub on completion (`dataset.finalize()` must run first —
the CLI does this for you; hand-rolled recording loops must call it
explicitly). See `references/datasets.md`.

## Platform gotchas

- **GPU vs Apple Silicon (MPS) vs CPU training expectations differ by an
  order of magnitude.** `--policy.device` (`cuda`/`mps`/`cpu`, usually
  auto-detected) selects the accelerator. Per LeRobot's own compute-hardware
  guide (fetched directly this session): ACT on a single RTX 4090 does ~5
  epochs over a ~50-episode/45k-frame dataset in ~30-60 min; the same run on
  Apple Silicon (M1/M2/M3 Max, MPS) takes ~6-14 h. CPU-only is not a training
  target — use it only for a tiny smoke test (a few dozen steps) to confirm
  the pipeline runs, then move to a GPU (local, or `--job.target=<flavor>`
  on Hugging Face Jobs — see `references/policies-and-training.md`) for
  anything real. See the `environments` skill's GPU-and-remote reference for
  the general CUDA-driver/host-parity checklist; the CUDA-wheel variant itself
  (which `torch`/`torchvision` build LeRobot pulls) is covered in
  `references/datasets.md`'s install notes.
- **Headless eval/training on a remote server needs no display, but sim
  rendering backends do.** `lerobot-eval` and `lerobot-train` write videos
  to disk (`render_mode="rgb_array"`) and need no `$DISPLAY` at all — but
  MuJoCo-based sim suites (LIBERO) need an explicit headless rendering
  backend: `export MUJOCO_GL=egl` before evaluating on a server with no GPU
  display attached. `lerobot-dataset-viz` supports a `--mode distant
  --grpc-port=<port>` streaming mode so a local machine can `rerun
  rerun+http://<remote-ip>:<port>/proxy` against a dataset that never left
  the remote box — the general remote-visualization strategy (as opposed to
  X11 forwarding) is `environments`' territory; this is the LeRobot-specific
  invocation of it. See `references/eval-and-sim.md`.
- **Recording's keyboard control flow is more portable than teleoperation
  itself.** `lerobot-record`'s episode-boundary keys (`→`/`n` next, `←`/`r`
  re-record, `Esc`/`q` stop) work over X11, Wayland, and headless/SSH
  sessions as long as it runs in an interactive terminal — but keyboard
  *teleoperation* (driving the robot itself with the keyboard) needs a
  global key backend and only works on X11, a Windows desktop, or macOS with
  Accessibility permission granted, not Wayland or headless. Don't assume a
  working `lerobot-record` session implies keyboard teleop will also work
  remotely.

## Customization

- **Different sim env or dataset:** swap `--env.type`/`--env.task` and
  `--dataset.repo_id` together, keeping them paired — a policy's
  `input_features`/`output_features` are inferred from the dataset it
  trains on, and `lerobot-eval`'s env must expose matching observation/
  action shapes (LIBERO's `.images.*`-prefixed keys are a good example of
  this coupling). See `references/eval-and-sim.md`.
- **Different policy family:** `--policy.type=<act|diffusion|smolvla|pi05|...>`
  swaps the architecture; VLA-family policies (Pi0/Pi0.5/SmolVLA) need
  substantially more VRAM and their own pip extra (e.g. `lerobot[pi]`,
  `lerobot[smolvla]`) — see the compute table in
  `references/policies-and-training.md` before picking one for constrained
  hardware.
- **Real robot instead of sim:** the `--robot.type`/`--teleop.type` surface
  (`lerobot-teleoperate`, `lerobot-record`, `lerobot-rollout`) is the same
  CLI family used throughout this skill, but hardware bring-up (ports,
  calibration, camera indices) is robot-specific and only lightly touched
  here — see LeRobot's own hardware docs (linked in References) for a
  specific arm.
- **No local GPU:** add `--job.target=<flavor>` (e.g. `a10g-small`) to a
  `lerobot-train` command to run it on Hugging Face Jobs instead of locally;
  list current flavors/pricing with `hf jobs hardware`. See
  `references/policies-and-training.md`.

## References

- `references/datasets.md` — the LeRobotDataset v3.0 format (directory
  layout, Parquet+MP4 storage), loading/streaming, recording and
  `finalize()`, dataset editing tools, visualization, v2.1→v3.0 migration.
- `references/policies-and-training.md` — the shipped policy families (ACT,
  Diffusion, VQ-BeT, Pi0-family, SmolVLA, GR00T, and others), the
  `lerobot-train` CLI, compute/VRAM sizing, multi-GPU and Hugging Face Jobs.
- `references/eval-and-sim.md` — the `lerobot-eval` CLI, sim envs shipped
  (pusht, aloha, LIBERO and its suites, MetaWorld, RoboCasa, and others via
  EnvHub), headless rendering, and `lerobot-rollout` for real-hardware
  deployment.
- `examples/train-act-command.md` — a small-scale ACT training smoke-run
  command against `lerobot/pusht` (status: unverified — file header states
  the exact source and how it was checked).
- `examples/load-dataset-snippet.py` — loads and inspects `lerobot/pusht`
  with `LeRobotDataset`, matching the dataset the training example uses
  (status: unverified — file header states the exact source).
- Upstream: [huggingface/lerobot](https://github.com/huggingface/lerobot)
  (primary source for this skill, README + `docs/source/` +
  `src/lerobot/scripts/` fetched directly via raw GitHub URLs and the
  GitHub Contents API this session), [LeRobot
  documentation](https://huggingface.co/docs/lerobot/index) (mirrors
  `docs/source/`), [Hugging Face Hub API](https://huggingface.co/api/) (used
  to confirm dataset/model repo IDs referenced in this skill actually exist).
  Sibling skills: `huggingface` (hub mechanics), `environments` (uv-first
  install, GPU/remote), `data` (dataset sourcing), `rerun` (episode
  visualization), `isaac-lab` (NVIDIA RL stack), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->
