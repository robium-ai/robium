- [none] user-correction <!-- id: lrn-0817-22 -->
  symptom: The app was initially discussed as `vla-language-learning`; the user corrected the scope to pick-and-place and selected `vla-pick-and-place`.
  root-cause: The capability name described the model family rather than the task visitors can run.
  fix: Use the task-first `vla-pick-and-place` name across the app and website — check: registry, app manifest, demo route, and page title use the same id.
  dead-ends: `vla-language-learning` was rejected because it did not name the concrete robot task.

- [huggingface] user-correction <!-- id: lrn-0817-23 -->
  symptom: The proposed workflow moved toward training before checking whether an existing Hugging Face or local checkpoint was available.
  root-cause: Checkpoint discovery was not treated as the first step when reviving an existing VLA app.
  fix: Run the existing `robium-admin/train_2026-07-15_08-09-36` checkpoint locally and defer new training — check: the demo loaded the checkpoint and the 10-episode evaluation result remained 0/10.
  dead-ends: Starting another training run before validating the existing artifact would spend money without improving the local demo path.
  anchors: huggingface#find-manipulation-dataset-lerobot-tag

- [rerun] figured-out-from-scratch <!-- id: lrn-0817-24 -->
  symptom: The embedded viewer opened on Rerun's empty welcome screen; passing initial recording bytes with `streaming=True` then failed in the browser with `Failed to open recording` and a JavaScript `TypeError` involving `length`.
  root-cause: `gradio_rerun` accepts streamed bytes for generator updates, but the component's initial value needs a supported static recording value; the unit-level non-empty-bytes check did not exercise the browser transport.
  fix: Save one real MuJoCo reset frame to a cached `.rrd` Path for the initial value, while keeping byte chunks for live episode updates — check: browser showed scene and wrist cameras before Run, then transitioned to the streamed oracle episode and reported `Cube placed in the bin`.
  dead-ends: A raw bytes initial value passed the Python test but failed in the embedded web viewer.
  anchors: rerun#gradio-rerun-embed

- [testing] better-method <!-- id: lrn-0817-04 -->
  symptom: The isolated UI regression test passed with a non-empty recording value even though the embedded viewer could not open it.
  root-cause: The Python type/content assertion did not cover the Gradio-to-Rerun browser boundary.
  fix: Pair the focused regression with a real browser load and controller run — check: initial cameras rendered, the timeline updated, and the oracle finished successfully.
  dead-ends: Treating the component's Python return value as sufficient integration coverage.
  anchors: testing#test-at-right-layer-not-everything-in-sim

- [testing] figured-out-from-scratch <!-- id: lrn-0817-05 -->
  symptom: `make smoke` treated the missing absolute local checkpoint path as a Hub repo id and failed with `Repo id must be in the form 'repo_name' or 'namespace/repo_name'`.
  root-cause: The documented pipe-test pass bar depends on `make train-smoke`; the generated checkpoint had not been recreated in this checkout.
  fix: Run `make train-smoke` before `make smoke` as documented in the app README — check: the generated `checkpoints/000005/pretrained_model` exists and the eval smoke completes against it.
  dead-ends: Retrying `make smoke` cannot create its prerequisite and sends the missing path into Hub resolution.
  anchors: testing#confirm-smoke-passes-before-done

- [testing] better-method <!-- id: lrn-0817-06 -->
  symptom: The gateway smoke completed the oracle episode, but failed because it asserted the presentation marker `✅` after the UI copy was simplified.
  root-cause: The test used an emoji as the success contract instead of the task outcome rendered by the status bar.
  fix: Assert `Cube placed in the bin`, the stable completion message shared by the UI and gateway stream — check: all five `make demo-smoke` checks pass.
  dead-ends: Restoring the emoji would couple functional acceptance to decorative copy again.
  anchors: testing#test-at-right-layer-not-everything-in-sim

## End-of-block retro

- rerun — fired: yes; accurate: yes for recording streams, blueprints, and the embedded viewer; complete: partial because the difference between an initial static `.rrd` value and streamed byte updates required browser-level discovery; lean: yes.
- testing — fired: yes; accurate: yes for focused regression tests plus the app's full smoke bars; complete: improved by adding browser acceptance for the Gradio/Rerun boundary; lean: yes.

