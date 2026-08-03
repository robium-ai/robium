---
name: lerobot
version: 2.1.1
description: >
  HuggingFace LeRobot for physical-AI manipulation: the LeRobotDataset
  format, loading and recording episodes, training policies (ACT, diffusion,
  pi0) and VLAs (SmolVLA), evaluating in simulation, and teleoperation. Use
  when: 'lerobot', 'manipulation policy', 'imitation learning', 'train a
  robot arm policy', 'ACT', 'diffusion policy', 'smolvla', 'VLA',
  'vision-language-action', 'fine-tune a policy', physical-AI
  dataset/training/eval tasks. Core skill of the manipulation vertical;
  pairs with huggingface (hub mechanics), environments (uv-first install),
  and data (sourcing strategy). Not for: classical motion planning or the
  NVIDIA RL stack (isaac-lab).
---

# lerobot

The manipulation-vertical core tool skill for robium: the LeRobotDataset
format, loading and recording episodes, training imitation-learning and
VLA policies (ACT, Diffusion, Pi0/Pi0.5/SmolVLA and others), evaluating in
simulation, and teleoperation. LeRobot (`huggingface/lerobot`, PyPI package
`lerobot`, version **0.6.0** as of 2026-07-12 (PyPI-verified; re-check —
this number goes stale fast), `requires-python >=3.12`)
is HuggingFace's end-to-end robot-learning library — this skill embeds the
robotics-specific glue (dataset shape, training/eval CLI, sim envs,
teleoperation) and delegates hub mechanics (auth, upload/download, model
cards) to the `huggingface` skill's territory. LeRobot moves fast; every
command below is either a direct upstream docstring/doc example fetched
on 2026-07-10 or marked with how it was verified — re-check before relying
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
- **uv-first, per `environments`.** <!-- id: uv-first-install --> LeRobot is a pure-Python ML package —
  `environments`' decision tree routes it to uv, not Docker, unless the
  project also needs ROS 2 or another system dependency. LeRobot's own
  installation docs default to conda but explicitly document a uv path
  (`uv python install 3.12`, `uv venv --python 3.12`, PyTorch >= 2.10
  only) — this skill's Quick start uses `environments`' `uv add`/`uv run`
  pattern instead, since a robium project depends on `lerobot` as a
  package rather than developing it from source. See Quick start and
  the `environments` skill's uv-patterns reference.
