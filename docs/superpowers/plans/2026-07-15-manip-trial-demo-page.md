# manip-trial demo page (v1, local-only) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An interactive demo page at `/demos/manip-trial/` where a visitor picks a checkpoint from a training ladder (1k/3k/5k/10k steps), runs it live in the PushT sim on an embedded Rerun timeline, and browses a gallery of each rung's real eval videos and metrics.

**Architecture:** Clone of the vla-trial demo v1 (spec `docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md`): a FastAPI session gateway implementing nav-trial's contract, with a Gradio 6 app mounted at `/ui` streaming episodes to a `gradio_rerun` viewer. New training work first: one 5k-step ACT run with `save_freq=1000` pruned to 3 rungs, plus the existing 10k baseline checkpoint as the free top rung; a generated `outputs/demo/ladder.json` manifest is the single source for both the checkpoint radio and the gallery.

**Tech Stack:** LeRobot 0.6.0 (ACT, `lerobot/pusht`), gym-pusht (pygame/pymunk — no GL), rerun-sdk 0.34.1 + gradio_rerun 0.34.1, Gradio ≥6, FastAPI, uvicorn, uv, Docker (python:3.12-slim), Astro 6 + React island (website).

## Global Constraints

- Two repos: backend tasks 1–7 run in `~/repos/robium-applications` (commit there); task 8 runs in `~/repos/robium-website` (commit there). Task 9 commits in robium-applications.
- **Two-hats rule (robium-applications CLAUDE.md):** append friction/gotcha notes to `learnings/2026-07-15.md` at the moment they happen, tagged `[skill-name]` or `[none]`. NEVER edit anything under `~/repos/robium-plugin/skills/` — surface candidates at the end instead.
- Honesty rule: every metric shown comes from a real eval; `pc_success` is expected 0% at every rung and the UI says so. No invented numbers, no success theater.
- All run parameters live in `src/manip_trial/config.py` (the app's single-source rule) — Makefile and tests build commands from it.
- The known PushT eval gotcha applies everywhere: `--eval.use_async_envs=false` (already encoded in `config.eval_cmd`); the demo's episode runner drives a single sync env directly, so it is immune by construction.
- Rerun/gradio pins are coupled: `rerun-sdk==0.34.1` and `gradio_rerun==0.34.1` must match (same rule as vla-trial's pyproject).
- Python for all backend work: `uv run …` inside `apps/manip-trial` (Python 3.12, uv-managed).
- Git commits end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Ladder config + `train-ladder` stage + the real 5k training run

**Files:**
- Modify: `apps/manip-trial/src/manip_trial/config.py`
- Modify: `apps/manip-trial/src/manip_trial/run.py`
- Modify: `apps/manip-trial/Makefile`
- Test: `apps/manip-trial/tests/test_ladder.py` (new)

**Interfaces:**
- Produces: `config.train_ladder_cmd() -> list[str]`, `config.ladder_rungs() -> list[dict]` (each dict: `name: str`, `steps: int`, `run: str`, `checkpoint: Path` absolute), constants `LADDER_TRAIN_OUTPUT_DIR`, `LADDER_KEEP_STEPS = (1_000, 3_000, 5_000)`, `LADDER_EVAL_EPISODES = 10`, `LADDER_EVAL_BATCH_SIZE = 5`, `LADDER_EVAL_OUTPUT_DIR`, `DEMO_LADDER_MANIFEST`; `run.py` stage `train-ladder` (train + prune); `run._prune_ladder()`.

- [ ] **Step 1: Write the failing tests**

Create `apps/manip-trial/tests/test_ladder.py`:

```python
"""Ladder plumbing tests — pure config/fs logic, no training, fast."""

from pathlib import Path

from manip_trial import config
from manip_trial.run import _prune_ladder


def test_ladder_rungs_shape():
    rungs = config.ladder_rungs()
    assert [r["name"] for r in rungs] == ["1k", "3k", "5k", "10k"]
    assert [r["steps"] for r in rungs] == [1000, 3000, 5000, 10000]
    # 1k/3k/5k come from the ladder run; 10k is the reused baseline.
    for r in rungs[:3]:
        assert str(config.LADDER_TRAIN_OUTPUT_DIR) in str(r["checkpoint"])
    assert str(config.BASELINE_TRAIN_OUTPUT_DIR) in str(rungs[3]["checkpoint"])
    for r in rungs:
        assert str(r["checkpoint"]).endswith("pretrained_model")


def test_train_ladder_cmd():
    cmd = config.train_ladder_cmd()
    assert "--steps=5000" in cmd
    assert "--save_freq=1000" in cmd
    assert f"--output_dir={config.LADDER_TRAIN_OUTPUT_DIR}" in cmd


def test_prune_ladder_keeps_only_rungs(tmp_path, monkeypatch):
    ckpt_root = tmp_path / "checkpoints"
    for name in ["001000", "002000", "003000", "004000", "005000"]:
        (ckpt_root / name / "pretrained_model").mkdir(parents=True)
        (ckpt_root / name / "training_state").mkdir()
    (ckpt_root / "last").symlink_to(ckpt_root / "005000")
    monkeypatch.setattr(config, "LADDER_TRAIN_OUTPUT_DIR", tmp_path)

    _prune_ladder()

    kept = sorted(p.name for p in ckpt_root.iterdir())
    assert kept == ["001000", "003000", "005000"]
    for name in kept:
        assert (ckpt_root / name / "pretrained_model").is_dir()
        # training_state (optimizer etc.) is dead weight for inference rungs
        assert not (ckpt_root / name / "training_state").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/repos/robium-applications/apps/manip-trial && uv run pytest tests/test_ladder.py -v`
Expected: FAIL — `AttributeError: module 'manip_trial.config' has no attribute 'ladder_rungs'` (or ImportError for `_prune_ladder`).

- [ ] **Step 3: Implement config + run.py + Makefile**

Append to `apps/manip-trial/src/manip_trial/config.py` (after the BASELINE block, before `TRAIN_OUTPUT_DIR`— actually append after the existing `BASELINE_EVAL_OUTPUT_DIR` line group; exact position: right after line 41's dir constants):

```python
# --- checkpoint ladder (demo spec: docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md)
# One 5k run saving every 1k, pruned to 3 rungs; the 10k baseline (a separate,
# earlier run — labeled as such in the UI) is the free top rung.
LADDER_STEPS = 5_000
LADDER_SAVE_FREQ = 1_000
LADDER_KEEP_STEPS = (1_000, 3_000, 5_000)
LADDER_EVAL_EPISODES = 10
LADDER_EVAL_BATCH_SIZE = 5
LADDER_TRAIN_OUTPUT_DIR = APP_ROOT / "outputs" / "train" / "act_pusht_ladder"
LADDER_EVAL_OUTPUT_DIR = APP_ROOT / "outputs" / "eval" / "ladder"
DEMO_LADDER_MANIFEST = APP_ROOT / "outputs" / "demo" / "ladder.json"


def train_ladder_cmd() -> list[str]:
    return _train_cmd(LADDER_STEPS, LADDER_SAVE_FREQ, 500, LADDER_TRAIN_OUTPUT_DIR)


def ladder_rungs() -> list[dict]:
    """The demo's checkpoint ladder, weakest to strongest."""
    rungs = [
        {
            "name": f"{s // 1000}k",
            "steps": s,
            "run": "ladder run (5k steps, 2026-07-15)",
            "checkpoint": LADDER_TRAIN_OUTPUT_DIR / "checkpoints" / f"{s:06d}" / "pretrained_model",
        }
        for s in LADDER_KEEP_STEPS
    ]
    rungs.append(
        {
            "name": "10k",
            "steps": BASELINE_STEPS,
            "run": "baseline run (10k steps, 2026-07-12)",
            "checkpoint": BASELINE_TRAIN_OUTPUT_DIR / "checkpoints" / f"{BASELINE_STEPS:06d}" / "pretrained_model",
        }
    )
    return rungs
```

NOTE: `_train_cmd` is defined below these lines in the current file — Python resolves it at call time, not definition time, so appending the block after the existing dir constants but before `_train_cmd` works; simplest is to append the whole block at the END of config.py (after `latest_checkpoint`). Do that.

In `apps/manip-trial/src/manip_trial/run.py`, add the stage and the prune helper. Full new file content:

```python
"""Config-driven runner for the manual pipeline stages.

Usage: python -m manip_trial.run <train-baseline|baseline-eval|train-smoke|eval-trained|train-ladder|eval-ladder>
Builds each stage's CLI invocation from config.py so manual runs and the
smoke test always agree on parameters.
"""

import shutil
import subprocess
import sys

from manip_trial import config


def _prune_ladder() -> None:
    """Keep only the rung checkpoints (and drop their optimizer state).

    A 5k run with save_freq=1000 leaves 5 checkpoints + a `last` symlink at
    ~400 MB each (half of it training_state). The demo needs 3 rungs of
    pretrained_model only.
    """
    ckpt_root = config.LADDER_TRAIN_OUTPUT_DIR / "checkpoints"
    keep = {f"{s:06d}" for s in config.LADDER_KEEP_STEPS}
    for d in sorted(ckpt_root.iterdir()):
        if d.name not in keep:
            d.unlink() if d.is_symlink() else shutil.rmtree(d)
        else:
            shutil.rmtree(d / "training_state", ignore_errors=True)


def main() -> int:
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    if stage == "train-baseline":
        shutil.rmtree(config.BASELINE_TRAIN_OUTPUT_DIR, ignore_errors=True)
        cmd = config.train_baseline_cmd()
    elif stage == "baseline-eval":
        shutil.rmtree(config.BASELINE_EVAL_OUTPUT_DIR, ignore_errors=True)
        cmd = config.eval_cmd(
            str(config.latest_checkpoint(config.BASELINE_TRAIN_OUTPUT_DIR)),
            config.BASELINE_EVAL_EPISODES,
            config.BASELINE_EVAL_BATCH_SIZE,
            config.BASELINE_EVAL_OUTPUT_DIR,
        )
    elif stage == "train-smoke":
        shutil.rmtree(config.TRAIN_OUTPUT_DIR, ignore_errors=True)
        cmd = config.train_smoke_cmd()
    elif stage == "eval-trained":
        shutil.rmtree(config.SMOKE_EVAL_OUTPUT_DIR, ignore_errors=True)
        cmd = config.eval_cmd(
            str(config.latest_checkpoint()),
            config.SMOKE_EVAL_EPISODES,
            config.SMOKE_EVAL_BATCH_SIZE,
            config.SMOKE_EVAL_OUTPUT_DIR,
        )
    elif stage == "train-ladder":
        shutil.rmtree(config.LADDER_TRAIN_OUTPUT_DIR, ignore_errors=True)
        rc = subprocess.run(config.train_ladder_cmd()).returncode
        if rc == 0:
            _prune_ladder()
        return rc
    elif stage == "eval-ladder":
        from manip_trial.ladder import eval_ladder

        return eval_ladder()
    else:
        print(__doc__)
        return 2
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
```

(`manip_trial.ladder` arrives in Task 2 — the `eval-ladder` branch imports lazily so this file is complete now and Task 1's tests don't touch it.)

Add to `apps/manip-trial/Makefile` (after the `eval-trained` target; also extend `.PHONY`):

```makefile
# Demo ladder: one 5k-step run saving every 1k, pruned to rungs 1k/3k/5k
# (~8 min on M2 Pro MPS). The 10k baseline run is reused as the top rung.
train-ladder:
	uv run python -m manip_trial.run train-ladder

# Eval every rung (10 seeded episodes each) + write outputs/demo/ladder.json.
eval-ladder:
	uv run python -m manip_trial.run eval-ladder
```

`.PHONY` line becomes:

```makefile
.PHONY: sync info train-baseline baseline-eval train-smoke eval-trained smoke clean train-ladder eval-ladder demo demo-image demo-smoke
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ladder.py -v`
Expected: 3 PASSED.

Also run the existing suite to prove nothing regressed: `uv run pytest tests/test_smoke.py -v` — this runs the full 200-step train+eval (~40 s), expected PASS.

- [ ] **Step 5: Run the real ladder training (~8 min)**

Run: `make train-ladder`
Expected: lerobot-train completes 5000 steps (loss falling from ~14 toward <1), then pruning leaves exactly:

```
outputs/train/act_pusht_ladder/checkpoints/001000/pretrained_model/
outputs/train/act_pusht_ladder/checkpoints/003000/pretrained_model/
outputs/train/act_pusht_ladder/checkpoints/005000/pretrained_model/
```

Verify: `ls outputs/train/act_pusht_ladder/checkpoints/` shows exactly `001000 003000 005000`, and `du -sh outputs/train/act_pusht_ladder` is ~600 MB.

- [ ] **Step 6: Commit**

```bash
cd ~/repos/robium-applications
git add apps/manip-trial/src/manip_trial/config.py apps/manip-trial/src/manip_trial/run.py apps/manip-trial/Makefile apps/manip-trial/tests/test_ladder.py
git commit -m "feat(manip-trial): checkpoint ladder — 5k train run pruned to 1k/3k/5k rungs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(Checkpoints themselves stay untracked — `outputs/` is gitignored.)

---

### Task 2: Ladder eval + `ladder.json` manifest

**Files:**
- Create: `apps/manip-trial/src/manip_trial/ladder.py`
- Test: `apps/manip-trial/tests/test_ladder.py` (extend)

**Interfaces:**
- Consumes: `config.ladder_rungs()`, `config.eval_cmd(...)`, `config.LADDER_EVAL_OUTPUT_DIR`, `config.DEMO_LADDER_MANIFEST` (Task 1).
- Produces: `ladder.build_manifest(rungs: list[dict], eval_root: Path, app_root: Path) -> dict` and `ladder.eval_ladder() -> int`. Manifest schema (consumed by Tasks 3 and 5):

```json
{
  "seed": 1000,
  "rungs": [
    {
      "name": "1k",
      "steps": 1000,
      "run": "ladder run (5k steps, 2026-07-15)",
      "checkpoint": "outputs/train/act_pusht_ladder/checkpoints/001000/pretrained_model",
      "metrics": {"avg_max_reward": 0.0, "avg_sum_reward": 0.0, "pc_success": 0.0, "n_episodes": 10},
      "videos": ["outputs/eval/ladder/1k/videos/pusht_0/eval_episode_0.mp4"]
    }
  ]
}
```

All paths are APP_ROOT-relative strings so native and container runs both resolve them.

- [ ] **Step 1: Write the failing test**

Append to `apps/manip-trial/tests/test_ladder.py`:

```python
import json

from manip_trial.ladder import build_manifest


def test_build_manifest(tmp_path):
    app_root = tmp_path
    eval_root = tmp_path / "outputs" / "eval" / "ladder"
    ckpt = tmp_path / "outputs" / "train" / "x" / "checkpoints" / "001000" / "pretrained_model"
    ckpt.mkdir(parents=True)
    rung_eval = eval_root / "1k"
    (rung_eval / "videos" / "pusht_0").mkdir(parents=True)
    (rung_eval / "videos" / "pusht_0" / "eval_episode_0.mp4").write_bytes(b"")
    (rung_eval / "eval_info.json").write_text(
        json.dumps({"overall": {
            "avg_max_reward": 0.1, "avg_sum_reward": 2.0, "pc_success": 0.0,
            "n_episodes": 10, "eval_s": 9.9, "video_paths": ["ignored"],
        }})
    )
    rungs = [{"name": "1k", "steps": 1000, "run": "ladder", "checkpoint": ckpt}]

    m = build_manifest(rungs, eval_root, app_root)

    r = m["rungs"][0]
    assert r["checkpoint"] == "outputs/train/x/checkpoints/001000/pretrained_model"
    assert r["metrics"] == {
        "avg_max_reward": 0.1, "avg_sum_reward": 2.0, "pc_success": 0.0, "n_episodes": 10,
    }
    assert r["videos"] == ["outputs/eval/ladder/1k/videos/pusht_0/eval_episode_0.mp4"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ladder.py::test_build_manifest -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'manip_trial.ladder'`.

- [ ] **Step 3: Write `src/manip_trial/ladder.py`**

```python
"""Ladder eval + manifest: eval every rung, write outputs/demo/ladder.json.

The manifest is the single source both the demo's checkpoint radio and its
gallery tab read — the eval target GENERATES it (never hand-edit), so every
number the page shows traces to a real eval_info.json.
"""

import json
import shutil
import subprocess
from pathlib import Path

from manip_trial import config

_METRIC_KEYS = ("avg_max_reward", "avg_sum_reward", "pc_success", "n_episodes")


def build_manifest(rungs: list[dict], eval_root: Path, app_root: Path) -> dict:
    entries = []
    for r in rungs:
        eval_dir = eval_root / r["name"]
        overall = json.loads((eval_dir / "eval_info.json").read_text())["overall"]
        videos = sorted(
            str(p.relative_to(app_root)) for p in eval_dir.glob("videos/**/*.mp4")
        )
        entries.append(
            {
                "name": r["name"],
                "steps": r["steps"],
                "run": r["run"],
                "checkpoint": str(r["checkpoint"].relative_to(app_root)),
                "metrics": {k: overall[k] for k in _METRIC_KEYS},
                "videos": videos,
            }
        )
    return {"seed": config.SEED, "rungs": entries}


def eval_ladder() -> int:
    rungs = config.ladder_rungs()
    for r in rungs:
        out = config.LADDER_EVAL_OUTPUT_DIR / r["name"]
        shutil.rmtree(out, ignore_errors=True)
        cmd = config.eval_cmd(
            str(r["checkpoint"]), config.LADDER_EVAL_EPISODES, config.LADDER_EVAL_BATCH_SIZE, out
        )
        print(f"$ {' '.join(cmd)}", flush=True)
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            return rc
    manifest = build_manifest(rungs, config.LADDER_EVAL_OUTPUT_DIR, config.APP_ROOT)
    config.DEMO_LADDER_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    config.DEMO_LADDER_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {config.DEMO_LADDER_MANIFEST}")
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ladder.py -v`
Expected: 4 PASSED.

- [ ] **Step 5: Run the real ladder eval (~3–5 min: 4 rungs × model load + 10 episodes)**

Run: `make eval-ladder`
Expected: four lerobot-eval runs complete; `outputs/demo/ladder.json` exists. Verify the story is monotonic-ish:

```bash
uv run python -c "
import json
m = json.load(open('outputs/demo/ladder.json'))
for r in m['rungs']:
    print(r['name'], r['steps'], round(r['metrics']['avg_max_reward'], 3), f\"{r['metrics']['pc_success']}%\")
"
```

Expected shape: avg_max_reward rises with steps (1k lowest, 10k ≈ 0.283 known from the baseline eval — the 10k rung re-evals with the same seed so it should reproduce ≈0.28). `pc_success` likely 0.0 everywhere — that is fine and expected. If a middle rung is non-monotonic, that's honest reality; keep it (the UI shows real numbers).

- [ ] **Step 6: Commit**

```bash
git add apps/manip-trial/src/manip_trial/ladder.py apps/manip-trial/tests/test_ladder.py
git commit -m "feat(manip-trial): eval-ladder — per-rung seeded evals + generated ladder.json manifest

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Demo deps + demo config constants + `episode_runner.py`

**Files:**
- Modify: `apps/manip-trial/pyproject.toml`
- Modify: `apps/manip-trial/src/manip_trial/config.py`
- Create: `apps/manip-trial/src/manip_trial/demo/__init__.py` (empty)
- Create: `apps/manip-trial/src/manip_trial/demo/episode_runner.py`
- Test: `apps/manip-trial/tests/test_demo.py` (new — runner part)

**Interfaces:**
- Consumes: `config.DEMO_LADDER_MANIFEST`, `config.APP_ROOT`, `config.SEED` (Task 1), the manifest file on disk (Task 2).
- Produces (consumed by Tasks 4–5):
  - config: `DEMO_PORT: int` (env `PORT`, default 8765), `DEMO_SESSION_SECONDS = 1800`, `DEMO_FLEET_BUDGET = 2`, `DEMO_DEFAULT_RUNG = "10k"`, `demo_device() -> str`.
  - `EpisodeRunner()` — loads the manifest, loads the default rung's policy, probes the env; attributes `device: str`, `rungs: dict[str, dict]` (manifest rungs keyed by name), `manifest: dict`, property `busy: bool`, methods `request_abort() -> None` and `run(rung: str, rec: rr.RecordingStream) -> Iterator[StepEvent]`.
  - `StepEvent` dataclass: `step: int`, `total: int`, `done: bool = False`, `success: bool = False`, `aborted: bool = False`, `max_reward: float = 0.0`.

- [ ] **Step 1: Add dependencies**

In `apps/manip-trial/pyproject.toml`, replace the `dependencies` list with:

```toml
dependencies = [
    "lerobot[diffusion,pusht,training,viz]==0.6.0",
    # Demo page (spec 2026-07-15). rerun-sdk and gradio_rerun are pinned to
    # each other — the viewer component and SDK must match minor versions.
    "rerun-sdk==0.34.1",
    "gradio>=6.0.0",
    "gradio_rerun==0.34.1",
    "fastapi>=0.115",
    "uvicorn>=0.30",
]
```

Run: `uv sync`
Expected: resolves and installs cleanly. If the resolver conflicts on `rerun-sdk` (lerobot's `viz` extra also pulls rerun), note the exact error in `learnings/2026-07-15.md` tagged `[lerobot]` and pin to whatever single version satisfies both, updating this plan's pins to match vla-trial's proven set.

- [ ] **Step 2: Write the failing runner test**

Create `apps/manip-trial/tests/test_demo.py` (runner-only part; the gateway tests are appended in Task 4):

```python
"""Demo tests. The EpisodeRunner test and the gateway smoke are both marked
slow (real checkpoint loads); run via `make demo-smoke`, not the default suite.
"""

import pytest
import rerun as rr

pytestmark = pytest.mark.slow


def test_episode_runner_completes_episode():
    from manip_trial.demo.episode_runner import EpisodeRunner

    runner = EpisodeRunner()
    assert "10k" in runner.rungs and len(runner.rungs) == 4

    rec = rr.RecordingStream(application_id="manip_trial_test", recording_id="t0")
    events = list(runner.run("1k", rec))

    assert events, "no StepEvents yielded"
    last = events[-1]
    assert last.done is True
    assert last.aborted is False
    assert 0.0 <= last.max_reward <= 1.0
    assert last.step <= last.total <= 300
    assert not runner.busy
```

Register the `slow` marker if not present: check `apps/manip-trial/pyproject.toml` for a `[tool.pytest.ini_options]` block; if absent, add:

```toml
[tool.pytest.ini_options]
markers = ["slow: loads real checkpoints / boots the gateway; run via make demo-smoke"]
addopts = "-m 'not slow'"
```

(`addopts` keeps `make smoke` fast — it now needs `-m ""` nowhere since test_smoke.py is unmarked; verify `uv run pytest tests/test_smoke.py -v` still collects it.)

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_demo.py -v -m slow`
Expected: FAIL — `ModuleNotFoundError: No module named 'manip_trial.demo'`.

- [ ] **Step 4: Implement config demo constants + the runner**

Append to `apps/manip-trial/src/manip_trial/config.py` (at the end, after the ladder block):

```python
# --- demo gateway (spec: docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md)
DEMO_PORT = int(os.environ.get("PORT", "8765"))
DEMO_SESSION_SECONDS = 1800  # mirrors demos.json sessionSeconds
DEMO_FLEET_BUDGET = 2  # mirrors demos.json maxInstances (ACT-CPU is light)
DEMO_DEFAULT_RUNG = "10k"  # strongest rung loads at boot; others load lazily


def demo_device() -> str:
    """mps native, cpu in the container — resolved at runtime, not import."""
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"
```

Add `import os` at the top of config.py (it currently only imports `Path`).

Create `apps/manip-trial/src/manip_trial/demo/__init__.py` (empty) and `apps/manip-trial/src/manip_trial/demo/episode_runner.py`:

```python
"""One-episode runner — the piece between the Gradio UI and the trained rungs.

Mirrors vla-trial's demo/episode_runner.py shape (lock-serialized runs, abort
event, fresh env per run) minus the MuJoCo GL thread-affinity machinery:
gym-pusht renders with pygame/pymunk on the CPU, so there is no GL context to
worry about. A fresh env per run is kept anyway — construction is milliseconds
and guarantees no state leaks between runs.

Policies load lazily per rung (ACT is ~200 MB on disk, seconds to load) and
stay cached; the gateway boots only the default rung so DEMO READY is fast.

The inference path is the same contract lerobot's own eval loop uses
(verified against lerobot 0.6.0's scripts/lerobot_eval.py rollout()):
preprocess_observation -> preprocessor pipeline -> policy.select_action ->
postprocessor pipeline. Single sync env — immune to the forkserver/async-env
gotcha by construction.
"""

import itertools
import json
import threading
from dataclasses import dataclass

import gymnasium as gym
import gym_pusht  # noqa: F401 — registers gym_pusht/PushT-v0
import numpy as np
import rerun as rr
import torch
from lerobot.envs.utils import preprocess_observation

from manip_trial import config

MAX_EPISODE_STEPS = 300  # gym_pusht registration default; lerobot's PushtEnv config agrees


def _log_step(rec: rr.RecordingStream, step: int, obs: dict, action, reward: float, max_reward: float) -> None:
    rec.set_time("step", sequence=step)
    # obs["pixels"] is the 96x96 frame the policy actually sees — honest by
    # construction. JPEG q85: tiny over the browser stream, fine to look at.
    rec.log("sim", rr.Image(obs["pixels"]).compress(jpeg_quality=85))
    rec.log("reward/coverage", rr.Scalars([float(reward)]))
    rec.log("reward/max_so_far", rr.Scalars([float(max_reward)]))
    rec.log("action/x", rr.Scalars([float(action[0])]))
    rec.log("action/y", rr.Scalars([float(action[1])]))


@dataclass
class StepEvent:
    step: int
    total: int
    done: bool = False
    success: bool = False
    aborted: bool = False
    max_reward: float = 0.0


class EpisodeRunner:
    """Owns the rung policies; serializes runs with a lock."""

    def __init__(self, device: str | None = None):
        self.device = device or config.demo_device()
        self.manifest = json.loads(config.DEMO_LADDER_MANIFEST.read_text())
        self.rungs = {r["name"]: r for r in self.manifest["rungs"]}
        self._policies: dict[str, tuple] = {}
        self._lock = threading.Lock()
        self._abort = threading.Event()
        self._seed_counter = itertools.count()

        self._load(config.DEMO_DEFAULT_RUNG)  # boot cost: one rung, not four
        # Boot probe: prove the env constructs + renders in this process.
        probe = gym.make(
            "gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array"
        )
        probe.reset(seed=0)
        probe.close()

    def _load(self, rung: str) -> tuple:
        if rung not in self._policies:
            from lerobot.policies.act.modeling_act import ACTPolicy
            from lerobot.policies.factory import make_pre_post_processors

            path = str(config.APP_ROOT / self.rungs[rung]["checkpoint"])
            policy = ACTPolicy.from_pretrained(path)
            policy.to(self.device)
            policy.eval()
            pre, post = make_pre_post_processors(
                policy_cfg=policy.config,
                pretrained_path=path,
                preprocessor_overrides={"device_processor": {"device": self.device}},
            )
            self._policies[rung] = (policy, pre, post)
        return self._policies[rung]

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    def request_abort(self) -> None:
        """Stop the in-flight episode at its next control step (page-refresh path)."""
        self._abort.set()

    def run(self, rung: str, rec: rr.RecordingStream):
        """Generator: one episode, yielding a StepEvent after each step."""
        if rung not in self.rungs:
            raise ValueError(f"unknown rung {rung!r}")
        # Wait, don't fail: an aborted predecessor exits within one control step.
        if not self._lock.acquire(timeout=30):
            raise RuntimeError("a run is already in progress")
        self._abort.clear()
        try:
            yield from self._run_locked(rung, rec)
        finally:
            self._lock.release()

    def _run_locked(self, rung: str, rec: rr.RecordingStream):
        policy, pre, post = self._load(rung)
        policy.reset()
        # Fresh seed per run so repeat runs show different starts; offset from
        # the eval SEED so the demo never replays the gallery's exact episodes.
        seed = config.SEED + 10_000 + next(self._seed_counter)

        env = gym.make(
            "gym_pusht/PushT-v0", obs_type="pixels_agent_pos", render_mode="rgb_array"
        )
        try:
            obs, _ = env.reset(seed=seed)
            success = False
            max_reward = 0.0
            step = 0
            for step in range(MAX_EPISODE_STEPS):
                if self._abort.is_set():
                    yield StepEvent(step=step, total=MAX_EPISODE_STEPS, done=True,
                                    aborted=True, max_reward=max_reward)
                    return
                batch = pre(preprocess_observation(obs))
                with torch.inference_mode():
                    action = policy.select_action(batch)
                action = post(action)
                action = action.squeeze(0).cpu().numpy().astype(np.float32)

                obs, reward, terminated, truncated, info = env.step(action)
                max_reward = max(max_reward, float(reward))
                success = bool(info["is_success"])
                _log_step(rec, step, obs, action, float(reward), max_reward)
                yield StepEvent(step=step, total=MAX_EPISODE_STEPS, max_reward=max_reward)
                if terminated or truncated:
                    break

            yield StepEvent(step=step, total=MAX_EPISODE_STEPS, done=True,
                            success=success, max_reward=max_reward)
        finally:
            env.close()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_demo.py::test_episode_runner_completes_episode -v -m slow`
Expected: PASS in ~1–3 min (10k policy load at init + 1k policy load + one ≤300-step episode on MPS). If `preprocess_observation(obs)` raises a key/shape error, inspect the actual `obs` dict keys from `env.reset()` and fix the call site (the gym obs dict for `pixels_agent_pos` is `{"pixels": HxWx3 uint8, "agent_pos": (2,) float}`); log the discrepancy to learnings tagged `[lerobot]`.

- [ ] **Step 6: Commit**

```bash
git add apps/manip-trial/pyproject.toml apps/manip-trial/uv.lock apps/manip-trial/src/manip_trial/config.py apps/manip-trial/src/manip_trial/demo/ apps/manip-trial/tests/test_demo.py
git commit -m "feat(manip-trial): demo episode runner — lazy per-rung ACT policies, Rerun step logging

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Session gateway (`gateway.py`) + contract tests

**Files:**
- Create: `apps/manip-trial/src/manip_trial/demo/gateway.py`
- Create: `apps/manip-trial/src/manip_trial/demo/ui.py` (STUB in this task — full UI in Task 5)
- Test: `apps/manip-trial/tests/test_demo.py` (extend)

**Interfaces:**
- Consumes: `EpisodeRunner` (Task 3); config demo constants (Task 3).
- Produces: `python -m manip_trial.demo.gateway` serving on `PORT` (default 8765): `POST /start?session=`, `GET /status?session=`, `POST /shutdown?session=`, `/ui` (Gradio). Prints `DEMO READY` on boot completion. `build_ui(get_runner) -> gr.Blocks` signature fixed here (Task 5 fills it in).

- [ ] **Step 1: Write the failing gateway tests**

Append to `apps/manip-trial/tests/test_demo.py`:

```python
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

PORT = 8798  # NOT 8765 (a dev gateway may be up) and NOT 8799 (vla-trial's test port)
BASE = f"http://127.0.0.1:{PORT}"
BOOT_TIMEOUT_S = 180
EPISODE_TIMEOUT_S = 300


def _http(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"content-type": "application/json"} if body is not None else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


@pytest.fixture(scope="module")
def gateway(tmp_path_factory):
    log_path = tmp_path_factory.mktemp("demo") / "gateway.log"
    env = {**os.environ, "PORT": str(PORT)}
    with open(log_path, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "manip_trial.demo.gateway"],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    deadline = time.time() + BOOT_TIMEOUT_S
    while time.time() < deadline:
        text = log_path.read_text()
        if "DEMO READY" in text:
            break
        if "BOOT FAILED" in text or proc.poll() is not None:
            break
        time.sleep(2)
    else:
        proc.kill()
        pytest.fail(f"gateway never reached DEMO READY in {BOOT_TIMEOUT_S}s:\n{log_path.read_text()[-3000:]}")
    if "DEMO READY" not in log_path.read_text():
        proc.kill()
        pytest.fail(f"gateway boot failed:\n{log_path.read_text()[-3000:]}")
    yield proc
    if proc.poll() is None:
        proc.kill()


def test_status_ready_then_claim(gateway):
    code, st = _http("GET", "/status?session=alice")
    assert code == 200
    assert st["ready"] is True
    assert st["claimed"] is False
    assert st["fleet"]["budget"] >= 1

    code, body = _http("POST", "/start?session=alice")
    assert code == 200 and body["ok"] is True

    code, st = _http("GET", "/status?session=alice")
    assert code == 200 and st["claimed"] is True


def test_intruder_session_rejected(gateway):
    code, _ = _http("GET", "/status?session=bob")
    assert code == 409
    code, _ = _http("POST", "/shutdown?session=bob")
    assert code == 403


def test_refresh_reclaims_claim(gateway):
    code, body = _http("POST", "/start?session=carol")
    assert code == 200 and body["ok"] is True
    code, st = _http("GET", "/status?session=carol")
    assert code == 200 and st["claimed"] is True
    code, _ = _http("GET", "/status?session=alice")
    assert code == 409
```

(The episode-through-Gradio test and the shutdown test are added in Task 5 — shutdown must run LAST in the module because it kills the shared fixture process.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_demo.py -v -m slow -k "status or intruder or refresh"`
Expected: FAIL/ERROR — the gateway module doesn't exist, so the fixture's subprocess dies immediately and `pytest.fail` fires with a `No module named manip_trial.demo.gateway` log tail.

- [ ] **Step 3: Implement the gateway (+ UI stub)**

Create `apps/manip-trial/src/manip_trial/demo/ui.py` as a stub so the gateway imports (Task 5 replaces the body):

```python
"""Demo Gradio app — full implementation lands with the UI task."""

import gradio as gr


def build_ui(get_runner) -> gr.Blocks:
    with gr.Blocks(title="manip-trial — robium live demo") as blocks:
        gr.Markdown("UI under construction.")
    return blocks
```

Create `apps/manip-trial/src/manip_trial/demo/gateway.py` — vla-trial's gateway with manip-trial imports (contract identical; comments trimmed to the manip-specific facts):

```python
"""Demo session gateway — one process, one port (8765), per the demo spec.

FastAPI implementing nav-trial's session contract (so robium-website's
Controls/demoClient/orchestrator reuse unchanged) + the Gradio app mounted at
/ui. Same design as vla-trial's demo/gateway.py; see that module and
docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md.

  POST /start?session=U    -> claim (takeable even mid-run: page-refresh path;
                              foreign takeover aborts the in-flight run)
  GET  /status?session=U   -> nav-trial's JSON shape; foreign session -> 409
  POST /shutdown?session=U -> foreign -> 403; own -> exit THIS process
  /ui                      -> the Gradio app (iframed by the website)

Runs identically native (uv, MPS) and in the demo container (CPU): readiness
is "default rung loaded + env probed", printed as DEMO READY (the
orchestrator's readyLog).
"""

import os
import threading
import time
from contextlib import asynccontextmanager

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from manip_trial.config import (
    DEMO_DEFAULT_RUNG,
    DEMO_FLEET_BUDGET,
    DEMO_PORT,
    DEMO_SESSION_SECONDS,
)
from manip_trial.demo.ui import build_ui

state = {
    "session": None,
    "claimed_at": None,
    "ready": False,
    "runner": None,
    "start": time.time(),
    "log": ["gateway up — loading checkpoints + env…"],
}


def _boot() -> None:
    """Heavy load in a thread so /status answers from the first second."""
    try:
        from manip_trial.demo.episode_runner import EpisodeRunner

        runner = EpisodeRunner()
        state["runner"] = runner
        state["ready"] = True
        state["log"].append(
            f"ready — {runner.device} inference, default rung {DEMO_DEFAULT_RUNG}, "
            f"{len(runner.rungs)} rungs on the ladder"
        )
        print("DEMO READY", flush=True)  # the orchestrator's readyLog line
    except Exception as e:  # surface boot failures in the page's log pane
        state["log"].append(f"BOOT FAILED: {e}")
        print(f"BOOT FAILED: {e}", flush=True)
        raise


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    threading.Thread(target=_boot, daemon=True).start()
    yield


app = FastAPI(lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    # Exact-origin reflect (ACAO:* is invalid with credentials): prod site +
    # localhost dev, same shape as nav-trial's gateway.
    allow_origin_regex=r"^https://(www\.)?robium\.(ai|org)$|^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _busy() -> bool:
    return state["runner"] is not None and state["runner"].busy


@app.post("/start")
def start(session: str | None = None):
    # Claims are ALWAYS takeable, even mid-run (page refresh mints a new
    # session id while Gradio keeps executing the orphaned episode; locally
    # this is the only instance, so the refresh must win). v1-local tradeoff,
    # stated honestly: a second visitor can steal the instance.
    if _busy() and session != state["session"]:
        state["runner"].request_abort()
    if session != state["session"]:
        state["claimed_at"] = time.time()
    state["session"] = session or "anonymous"
    state["claimed_at"] = state["claimed_at"] or time.time()
    return {"ok": True}


@app.get("/status")
def status(session: str | None = None):
    if state["session"] and session != state["session"]:
        return JSONResponse({"error": "not your instance"}, status_code=409)
    up = int(time.time() - (state["claimed_at"] or state["start"]))
    return {
        "claimed": state["session"] is not None,
        "ready": state["ready"],
        "rtf": None,  # kept for the shared Status shape; meaningless here
        "nodes": 0,
        "uptime_s": up,
        "remaining_s": max(0, DEMO_SESSION_SECONDS - up),
        "fleet": {"running": None, "budget": DEMO_FLEET_BUDGET},
        "log": state["log"],
    }


@app.post("/shutdown")
def shutdown(session: str | None = None):
    if state["session"] is None or session != state["session"]:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    # Answer first, then exit THIS process: PID 1 in the container (AutoRemove
    # reaps it), a plain uv-run process natively.
    threading.Timer(0.2, os._exit, args=(0,)).start()
    return {"bye": True}


@app.get("/")
def root():
    return {"service": "robium demo gateway (manip-trial)"}


app = gr.mount_gradio_app(app, build_ui(lambda: state["runner"]), path="/ui")


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=DEMO_PORT, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_demo.py -v -m slow -k "status or intruder or refresh"`
Expected: 3 PASSED (boot takes ~10–30 s: one ACT load + env probe).

- [ ] **Step 5: Commit**

```bash
git add apps/manip-trial/src/manip_trial/demo/gateway.py apps/manip-trial/src/manip_trial/demo/ui.py apps/manip-trial/tests/test_demo.py
git commit -m "feat(manip-trial): demo session gateway — nav-trial contract, DEMO READY boot line

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Gradio UI (Run tab + Gallery tab) + episode/shutdown tests + `make demo` / `make demo-smoke`

**Files:**
- Modify: `apps/manip-trial/src/manip_trial/demo/ui.py` (replace the stub)
- Modify: `apps/manip-trial/Makefile`
- Test: `apps/manip-trial/tests/test_demo.py` (extend)

**Interfaces:**
- Consumes: `EpisodeRunner.run(rung, rec)`, `runner.rungs`, `runner.manifest` (Task 3); `build_ui(get_runner)` mount point (Task 4).
- Produces: Gradio endpoint `api_name="run_episode"` taking one input (rung name string) and yielding `(rerun_bytes, status_text)`; status texts end with `finished at step N: …` including `max coverage reward X.XX`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/manip-trial/tests/test_demo.py` (ORDER MATTERS: these run after the Task 4 tests; shutdown stays last):

```python
def test_episode_completes_via_gradio_api(gateway):
    # "1k" — the weakest rung: honest flailing, but completion is the
    # assertion, not success (pc_success 0% is the expected reality here).
    code, sub = _http("POST", "/ui/gradio_api/call/run_episode", {"data": ["1k"]})
    assert code == 200 and "event_id" in sub, sub

    req = urllib.request.Request(f"{BASE}/ui/gradio_api/call/run_episode/{sub['event_id']}")
    final_status = None
    deadline = time.time() + EPISODE_TIMEOUT_S
    with urllib.request.urlopen(req, timeout=EPISODE_TIMEOUT_S) as r:
        for raw in r:
            if time.time() > deadline:
                break
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line == "data: null":
                continue
            payload = json.loads(line[len("data:"):])
            if isinstance(payload, list) and payload and isinstance(payload[-1], str):
                final_status = payload[-1]
                if "finished at step" in final_status:
                    break
    assert final_status is not None, "no status updates arrived on the SSE stream"
    assert "finished at step" in final_status, f"episode never finished: {final_status!r}"
    assert "reward" in final_status, f"verdict lacks the honest metric: {final_status!r}"


def test_shutdown_exits_process(gateway):
    # carol holds the claim after the reclaim test above.
    code, body = _http("POST", "/shutdown?session=carol")
    assert code == 200 and body["bye"] is True
    deadline = time.time() + 10
    while time.time() < deadline and gateway.poll() is None:
        time.sleep(0.2)
    assert gateway.poll() is not None, "gateway process still alive after /shutdown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_demo.py -v -m slow -k "gradio_api"`
Expected: FAIL — the stub UI has no `run_episode` api endpoint (404 or missing event_id).

- [ ] **Step 3: Implement the full UI**

Replace `apps/manip-trial/src/manip_trial/demo/ui.py` with:

```python
"""The demo's Gradio app: pick a rung on the training ladder -> Run ->
embedded Rerun. Plus a Gallery tab with every rung's REAL eval videos and
metrics (from outputs/demo/ladder.json — generated, never hand-edited).

Mounted at /ui by gateway.py; the website's Robot pane iframes it. Streaming
pattern (fresh RecordingStream + recording_id per Run, yield stream.read())
is vla-trial's, including the merge-on-same-id gotcha its docstring records.

Honesty is part of the layout: pc_success is 0% at every rung and the intro
says so — the rising avg_max_reward down the ladder IS the demo.
"""

import json
import uuid

import gradio as gr
import rerun as rr
import rerun.blueprint as rrb
from gradio_rerun import Rerun

from manip_trial import config

APP_ID = "manip_trial_demo"


def _manifest() -> dict:
    return json.loads(config.DEMO_LADDER_MANIFEST.read_text())


INTRO_MD = """\
**Pick a checkpoint from the training ladder, hit Run.** The ACT policy pushes
the gray T-block toward the green target zone; every control step streams onto
the Rerun timeline below (the 96×96 frame the policy sees, its actions, and
the coverage reward) — scrub it when the episode ends.

- The ladder is one training run frozen at increasing steps (plus the earlier
  10k baseline run on top) — **watching a policy get better with training.**
- Honest numbers: PushT counts "success" only at ≥95% target coverage, which
  ACT at this scale never reaches — `pc_success` is 0% at every rung. The
  rising max-coverage reward is the real story.
"""


def _blueprint() -> rrb.Blueprint:
    return rrb.Blueprint(
        rrb.Horizontal(
            rrb.Spatial2DView(origin="sim", name="what the policy sees"),
            rrb.Vertical(
                rrb.TimeSeriesView(origin="reward", name="coverage reward"),
                rrb.TimeSeriesView(origin="action", name="action (target xy)"),
            ),
            column_shares=[3, 2],
        ),
        collapse_panels=True,
    )


def _rung_choices(manifest: dict) -> list[tuple[str, str]]:
    return [
        (
            f"{r['name']} — {r['steps']:,} steps · avg_max_reward "
            f"{r['metrics']['avg_max_reward']:.3f} · {r['run']}",
            r["name"],
        )
        for r in manifest["rungs"]
    ]


def _gallery_md(manifest: dict) -> str:
    rows = [
        "| rung | steps | run | avg_max_reward | avg_sum_reward | pc_success |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in manifest["rungs"]:
        m = r["metrics"]
        rows.append(
            f"| {r['name']} | {r['steps']:,} | {r['run']} "
            f"| {m['avg_max_reward']:.3f} | {m['avg_sum_reward']:.1f} | {m['pc_success']:.0f}% |"
        )
    rows.append("")
    rows.append(
        f"Every row: a real {manifest['rungs'][0]['metrics']['n_episodes']}-episode "
        f"seeded eval (seed {manifest['seed']}) of that exact checkpoint."
    )
    return "\n".join(rows)


def build_ui(get_runner) -> gr.Blocks:
    """`get_runner` -> EpisodeRunner | None (None while the gateway boots)."""
    manifest = _manifest()

    def run_episode(rung: str):
        runner = get_runner()
        if runner is None:
            raise gr.Error("Still booting — checkpoints are loading (see the page's status pill).")

        # Fresh recording id per Run — same-id recordings MERGE in the viewer
        # (vla-trial learned this the hard way; see its ui.py docstring).
        rec = rr.RecordingStream(application_id=APP_ID, recording_id=str(uuid.uuid4()))
        stream = rec.binary_stream()
        rec.send_blueprint(_blueprint())
        yield stream.read(), f"resetting env — {rung} rung episode starting…"

        print(f"[demo] run_episode start: rung={rung}", flush=True)
        try:
            for ev in runner.run(rung, rec):
                if ev.step % 50 == 0 or ev.done:
                    print(f"[demo] step {ev.step} done={ev.done} success={ev.success}", flush=True)
                if ev.done:
                    if ev.aborted:
                        verdict = "⏹ aborted — the instance was reclaimed (page refresh or new visitor)"
                    elif ev.success:
                        verdict = f"✅ ≥95% coverage — solved (max reward {ev.max_reward:.2f})"
                    else:
                        verdict = (
                            f"❌ no success — max coverage reward {ev.max_reward:.2f} "
                            "(success needs ≥95% coverage; expected at this training scale)"
                        )
                    yield stream.read(), f"finished at step {ev.step + 1}: {verdict}"
                else:
                    yield stream.read(), f"step {ev.step + 1}/{ev.total} · max reward {ev.max_reward:.2f}"
        except RuntimeError as e:  # run lock held — another episode is executing
            raise gr.Error(str(e))

    with gr.Blocks(title="manip-trial — robium live demo") as blocks:
        with gr.Tab("Run"):
            gr.Markdown(INTRO_MD)
            rung = gr.Radio(
                choices=_rung_choices(manifest),
                value=config.DEMO_DEFAULT_RUNG,
                label="checkpoint (the training ladder, weakest → strongest)",
            )
            run_btn = gr.Button("Run episode", variant="primary")
            status = gr.Textbox(value="idle", label="status", interactive=False)
            viewer = Rerun(
                streaming=True,
                height=560,
                panel_states={"time": "collapsed", "blueprint": "hidden", "selection": "hidden"},
            )
            run_btn.click(run_episode, inputs=[rung], outputs=[viewer, status], api_name="run_episode")

        with gr.Tab("Gallery — the ladder, evaluated"):
            gr.Markdown(_gallery_md(manifest))
            with gr.Row():
                for r in manifest["rungs"]:
                    video = config.APP_ROOT / r["videos"][0]
                    gr.Video(
                        value=str(video),
                        label=f"{r['name']} ({r['steps']:,} steps) — eval episode 0",
                        interactive=False,
                    )

    return blocks
```

Add to `apps/manip-trial/Makefile` (after `eval-ladder`):

```makefile
# --- demo page (spec: docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md)

# The demo gateway, NATIVE (MPS inference). Pair with the website's dev
# backend dropdown: "direct localhost:8765". Needs the ladder built first
# (make train-ladder eval-ladder).
demo:
	uv run python -m manip_trial.demo.gateway

# Build the demo container (CPU inference). Checkpoints + ladder.json are
# baked from LOCAL outputs/ — no Hub access, no token.
demo-image:
	docker build -f docker/demo.Dockerfile -t manip-trial:latest .

# The live-demo skill's ship bar: gateway boots to DEMO READY, session guards
# hold (409/403), one episode COMPLETES through the Gradio API (completion is
# the assertion — success at this scale would be theater), /shutdown exits.
demo-smoke:
	uv run pytest tests/test_demo.py -v -m slow
```

- [ ] **Step 4: Run the full demo smoke**

Run: `make demo-smoke`
Expected: 6 PASSED (runner episode, 3 contract tests, gradio episode, shutdown) in ~5–10 min total. The Gradio episode runs the 1k rung: expect an honest `❌ no success — max coverage reward 0.xx` in the final status — that is a PASS.

- [ ] **Step 5: Eyeball it (manual, 2 min)**

Run: `make demo`, open `http://localhost:8765/ui` — Run tab streams frames + reward curves into the embedded viewer; Gallery tab shows the 4-row table + 4 videos. Ctrl-C when done.

- [ ] **Step 6: Commit**

```bash
git add apps/manip-trial/src/manip_trial/demo/ui.py apps/manip-trial/Makefile apps/manip-trial/tests/test_demo.py
git commit -m "feat(manip-trial): demo UI — ladder radio + streaming Rerun viewer + eval gallery tab

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Demo container (`docker/demo.Dockerfile` + `.dockerignore`)

**Files:**
- Create: `apps/manip-trial/docker/demo.Dockerfile`
- Create: `apps/manip-trial/.dockerignore`

**Interfaces:**
- Consumes: the gateway (Task 4/5), pruned ladder checkpoints + `ladder.json` + eval videos on the host (Tasks 1–2).
- Produces: image `manip-trial:latest`, serving the gateway on 8765, printing `DEMO READY` (consumed by the orchestrator in Task 8).

- [ ] **Step 1: Write `.dockerignore`**

Create `apps/manip-trial/.dockerignore` — keeps the build context to what the COPYs need (without it the context uploads the .venv and every training byproduct):

```
.venv/
.pytest_cache/
__pycache__/
data/
wandb/
outputs/train/act_pusht_smoke/
outputs/train/act_pusht_ladder/checkpoints/*/training_state/
outputs/eval/smoke/
outputs/eval/baseline*/
outputs/eval/eval_trained.log
outputs/train/*.log
outputs/train/act_pusht_10k/checkpoints/*/training_state/
outputs/viz/
```

- [ ] **Step 2: Write the Dockerfile**

Create `apps/manip-trial/docker/demo.Dockerfile`:

```dockerfile
# The demo container: the session gateway + Gradio/Rerun UI on :8765.
# CPU-only by design — Docker on macOS cannot see MPS; native MPS runs use
# `make demo` instead. Unlike vla-trial there is NO Hub fetch and NO token:
# gym-pusht renders with pygame (no GL stack), and every artifact the demo
# needs (rung checkpoints, ladder.json, eval videos) is COPY'd from local
# outputs/ — build after `make train-ladder eval-ladder`.
FROM python:3.12-slim

# ffmpeg: lerobot's video stack imports torchcodec, which needs the ffmpeg
# shared libraries present even though the demo never decodes a dataset.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# SDL dummy driver: pygame without a display (belt-and-braces — rgb_array
# rendering is offscreen already).
ENV SDL_VIDEODRIVER=dummy \
    PORT=8765 \
    HF_HOME=/opt/hf

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir uv && uv pip install --system .

# Bake the ladder: manifest, rung checkpoints (pretrained_model only — the
# .dockerignore drops training_state), and the gallery's eval videos.
COPY outputs/demo ./outputs/demo
COPY outputs/eval/ladder ./outputs/eval/ladder
COPY outputs/train/act_pusht_ladder ./outputs/train/act_pusht_ladder
COPY outputs/train/act_pusht_10k/checkpoints/010000/pretrained_model ./outputs/train/act_pusht_10k/checkpoints/010000/pretrained_model

# Boot probe at BUILD time: loads the default rung + constructs/renders the
# env — a broken bake fails the build, not a visitor's session.
RUN python -c "from manip_trial.demo.episode_runner import EpisodeRunner; EpisodeRunner()"

# Runtime never touches the Hub.
ENV HF_HUB_OFFLINE=1

EXPOSE 8765
CMD ["python", "-m", "manip_trial.demo.gateway"]
```

NOTE for the implementer: `uv pip install --system .` (not `-e .`) because `uv_build` needs the package importable from site-packages; if the build backend complains about README/metadata, mirror whatever vla-trial's working Dockerfile line does (`uv pip install --system -e .`). If `EpisodeRunner()` in the probe fails on a torch/MPS import inside the container, that's a bug in `demo_device()` — it must return `cpu` when MPS is unavailable (torch.backends.mps.is_available() is False on linux; no code change expected).

- [ ] **Step 3: Build and verify**

```bash
cd ~/repos/robium-applications/apps/manip-trial
make demo-image
docker run --rm -p 8765:8765 --name manip-demo-check manip-trial:latest &
sleep 45
curl -s http://localhost:8765/status?session=t | python3 -m json.tool
docker logs manip-demo-check 2>&1 | grep "DEMO READY" && echo CONTAINER_OK
curl -s -X POST "http://localhost:8765/start?session=t"
curl -s -X POST "http://localhost:8765/shutdown?session=t"
```

Expected: build succeeds (probe RUN line proves the bake); `/status` shows `"ready": true`; `DEMO READY` in logs; shutdown exits the container (the `docker run --rm` foreground job ends). If boot is slower than 45 s on CPU, poll rather than fail.

- [ ] **Step 4: Commit**

```bash
git add apps/manip-trial/docker/demo.Dockerfile apps/manip-trial/.dockerignore
git commit -m "feat(manip-trial): demo container — ladder baked from local outputs, no Hub access

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: App README + REGISTRY.md card update

**Files:**
- Modify: `apps/manip-trial/README.md`
- Modify: `REGISTRY.md` (repo root)

**Interfaces:**
- Consumes: everything above (documents it).

- [ ] **Step 1: Update the app README**

In `apps/manip-trial/README.md`, extend the Run table with the new targets and add a demo section. Add rows to the existing table:

```markdown
| `make train-ladder` | 5k-step ACT run saving every 1k, pruned to rungs 1k/3k/5k → `outputs/train/act_pusht_ladder/` (~8 min MPS). |
| `make eval-ladder` | 10-episode seeded eval of every rung (incl. the reused 10k baseline) → `outputs/eval/ladder/` + `outputs/demo/ladder.json`. |
| `make demo` | The live-demo gateway, native/MPS, on :8765 (needs the ladder built). |
| `make demo-image` | Build `manip-trial:latest` (CPU) — checkpoints baked from local outputs, no HF token. |
| `make demo-smoke` | The demo ship bar: boot → ready, session guards, one episode completes via the Gradio API, shutdown. |
```

And after the Run section add:

```markdown
## Live demo

The demo page (spec: `docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md`
at the repo root) serves a checkpoint-ladder story: pick a rung (1k/3k/5k from one
training run + the 10k baseline), watch ACT push the T-block live on an embedded
Rerun timeline, and browse each rung's real eval videos in the Gallery tab.
v1 is local-only — the robium-website page's Start button spawns
`manip-trial:latest` via the local orchestrator (`npm run dev` there), or run
`make demo` and use the page's direct-host mode. Honest numbers: `pc_success`
is 0% at every rung (PushT success needs ≥95% coverage); the rising
`avg_max_reward` down the ladder is the story.
```

- [ ] **Step 2: Update REGISTRY.md**

In the repo-root `REGISTRY.md`: on the manip-trial quick-index row, update the Viz column to `rerun / MP4s (+ gradio_rerun demo UI)` and the verified date to today with `(demo gateway validated)` appended. On the manip-trial card, add after the "Battle scars encoded" bullet:

```markdown
- **Live demo (v1, local-only; spec
  `docs/superpowers/specs/2026-07-15-manip-trial-demo-page-design.md`):**
  `src/manip_trial/demo/` — FastAPI session gateway (nav-trial's contract) +
  Gradio/Rerun UI with a checkpoint-ladder radio (1k/3k/5k from one run + the
  10k baseline) and a real-eval gallery tab. `make demo` = native/MPS;
  `make demo-image` = the CPU container (no Hub access — everything baked
  from local outputs); `make demo-smoke` = the gate. Frontend lives in
  robium-website (`/demos/manip-trial/`, orchestrator `demos.json`).
```

- [ ] **Step 3: Commit**

```bash
git add apps/manip-trial/README.md REGISTRY.md
git commit -m "docs(manip-trial): README + registry card — live demo v1 (checkpoint ladder)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Website — orchestrator entry, page, workspace island, Apps card, smoke assertions

**Files (all in `~/repos/robium-website`):**
- Modify: `demo-orchestrator/src/demos.json`
- Create: `src/pages/demos/manip-trial.astro`
- Create: `src/components/demo/ManipWorkspace.tsx`
- Modify: `src/components/Apps.astro`
- Modify: `tests/smoke.sh`

**Interfaces:**
- Consumes: image `manip-trial:latest` (Task 6), gateway contract (Task 4), demo id `manip-trial`.
- Produces: `/demos/manip-trial/` page; orchestrator can spawn/reap the demo.

- [ ] **Step 1: Orchestrator entry**

In `demo-orchestrator/src/demos.json`, add as the first array element (before vla-trial):

```json
{
  "id": "manip-trial",
  "title": "ACT imitation learning on PushT — a checkpoint ladder (LeRobot + Rerun)",
  "image": "manip-trial:latest",
  "command": ["python", "-m", "manip_trial.demo.gateway"],
  "gatewayPort": 8765,
  "readyLog": "DEMO READY",
  "maxInstances": 2,
  "sessionSeconds": 1800
},
```

Run the orchestrator's own tests: `cd ~/repos/robium-website/demo-orchestrator && npm test` — expected PASS (the entry is data; tests validate the file loads).

- [ ] **Step 2: Workspace island**

Create `src/components/demo/ManipWorkspace.tsx` — a copy of `VlaWorkspace.tsx` with these exact substitutions (the lifecycle machinery is identical and proven; do not restructure it):

- Component name `VlaWorkspace` → `ManipWorkspace`; header comment first line → `// manip-trial's minimal workspace (v1): Controls + one Robot pane (the`
- localStorage key `'vlaDemoMode'` → `'manipDemoMode'` (both occurrences: the `useState` initializer and `changeMode`)
- `createInstance('vla-trial', s)` → `createInstance('manip-trial', s)`
- Topbar label `vla-trial live demo` → `manip-trial live demo`
- Cloud-unsupported notice text → `` The hosted version of this demo isn't up yet. Run it locally: clone robium-applications, `make demo-image` in apps/manip-trial, then `npm run dev` in robium-website and open this page on localhost. ``
- Controls description metric →

```tsx
<span className="metric">
  the checkpoint ladder: the same ACT policy frozen at 1k/3k/5k/10k
  training steps — pick a rung and watch it get better. pc_success is
  0% at every rung (PushT "success" needs ≥95% coverage) — the page
  is honest about it.
</span>
```

- Unreachable hint `cd apps/vla-trial && make demo` → `cd apps/manip-trial && make demo`
- Booting text → `<p>Booting — loading the ACT checkpoints and the PushT env…</p>`
- iframe title → `manip-trial robot UI (Gradio + Rerun)`
- Idle hint → `'Start an instance: the PushT sim, the checkpoint ladder, and the Rerun timeline appear here.'`

- [ ] **Step 3: Page**

Create `src/pages/demos/manip-trial.astro`:

```astro
---
import Base from '../../layouts/Base.astro';
import ManipWorkspace from '../../components/demo/ManipWorkspace.tsx';
---
<Base title="manip-trial live demo — robium">
  <ManipWorkspace client:only="react" />
</Base>
```

- [ ] **Step 4: Apps card button**

In `src/components/Apps.astro`, the manip-trial card currently has no demo button. After its `<p>…real evaluation rollout.</p>` paragraph (inside `.app-body`, matching the vla-trial card's shape), add:

```html
<a href="/demos/manip-trial/" class="btn btn-primary demo-btn">Try the live demo (local) →</a>
```

Also update the card's paragraph to mention the ladder — replace the existing `<p>` content with:

```html
<p>
  An imitation-learning policy trains on the PushT dataset and evaluates
  in sim with metrics — on a GPU-less laptop. The live demo is a
  checkpoint ladder: the same policy at 1k/3k/5k/10k steps, runnable
  side by side. Right: a real evaluation rollout.
</p>
```

- [ ] **Step 5: Smoke assertions**

In `tests/smoke.sh`, after the vla-trial block (line ~37), add:

```bash
  # manip-trial demo page (v1, local-only)
  D3=$(cat dist/demos/manip-trial/index.html)
  grep -q "manip-trial live demo" <<<"$D3" && echo "ok: manip-trial demo page" || { echo "FAIL: manip-trial demo page"; fail=1; }
  grep -rq "ManipWorkspace" dist/demos/manip-trial/ dist/_astro/ 2>/dev/null && echo "ok: manip workspace island" || { echo "FAIL: manip workspace island"; fail=1; }
  grep -q "/demos/manip-trial" dist/index.html && echo "ok: homepage manip-trial link" || { echo "FAIL: homepage manip-trial link"; fail=1; }
```

- [ ] **Step 6: Run the website smoke**

Run: `cd ~/repos/robium-website && make smoke`
Expected: build + all assertions `ok`, including the three new ones, exit 0.

- [ ] **Step 7: Commit (in robium-website)**

```bash
cd ~/repos/robium-website
git add demo-orchestrator/src/demos.json src/pages/demos/manip-trial.astro src/components/demo/ManipWorkspace.tsx src/components/Apps.astro tests/smoke.sh
git commit -m "feat(demos): manip-trial demo page — checkpoint-ladder workspace, orchestrator entry

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: End-to-end verification (both run modes) + learnings retro

**Files:**
- Modify: `learnings/2026-07-15.md` (robium-applications — should already have in-flight entries from earlier tasks)

- [ ] **Step 1: E2E orchestrator mode**

With Docker up and `manip-trial:latest` built:

```bash
cd ~/repos/robium-website && npm run dev
```

Open `http://localhost:4321/demos/manip-trial/` → Start instance → wait for `ready` → in the Robot pane run one episode on the **1k** rung and one on the **10k** rung; confirm the Rerun timeline streams and the final status shows the honest verdict with a max-reward number; open the Gallery tab; Stop instance → confirm the container is removed (`docker ps`).

- [ ] **Step 2: E2E direct/native mode**

```bash
cd ~/repos/robium-applications/apps/manip-trial && make demo
```

Open `http://localhost:4321/demos/manip-trial/?host=localhost:8765` → same checks (inference now MPS — visibly faster steps). Ctrl-C the gateway when done.

- [ ] **Step 3: Full backend test suite one last time**

```bash
cd ~/repos/robium-applications/apps/manip-trial
uv run pytest tests/ -v          # fast suite (ladder plumbing + smoke)
```

Expected: all PASS (`test_demo.py` is excluded by the `-m 'not slow'` addopts; it passed in Task 5/6).

- [ ] **Step 4: End-of-block retro (mandatory, robium-applications CLAUDE.md)**

Append to `learnings/2026-07-15.md` one line per robium skill that loaded during the block (expected: live-demo, lerobot, rerun, testing, environments, integration), scoring fired/accurate/complete/lean. Then commit:

```bash
cd ~/repos/robium-applications
git add learnings/2026-07-15.md
git commit -m "learnings: manip-trial demo build session

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Offer skill-updater candidates (do NOT edit skills)**

Present any `[skill]` findings from the session as `[target-skill] finding → smallest intended edit` and ask whether to run skill-updater. This is an offer only.