## SO101-Nexus migration block

- [data] figured-out-from-scratch <!-- id: lrn-0817-07 -->
  symptom: Two published LeRobot datasets for `MuJoCoPickAndPlace-v1` both passed every schema check — same 6-dim state/action, same two 480x640 cameras, same task string — but one was recorded in a completely different scene (wood ground, orange robot, angled side view instead of top-down overhead).
  root-cause: A LeRobot dataset carries no record of the scene configuration it was collected in, so feature shapes and camera counts cannot distinguish "same environment" from "same environment class".
  fix: Split dataset verification into a schema check and a SCENE check that compares a real dataset frame's mean per-channel colour against a freshly rendered frame from the pinned env — check: `./app dataset-check` scores the matching dataset 0.0023 and rejects the other by name.
  dead-ends: Trusting the dataset card, which described "overhead + wrist" for cameras literally named `cam0`/`cam1` that do not match either view.
  anchors: data#verify-dataset-matches-environment

- [data] figured-out-from-scratch <!-- id: lrn-0817-08 -->
  symptom: A scene-appearance check comparing BOTH cameras failed on the correct dataset (wrist distance 0.108 against a 0.10 tolerance) while the overhead camera matched at 0.002.
  root-cause: The wrist camera is mounted on the arm AND so101-nexus randomizes its FOV, pitch and mount offset per reset by design, so two frames of the same scene differ by however far the arm has moved.
  fix: Run scene-identity checks against a STATIC camera only, recorded per dataset as `scene_reference_camera` — check: tolerance tightened from 0.10 to 0.05 with the match still 20x inside it.
  dead-ends: Loosening the tolerance to admit the wrist camera, which would have admitted the mismatched dataset too.

- [lerobot] figured-out-from-scratch <!-- id: lrn-0817-09 -->
  symptom: Dataset `action`/`observation.state` rows read as values like -88.7 and +39.2 while the env action space is bounded at +/-2.74 radians.
  root-cause: LeRobot records body joints in DEGREES and the gripper as RANGE_0_100 percent of jaw travel; the six-vector MIXES units, so a whole-vector `np.deg2rad` silently corrupts the gripper channel.
  fix: Route every conversion through so101-nexus's published `dataset_row_to_sim_qpos`, and show recorded numbers in the dataset's own units with a visible `units` label rather than converting behind the viewer's back — check: `test_dataset_rows_are_not_simulator_units` asserts the difference in both directions.
  dead-ends: Assuming a shared 6-vector shape implies a shared unit convention.

- [lerobot] wrong-guidance <!-- id: lrn-0817-10 -->
  symptom: Trimming `lerobot[smolvla,training]` to bare `lerobot` for an app that runs no policy broke all seven dataset tests with image-decode errors.
  root-cause: `torchcodec` — required to decode any dataset with video frames — ships only under the `dataset` extra, whose name reads optional.
  fix: Depend on `lerobot[dataset]==0.6.0`; it is the minimum for reading a video-backed LeRobot dataset — check: 49/49 pass, and the venv drops transformers/wandb/twine.
  dead-ends: Bare `lerobot`, which resolves and imports fine and fails only at the first frame read.

- [mujoco] noise <!-- id: lrn-0817-11 -->
  symptom: Slider updates from a reset pose were rejected client-side with "Value -0.17454060912132263 is less than minimum value -0.17453".
  root-cause: `robot_init_qpos_noise` means a reset joint POSITION can settle marginally outside the actuator CONTROL range; joint position and control range are different bounds.
  fix: Clamp any joint vector before binding it to a bounded widget, and clamp to the WIDGET's bounds when those are rounded inward from the true range — check: `test_reset_state_is_clamped_into_the_slider_range`.
  dead-ends: Clamping to the true actuator range, which is still outside a slider bound rounded inward for display.