- **Validate the pipeline with a tiny self-trained checkpoint; treat
  pre-0.6 hub checkpoints as unloadable.** <!-- id: pre-06-checkpoints-unloadable --> Since 0.6.0, `--policy.path`
  requires the processor-pipeline files (`policy_preprocessor.json` /
  `policy_postprocessor.json`) next to the weights, with no fallback when
  they're missing — older checkpoints, including `lerobot/diffusion_pusht`
  (still cited in upstream's own eval docstring), fail with
  `FileNotFoundError: Could not find 'policy_preprocessor.json'` (verified
  2026-07-12, manip-trial; check a hub repo's file tree for those JSONs
  before relying on it). The zero-risk eval-pipeline check is therefore a
  minutes-long smoke train (`--policy.type=act`, a few hundred `--steps`)
  followed by eval of that checkpoint — see Quick start. When you train
  for real, start from `--policy.type=act` (or another shipped policy
  type) against an existing dataset rather than hand-rolling a new policy
  config; reach for `--policy.path` fine-tuning only with a
  processor-era checkpoint. See `references/policies-and-training.md`. A
  fine-tuned VLA checkpoint's `policy_preprocessor.json` can also encode a
  *different* camera layout than its base checkpoint (e.g. a
  `--policy.empty_cameras` value baked in at fine-tune time that the base
  didn't have) — treat two checkpoints of the same policy family as
  non-interchangeable at eval until you've diffed their processor configs,
  not just their weights. See `references/policies-and-training.md`'s
  Fine-tuning a VLA on a non-matching camera layout section.
- **Small-scale fine-tune before a long run.** <!-- id: smoke-train-before-scale --> Run a short `--steps` smoke
  training (low thousands, not tens of thousands) against the target
  dataset/policy combination first, confirm the loss curve and an eval
  pass both look sane, *then* scale `--steps` up for the real run. See
  `examples/train-act-command.md` and `references/policies-and-training.md`
  for the compute-hardware guide this scales against.
- **Never write LeRobot CLI flags, dataset schema fields, or the shipped
  policy/env list from memory.** <!-- id: no-cli-facts-from-memory --> LeRobot ships new policies, environments,
  and CLI scripts frequently, and its own docs note the dataset format
  itself has changed major versions (v2.1 to v3.0) — flags and script names
  that were correct in an older tutorial or a training run's memory are not
  a safe default. Every command and claim in this skill is marked with
  how it was verified on 2026-07-10 (direct fetch of the `huggingface/lerobot`
  GitHub repo's README/`docs/source`/`src/lerobot` at the `main` branch, or
  the HF Hub API for dataset/model existence) — re-verify against
  `github.com/huggingface/lerobot` or `huggingface.co/docs/lerobot` before
  repeating a claim in a real project.

## Quick start

This walks through the manipulation-vertical trial-run backbone: a uv
environment, a small-scale training run, then eval of that checkpoint —
all against the same dataset/env pair (`lerobot/pusht` dataset, `pusht`
sim env) so every step is internally consistent. Source:
`huggingface/lerobot`'s README, `docs/source/installation.mdx`, and
`src/lerobot/scripts/lerobot_eval.py`'s docstring example (adapted — see
step 4); exercised end-to-end 2026-07-12 (manip-trial, lerobot 0.6.0).

**1. Set up a uv environment** <!-- id: uv-env-setup --> (see the `environments` skill's uv-patterns
reference for the general pattern):

```bash
uv python pin 3.12          # LeRobot requires Python >=3.12
uv add "lerobot[training,pusht]"
```

`training` adds `accelerate` and `wandb`; `pusht` adds the `gym-pusht` sim
environment used below. Add `diffusion` if you'll load *any*
diffusion-policy checkpoint — its deps sit behind that extra and loading
one without it raises `ImportError: 'diffusers' is required` (verified
2026-07-12, manip-trial). Add `core_scripts` only for the hardware CLIs
(`lerobot-record`/`-replay`/`-calibrate`); the train/eval/dataset-viz path
doesn't need it. Install
`ffmpeg` for video decoding — `sudo apt install ffmpeg` (Linux) or
`brew install ffmpeg` (Apple Silicon) if on PyTorch >= 2.10, otherwise
`conda install ffmpeg -c conda-forge`. See `references/datasets.md` and the
`environments` skill's GPU guidance for the CUDA-wheel variant if training on
an NVIDIA GPU.

**2. Sanity-check the install:** <!-- id: sanity-check-install -->

```bash
uv run lerobot-info
```

**3. Run a small-scale ACT training** <!-- id: act-smoke-training-step --> — see `examples/train-act-command.md`
for the full command (a short `--steps` smoke run before scaling up). Don't
reach for a hub pretrained baseline as the validation shortcut: pre-0.6
checkpoints can't load on current LeRobot (see Key directives), and as of
2026-07 no working processor-era PushT baseline exists on the Hub.

**4. Evaluate that checkpoint in sim** <!-- id: eval-checkpoint-sim-command --> (adapted from `lerobot_eval.py`'s
docstring example; `--eval.use_async_envs=false` added because the async
default crashes on shipped sim envs — see Platform gotchas):

```bash
uv run lerobot-eval \
  --policy.path=outputs/train/act_pusht_smoke/checkpoints/last/pretrained_model \
  --env.type=pusht \
  --eval.batch_size=10 \
  --eval.n_episodes=10 \
  --eval.use_async_envs=false \
  --policy.device=cuda   # or mps / cpu — see Platform gotchas
```

Metrics land in `<output_dir>/eval_info.json` under the top-level
`overall` key (`pc_success`, `avg_sum_reward`, `avg_max_reward`,
`video_paths`, ...) — older LeRobot used an `aggregated` key. A
few-hundred-step smoke policy scoring `pc_success` 0 is expected;
completion + numeric metrics is what this step validates.

**5. Scale up:** raise `--steps` for the real run, then re-run step 4's
eval against the new checkpoint to confirm it improves on the smoke
baseline.

For loading/recording datasets, see the Usage patterns below and
`references/datasets.md`; for the full policy/training picture, see
`references/policies-and-training.md`; for sim envs beyond `pusht`, see
`references/eval-and-sim.md`.

## Usage patterns

**Browse/load a hub dataset.** <!-- id: load-hub-dataset --> `LeRobotDataset(repo_id)` downloads and
caches a dataset from the Hub (`~/.cache/huggingface/lerobot/{repo_id}`);
`StreamingLeRobotDataset(repo_id)` iterates it directly from the Hub with no
local copy. Browse candidate datasets via the hub's `LeRobot` tag or the
hosted [dataset visualizer](https://huggingface.co/spaces/lerobot/visualize_dataset)
before committing to one — actually pulling/searching the Hub beyond that is
the `huggingface` skill's territory. See `references/datasets.md` and
`examples/load-dataset-snippet.py`.

**Visualize episodes.** <!-- id: visualize-episodes-rerun --> `lerobot-dataset-viz --repo-id=<id> --episode-index=0`
renders a recorded/loaded episode through Rerun, locally or streamed from a
headless machine (`--mode distant`); `--display-mode foxglove` serves it to
the Foxglove app instead, and `--save 1 --output-dir <dir>` writes a `.rrd`
file with no viewer at all (headless/CI-friendly; verified 2026-07-12,
manip-trial). The visualization mechanics themselves belong to the `rerun`
skill; this skill only owns invoking the LeRobot-side command. See
`references/datasets.md` and Platform gotchas.

**Train a policy on an existing dataset.** <!-- id: train-policy-command --> `lerobot-train --dataset.repo_id=<id>
--policy.type=act --output_dir=<dir> --policy.device=<cuda|mps|cpu>
--policy.repo_id=<hub-id>` trains a fresh policy shaped to the dataset's own
state/action/camera features; swap `--policy.type` for another shipped
policy or `--policy.path=<hub-id>` to fine-tune an existing checkpoint
instead. See `examples/train-act-command.md` and
`references/policies-and-training.md`.

**Evaluate in a sim env.** <!-- id: eval-sim-env-command --> `lerobot-eval --policy.path=<id-or-dir>
--env.type=<pusht|aloha|libero|...> --eval.n_episodes=<n>` runs rollouts in
a gym-vectorized sim env and reports success/reward metrics; multi-task
suites like LIBERO accept a comma-separated `--env.task` list. See
`references/eval-and-sim.md`.

**Record new episodes.** <!-- id: record-episodes-command --> `lerobot-record --robot.type=<id> --teleop.type=<id>
--dataset.repo_id=<id> --dataset.num_episodes=<n> --dataset.single_task=<desc>`
drives a real robot via teleoperation, saves a LeRobotDataset locally, and
pushes it to the Hub on completion (`dataset.finalize()` must run first —
the CLI does this for you; hand-rolled recording loops must call it
explicitly). See `references/datasets.md`.

## Platform gotchas

- **GPU vs Apple Silicon (MPS) vs CPU training expectations differ by an
  order of magnitude.** <!-- id: gpu-mps-cpu-training-speed --> `--policy.device` (`cuda`/`mps`/`cpu`, usually
  auto-detected) selects the accelerator. Per LeRobot's own compute-hardware
  guide (fetched directly on 2026-07-10): ACT on a single RTX 4090 does ~5
  epochs over a ~50-episode/45k-frame dataset in ~30-60 min; the same run on
  Apple Silicon (M1/M2/M3 Max, MPS) takes ~6-14 h. That MPS anchor is for
  640x480-image datasets — small-observation sims run an order of magnitude
  faster: measured 2026-07-12 (manip-trial), ACT on `lerobot/pusht` (96x96,
  batch 8) sustained 11.6 steps/s on an M2 Pro (~5 min/epoch), so don't rule
  out MPS for small-sim work. That MPS viability does not extend to VLA
  fine-tuning, though: never fine-tune a VLA (SmolVLA, Pi0-family) on MPS —
  `--policy.device=mps` is accepted and the run starts, but a SmolVLA
  fine-tune on MPS measured only ~2h for 20 of ~20,000 steps (verified
  2026-07-14, vla-trial), i.e. on the order of weeks to complete. MPS/CPU
  are for VLA inference and for proving the training loop starts, not for
  actually training a VLA — our own train-smoke check ran 5 steps on CPU at
  ~60s/step to confirm the pipeline runs, nothing more. CPU-only is not a
  training
  target — use it only for a tiny smoke test (a few dozen steps) to confirm
  the pipeline runs, then move to a GPU (local, or `--job.target=<flavor>`
  on Hugging Face Jobs — see `references/policies-and-training.md`) for
  anything real. See the `environments` skill's GPU-and-remote reference for
  the general CUDA-driver/host-parity checklist; the CUDA-wheel variant itself
  (which `torch`/`torchvision` build LeRobot pulls) is covered in
  `references/datasets.md`'s install notes.
- **MPS *eval* is fully workable and matches CPU** <!-- id: mps-eval-workable --> (✓ observed 2026-07-12).
  On lerobot 0.6.0 / torch 2.11, `lerobot-eval` on Apple Silicon runs fine
  and `--policy.device=mps` vs `cpu` produced identical rollouts; the old
  issue-#143-era float64/MPS eval failures did not reproduce. This is about
  eval only — VLA *fine-tuning* on MPS is still a no-go (see the GPU-vs-MPS
  bullet above).
- **Headless eval/training on a remote server needs no display, but sim
  rendering backends do.** <!-- id: headless-eval-training-display --> `lerobot-eval` and `lerobot-train` write videos
  to disk (`render_mode="rgb_array"`) and need no `$DISPLAY` at all — but
  MuJoCo-based sim suites (LIBERO) need an explicit headless rendering
  backend: `export MUJOCO_GL=egl` before evaluating on a server with no GPU
  display attached. `lerobot-dataset-viz` supports a `--mode distant
  --grpc-port=<port>` streaming mode so a local machine can `rerun
  rerun+http://<remote-ip>:<port>/proxy` against a dataset that never left
  the remote box — the general remote-visualization strategy (as opposed to
  X11 forwarding) is `environments`' territory; this is the LeRobot-specific
  invocation of it. See `references/eval-and-sim.md`.
- **`lerobot-eval`'s async vector envs crash on the shipped sim envs.** <!-- id: async-envs-crash-eval --> The
  eval default `--eval.use_async_envs=true` builds `AsyncVectorEnv` with a
  forkserver context whose worker processes never import the env package
  (`gym_pusht` etc.), so every worker dies with
  `gymnasium.error.NamespaceNotFound` and the parent surfaces only a
  `BrokenPipeError` from `_check_spaces` — the real error is buried mid-log.
  Pass `--eval.use_async_envs=false` (sync envs are fine at eval scale).
  Verified 2026-07-12 (manip-trial, lerobot 0.6.0, macOS arm64; the
  fresh-worker mechanism is platform-independent).
- **Recording's keyboard control flow is more portable than teleoperation
  itself.** <!-- id: keyboard-teleop-portability --> `lerobot-record`'s episode-boundary keys (`→`/`n` next, `←`/`r`
  re-record, `Esc`/`q` stop) work over X11, Wayland, and headless/SSH
  sessions as long as it runs in an interactive terminal — but keyboard
  *teleoperation* (driving the robot itself with the keyboard) needs a
  global key backend and only works on X11, a Windows desktop, or macOS with
  Accessibility permission granted, not Wayland or headless. Don't assume a
  working `lerobot-record` session implies keyboard teleop will also work
  remotely.
- **`lerobot[viz]` and `gradio_rerun` can't co-exist — drop the viz extra.** <!-- id: viz-extra-gradio-rerun-conflict -->
  `lerobot[viz]==0.6.0` pins `rerun-sdk>=0.24.0,<0.34.0`, which is
  unsatisfiable next to `gradio_rerun==0.34.1` (which needs
  `rerun-sdk==0.34.1`) — the resolver fails with "Because
  lerobot[viz]==0.6.0 depends on rerun-sdk>=0.24.0,<0.34.0 … requirements
  are unsatisfiable." Fix: drop the `viz` extra and pin `rerun-sdk==0.34.1`
  explicitly; no `gradio_rerun` release targets rerun <0.34 with the
  streaming API, so downgrading `gradio_rerun` is not an option (verified
  2026-07-15, vla-trial). See the `rerun` skill for the gradio_rerun
  streaming pattern this pin supports.
- **macOS arm64 decodes AV1 fine at current versions** <!-- id: macos-av1-decode-ok --> (✓ 2026-07-12).
  `torchcodec` 0.11.1 + Homebrew `ffmpeg` 8.1.2 on macOS arm64 decoded
  `lerobot/pusht`'s AV1 videos during training (torchcodec video backend,
  zero decode errors); the "torchcodec is strict about ffmpeg majors" worry
  did not bite at these versions.

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
  hardware. Of the VLA family, SmolVLA is the one with a workable non-CUDA
  dev path (install + inference/smoke-train run on MPS/CPU; GR00T needs
  flash-attn/CUDA, Pi0-family needs a real CUDA GPU) and it's
  SO-100-pretrained, making an SO-100/SO-101 fine-tune the cheapest
  in-embodiment VLA adaptation — see `references/policies-and-training.md`'s
  What ships section.
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
  command against `lerobot/pusht` (status: unverified, but exercised via
  adaptation 2026-07-12 in manip-trial — file header states the exact
  source and evidence).
