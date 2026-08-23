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

- [none] error (seen 2x) <!-- id: lrn-0823-12 -->
  symptom: The first verification command reported `public/articles/act-aloha-cube-transfer/live-workspace.png: No such file or directory` even though the captured image existed.
  root-cause: The command ran from the robium plugin repository while the generated public asset belongs to the sibling robium-website repository.
  fix: Run repository-owned asset checks and file-mode changes with the owning sibling repository as the working directory — check: the 168,012-byte real workspace image was found, ingested, built, and rendered on the ACT demo page; the capture script was made executable from `robium-apps` and the controller scripts from `robium-website`.
  dead-ends: Re-capturing the browser screenshot; assuming article ingestion deleted the source image; using one combined `chmod` command from the website repository for scripts split across two repositories.
  source: captured command error and successful website build, 2026-08-23

- [live-demo] verified <!-- id: lrn-0823-13 -->
  symptom: The ACT app needed proof that the website lifecycle represented a private real-policy session rather than a static iframe or UI-only health check.
  root-cause: A passing app smoke does not verify orchestrator registration, browser lifecycle state, session cleanup, or the website handoff.
  fix: Run the complete local website flow: Start a private instance, wait for real-inference READY, confirm the ACT workspace iframe loads, press Stop, and verify no container remains — check: orchestrator tests (12 passed), site smoke, build, and the browser Start/READY/Stop lifecycle all passed on 2026-08-23.
  dead-ends: Treating the choice page render as a lifecycle test; deploying before verifying local cleanup.
  source: local robium-website and demo-orchestrator verification, 2026-08-23

## Site-integration retro

- live-demo — fired: yes; accurate: yes for the private session gateway, real-inference readiness, and lifecycle smoke; complete: yes for local Start/READY/Stop and cleanup; lean: yes.
- testing — fired: yes; accurate: yes for exact route, article, media, registry, sitemap, and lifecycle assertions; complete: yes; lean: yes.

- [live-demo] figured-out-from-scratch <!-- id: lrn-0823-14 -->
  symptom: The first website smoke after adding per-demo Cloud Run resources failed because the checked-in controller registry JSON did not match its generated source.
  root-cause: Cloud resource settings were added directly to generated controller files instead of to each application's canonical `robium-app.yaml`, and the sync generator did not yet project the `cloud` block.
  fix: Store CPU, memory, CPU-idle, and startup-boost settings in each app manifest and extend `sync-demos.mjs` to copy them into the controller registry — check: sync verification, 20 controller tests, site build, and site smoke all passed from clean committed snapshots.
  dead-ends: Treating generated demo JSON as independently maintained production configuration.
  source: ACT/Navigation multi-demo controller integration, 2026-08-23

- [cloud-run] error <!-- id: lrn-0823-15 -->
  symptom: Digest lookup returned `Image not found` after a successful controller Cloud Build.
  root-cause: The lookup guessed an image name from the package directory (`demo-orchestrator`) while the Cloud Build config deliberately retained the compatibility repository name `demo-robot-navigation-control`.
  fix: Resolve the exact repository/tag declared by the submitted Cloud Build config, then deploy that immutable digest — check: digest `sha256:33b7cb1e…b73e2` deployed as zero-traffic controller revision `00004-nal`.
  dead-ends: Inferring Artifact Registry image names from local directory names.
  source: production controller build and canary deployment, 2026-08-23

- [live-demo] verified <!-- id: lrn-0823-16 -->
  symptom: A multi-demo release needed production evidence without risking the existing Navigation service or exposing policy containers to credentials.
  root-cause: Unit tests cannot establish that Cloud Run resource propagation, cold-start policy loading, private session ownership, browser embedding, terminal rollout delivery, and cleanup work together.
  fix: Deploy immutable ACT/controller/site images as no-traffic tagged revisions; run ACT seed 1001 and Navigation readiness through the controller canary; promote only after both temporary services delete; then repeat ACT Start, real-inference READY, seed-1001 transfer, and Stop through `robium.ai` — check: ACT completed at step 231, Navigation reported seven nodes and READY, foreign-session access returned 409, both services deleted, and no `robium-demo-*` services remained.
  dead-ends: Promoting after health-only checks; using a static UI render as policy readiness; rebuilding from a dirty worktree instead of committed `git archive` snapshots.
  source: production Cloud Run release, 2026-08-23

## Production-release retro

- live-demo — fired: yes; accurate: yes for the private gateway, per-demo fleet limits, lifecycle states, and tagged-canary release shape; complete: yes after adding unavailable-demo semantics and real browser acceptance; lean: yes.
- cloud-run — fired: yes; accurate: yes for immutable digests, no-traffic revisions, scale-to-zero controller/site services, and explicit traffic promotion; complete: yes for this CPU-only release; lean: yes.
- lerobot — fired: yes; accurate: yes for pinned checkpoint use, action-chunk semantics, and keeping published evaluation separate from local evidence; complete: yes; lean: yes.
- testing — fired: yes; accurate: yes for deterministic media checks, real inference readiness, API status codes, cross-demo regression, cleanup, and production acceptance; complete: yes; lean: yes.