- [rerun] verified <!-- id: lrn-0817-12 -->
  symptom: The embedded `gradio_rerun` viewer rendered a pure black canvas through both an initial `.rrd` Path value and a `blocks.load` byte stream — reversing lrn-0817-24, which had reported the Path approach working.
  root-cause: Not determined. Everything measurable is healthy: the bytes are a valid RRF2 stream (85 KB with real image data, readable off disk), Gradio's media-stream chunks are fetched with 200s, the component logs "Rerun viewer ready" and "Adding new log receiver", wgpu initialises, the canvas is correctly sized, and no error reaches the console.
  fix: Render camera frames directly in-page with `gr.Image` plus an HTML joint/reward/success readout, and keep Rerun as the OFFLINE surface where it demonstrably works (`./app sim` / `./app play` write .rrd files that open in the desktop viewer) — check: browser shows both cameras and live numbers for manual control and dataset playback; `make demo-smoke` asserts returned frames are neither black nor flat.
  dead-ends: The `.rrd` Path initial value (postprocesses to a FileData path the frontend cannot fetch under `streaming=True`); a `blocks.load` byte stream through the working chunk transport.
  anchors: rerun#gradio-rerun-embed

- [testing] better-method <!-- id: lrn-0817-13 -->
  symptom: The previous gateway smoke asserted HTTP 200s and a status string, and passed against a build whose main viewer displayed nothing at all.
  root-cause: Status codes and copy do not cover "did a picture arrive"; the visual surface had no assertion at any layer.
  fix: Fetch the returned camera payloads in the smoke test and assert `mean > 20` and `std > 5` (not black, not a flat fill), and assert the source label names a dataset rather than a policy — check: `make demo-smoke`, 7 passed, from a clean checkout.
  dead-ends: Trusting a passing endpoint test as evidence the page works.
  anchors: testing#test-at-right-layer-not-everything-in-sim

- [none] figured-out-from-scratch <!-- id: lrn-0817-14 -->
  symptom: Whole control panels rendered at full size, reported `visibility: visible`, and were nowhere on screen; the rail's `overflow-y: auto` never engaged.
  root-cause: Gradio's `.row`/`.column` classes carry `flex-wrap: wrap`, and every container in the workspace shell is one. In a column-direction flex box an over-tall child starts a NEW COLUMN to the right, past the viewport — silently, and differently per viewport.
  fix: Force `flex-wrap: nowrap` on every container in `dashboard.css`, with a per-selector test asserting it — check: `test_no_workspace_container_may_wrap`, and the rail scrolls as designed.
  dead-ends: Suspecting the extra `gr.Column` mode wrappers; removing them changed nothing because the wrap was the cause, not the nesting. A shell with few enough short sections fits in one column and hides the bug entirely.

- [environments] better-method <!-- id: lrn-0817-15 -->
  symptom: A warm dev machine cannot show whether first-run setup works — the app had previously shipped with a fetch step no fresh clone exercised.
  root-cause: Cached venv and cached HF assets make "it works here" independent of the setup path.
  fix: Verify from an rsync'd clean copy with an EMPTY `HF_HOME`, running doctor/build/contract/dataset-check/test/demo-smoke/sim/play — check: all green cold, including the first pinned-revision Hub pull.
  dead-ends: Running the suite in the working tree only.

## End-of-block retro (SO101-Nexus migration)

- data — fired: yes; accurate: partial, the guidance covers sourcing but not verifying a dataset was recorded in YOUR environment; complete: no — schema-vs-scene verification and static-camera-only comparison are new; lean: yes.
- lerobot — fired: yes; accurate: yes; complete: no — the mixed-unit row convention and the `[dataset]`/torchcodec trap both cost real time; lean: yes.
- rerun — fired: yes; accurate: partial, lrn-0817-24's fix did not reproduce; complete: no — the embedded-viewer path needs a documented "when to give up and render frames directly"; lean: yes.
- testing — fired: yes; accurate: yes; complete: improved by asserting on returned pixels rather than status codes; lean: yes.

## Scripted-expert block (own training data on the stock scene)

