- [lerobot] figured-out-from-scratch <!-- id: lrn-0821-02 -->
  symptom: The 1k/3k/5k/10k ACT ladder reached 0% PushT success at every checkpoint; the best 10-episode average maximum normalized reward was 0.322 at 5k and regressed to 0.310 at 10k.
  root-cause: The app used ACT's ALOHA-oriented defaults (`n_obs_steps=1`, `chunk_size=100`, `n_action_steps=100`) at 10 Hz, so it could execute roughly 80% of an average episode without observing again; the longest run was also only one tenth of LeRobot's 100k default budget.
  fix: Replace the app with visual Diffusion Policy, make its PushT-specific config explicit, calibrate executed-action and inference horizons at 5k, and train/evaluate a 100k fixed-seed ladder — check: pending implementation; existing failure evidence is `outputs/demo/ladder.json` and each checkpoint's saved config.
  dead-ends: Treating more ACT steps alone as the first fix would retain the task/policy mismatch and the 100-action open-loop execution contract.
  anchors: lerobot#smoke-train-before-scale

- [testing] better-method <!-- id: lrn-0821-03 -->
  symptom: Ten seeded episodes per checkpoint produced a noisy, non-monotonic ladder and could not establish whether a policy reliably solves randomized PushT layouts.
  root-cause: The old demo optimized for a quick illustrative ladder rather than a release-quality policy benchmark.
  fix: Evaluate every retained checkpoint on the same 50 fixed T-layout seeds, select the default by success then coverage, and require at least 70% success before calling the new app stable — check: pending the Diffusion Policy training run.
  dead-ends: Selecting the latest checkpoint or highest 10-episode average coverage without a success threshold.
  anchors: testing#determinism-makes-a-test-a-test

- [none] user-correction <!-- id: lrn-0821-04 -->
  symptom: `imitation-manipulation` hid the benchmark and selected policy family, while the user wanted the app name to identify Diffusion Policy explicitly.
  root-cause: The old capability-level name remained after the application became a concrete PushT reference demo.
  fix: Rename the app id to `diffusion-policy-pusht` and use “PushT with Diffusion Policy” as its display title — check: name and direction approved in conversation; implementation pending written-spec review.
  dead-ends: `pusht-diffusion-policy`, `diffusion-pusht`, and `diffusion-manipulation` were considered but not selected.

- [environments] figured-out-from-scratch (seen 2x) <!-- id: lrn-0821-05 -->
  symptom: After the application directory was renamed, `make smoke` escaped the uv environment and used system Python 3.14; the `lerobot-train` console script could not be found even though `.venv` had moved with the app.
  root-cause: Virtualenv console-script shebangs contain the environment's absolute path, so moving an existing `.venv` leaves its executables pointing at the former application directory.
  fix: Recreate the environment in place with `uv venv --clear --python 3.12 && uv sync` after any app-directory rename — check: the same preliminary smoke command then completed a 20-step Diffusion train, two-episode eval, and both pytest assertions; the approved 200-step smoke remains the release check.
  dead-ends: Treating the moved `.venv` directory as portable, installing the missing CLI into system Python, or invoking bare `python` on this host (the executable is intentionally available only through uv).
  source: local Apple M5 app run, 2026-08-21

- [lerobot] worked-as-documented ✓ <!-- id: lrn-0821-06 -->
  symptom: The full visual Diffusion Policy recipe needed an execution check on a 16 GB Apple Silicon host before committing to a long PushT run.
  root-cause: The model has about 263 million parameters and the practical MPS memory/performance floor was not established by the prior ACT app.
  fix: Keep the task-matched full model with batch size 8: a preliminary 20-step train and two seeded eval episodes passed, and the 5k run reached roughly 2 steps/s after warm-up on an Apple M5 — check: the probe reported `2 passed in 120.88s`; the saved checkpoint contains config, model, and both processor files. The approved 200-step smoke remains pending.
  dead-ends: Pre-emptively shrinking the vision backbone or network before measuring the real MPS recipe.
  source: LeRobot 0.6.0 local MPS run, 2026-08-21

