# When a LeRobot pipeline fails

Start at the first contract that has contrary evidence.

## A checkpoint will not load

- Inspect the repository or directory for model configuration, weights,
  `policy_preprocessor.json`, `policy_postprocessor.json`, and their statistics.
- Pre-processor-pipeline checkpoints can have valid weights but remain
  unloadable on current LeRobot. In Robium's 0.6.0 trial,
  `lerobot/diffusion_pusht` failed because the processor files were absent.
- Do not substitute a similarly named base or fine-tuned checkpoint without
  comparing processor configuration and expected features.

## Training rejects dataset features

- Compare dataset feature names and shapes with the policy's expected state,
  action, and camera inputs.
- VLA policies may require fixed camera keys. Consult the current rename-map
  and empty-camera support before adapting them.
- A rename saved into the fine-tuned checkpoint's processor should not be
  applied a second time during evaluation.

## Evaluation ends in BrokenPipe or missing environments

- Find the first worker exception rather than the parent's final pipe error.
- Robium observed shipped environments failing under the asynchronous vector
  environment default on LeRobot 0.6.0; synchronous evaluation worked. Verify
  whether that still applies to the installed release before carrying the
  workaround forward.
- Match environment observation/action shapes and control mode to the trained
  policy before changing evaluation parallelism.

## Training runs but is impractically slow

- Separate a pipeline smoke test from a viable training target. CPU and Apple
  MPS can prove that some loops start; they do not make large VLA fine-tuning
  practical.
- In the Robium VLA trial, SmolVLA on MPS advanced only about 20 of 20,000
  steps in roughly two hours. Preserve that as a measured warning, not a
  universal benchmark.
- Check data-loading time, image size, batch size, accelerator use, and policy
  memory before adding GPUs. Rescale a policy's learning-rate schedule when a
  smoke run drastically shortens its configured steps.

## A remote Job does not behave like the local command

- A 402 response means paid-compute credit is unavailable, not that the job is
  waiting.
- Robium observed the Jobs path ignoring `--policy.repo_id` and publishing to
  an auto-generated repository; read the logs for the actual destination.
- Local absolute output paths are passed into the remote container unchanged.
  In the same trial, a `/Users/...` path trained successfully and failed only
  when saving. Use a container-local path after verifying current behavior.

## Visualization or recording fails

- Resolve `lerobot` and `rerun-sdk` constraints together. Robium observed the
  LeRobot 0.6.0 `viz` extra conflicting with `gradio_rerun` 0.34.1; dropping
  that extra and pinning the required Rerun SDK resolved that application.
- Dataset visualization can save an `.rrd` or serve a remote viewer without a
  local display; do not force `spawn()` on a headless host.
- Recording controls can work in an interactive terminal while keyboard
  teleoperation still fails. Global keyboard capture needs a supported desktop
  session or macOS Accessibility permission.
- Video decode failures belong first to the installed FFmpeg/TorchCodec path,
  not the dataset schema.
