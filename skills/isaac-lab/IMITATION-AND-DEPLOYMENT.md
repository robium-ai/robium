# Imitation learning and deployment

Use this card only when the task goes beyond the common RL train/play loop.
Isaac Lab's Mimic, teleoperation, robomimic scripts, exporters, and deployment
examples change quickly; the current official workflow is the source of truth.

## Imitation learning

- Start from an installed task that supports the selected teleoperation device
  and demonstration schema. Prove reset, task completion, and one replay before
  collecting volume.
- Keep the stages distinct: collect demonstrations, annotate or inspect success,
  generate augmented demonstrations with Mimic when appropriate, train through
  the supported imitation library, then evaluate named checkpoints.
- Generated demonstrations inherit the source task, scene, controller, and
  success predicate. Inspect their coverage and failures rather than treating a
  successful generation command as valid training data.
- The current official examples use Isaac Lab Mimic and robomimic, but script
  names, extras, tasks, and dataset formats are release-sensitive. Follow the
  [teleoperation and imitation guide](https://isaac-sim.github.io/IsaacLab/main/source/overview/imitation-learning/teleop_imitation.html)
  for the installed release.
- Cross into `data` for source-mix and demonstration-quality decisions. Cross
  into `lerobot` only when the artifact is a LeRobotDataset or the policy is
  trained through LeRobot.

## Export and deployment

- Playback is not deployment. First record the exact observation ordering,
  normalization, action scaling, recurrent state, control rate, and actuator
  limits that wrap the checkpoint.
- Prefer an exporter that preserves those semantics. Current Isaac Lab
  documentation includes LEAPP for supported manager-based RL workflows and
  policy-deployment examples; confirm the learning library, environment type,
  physics preset, and optional extras before choosing it.
- Re-run the policy in a second simulation or deployment harness before hardware
  when that can expose hidden simulator dependencies.
- Hardware rollout adds timing, estimator, actuator, network, and safety
  contracts. Begin with bounded commands and an independent stop path; do not
  infer safe behavior from the Isaac Lab playback video.
- Use the current [policy deployment guide](https://isaac-sim.github.io/IsaacLab/main/source/policy_deployment/index.html)
  and the selected robot/example repository for the actual export and hardware
  bridge. Do not generalize a HOVER, gear-insertion, ROS, or LEAPP recipe to an
  unrelated task.

## Evidence to keep

- Matched Isaac Lab/Isaac Sim release and physics preset.
- Dataset or reward configuration and task revision.
- Checkpoint plus preprocessing, postprocessing, and export metadata.
- Sim playback, cross-simulator result when used, control frequency, and the
  exact hardware safety envelope.