- [live-demo] figured-out-from-scratch <!-- id: lrn-0821-07 -->
  symptom: The first Gradio 6 browser render kept white radio cards, inputs, and image-panel regions inside an otherwise dark navigation-themed shell; passing `theme` and `css` to `gr.Blocks` also emitted a Gradio 6 deprecation warning.
  root-cause: Gradio 6 moved `theme`/`css` to `launch()`, and its Base theme still supplied light component variables such as `--checkbox-label-background-fill: #e4e4e7` even when outer containers were dark.
  fix: Pass theme/CSS at launch and explicitly override the block/input/checkbox/button design variables on `.gradio-container` — check: real in-app-browser screenshots showed dark cards, teal selected outlines, readable controls, direct RGB observation, chart, and evidence table at 1280 px.
  dead-ends: Styling only `body`, `.gradio-container`, and the app's outer panels; those rules do not change Gradio's internal theme variables.
  source: local Gradio 6.20.0 render inspection, 2026-08-21

- [environments] figured-out-from-scratch <!-- id: lrn-0821-08 -->
  symptom: The uninterrupted portions of the 5k MPS run sustained about 2 steps/s, but the progress clock jumped forward by roughly 17, 10, and 4 minutes while no training steps completed; the run still saved normally at 1:22:26 wall time.
  root-cause: The macOS host suspended or descheduled the long-running process while unattended; the optimizer and MPS execution were healthy before and after every gap.
  fix: Report active-compute and wall-clock timings separately, and keep the Mac awake for long local policy work; for an already-running process, attach `caffeinate -w <pid>` so the assertion ends with that process — check: 5k completed with final loss 0.034 and gradient norm 0.489; about 50 minutes of active compute implies roughly 1.7 steps/s average and a 16–17-hour uninterrupted 100k build. The later 50-seed evaluator reached only 14 saved seeds in 8h45 wall time before `caffeinate -w 99250` was attached.
  dead-ends: Attributing the gaps to thermal throttling or optimizer instability; throughput immediately returned to about 2 steps/s and no NaNs or abnormal gradients appeared.
  source: local Apple M5 LeRobot Diffusion run, 2026-08-21

- [environments] figured-out-from-scratch <!-- id: lrn-0821-09 -->
  symptom: Every evaluation process on macOS warns that AVFFrameReceiver/AVFAudioReceiver are implemented by both OpenCV's and PyAV's bundled FFmpeg libraries, and SDL classes are implemented by both OpenCV and Pygame.
  root-cause: The LeRobot/PushT demo environment loads wheels that bundle overlapping Objective-C AVFoundation and SDL implementations in one process.
  fix: Treat the messages as a known warning while seeded headless rollouts remain stable, but keep rollout and video smoke tests as the check for actual casting/crash regressions — check: direct CPU rollouts and the MPS calibration process continued successfully after the warnings.
  dead-ends: Removing or renaming wheel-bundled dylibs ad hoc; that would make the uv environment non-reproducible and can break video or simulator dependencies.
  source: local macOS arm64 evaluation process, 2026-08-21

- [testing] better-method <!-- id: lrn-0821-10 -->
  symptom: A 300-step PushT rollout with 8 executed actions and 100 diffusion inference steps averaged 145.6 seconds on the Apple M5 versus 11.9 seconds at 10 inference steps, making the six-candidate, ten-seed calibration sweep long and interruption-sensitive; host sleep gaps made provisional wall-clock estimates even noisier.
  root-cause: The slowest candidate replans about 38 times per episode and performs 100 denoising iterations per replan; the original evaluator wrote calibration JSON only after all 60 episodes completed.
  fix: Persist metrics and episode records after every seed, reuse completed candidates, verify that resumed seed records are an exact prefix of the configured set, reject partial calibration files in benchmark evaluation, and compare the rollout-recorded `elapsed_s` field rather than outer wall time — check: the full pre-change compatibility sweep completed all 60 episodes and selected 8 actions / 100 denoising steps by raw coverage; source compilation and diff checks pass.
  dead-ends: Dropping the agreed 100-step candidate mid-run, selecting by training loss, or treating an incomplete calibration file as sufficient to resume training.
  source: local 5k Diffusion checkpoint calibration, 2026-08-21