- `examples/load-dataset-snippet.py` — loads and inspects `lerobot/pusht`
  with `LeRobotDataset`, matching the dataset the training example uses
  (status: unverified — file header states the exact source).
- Upstream: [huggingface/lerobot](https://github.com/huggingface/lerobot)
  (primary source for this skill, README + `docs/source/` +
  `src/lerobot/scripts/` fetched directly via raw GitHub URLs and the
  GitHub Contents API on 2026-07-10), [LeRobot
  documentation](https://huggingface.co/docs/lerobot/index) (mirrors
  `docs/source/`), [Hugging Face Hub API](https://huggingface.co/api/) (used
  to confirm dataset/model repo IDs referenced in this skill actually exist).
  Sibling skills: `huggingface` (hub mechanics), `environments` (uv-first
  install, GPU/remote), `data` (dataset sourcing), `rerun` (episode
  visualization), `isaac-lab` (NVIDIA RL stack), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 2.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 2.1.0 (2026-07-31): manip-trial + vla-trial absorption — three Platform
  gotchas: lerobot[viz]==0.6.0 pins rerun-sdk<0.34.0, unsatisfiable next to
  gradio_rerun==0.34.1 (drop the viz extra, pin rerun-sdk==0.34.1); macOS
  arm64 AV1 decode confirmed with torchcodec 0.11.1 + ffmpeg 8.1.2 (✓,
  ffmpeg-major worry did not bite); MPS eval confirmed fully workable on
  0.6.0/torch 2.11 with cpu==mps rollouts and the old issue-#143 float64
  failures gone (✓).

- 2.0.0 (2026-07-15): vla-trial absorption — description gains VLA trigger keywords (smolvla/VLA/vision-language-action); SmolVLA embodiment-match note; MPS-viability scoped to exclude VLA fine-tuning (never fine-tune a VLA on MPS, ~2h/20 steps); SmolVLA Jobs cost anchor (~20k steps ≈ 4h A100) + 3 HF Jobs failure modes (402 prepaid credits, --policy.repo_id ignored, --output_dir verbatim to remote); new camera-layout mismatch section (rename_map + empty_cameras; base-vs-fine-tune processor incompatibility).

- 1.1.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.

- 1.1.0 (2026-07-12): manip-trial absorption — version fact 0.6.1→0.6.0
  (PyPI-verified); Quick start reworked to smoke-train-then-eval (pre-0.6
  hub checkpoints lack processor files and cannot load on 0.6+; no working
  PushT baseline exists on the Hub); extras corrected (`core_scripts` not
  needed for sim train/eval, `diffusion` required for diffusion
  checkpoints); new async-env eval-crash gotcha
  (`--eval.use_async_envs=false`); MPS speed anchor scoped (small-obs
  datasets ~10x faster, measured); `eval_info.json` `overall` schema;
  dataset-viz `--display-mode foxglove` / `--save` modes.
