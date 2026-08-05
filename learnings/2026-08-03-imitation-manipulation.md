# Learnings — 2026-08-03/05 (imitation-manipulation public rescope + polish)

- [live-demo] Session-blind demo pattern validated end-to-end: delete the
  per-app FastAPI session gateway (claims/409/403/timers) and make the app
  = Gradio + backend only, printing `DEMO READY` once checkpoints are
  loaded and the server is up. Per-user isolation moves entirely to the
  container boundary (orchestrator spawns one container per visitor;
  locally there is nobody to guard against). Operator-directed redesign:
  "the app should not know how many users — abstract it away." The old
  gateway contract survives only as the readiness log line, which is
  app-agnostic. Consequence to encode in the skill: the website page that
  spoke the gateway contract (`/demos/manip-trial/`) breaks and needs a
  website-side update; readiness-log + container-lifecycle is the simpler
  contract for new demos.

- [lerobot] Gradio 6.20 removed `launch(show_api=...)` — passing it raises
  `TypeError: Blocks.launch() got an unexpected keyword argument`. Caught
  by probing a minimal Blocks app before wiring the real one; the
  `/gradio_api/call/<api_name>` + SSE contract from Gradio 5 is unchanged
  in 6.20, and `launch(prevent_thread_lock=True)` works for
  serve-then-signal patterns. Seen 1x.

- [lerobot] gym-pusht's env is cleanly extensible for generalization
  demos: `PushTEnv._setup` builds the block via `self.add_tee(...)`, and
  BOTH `_get_coverage` and the goal-zone rendering derive from
  `block.shapes` — so a subclass overriding `add_tee` to install different
  convex-quad sets (L/I/Z variants of the T) gets a correctly-shaped goal
  silhouette and a meaningful coverage reward for free. Constraint: rects
  must not overlap (shapely MultiPolygon coverage math double-counts
  overlaps); edge-sharing is fine. Upstream T = bar
  `[(-60,30),(60,30),(60,0),(-60,0)]` + stem
  `[(-15,30),(-15,120),(15,120),(15,30)]` at scale 30. Candidate example
  for the lerobot skill (OOD-probe demo pattern).

- [huggingface] ACT checkpoint size reality: one `pretrained_model` dir is
  ~197 MB (fp32), so a 4-rung ladder bundle is ~794 MB, not the ~200 MB a
  50-MB-per-checkpoint guess suggests. Plan Hub-repo sizing and upload
  time accordingly. `hf upload <repo> outputs . --include ...` mirroring
  the `outputs/` subtree works as a clean artifact-distribution scheme:
  `hf download <repo> --local-dir outputs` (and the same line in the
  Dockerfile) rehydrates it identically for native and container runs.

- [testing] Rebuilt-from-scratch artifacts reproduced the July ladder's
  *story* but not its numbers: fresh 10-episode seeded evals gave 1k 0.182
  / 3k 0.239 / 5k 0.322 / 10k 0.310 avg_max_reward (July: 5k 0.474 vs 10k
  0.283). Non-monotonicity held; magnitudes didn't. Any README/UI copy
  that quotes eval numbers must be regenerated with the artifacts, never
  carried forward — the ladder.json manifest-generated-by-eval pattern
  makes the UI immune, but prose isn't.

- [live-demo] The 2026-07-15 learning "CPU demo images pull the CUDA wheel
  train — size, not correctness; not applied" escalated to a build-breaker:
  on this host the plain `uv pip install --system -e .` layer was still
  downloading nvidia-*/triton wheels at the 40-minute mark (log:
  `#10 2400.3 Downloaded triton` … `CANCELED`), long enough that every
  build attempt got killed before finishing. The fix from that learning is
  now applied and should graduate from "candidate" to standard container
  pattern: install `torch==<lock-version> torchvision==<lock-version>`
  from `https://download.pytorch.org/whl/cpu` FIRST (uv respects the
  already-satisfied requirement in the subsequent `-e .` install), then
  the project. Upgrade this in the live-demo/integration skill from
  optional size optimization to default for CPU demo images. Seen 3x
  (manip-trial July, vla-trial July, this build).

- [environments] A worktree fresh-clone has no `outputs/` (gitignored), so
  demo work that "bakes from local outputs" silently loses its inputs on
  any new machine/worktree — the Hub-artifact distribution above removes
  this whole failure class.

- [environments] (meta) An untracked learnings file written to
  ~/repos/robium/learnings/ disappeared mid-session while parallel agents
  worked in that repo — dated-and-app-suffixed files prevent content
  collisions but not workspace-level sweeps (e.g. a `git clean`). Recheck
  the file exists before ending a session.