- [lerobot] figured-out-from-scratch <!-- id: lrn-0822-01 -->
  symptom: The official `lerobot/diffusion_pusht` 175k repository contains `model.safetensors` and `config.json` but not the `policy_preprocessor.json` / `policy_postprocessor.json` files required by LeRobot 0.6; direct loading is therefore incomplete, and converted loading reports legacy normalization buffers as unexpected model keys.
  root-cause: The published checkpoint predates LeRobot's processor split: normalization statistics were stored as model buffers, while the current runtime owns normalization in standalone processors.
  fix: Pin revision `84a7c23178445c6bbf7e1a884ff497017910f653`, transplant the checkpoint's embedded image/state/action buffers into current processors, preserve the original weights, and write a provenance sidecar — check: processor tensors match the legacy model tensor-for-tensor and a 100-denoise MPS rollout solved official seed 1000 at 0.955 raw coverage in 231 steps.
  dead-ends: Loading the Hub repo directly under LeRobot 0.6 without processors; treating the legacy buffer warnings as corrupted weights; using current `lerobot/pusht` image statistics, which are about `[0.972, 0.981, 0.977]` rather than the checkpoint's ImageNet mean `[0.485, 0.456, 0.406]`; retraining only to obtain a current checkpoint layout.
  anchors: lerobot#load-evaluate-a-pretrained-policy
  source: official Hub revision and local LeRobot 0.6 MPS smoke, 2026-08-22

- [testing] user-correction <!-- id: lrn-0822-02 -->
  symptom: The locally trained 5k checkpoint's sequential 50-seed macOS benchmark remained expensive and was stopped at 30/50 episodes after the user said the workflow was taking too long; it had 1 success and 0.376 average maximum raw coverage at interruption.
  root-cause: Reproducing long evaluation evidence locally was being treated as a prerequisite for a demonstration even though a task-matched official checkpoint already publishes a 500-episode evaluation.
  fix: Make the pinned official 175k policy and its attributed 500-episode result the primary reference, use a single full rollout as the local platform smoke, and preserve the 5k result only as explicitly incomplete, separate evidence — check: `make smoke` passed 2/2 and `make demo-smoke` passed 3/3 on macOS without training or completing the local benchmark.
  dead-ends: Continuing the interrupted benchmark, moving training to RunPod before checking for a published model, or plotting the unlike local and official runs as one learning curve.
  anchors: testing#policy-evaluation
  source: user correction and local pass-bar runs, 2026-08-22

- [live-demo] verified <!-- id: lrn-0822-03 -->
  symptom: The official-checkpoint pivot needed proof that the browser app still streamed visible policy frames and remained controllable on native MPS.
  root-cause: Replacing the evidence schema and adding inference mode changed the Gradio API from three to four inputs and could have broken the existing demo contract.
  fix: Exercise the launched application through its public API with official fast-mode T and L rollouts, verify a direct non-flat 96×96 RGB frame, deterministic Z preview, cooperative cancellation, and lock release — check: `make demo-smoke` passed 3/3 in 43.11 seconds.
  dead-ends: Treating UI construction or a prerecorded replay as sufficient proof of an interactive live policy.
  source: local Gradio 6 / MPS demo smoke, 2026-08-22

