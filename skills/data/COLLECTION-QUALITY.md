# Collection quality

Use this when episode count is growing but the learned behavior is not.

## Coverage before volume

- Define the smallest workspace and variation needed by the application, then
  sample it densely. Add range only after the policy is reliable inside that
  envelope.
- In Robium's VLA trial, 50 episodes spread over roughly 30 cm failed to locate
  grasps reliably. Seventy-five episodes over roughly 10 cm reached 80%
  success. These are observations from that task and embodiment, not universal
  collection targets.
- Track coverage across object pose, robot pose, camera visibility, action
  range, and failure-relevant conditions. Raw episode count hides holes in all
  of them.

## Demonstration integrity

- Store an explicit success result for every episode.
- In a successful-expert dataset, when a scripted oracle misses, retry or
  discard the episode. Do not label a failed terminal state as a successful
  expert demonstration. Corrective, recovery, DAgger, and failure-learning
  collections may retain it under an explicit, different label and sampling
  plan.
- Put a bounded-attempt or minimum-success-rate guard around automated
  generation. A broken oracle should fail the run rather than loop until it
  eventually reaches a requested count.
- Review teleoperation for accidental pauses, resets, camera occlusion, and
  inconsistent task completion before publishing or training. LeRobot owns
  device, keyboard, desktop-permission, and headless teleoperation mechanics.

## Validate before scaling

- Load a small slice through the intended training stack and verify feature
  names, shapes, rates, temporal alignment, and episode boundaries.
- Train a cheap smoke run only to expose schema and pipeline failures. Do not
  interpret smoke-run quality as evidence that the dataset is sufficient.
- Evaluate by condition, not only aggregate success, so missing coverage is
  visible.
