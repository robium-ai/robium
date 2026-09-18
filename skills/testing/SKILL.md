---
name: testing
description: Choose proportional evidence for robotics software before claiming it works.
---

# Testing

Test the claim at the cheapest layer that can falsify it.

## Match evidence to the claim

- Pure logic belongs in a fast unit test without ROS, a robot, or a simulator.
- A node or launch claim needs the expected processes and interfaces to appear,
  not merely a successful build.
- Behavior that depends on physics, sensors, timing, or closed-loop control
  needs a deterministic scenario in simulation or on the target robot.
- A learned-policy pipeline smoke proves that data, training, evaluation, and
  metrics connect. A regression claim needs a known checkpoint and a stated
  performance bar.
- Add costlier layers only when the risk or claim requires them. A demo does
  not need a fleet-scale qualification suite, but it still needs a real smoke.

Read [ROS2-AND-SIM.md](ROS2-AND-SIM.md) for ROS launch, simulator, map, and
headless-CI concerns. Read [POLICY-EVAL.md](POLICY-EVAL.md) for learned-policy
smokes and regression gates. Tool-specific syntax remains in official docs and
the owning `ros2`, simulator, or `lerobot` skill.

## Make the result trustworthy

- Seed controllable randomness, use simulation time consistently, bound the
  run, and record the fixture and environment that produced the result.
- Assert observable behavior and interfaces, not duplicated configuration
  literals or log wording.
- For a camera or rendered demo, fetch the image payload and assert meaningful
  pixels, such as non-black mean and non-flat variance. HTTP success and a
  “camera ready” status can both pass while the viewer is blank.
- Guard measurement tools against an empty run. Exiting successfully after
  measuring zero devices or episodes is a test-harness failure.
- Keep benchmarks and long evaluations outside the default suite unless their
  cost is justified on every change.
- Use `test-assets` when fixtures, worlds, datasets, recordings, or goldens need
  provenance and maintenance rules.

If a suite is flaky, slow, green without useful evidence, or fails only on a
particular runner, read [FAILURES.md](FAILURES.md).

## Keep remote cost proportional

- Run the same pipeline locally at tiny scale before any paid remote test.
- After changing gateway or session lifecycle code, rebuild the target-platform
  fake deployment image and prove allocation, capability isolation, one real
  request, cancellation or deletion, and zero-resource cleanup before a paid
  remote smoke. A stale digest does not test the change.
- Keep GPU- or hardware-dependent tests explicit and schedulable; do not make a
  default CI job depend on unavailable hardware.
- A remote success should preserve the exact image, model, data, seed,
  hardware, result, and cost window needed to understand the claim.

## Done

- The changed behavior has evidence at the lowest meaningful layer.
- A robotics app's smoke exercises the behavior it exists to demonstrate, not
  only process health.
- CI runs the stable, affordable evidence by default and clearly separates
  slow, paid, hardware, and manual checks.
