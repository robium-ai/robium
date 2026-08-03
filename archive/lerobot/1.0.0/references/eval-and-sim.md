# Evaluation and simulation environments

The `lerobot-eval` CLI, which sim environments LeRobot ships (as opposed to
loads from EnvHub), headless rendering, and `lerobot-rollout` for
real-hardware deployment.

Sources: `huggingface/lerobot`'s README, `docs/source/libero.mdx`,
`docs/source/envhub.mdx`, `docs/source/il_robots.mdx`, and
`src/lerobot/scripts/lerobot_eval.py`'s own module docstring, all fetched
directly via raw GitHub URLs and the GitHub Contents API this session
(`main` branch). The registered `EnvConfig` subclasses (`aloha`, `pusht`,
`libero`, `libero_plus`, `metaworld`, `robocasa`, `robotwin`, `robomme`,
`vlabench`, `isaaclab_arena`) were confirmed by fetching
`src/lerobot/envs/configs.py` directly, not inferred from the docs alone —
some of these (`aloha`, `pusht`) are defined inline in that file rather than
having their own module, so they don't show up in a directory listing of
`src/lerobot/envs/`.

## The `lerobot-eval` CLI

This is `lerobot_eval.py`'s own docstring example, fetched directly — it
evaluates a hub-hosted pretrained policy with zero training required, the
"start from pretrained" path from `SKILL.md`'s Key directives:

```bash
lerobot-eval \
  --policy.path=lerobot/diffusion_pusht \
  --env.type=pusht \
  --eval.batch_size=10 \
  --eval.n_episodes=10 \
  --policy.use_amp=false \
  --policy.device=cuda
```

`--policy.path` also accepts a local training checkpoint directory
(`outputs/train/.../checkpoints/005000/pretrained_model`) — that directory
must contain at least `config.json` and `model.safetensors`. `--env.type`
selects the environment (see table below); `--eval.batch_size` controls how
many environments run in parallel, `--eval.n_episodes` how many episodes
per task.

## Sim environments shipped

| `--env.type` | What it is | Notes |
| --- | --- | --- |
| `pusht` | 2D pushing task (`gym-pusht`) | `task="PushT-v0"`, 10 fps, single task; pairs with the `lerobot/pusht` dataset used throughout this skill. Install via `lerobot[pusht]`. |
| `aloha` | Bimanual manipulation sim (`gym-aloha`) | `task="AlohaInsertion-v0"` by default, 50 fps, 14-dim action (two 7-DoF arms). Install via `lerobot[aloha]`. |
| `libero` | LIBERO lifelong-learning benchmark | 5 task suites (`libero_spatial`, `libero_object`, `libero_goal`, `libero_90`, `libero_10`), 130 tasks total. Linux-only (MuJoCo); see Headless rendering below. Install via `lerobot[libero]`. |
| `libero_plus` | Extended LIBERO variant | Subclasses `libero`'s config. |
| `metaworld` | MetaWorld manipulation benchmark | |
| `robocasa` | Kitchen-scale manipulation sim | |
| `robotwin` | Bimanual manipulation benchmark | |
| `robomme` | Multi-modal-evaluation env | |
| `vlabench` | VLA-focused benchmark suite | |
| `isaaclab_arena` | Isaac Lab Arena, loaded via EnvHub (`HubEnvConfig`) | This is the seam to the NVIDIA RL stack — deep Isaac Lab usage is `isaac-lab`'s territory; this skill only notes that LeRobot can evaluate against it. |

`aloha` and `pusht` are LeRobot's original, longest-supported sim envs and
the ones with the most hub-hosted pretrained baselines — they're the
default choice for validating a new pipeline (see `SKILL.md`'s Quick start).
`libero` is the standard published benchmark for comparing VLA policies.

### LIBERO example (multi-suite)

```bash
lerobot-eval \
  --policy.path="your-policy-id" \
  --env.type=libero \
  --env.task=libero_spatial,libero_object,libero_goal,libero_10 \
  --eval.batch_size=1 \
  --eval.n_episodes=10 \
  --env.max_parallel_tasks=1
```

`--env.task` accepts a comma-separated suite list; `--env.task_ids`
restricts to specific task indices within a suite (`[0]`, `[1,2,3]`) and
defaults to all tasks. `--env.control_mode` (`relative` default, or
`absolute`) must match how the target policy was trained — different VLA
checkpoints use different action parameterizations.

## EnvHub: loading a sim env from the Hub without installing it

Beyond the built-in `--env.type` list above, `lerobot.envs.make_env` can
load an arbitrary environment published on the Hub as a Git repo containing
an `env.py` with a `make_env(n_envs, use_async_envs)` entry point — no
package install required:

```python
from lerobot.envs import make_env

env = make_env("lerobot/cartpole-env", trust_remote_code=True)
```

`trust_remote_code=True` is mandatory and executes third-party Python code —
review the `env.py` first and pin to a specific commit
(`"user/repo@<commit-sha>"`) for anything beyond local experimentation. This
is how `isaaclab_arena` and community-contributed sim envs are consumed;
building/publishing a new EnvHub env is out of this skill's depth (see the
upstream `docs/source/envhub.mdx` if that's the actual task).

## Headless rendering on remote/server hosts

`lerobot-eval` itself needs no display — sim envs render via
`render_mode="rgb_array"` and videos are written to disk. But the
**rendering backend** the sim uses to produce those frames still needs a
headless-capable path on a server with no attached display:

```bash
export MUJOCO_GL=egl   # required for LIBERO (MuJoCo-based) on headless servers
```

This is orthogonal to `environments`' general headless/remote-display
guidance (X11 forwarding vs. web-based viz) — `MUJOCO_GL` controls how
MuJoCo itself renders, not how a human views the result. See
`references/datasets.md` for the equivalent concern on the visualization
side (`lerobot-dataset-viz --mode distant`).

## `lerobot-rollout`: real-hardware deployment

Evaluation *in simulation* uses `lerobot-eval` (above); running a trained
policy *on a real robot* uses `lerobot-rollout` instead — a different
script because it drives physical hardware rather than a gym vector env:

```bash
lerobot-rollout \
  --strategy.type=base \
  --policy.path=${HF_USER}/my_policy \
  --robot.type=so100_follower \
  --robot.port=/dev/ttyACM1 \
  --task="Put lego brick into the transparent box" \
  --duration=60
```

`--strategy.type` selects the execution mode: `base` (no recording, quick
check), `sentry` (continuous recording with auto-upload, for large-scale
evaluation), `highlight` (ring-buffer recording, save-on-keystroke),
`dagger` (human-in-the-loop data collection), `episodic` (episode-oriented
with reset phases). All strategies support `--inference.type=rtc` for
smoother execution with slower VLA policies (Pi0, Pi0.5, SmolVLA). Real-
hardware bring-up (ports, calibration, camera setup) is deliberately not
covered in depth by this skill — see LeRobot's own hardware docs
(`SKILL.md`'s References) for a specific robot.
