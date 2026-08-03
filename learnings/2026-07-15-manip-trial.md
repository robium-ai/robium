# Learnings — 2026-07-15/16 (manip-trial demo page build)

- [lerobot] `lerobot[viz]==0.6.0` pins `rerun-sdk>=0.24.0,<0.34.0`, which is
  unsatisfiable next to `gradio_rerun==0.34.1` (needs rerun-sdk==0.34.1).
  Exact error: `Because lerobot[viz]==0.6.0 depends on rerun-sdk>=0.24.0,<0.34.0
  … your project's requirements are unsatisfiable.` Fix that passed: drop the
  `viz` extra and pin `rerun-sdk==0.34.1` explicitly (vla-trial's pyproject
  already encodes this — the extra-less shape is why its resolve works).
  Dead-end ruled out: keeping `viz` and downgrading gradio_rerun — there is no
  gradio_rerun release for rerun <0.34 with the streaming API the demo uses.
  Verified by: `uv sync` succeeding after the change (and the demo tests later
  in the session). Candidate for the lerobot skill's platform gotchas
  (seen 1x; vla-trial hit the adjacent shape on 07-14, so effectively 2x).

- [integration] In a demo Dockerfile, `uv pip install --system -e .` — the
  `-e` is load-bearing, not style: an app whose config derives APP_ROOT from
  `config.py.__file__` (manip-trial, vla-trial both do) resolves to
  site-packages under a non-editable install, and every baked `outputs/` path
  silently misses. Caught at plan-review time by reading vla-trial's working
  Dockerfile; no failing build needed. Worth a line in the integration (or
  live-demo) skill's container patterns.

- [live-demo] CPU-only demo images built with plain `uv pip install` pull the
  default linux torch wheel with the full CUDA dependency train
  (nvidia-cudnn/cusolver/... — multi-GB) that a CPU container never uses.
  vla-trial's demo image has the same trait, so this is seen 2x. Candidate
  fix for the skill's container patterns: install torch from the
  `https://download.pytorch.org/whl/cpu` index in demo Dockerfiles. Not
  applied this session (build already green; size, not correctness).

- [environments] `pymunk` (via `lerobot[pusht]`) ships no linux/arm64 wheel —
  a python:3.12-slim image fails at `uv pip install` with
  `error: command 'gcc' failed: No such file or directory`. Fix that passed:
  `apt-get install build-essential` in the image (verified: rebuild
  completed). Dead-end ruled out: pinning older pymunk (6.x line has no
  arm64 manylinux wheels either).

- [none] Honest-numbers payoff: the checkpoint ladder came out NON-monotonic
  (5k rung from the new run evals at 0.474 avg_max_reward; the older 10k
  baseline at 0.283, seed-identical eval reproduced its 2026-07-12 number to
  6 decimals). The demo shipped the real curve with the default rung set to
  the strongest MEASURED checkpoint rather than the most-trained one. Pattern
  worth remembering for demo copy: label rungs with measured numbers, never
  imply monotonic improvement.

## End-of-block retro (manip-trial demo build, 2026-07-16)

- live-demo: fired (demo-page build matched its trigger surface), accurate
  (session-contract + readyLog + smoke-bar shape all reused verbatim from the
  vla-trial application of it), complete for v1-local scope, lean. One gap:
  no guidance on CPU-torch wheel selection for demo images (logged above).
- lerobot: fired, accurate on eval mechanics (`--eval.use_async_envs=false`
  carried straight into the runner design). Gap: the `viz`-extra/rerun-sdk
  pin conflict is undocumented (logged above, seen 2x counting vla-trial).
- environments: fired (uv-first held; MPS-native exception documented in the
  app already). Gap: no arm64-wheel/build-essential note for slim images
  (logged above).
- integration: quiet under real load except container patterns consulted via
  the vla-trial Dockerfile rather than the skill — the `-e`/APP_ROOT gotcha
  belongs somewhere durable (logged above).
- rerun: accurate; the gradio_rerun streaming pattern + fresh-recording-id
  gotcha came from vla-trial's encoded learnings and worked first try. ✓
- testing: fired (smoke-bar discipline shaped test_demo.py); no findings
  under real load.

<!-- absorbed: 2026-07-31 (skill-updater pass) —
  → lerobot 2.1.0: lerobot[viz]==0.6.0 rerun-sdk pin conflict with gradio_rerun==0.34.1 (drop viz, pin rerun-sdk==0.34.1).
  → live-demo 1.2.0: CPU demo images should install torch from the CPU index (seen 2x).
  → environments 1.5.0: arm64 slim images need build-essential for source-only wheels (pymunk via lerobot[pusht]).
  left as notes (fail 3-part bar): -e/APP_ROOT editable-install, non-monotonic checkpoint-ladder honest-numbers discipline. -->
