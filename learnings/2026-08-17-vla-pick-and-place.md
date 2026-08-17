- [none] user-correction <!-- id: lrn-0817-01 -->
  symptom: The app was initially discussed as `vla-language-learning`; the user corrected the scope to pick-and-place and selected `vla-pick-and-place`.
  root-cause: The capability name described the model family rather than the task visitors can run.
  fix: Use the task-first `vla-pick-and-place` name across the app and website — check: registry, app manifest, demo route, and page title use the same id.
  dead-ends: `vla-language-learning` was rejected because it did not name the concrete robot task.

- [huggingface] user-correction <!-- id: lrn-0817-02 -->
  symptom: The proposed workflow moved toward training before checking whether an existing Hugging Face or local checkpoint was available.
  root-cause: Checkpoint discovery was not treated as the first step when reviving an existing VLA app.
  fix: Run the existing `robium-admin/train_2026-07-15_08-09-36` checkpoint locally and defer new training — check: the demo loaded the checkpoint and the 10-episode evaluation result remained 0/10.
  dead-ends: Starting another training run before validating the existing artifact would spend money without improving the local demo path.
  anchors: huggingface#find-manipulation-dataset-lerobot-tag

- [rerun] figured-out-from-scratch <!-- id: lrn-0817-03 -->
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
