# Policies and training

Which policies LeRobot ships, the `lerobot-train` CLI, and how to size
compute for a training run. Hub mechanics (pushing a trained checkpoint,
model cards, private repos) are the `huggingface` skill's territory; this
file covers only what's needed to launch and size a training run.

Sources: `huggingface/lerobot`'s README (policy table), `docs/source/cheat-sheet.mdx`,
`docs/source/il_robots.mdx`, `docs/source/hardware_guide.mdx`, and
`docs/source/torch_accelerators.mdx`, all fetched directly via raw GitHub
URLs on 2026-07-10 (`main` branch). Model repo IDs referenced below
(`lerobot/act_aloha_sim_transfer_cube_human`, `lerobot/diffusion_pusht`,
`lerobot/vqbet_pusht`) were confirmed to exist via the Hugging Face Hub API
on 2026-07-10, not assumed from memory.

## What ships (as of 2026-07-10)

LeRobot's policy catalogue spans several families, cataloged in the
README's own table:

| Category | Examples |
| --- | --- |
| Imitation Learning | ACT, Diffusion, VQ-BeT, Multitask DiT |
| Reinforcement Learning | HIL-SERL, TDMPC |
| Vision-Language-Action (VLA) | Pi0, Pi0Fast, Pi0.5, SmolVLA, GR00T N1.7, XVLA, EO-1, and others |
| World models / Reward models | several, newer and more experimental |

