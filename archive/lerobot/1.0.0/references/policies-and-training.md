# Policies and training

Which policies LeRobot ships, the `lerobot-train` CLI, and how to size
compute for a training run. Hub mechanics (pushing a trained checkpoint,
model cards, private repos) are the `huggingface` skill's territory; this
file covers only what's needed to launch and size a training run.

Sources: `huggingface/lerobot`'s README (policy table), `docs/source/cheat-sheet.mdx`,
`docs/source/il_robots.mdx`, `docs/source/hardware_guide.mdx`, and
`docs/source/torch_accelerators.mdx`, all fetched directly via raw GitHub
URLs this session (`main` branch). Model repo IDs referenced below
(`lerobot/act_aloha_sim_transfer_cube_human`, `lerobot/diffusion_pusht`,
`lerobot/vqbet_pusht`) were confirmed to exist via the Hugging Face Hub API
this session, not assumed from memory.

## What ships (as of this session)

LeRobot's policy catalogue spans several families, cataloged in the
README's own table:

| Category | Examples |
| --- | --- |
| Imitation Learning | ACT, Diffusion, VQ-BeT, Multitask DiT |
| Reinforcement Learning | HIL-SERL, TDMPC |
| Vision-Language-Action (VLA) | Pi0, Pi0Fast, Pi0.5, SmolVLA, GR00T N1.7, XVLA, EO-1, and others |
| World models / Reward models | several, newer and more experimental |

For a robium manipulation-vertical build, **ACT and Diffusion are the
default starting points** — they're the smallest (see compute table below),
have the longest track record, and both have hub-hosted pretrained
checkpoints on common benchmark datasets (e.g.
`lerobot/act_aloha_sim_transfer_cube_human`, `lerobot/diffusion_pusht`,
`lerobot/vqbet_pusht`). Reach for a VLA-family policy (SmolVLA, Pi0-family)
once the pipeline is proven and the task needs language conditioning or
broader generalization than a single-task BC policy provides — they cost
substantially more VRAM (see below) and are still a fast-moving area
upstream.

This skill does not re-teach every policy's architecture — see the linked
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

- `--dataset.repo_id` — the dataset to train against; the policy
  automatically adapts to that dataset's own state/action/camera features.
- `--policy.type` — selects the architecture (`act`, `diffusion`, `smolvla`,
  `pi05`, ...) and loads its default config.
- `--policy.device` — `cuda` (NVIDIA), `mps` (Apple Silicon), or `cpu`;
  usually auto-detected and can be omitted (see `SKILL.md`'s Platform
  gotchas and `docs/source/torch_accelerators.mdx`).
- `--wandb.enable=true` — optional Weights & Biases logging (`wandb login`
  first).
- `--policy.repo_id` — where the trained policy is pushed on the Hub
  (`--policy.push_to_hub=false` to skip).
- `--steps` — total training steps; not shown above because the upstream
  example omits it (uses the config default), but should be set explicitly
  for the "small-scale first" directive — see below.

**Fine-tuning an existing checkpoint** instead of training from scratch:
swap `--policy.type=act` for `--policy.path=<hub-id-or-local-dir>` — the
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
`configuration_act.py` directly this session), so it trains at a constant
LR and has no `--policy.scheduler_decay_steps` field to rescale — see
`examples/train-act-command.md`. `--save_freq` should still be lowered for
a short smoke run regardless of policy type, so at least one checkpoint
actually gets written.

## Compute sizing

Order-of-magnitude figures from LeRobot's own compute-hardware guide —
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

Robotics imitation learning typically converges in **5-10 epochs over the
dataset**, not hundreds of thousands of raw steps — pick an epoch target,
then derive `--steps` from `total_frames / (num_gpus * batch_size) *
epochs`. `lerobot/pusht` (206 episodes, 25,650 frames — confirmed via its
Hub `meta/info.json` this session) is close in order of magnitude to the
anchor dataset above, so these figures are a reasonable starting estimate
for `examples/train-act-command.md`'s smoke run.

**Multi-GPU:** `accelerate launch --num_processes=N` roughly linearly
speeds up compute-bound runs — each optimizer step processes `N *
batch_size` samples in about the same wall-clock as a single-GPU step. When
`dataloading_s` approaches `update_s` in the training logs, more GPUs stop
helping; look at `--num_workers`, image resolution, and disk speed instead
of adding compute.

## No local GPU: Hugging Face Jobs

`lerobot-train` runs locally by default; add `--job.target=<flavor>` to run
the same command on managed Hugging Face infrastructure, billed by the
second:

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.type=act \
  --policy.repo_id=${HF_USER}/my_policy \
  --job.target=a10g-small
```

`hf auth login` must be run once before submitting (the job runs under your
token — this login step is the `huggingface` skill's territory, referenced
here only because `lerobot-train` calls it inline). List current
flavors/pricing with `hf jobs hardware`; flavors include `t4-small`/
`t4-medium` (ACT-only), `l4x1`/`l4x4`, `a10g-small/large/largex2/largex4`,
and `a100-large`. The job defaults to a 48h timeout — override with
`--job.timeout=4h` (or another duration string). Re-attach or cancel a
detached job with `hf jobs logs <job-id>` / `hf jobs cancel <job-id>`.
