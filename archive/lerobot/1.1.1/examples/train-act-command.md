# Small-scale ACT training smoke run on `lerobot/pusht`

**Status:** unverified as written, but exercised via adaptation 2026-07-12
(manip-trial, lerobot 0.6.0, M2 Pro/MPS): the same command shape with
`--steps=200 --save_freq=200 --batch_size=8 --policy.device=mps` trained in
31 s (loss 14.4→3.5) and at `--steps=10000` in 14.5 min (loss→0.33); the
`checkpoints/last/pretrained_model` eval path below resolved exactly as
written.

**Source:** the command shape below is assembled from two directly-fetched
upstream sources on 2026-07-10 — huggingface/lerobot's README ("Training a
policy is as simple as running a script configuration", `lerobot-train
--policy.type=act --dataset.repo_id=...`) and its `docs/source/cheat-sheet.mdx`'s
training section (`--output_dir`, `--job_name`, `--policy.device`,
`--wandb.enable`, `--policy.repo_id`, `--steps`). The dataset (`lerobot/pusht`)
was confirmed to exist and to already be on LeRobotDataset v3.0 via a direct
fetch of its `meta/info.json` from huggingface.co on 2026-07-10 (206
episodes, 25,650 frames). `--steps=3000` below is a deliberately small
smoke-run value, not an upstream default — see the reasoning below and
`references/policies-and-training.md`'s compute-sizing table before scaling
it up for a real run.

Pairs with `load-dataset-snippet.py` in this same directory (same dataset,
`lerobot/pusht`) and with the "start from pretrained, then small-scale
fine-tune" key directive in `SKILL.md`: run this only after evaluating
`lerobot/diffusion_pusht` per `SKILL.md`'s Quick start step 3, to confirm
the eval pipeline works before spending compute on training.

Requires the `training` and `pusht` extras (`uv add
"lerobot[training,pusht]"` — see `SKILL.md`'s Quick start; `core_scripts`
is only for the hardware CLIs and not needed here).

```bash
uv run lerobot-train \
  --dataset.repo_id=lerobot/pusht \
  --policy.type=act \
  --output_dir=outputs/train/act_pusht_smoke \
  --job_name=act_pusht_smoke \
  --policy.device=cuda \
  --steps=3000 \
  --save_freq=1000 \
  --wandb.enable=false \
  --policy.repo_id=${HF_USER}/act_pusht_smoke \
  --policy.push_to_hub=false
```

**Why these values:**

- `--policy.type=act` — the smallest policy family (`references/policies-and-training.md`'s
  compute table: ~2-6 GB VRAM, ~30-60 min for 5 epochs on an RTX 4090-class
  GPU) — the right choice for a first smoke run, not a VRAM-bound VLA policy.
- `--steps=3000` — deliberately short. `lerobot/pusht` has 25,650 frames;
  3,000 steps at the ACT default batch size is well under one full epoch,
  enough to confirm the loss curve moves and a checkpoint saves/evaluates
  cleanly, not a converged policy. ACT trains at a constant LR (its
  `get_scheduler_preset()` returns no scheduler — confirmed by fetching
  `configuration_act.py` directly on 2026-07-10), so there's no LR-decay
  schedule to rescale when changing `--steps`, unlike scheduler-based
  policies (diffusion, SmolVLA, the Pi0 family) — see
  `references/policies-and-training.md` if switching `--policy.type` to one
  of those.
- `--policy.device=cuda` — swap for `mps` (Apple Silicon) or `cpu` (smoke
  test only, expect it to be much slower) per `SKILL.md`'s Platform gotchas.
- `--wandb.enable=false` and `--policy.push_to_hub=false` — kept off for a
  throwaway smoke run; flip both on for a real tracked run (`wandb login`
  first; dropping `--policy.push_to_hub=false` pushes the trained policy to
  `--policy.repo_id` on the Hub, which is the `huggingface` skill's
  territory once you get there).

**After this run**, evaluate the checkpoint per `SKILL.md`'s Quick start
step 4, pointing `--policy.path` at
`outputs/train/act_pusht_smoke/checkpoints/last/pretrained_model` (path
verified 2026-07-12):

```bash
uv run lerobot-eval \
  --policy.path=outputs/train/act_pusht_smoke/checkpoints/last/pretrained_model \
  --env.type=pusht \
  --eval.batch_size=10 \
  --eval.n_episodes=10 \
  --eval.use_async_envs=false \
  --policy.device=cuda
```

A smoke run at this scale is not expected to solve PushT (success needs
≥95% T-coverage; even 10k steps measured `pc_success` 0 with
`avg_max_reward` 0.28) — the goal is confirming the train -> checkpoint ->
eval loop works end to end before committing to a long run.