For a robium manipulation-vertical build, **ACT and Diffusion are the
default starting points**: they're the smallest (see compute table below),
have the longest track record, and both have hub-hosted pretrained
checkpoints on common benchmark datasets (e.g.
`lerobot/act_aloha_sim_transfer_cube_human`, `lerobot/diffusion_pusht`,
`lerobot/vqbet_pusht`; note these predate the 0.6 processor-pipeline
format and cannot be *loaded* on 0.6+; see `SKILL.md`'s Key directives).
Reach for a VLA-family policy (SmolVLA, Pi0-family)
once the pipeline is proven and the task needs language conditioning or
broader generalization than a single-task BC policy provides; they cost
substantially more VRAM (see below) and are still a fast-moving area
upstream.

SmolVLA (`lerobot/smolvla_base`, 450M, confirmed
`docs/source/notebooks.mdx`) is the constrained-hardware VLA entry point:
the smallest VLA in-catalog and the only one whose install plus
inference/smoke-train works on non-CUDA hardware. GR00T N1.7 needs
flash-attn and is CUDA-only (`docs/source/groot.mdx`); the Pi0-family
(~3B) needs a real CUDA GPU. `smolvla_base` is itself SO-100-pretrained, so
an SO-100/SO-101 fine-tune is in-embodiment and the cheapest VLA adaptation
available (verified 2026-07-14, vla-trial). OpenVLA and MolmoAct2 aren't
LeRobot-shipped; cross-framework VLA comparison belongs to `architect`,
not this skill.

This skill does not re-teach every policy's architecture; see the linked
`docs/source/policy_*.md`/`.mdx` pages in the README's table for that. What
it owns is getting a training run started and sized correctly.

## The `lerobot-train` CLI

Minimal shape, training from scratch against an existing dataset (the
"official example config" path from `SKILL.md`'s Key directives):

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_test \
  --job_name=act_so101_test \
  --policy.device=cuda \
  --wandb.enable=true \
  --policy.repo_id=${HF_USER}/my_policy
```

- `--dataset.repo_id`: the dataset to train against; the policy
  automatically adapts to that dataset's own state/action/camera features.
- `--policy.type`: selects the architecture (`act`, `diffusion`, `smolvla`,
  `pi05`, ...) and loads its default config.
- `--policy.device`: `cuda` (NVIDIA), `mps` (Apple Silicon), or `cpu`;
  usually auto-detected and can be omitted (see `SKILL.md`'s Platform
  gotchas and `docs/source/torch_accelerators.mdx`).
- `--wandb.enable=true`: optional Weights & Biases logging (`wandb login`
  first).
- `--policy.repo_id`: where the trained policy is pushed on the Hub
  (`--policy.push_to_hub=false` to skip).
- `--steps`: total training steps; not shown above because the upstream
  example omits it (uses the config default), but should be set explicitly
  for the "small-scale first" directive; see below.

**Fine-tuning an existing checkpoint** instead of training from scratch:
swap `--policy.type=act` for `--policy.path=<hub-id-or-local-dir>`: the
type is inferred from the checkpoint, so it can be omitted:

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.path=username/the_policy_to_finetune \
  --policy.device=cuda \
  --policy.repo_id=${HF_USER}/my_policy \
  --output_dir=outputs/train/act_so101_test \
  --steps=20000
```

**Resuming** a run (local or Hub-hosted checkpoint) uses `--config_path` +
`--resume=true`:

```bash
lerobot-train --config_path=${HF_USER}/my_policy --resume=true
```

If training is shortened (fewer `--steps` for a smoke run) on a policy that
uses a decaying LR schedule (SmolVLA, the Pi0 family, and others whose
config exposes `scheduler_decay_steps`), also shorten that schedule to
match, otherwise the learning rate never decays. ACT is the exception: its
`get_scheduler_preset()` returns no scheduler at all (confirmed by fetching
`configuration_act.py` directly on 2026-07-10), so it trains at a constant
LR and has no `--policy.scheduler_decay_steps` field to rescale; see
`examples/train-act-command.md`. `--save_freq` should still be lowered for
a short smoke run regardless of policy type, so at least one checkpoint
actually gets written.

## Fine-tuning a VLA on a non-matching camera layout

SmolVLA, Pi0, Pi0.5, Pi0Fast, and XVLA expect a fixed camera-key contract
baked into their config: SmolVLA expects exactly
`observation.images.camera1`/`camera2`/`camera3`. Fine-tuning against a
dataset with fewer cameras, or cameras named something else (e.g.
`observation.images.wrist`), fails at train start with
`ValueError: Feature mismatch ... Missing features: camera1/2/3`.

Fix (`docs/source/rename_map.mdx`): remap the dataset's camera keys onto
the policy's expected names with `--rename_map`, and pad any remaining
unfilled camera slots with `--policy.empty_cameras=<n>`, a masked
placeholder the policy is trained to ignore, not a fake/black image.
`--policy.empty_cameras` is supported on PI0, PI05, PI0Fast, SmolVLA, and
XVLA.

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_pick \
  --policy.path=lerobot/smolvla_base \
  --rename_map='{"observation.images.wrist": "observation.images.camera1"}' \
  --policy.empty_cameras=2 \
  --steps=20000 \
  --policy.device=cuda \
  --output_dir=outputs/train/smolvla_so101_pick
```

The same `--rename_map` applies at eval time if feeding the sim/dataset's
raw camera keys, but a checkpoint fine-tuned with a rename already bakes
that mapping into its saved `policy_preprocessor.json`, so evaluating it by
feeding its own original (renamed) keys works with no `--rename_map` at
all; applying the rename a second time at eval double-maps the keys and is
wrong. Relatedly: a base checkpoint (`empty_cameras=0`) and a fine-tune of
it (`empty_cameras=1`, say) bake *different* camera layouts into their
processor configs; don't assume two checkpoints of the same policy family
are interchangeable at eval; check each one's `policy_preprocessor.json`
explicitly before feeding it observations (verified 2026-07-14, vla-trial).

## Compute sizing

Order-of-magnitude figures from LeRobot's own compute-hardware guide,
useful for "will this run take an hour or a day", not exact predictions.
Memory scales roughly linearly with batch size; AdamW (the default
optimizer) adds ~30-100% VRAM over a bare forward+backward pass.

| Group | Policies | Peak VRAM (batch 8, AdamW) | Starter GPU |
| --- | --- | ---: | --- |
| Light BC | `act`, `vqbet`, `tdmpc` | ~2-6 GB | RTX 3060, L4, A10G |
| Diffusion | `diffusion`, `multi_task_dit` | ~8-14 GB | RTX 4070+, L4, A10G |
| Small VLA | `smolvla` | ~10-16 GB | RTX 4080+, L4, A10G |
| Large VLA | `pi0`, `pi0_fast`, `pi05`, `xvla`, `wall_x` | ~24-40 GB | A100 40 GB+ |
| Multimodal | `groot`, `eo1` | ~24-40 GB | A100 40 GB+ |

Wall-clock anchors, 5 epochs over a ~50-episode/~45k-frame dataset,
640x480 images, AdamW:

| Setup | Policy | Batch | Wall-clock |
| --- | --- | --- | ---: |
| RTX 4090/3090 (24 GB) | `act` | 8 | ~30-60 min |
| RTX 4090/3090 (24 GB) | `diffusion` | 8 | ~2-4 h |
| L4/A10G (24 GB) | `act` | 8 | ~1-2 h |
| L4/A10G (24 GB) | `smolvla` | 4 | ~3-6 h |
| A100 40 GB | `smolvla` | 16 | ~1-2 h |
| A100 40 GB | `pi0`/`pi05` | 4 | ~4-8 h |
| Apple Silicon M1/M2/M3 Max (MPS) | `act` | 4 | ~6-14 h |

The MPS anchor holds for 640x480-image datasets; small-observation sims
run an order of magnitude faster on Apple Silicon; measured 2026-07-12
(manip-trial): ACT on `lerobot/pusht` (96x96 images, batch 8, M2 Pro)
sustained 11.6 steps/s ≈ 93 samples/s, i.e. ~5 min per epoch and a
200-step pipeline-smoke train in ~31 s.

Robotics imitation learning typically converges in **5-10 epochs over the
dataset**, not hundreds of thousands of raw steps: pick an epoch target,
then derive `--steps` from `total_frames / (num_gpus * batch_size) *
epochs`. `lerobot/pusht` (206 episodes, 25,650 frames, confirmed via its
Hub `meta/info.json` on 2026-07-10) is close in order of magnitude to the
anchor dataset above, so these figures are a reasonable starting estimate
for `examples/train-act-command.md`'s smoke run.

**Multi-GPU:** `accelerate launch --num_processes=N` roughly linearly
speeds up compute-bound runs: each optimizer step processes `N *
batch_size` samples in about the same wall-clock as a single-GPU step. When
`dataloading_s` approaches `update_s` in the training logs, more GPUs stop
helping; look at `--num_workers`, image resolution, and disk speed instead
of adding compute.

## No local GPU: Hugging Face Jobs

`lerobot-train` runs locally by default. Current releases may expose
`--job.target=<flavor>` to submit the same training command to managed Hugging
Face infrastructure. Treat this as a paid external action: first inspect
`lerobot-train --help`, then use the `huggingface` skill to verify identity,
list current hardware and pricing, and present the exact namespace, hardware,
timeout, output destination, and command for explicit approval.

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.type=act \
  --policy.repo_id=${HF_USER}/my_policy \
  --job.target=<approved-live-flavor>
```

Do not preserve a flavor list, price, or default timeout in this reference.
They are volatile. Use `hf jobs hardware`, `hf jobs run --help`, and
`hf jobs uv run --help` immediately before approval. After submission, the
`huggingface` skill owns `hf jobs logs`, `inspect`, `stats`, `wait`, and the
explicitly authorized `cancel` operation. The LeRobot-specific concerns are
the dataset/policy fields and remote output behavior below.

Three Jobs failure modes hit during vla-trial (all verified 2026-07-14):

- **402 Payment Required** if the account has no prepaid credits: authentication
  alone is not sufficient; a job submitted against a zero-balance
  account fails at submission with `402 Payment Required`, not a queued or
  running state.
- **`--policy.repo_id` is silently ignored on the Jobs path**: the trained
  model pushes to an auto-generated `<user>/train_<timestamp>` repo
  instead; read the job log's `Model pushed to <url>` line to find where it
  actually landed, don't assume it's the repo_id you passed.
- **`--output_dir` is passed verbatim to the remote container.** A local
  path like `/Users/...` trains to completion and then crashes at save time
  with `PermissionError: '/Users'`; the remote container has no such
  filesystem. Use a container-local path (`/tmp/...`) for `--output_dir`
  when running on Jobs.
