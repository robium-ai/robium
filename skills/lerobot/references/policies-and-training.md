# Policies and training

Use this guide after the dataset and embodiment contract are known. LeRobot's
policy catalog, configuration fields, accelerator support, and hosted-job path
move quickly; inspect the installed CLI and current official guide before
copying a recipe.

## Choose a policy for the next unknown

- Start with ACT when the goal is to prove a first imitation-learning pipeline.
  LeRobot's current documentation recommends it as the first policy because it
  is comparatively light and fast. This is a starting probe, not a claim that
  ACT is best for every task.
- Choose a larger VLA only when language conditioning, pretrained visual
  knowledge, or cross-task generalization is part of the requirement. First
  confirm that its camera, state, action, precision, dependency, and accelerator
  contracts fit the dataset and target runtime.
- Treat every policy not shown by the installed release and current
  [policy catalog](https://huggingface.co/docs/lerobot/main/en/api/policies) as
  unavailable until verified. Do not maintain negative lists of policies that
  LeRobot does not ship; those become obsolete as integrations land.
- Use the policy's own current guide for its training recipe. Architecture
  names alone do not establish compatible processors, checkpoints, or compute.

## Prove training before sizing it

The common CLI shape is:

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_test \
  --job_name=act_so101_test \
  --policy.device=cuda \
  --policy.repo_id=${HF_USER}/my_policy \
  --steps=<small-explicit-count> \
  --save_freq=<at-least-one-checkpoint>
```

- Confirm this shape with `lerobot-train --help` and the current
  [cheat sheet](https://huggingface.co/docs/lerobot/main/cheat-sheet).
- For fine-tuning, use `--policy.path=<hub-id-or-local-dir>` only after
  inspecting that checkpoint's config and processor files. Do not also assume a
  policy type from its repository name.
- A smoke run proves data loading, forward/backward passes, logging, checkpoint
  creation, and reload. It does not establish convergence or policy quality.
- Shorten any save and scheduler horizons that would otherwise fall beyond the
  smoke run. Read the resolved policy configuration first; scheduler fields are
  not uniform across families.
- Measure peak memory and steps per second on a small batch, then choose batch
  size, steps, and hardware. Do not use a timeless policy-to-VRAM table as a
  procurement promise.

Robium evidence, scoped to its measured conditions: on 2026-07-12, ACT on
`lerobot/pusht` with 96×96 images and batch 8 sustained about 11.6 steps/s on an
M2 Pro through MPS; a 200-step pipeline smoke train took about 31 seconds. That
does not predict a 640×480 real-robot dataset or another policy family.

## Camera and processor contracts

- Compare dataset feature keys with the selected policy's current input
  features before training. Camera count and names can differ even between a
  base checkpoint and its fine-tune.
- Where the installed release supports them, use `rename_map` to align real
  feature keys and `empty_cameras` only for policy-supported masked slots. Check
  the current policy guide rather than assuming every VLA supports the same
  fields.
- Inspect the saved preprocessor and postprocessor after training. At
  evaluation, do not apply a rename a second time when the saved processor
  already owns it.

Robium's 2026-07-14 SmolVLA trial found that a base checkpoint and fine-tune
could carry different camera layouts in their processor configuration. Preserve
that as a failure signature, not a universal list of camera keys.

## Remote training

Local training is the normal path. If the installed release exposes
`--job.target`, treat it as paid external compute:

- Use `huggingface` to verify identity, current hardware, pricing, approval,
  logs, output repositories, and cancellation.
- Keep `--output_dir` inside the remote container and discover the actual model
  destination from the completed job rather than assuming a requested Hub repo
  was honored.
- Do not preserve a flavor list, price, or timeout here. Read live CLI help and
  current Hugging Face Jobs documentation immediately before submission.

Robium's 2026-07-14 VLA trial observed three version-specific signatures: an
account without prepaid credit failed at submission with HTTP 402; the managed
path ignored the requested policy repository and logged an auto-generated one;
and a macOS host path passed as `output_dir` failed only when the remote run
saved. Compare these signatures with current behavior before relying on them.

## Current sources

Re-checked on 2026-09-07; use the live pages rather than treating this date as a
version guarantee.

- [LeRobot overview](https://huggingface.co/docs/lerobot/main/en/index)
- [ACT guide](https://huggingface.co/docs/lerobot/act)
- [Policy API and catalog](https://huggingface.co/docs/lerobot/main/en/api/policies)
- [Training cheat sheet](https://huggingface.co/docs/lerobot/main/cheat-sheet)