- [live-demo] user-correction <!-- id: lrn-0822-04 -->
  symptom: The direct `gr.Image` policy view visibly faded out and back in as each streamed rollout frame replaced the previous Gradio file URL, making continuous motion look like display instability.
  root-cause: Gradio applies frontend transition/animation behavior to output-image updates; a generator-driven simulator stream needs immediate, continuously opaque replacement instead.
  fix: The initial scoped CSS suppression appeared to keep one image at opacity one, but the check did not test `complete` / `naturalWidth`; the user then observed a black viewer, proving the fix incomplete.
  dead-ends: Treating the fade as Diffusion Policy denoising, simulator rendering, or image content; suppressing Gradio's full descendant animation lifecycle.
  source: user screenshot and local Gradio browser probe, 2026-08-22

- [live-demo] user-correction <!-- id: lrn-0822-05 -->
  symptom: After the CSS-only crossfade fix, the live surface could remain black even though an `<img>` element existed and computed opacity was one.
  root-cause: Ordinary `gr.Image` updates replace temporary file URLs, and even Gradio's documented `streaming=True` output path briefly cleared or unloaded the image: a browser probe found 11 unloaded samples during 22 replacements. Element presence and opacity alone were insufficient acceptance checks.
  fix: Replace the output component with a stable `gr.HTML` surface whose complete 96×96 PNG is embedded as an inline data URL on every update; update the API smoke to decode and validate the inline PNG — check: 27 real frame changes produced one image continuously, zero missing samples, zero unloaded samples, and correct inline data URLs; all 5 policy/demo tests passed.
  dead-ends: CSS-only opacity/animation suppression; `gr.Image(streaming=True)`, which still exposed empty/unloaded replacement windows in Gradio 6.20.
  source: user correction, local Gradio source inspection, and browser rollout probes, 2026-08-22

- [lerobot] user-correction <!-- id: lrn-0822-06 -->
  symptom: The user reported that the official 175k policy still performed poorly at 100 denoising steps even though the published policy reports 65.4% success.
  root-cause: The compatibility converter incorrectly generated processors from current dataset image statistics while the legacy checkpoint's embedded buffers specify ImageNet normalization; the current runtime ignored those legacy model keys after loading them as unexpected. The custom T builder also produced moment of inertia 7875 versus upstream gym-pusht's historical 3000.
  fix: Build current processors from the embedded legacy buffers and route benchmark T to untouched `gym_pusht/PushT-v0`; reserve the generalized builder for L/I/Z — check: exact tensor assertions and inertia assertions pass, and the corrected 100-denoise MPS seed-1000 rollout succeeded at 0.955 raw coverage / 1.0 normalized reward in 164 seconds.
  dead-ends: Increasing denoising beyond the checkpoint's trained 100-step diffusion schedule; assuming identical visible T geometry implies identical dynamics; treating unexpected legacy normalization keys as harmless without relocating their values.
  anchors: lerobot#load-evaluate-a-pretrained-policy
  source: checkpoint tensors, upstream gym-pusht source, user correction, and local MPS reference rollout, 2026-08-22

- [testing] figured-out-from-scratch <!-- id: lrn-0822-07 -->
  symptom: The demo chart called official `avg_max_reward` and local raw `avg_max_coverage` the same “avg max overlap,” and initial schema-v4 smoke failed because `EpisodeRunner` still required schema 3.
  root-cause: gym-pusht normalizes coverage by the 0.95 success threshold before exposing reward, so published average max reward and local raw coverage are different quantities; the manifest consumer's schema guard was not advanced with its producer.
  fix: Chart only the comparable success rate, show normalized reward and raw coverage in separate table/status fields, use the official 1000–1499 seed range by default, and advance producer/consumer together — check: the first `make demo-smoke` exposed the stale schema guard; after correction `make smoke` passed 2/2 and `make demo-smoke` passed 3/3.
  dead-ends: Comparing the two values as one metric; claiming per-seed bit parity between published CUDA batch evaluation and sequential MPS stochastic inference.
  anchors: testing#policy-evaluation
  source: official eval_info, gym-pusht reward source, failed and passing local smoke runs, 2026-08-22

