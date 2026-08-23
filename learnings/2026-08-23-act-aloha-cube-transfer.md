- [lerobot] better-method <!-- id: lrn-0823-01 -->
  symptom: The official LeRobot ACT ALOHA checkpoints contain `config.json` and weights but no processor-pipeline files, while the current eval path requires those files.
  root-cause: The checkpoints predate LeRobot 0.6's processor-pipeline format.
  fix: Current LeRobot ships `src/lerobot/processor/migrate_policy_normalization.py`, and its loader detects legacy checkpoints and emits that migration command; design the app around a pinned, verified upstream migration rather than classifying every pre-0.6 checkpoint as permanently unloadable — check: LeRobot 0.6.1 was PyPI-verified and the current `factory.py`/`pipeline.py` paths were fetched directly on 2026-08-23; execution verification remains the first implementation gate.
  dead-ends: Retraining solely to obtain processor files; generating normalization from an unrelated current dataset; assuming a model-repository config migration also created processor pipelines.
  anchors: lerobot#pre-06-checkpoints-unloadable
  source: official LeRobot model repositories, PyPI API, and current LeRobot source, 2026-08-23

- [lerobot] figured-out-from-scratch <!-- id: lrn-0823-02 -->
  symptom: The official ALOHA Insertion model card reports 20.6% success, but its current `eval_info.json` returns the same 83% aggregate values and 500-episode structure as Transfer Cube.
  root-cause: The Insertion repository appears to contain a copied or stale evaluation artifact; the repository does not provide internally consistent benchmark evidence.
  fix: Exclude Insertion from the first ACT reference app and treat the model-card number as unverified until upstream reconciles the artifact — check: both raw model cards and both raw evaluation JSON files were compared directly on 2026-08-23.
  dead-ends: Presenting Insertion as a trustworthy side-by-side checkpoint comparison; using its JSON aggregate without checking the task-specific model card.
  source: `lerobot/act_aloha_sim_transfer_cube_human` and `lerobot/act_aloha_sim_insertion_human`, 2026-08-23

- [architect] verified <!-- id: lrn-0823-03 -->
  symptom: A new ACT reference app needed a stack and donor choice that remained viable on the maintainer's Mac and in the existing hosted-demo architecture.
  root-cause: ALOHA is a bimanual MuJoCo simulation with an older checkpoint format, so choosing it from reputation alone would leave environment and compatibility assumptions implicit.
  fix: Select official ACT ALOHA Transfer Cube, bootstrap the operator/demo/test shape from `diffusion-policy-pusht`, choose native uv plus a separate CPU image, and record migration, MPS, success-semantics, seed, and CPU-latency risks in the canonical architecture brief — check: `npx robium-ai doctor --json` passed Apple MPS, Docker, disk, and uv checks; the brief was self-reviewed and committed as `f37942e`.
  dead-ends: Reusing PushT for a second policy demo; choosing Isaac Sim without a task requirement or NVIDIA host; scaffolding before checking `REGISTRY.md`.
  anchors: architect#always-produce-brief, architect#env-first-route-environments, architect#bootstrap-first-scaffold, architect#state-open-risks-explicitly
  source: approved architecture design and local preflight, 2026-08-23

## End-of-block retro

- architect — fired: yes; accurate: yes, especially bootstrap-first and explicit-risk guidance; complete: yes for selection and the architecture brief; lean: yes.
- lerobot — fired: yes; accurate: partial, it correctly identified the legacy processor incompatibility but its blanket unloadable guidance has been overtaken by the current official migration tool; complete: partial until the pinned ACT migration and rollout execute; lean: yes.
- data — fired: yes; accurate: yes, offline-first and embodiment matching led directly to the official ALOHA model/dataset pair; complete: yes for a no-training MVP; lean: yes.
- environments — fired: yes; accurate: yes, the doctor preflight confirmed native uv/MPS plus a separate CPU container as the correct split; complete: yes for design, pending measured parity; lean: yes.

- [none] user-correction <!-- id: lrn-0823-06 -->
  symptom: The implementation conversation paused for repeated plan and approval confirmations after the initial design had already been approved.
  root-cause: The workflow treated each implementation phase as a new decision gate instead of continuing within the approved scope.
  fix: Use the requested plan mode for the initial architecture decision, then when the user says start, implement and verify continuously; pause only for a real blocker or a materially different decision — check: the remaining ACT app, browser, container, docs, and registry work continued without additional approval requests.
  dead-ends: Re-showing the implementation plan; asking “go ahead?” between already approved phases.
  source: user corrections “don't do it that way; let's use plan mode” and “you don't need to ask this much frequent,” 2026-08-23