- [data] figured-out-from-scratch <!-- id: lrn-0817-16 -->
  symptom: A Hub-wide survey found NO dataset recorded in the stock `MuJoCoPickAndPlace-v1` scene larger than 10 episodes, and no trained policy for it from anyone — while three large datasets exist for *neighbouring* scenes (different ground/robot, or a two-disc subclass).
  root-cause: Simulator environments fork trivially. Everyone who trains on one customises the scene, and nothing in a LeRobot dataset records which scene it was.
  fix: Generate demonstrations in the app's own pinned environment with a scripted expert, and keep only episodes upstream scores successful — check: `./app record` writes a LeRobot dataset whose actions replay to `success` in the demo's own control mode.
  dead-ends: Adopting `zwan1003`'s fork (needs so101-nexus 0.3.12 split packages + LeRobot 0.4.4 + hardened contacts); their published env script reproduced frames 0.104 from their own training data, further than their data is from ours.

- [mujoco] figured-out-from-scratch <!-- id: lrn-0817-17 -->
  symptom: A scripted pick-and-place expert scored 13% (4/30), with the grasp forming ~60% of the time and then slipping during the carry. Parameter sweeps over gripper angle, carry speed and motion easing all stayed under 25%.
  root-cause: The TCP site is not the fingertip. Measured from MuJoCo contact positions between the cube geom and the gripper bodies, the jaws pinch ~9 mm BELOW the TCP site (std 2.6 mm across seeds), so commanding the TCP at cube-centre height puts the pinch above the cube and the grasp is marginal by construction.
  fix: Command the TCP low — `GRASP_Z` 0.006 m above cube centre — measured grasp-then-lift survival 0.006 -> 100%, 0.009 -> 83%, 0.012 -> 33%, 0.016 -> 0% over 12 seeds; end-to-end 13% -> 79/100 — check: `./app expert 100`.
  dead-ends: Sweeping grip angle (best 25%), slowing the carry (WORSE — see next entry), easing the interpolation, and aligning gripper yaw to cube yaw. All were tuning around a 6 mm aiming error.
  anchors: mujoco#grasp-calibration

- [mujoco] figured-out-from-scratch <!-- id: lrn-0817-18 -->
  symptom: Carrying the cube MORE slowly made the grasp fail more often, not less: at gripper target -0.174 rad, n_carry=120 scored 0/12 against 3/12 at n_carry=50.
  root-cause: A position-controlled gripper commanded fully closed keeps pressing; on a 25 mm cube it extrudes it. More carry steps = more time under the press. "Slower is safer" is a manipulator intuition that inverts for position-controlled jaws on a compliant contact.
  fix: Command a HOLD, not a crush — gripper target 0.0 rad rather than the actuator minimum — check: no speed/grip interaction left once GRASP_Z was corrected.
  dead-ends: Reading the slowdown as insufficient grip and squeezing harder.

- [mujoco] better-method <!-- id: lrn-0817-19 -->
  symptom: Writing a scripted expert threatened to re-introduce the IK solver, grasp calibration and success predicate the migration had just deleted.
  root-cause: Treating "scripted controller" as necessarily app-owned.
  fix: Build the env in so101-nexus's `pd_ee_pose` control mode so an action IS a TCP pose and UPSTREAM solves the IK; record `data.ctrl[actuator_ids]` (the joint targets the env derived) as the dataset action so the data stays on the app's `pd_joint_pos` contract — check: recorded actions replayed in `pd_joint_pos` reproduce success; the expert module inverts no Jacobian and defines no success predicate.
  dead-ends: Replicating `_solve_ee_ik`'s loop locally with upstream's `ee_ik_delta_q`; recording TCP poses as actions (would have changed the app's declared action contract).
  anchors: mujoco#let-the-env-own-the-ik

## End-of-block retro (scripted expert)

- data — fired: yes; accurate: yes; complete: no — "no published dataset matches your scene, generate your own" is the common case in sim and is not covered; lean: yes.
- mujoco — fired: yes; accurate: partial; complete: no — the TCP-site-is-not-the-fingertip trap and the position-controlled-gripper extrusion effect are both recurring and both cost the majority of the debugging here; lean: yes.