- [environments] better-method (seen 3x) <!-- id: lrn-0822-08 -->
  symptom: The first CPU demo-image build stalled while resolving the pinned `ghcr.io/astral-sh/uv:0.8.14` helper stage with `DeadlineExceeded: context deadline exceeded`; a later builder run selected CUDA wheels; and the first multi-stage checkpoint conversion failed with `ImportError: libxcb.so.1: cannot open shared object file`.
  root-cause: A second container registry added an avoidable availability dependency, transitive torch resolution was not constrained to CPU on Linux, and the disposable builder needed the same OpenCV runtime libraries as the final image because it executes checkpoint conversion during the build.
  fix: Bootstrap the exact local uv version from PyPI in the builder, use a Linux-only explicit PyTorch CPU index for direct torch pins, install the OpenCV runtime libraries in both stages, and copy only the environment/checkpoint/application into the runtime image — check: the lock removed 18 NVIDIA/CUDA packages, the multi-stage image built with `torch==2.11.0+cpu` at 1,916,474,512 bytes, and `make demo-container-smoke` solved seed 1000 in 116 steps at 0.953 raw coverage.
  dead-ends: Retrying an extra registry indefinitely; leaving torch as an unconstrained transitive dependency; using an unpinned `pip install uv`; installing application dependencies into system Python; assuming build-time Python never imports OpenCV.
  anchors: environments#docker-is-for-reproducibility-not-as-a-default
  source: local Docker Desktop arm64 build, 2026-08-22

- [live-demo] verified <!-- id: lrn-0822-09 -->
  symptom: Moving the Gradio app behind a session gateway could have changed API paths, delayed status until model load, or broken real rollouts.
  root-cause: Hosted demos need a lifecycle control plane in addition to the native single-process Gradio entry point.
  fix: Mount Gradio at `/ui`, expose the established start/status/shutdown contract, load the real policy on a background thread, and keep native `make demo` unchanged — check: `make demo-smoke` passed 3/3 in 53.13 seconds with a real T rollout, an OOD rollout, 409/403 foreign-session guards, non-flat inline RGB frames, and cooperative cancellation.
  dead-ends: Sharing one unclaimed Gradio process among visitors; treating a constructed UI or prerecorded video as a hosted-demo smoke.
  source: local FastAPI + Gradio 6.20 gateway smoke, 2026-08-22

- [live-demo] verified <!-- id: lrn-0822-10 -->
  symptom: The new website path needed proof that lifecycle status, iframe readiness, the radio-state fix, real inference, and teardown worked together rather than only in isolated app tests.
  root-cause: Static site builds and gateway API checks cannot catch a mismatched orchestrator ID, missing local image, iframe path error, invisible selected state, or stale container after Stop.
  fix: Exercise the full local website path in the in-app browser through the real local Docker orchestrator — check: Start advanced IDLE → BOOTING → READY, `/ui` showed a non-black inline 96×96 observation and filled selected dots for policy/inference/shape, keyboard activation completed a solved rollout, and Stop deleted the container and returned the page to IDLE; website smoke and 11 orchestrator tests also passed.
  dead-ends: Treating Astro build output, a direct gateway URL, or screenshot-only inspection as lifecycle acceptance.
  source: local Astro + orchestrator + Docker + in-app-browser run, 2026-08-22

- [live-demo] user-correction <!-- id: lrn-0822-11 -->
  symptom: The full-screen PushT live workspace showed a large blank band above its 62px control bar even though the bar's own spacing matched Robot Navigation.
  root-cause: The workspace root is a `<section>`, so the site's global `section { padding: 60px 0; }` leaked into it; Robot Navigation already reset this inherited page-section spacing with `padding: 0`, while the PushT workspace omitted that declaration.
  fix: Reset `.dpp-workspace` to `padding: 0` and pin the reset in the website smoke test — check: the full Astro build and website smoke passed; browser geometry measured workspace top 0px, padding top 0px, and bar top 0px with the intended 62px bar height.
  dead-ends: Tuning `.dpp-bar` height or padding; the extra space belonged to its parent section.
  source: user screenshot and CSS cascade inspection, 2026-08-22

