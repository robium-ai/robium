# When Isaac Lab fails

Start below the policy: runtime, task registration, environment, training, then
artifact.

## Isaac Lab does not import or start

- Verify the Isaac Sim/Lab compatibility pair and how both were installed.
- On cloud hosts, prefer a matched prebuilt image before layering source
  installs into an unknown runtime.
- Confirm the Isaac Sim hardware and driver gate independently.

## The task cannot be found

- List the installed registry and compare the exact task entry point. Task IDs
  and script directories move across releases.
- In a pip-installed/prebuilt environment, make a custom task an external
  project that registers itself. Robium observed the internal-task route being
  disabled there because it is meant for upstream development.

## Training exits cleanly but the checkpoint seems missing

- Inspect the training library's experiment name and resolved configuration.
  Robium's Go2 RSL-RL run wrote under `unitree_go2_flat`, not the full task ID.
- Confirm save interval and output mount before rerunning paid compute.
- On the prebuilt image, a persistent volume mounted at `/workspace` can hide
  the bundled application. Robium used a non-overlapping path such as `/data`.

## Training is slow or unstable

- Reduce environments and iterations until resets and metrics are observable.
- Separate data loading, physics, rendering, and policy-update throughput.
- Run full training headless. Produce selected videos afterward rather than
  paying the rendering cost throughout training.
- Inspect the resolved reward configuration. In the verified Go2 task, costs
  were negative-weight reward terms and robot-specific configs overrode base
  weights through multiple layers.

## Playback or custom scripts fail

- Use the play script from the same library and release as the training run.
- A copied RSL-RL play script may import a sibling `cli_args` module; keep the
  script tree intact or provide the corresponding module path.
- Verify observation/action dimensions before assuming a checkpoint is portable
  across versions. Robium observed portability across one patch pair only.
- Interactive editor control and policy stepping can compete for the simulation
  timeline. Use headless execution and a view-only stream unless the combination
  is proven on the target release.