- [testing] figured-out-from-scratch <!-- id: lrn-0823-07 -->
  symptom: The first truncation test broke only the inner action-chunk loop, then the rollout immediately replanned and continued stepping a finished environment.
  root-cause: Episode termination was scoped to chunk execution rather than the outer policy-call loop.
  fix: Carry an episode-level ended flag through both loops and emit one terminal result — check: deterministic rollout/truncation tests and the real-policy smoke suite passed.
  dead-ends: Breaking only the inner loop; relying on the environment to tolerate steps after truncation.
  source: failing `uv run pytest tests/test_rollout.py tests/test_environment.py -v` followed by passing smoke, 2026-08-23

- [environments] figured-out-from-scratch <!-- id: lrn-0823-08 -->
  symptom: Creating gym-aloha from a Gradio worker crashed macOS with `NSInternalInconsistencyException: NSWindow should only be instantiated on the main thread!`.
  root-cause: MuJoCo's GLFW context inherited AppKit's main-thread constraint, while Gradio invokes callbacks from worker threads.
  fix: Create previews and rollouts in spawned child processes so each GLFW context is initialized on that process's main thread — check: preview, complete seed-1001 browser rollout, Stop path, and local gateway API all ran without the AppKit crash.
  dead-ends: Constructing the environment directly in the Gradio handler; moving only the initial preview outside the callback.
  source: local macOS browser verification, 2026-08-23

- [rerun] better-method <!-- id: lrn-0823-09 -->
  symptom: The Rerun custom component rendered a blank panel and logged a null `send_rrd` error under Gradio 6.25.
  root-cause: `gradio-rerun` 0.34.1 was incompatible with the newer Gradio custom-component runtime in this app.
  fix: Pin the donor-proven trio `gradio==6.20.0`, `gradio-rerun==0.34.1`, and `rerun-sdk==0.34.1` — check: an actual browser rollout populated camera, reward, action, and state panels with no console errors.
  dead-ends: Treating DOM presence as proof the viewer had received telemetry; upgrading Gradio independently.
  source: local browser console and rendered Rerun panels, 2026-08-23

- [environments] figured-out-from-scratch <!-- id: lrn-0823-10 -->
  symptom: `docker build` remained at zero completed steps for more than six minutes even though dependency resolution had not started.
  root-cause: The new app had no `.dockerignore`, so Docker Desktop was uploading the local `.venv`, checkpoint outputs, and test caches as build context.
  fix: Exclude local environments, outputs, run state, tests, docs, and caches from the image context — check: the rebuilt context transferred 4.1 kB and immediately entered the Dockerfile stages.
  dead-ends: Waiting for model calibration; interpreting the delay as slow ACT CPU inference.
  source: Docker Buildx history and process inspection, 2026-08-23

- [testing] verified <!-- id: lrn-0823-11 -->
  symptom: A hosted ACT image needed evidence that “ready” meant the real policy was usable, that the terminal transfer event arrived, and that no hidden runtime download was required.
  root-cause: UI availability alone can pass while model initialization or a lazy torchvision backbone fetch remains deferred until the first visitor rollout.
  fix: Make gateway readiness execute one real 100-by-14 CPU inference, bake the torchvision backbone cache, wait for the terminal result HTML in the API smoke, and reject any runtime `Downloading:` log — check: CPU container/session/API smoke completed seed 1001 with terminal transfer status and a 900 ms final inference without a lazy download.
  dead-ends: Marking ready after only an environment preview; accepting a progress event whose phase text happened to say transfer complete.
  source: `make demo-container-smoke`, 2026-08-23

## Implementation-block retro

- lerobot — fired: yes; accurate: yes after using its current official migration path; complete: yes for checkpoint loading, ACT inference, and evaluation semantics; lean: yes.
- environments — fired: yes; accurate: yes for the uv/native-MPS and separate CPU-image split; complete: partial because the GLFW worker-thread failure and missing Docker context exclusion required app-specific fixes; lean: yes.
- testing — fired: yes; accurate: yes, especially deterministic fixtures plus real-policy smoke; complete: yes after adding actual browser, terminal-event, session-guard, readiness-inference, and lazy-download checks; lean: yes.
- rerun — fired: yes; accurate: yes for additive telemetry and typed timelines; complete: partial because component compatibility required using the sibling app's proven version trio; lean: yes.