## End-of-block retro

- environments — fired: yes; accurate: yes, the preflight confirmed macOS arm64 + MPS and reinforced native uv for training because Docker cannot expose MPS; complete: yes for this design; lean: yes.
- lerobot — fired: yes; accurate: partial, its general smoke-first guidance was useful but the existing ACT-first default produced a poor task-specific baseline; live upstream/local config inspection was still required to select and pin the Diffusion recipe; complete: partial until the MPS training run measures memory and speed; lean: yes.
- rerun — fired: yes; accurate: partial, the documented Gradio streaming pattern does not protect against a visually black embedded canvas observed in the sibling app; the design therefore makes direct RGB frames primary and Rerun additive; complete: no for browser-visible acceptance; lean: yes.
- testing — fired: yes; accurate: yes, especially the separation between a pipeline smoke and a known-good regression threshold; complete: yes for the design; lean: yes.
- live-demo — fired: yes; accurate: yes for demo lifecycle and honest readiness, with the non-ROS Gradio/FastAPI path relevant here; complete: yes for local design, while hosting remains deliberately out of scope; lean: yes.
- environments (official-checkpoint pivot) — fired: yes; accurate: yes, native uv + MPS ran the published model without a server; complete: yes for local use; lean: yes.
- lerobot (official-checkpoint pivot) — fired: yes; accurate: yes, including its warning that older Hub checkpoints may lack current processor files; complete: partial because the exact legacy-to-0.6 conversion still required source inspection and an execution check; lean: yes.
- testing (official-checkpoint pivot) — fired: yes; accurate: yes, the full policy episode and launched-app API checks gave proportional evidence without another long benchmark; complete: yes; lean: yes.
- live-demo (official-checkpoint pivot) — fired: yes; accurate: yes, the direct frame plus additive Rerun pattern survived the model/evidence change; complete: yes for local demo QA; lean: yes.
- live-demo (frame transition fix) — fired: yes; accurate: partial, direct RGB remained the right primary surface but neither the skill nor the first browser check anticipated Gradio's unloaded replacement window; complete: yes after validating image load state and inline frame payloads; lean: yes.
- lerobot (checkpoint parity correction) — fired: yes; accurate: partial, it correctly routed pretrained evaluation but did not surface that a legacy model's normalization buffers must be migrated rather than regenerated from current dataset metadata; complete: yes after checkpoint/upstream source inspection and a successful reference rollout; lean: yes.
- testing (checkpoint parity correction) — fired: yes; accurate: yes, exact contract assertions caught normalization and dynamics drift while the full MPS rollout supplied proportional behavior evidence; complete: yes; lean: yes.
- environments (hosted demo) — fired: yes; accurate: yes on the uv-first native path and Docker parity requirement; complete: partial because transitive PyTorch initially selected large CUDA wheels until the official uv platform-index pattern was applied to direct pins; lean: yes.
- integration (hosted demo) — fired: yes; accurate: yes, one gateway process and one mounted UI kept the module boundary small; complete: yes for local lifecycle; lean: yes.
- cloud-run (hosted demo) — fired: yes; accurate: yes, the implementation preserved per-visitor lifecycle and deferred CPU sizing, immutable image publication, IAM, and production mutation; complete: yes for the authorized local scope; lean: yes.
- live-demo (hosted demo) — fired: yes; accurate: yes, the start/status/stop contract and browser acceptance bar directly covered the failure modes encountered; complete: yes; lean: yes.
- testing (hosted demo) — fired: yes; accurate: yes, the five-test app bar, container smoke, orchestrator suite, website smoke, and browser lifecycle gave proportional layered evidence; complete: yes; lean: yes.
