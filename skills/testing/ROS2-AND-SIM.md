# ROS 2 and simulation test patterns

Use these patterns when automated evidence is warranted, not as a checklist
requiring a new test layer for every demo or edit.

## Choose the layer

- Use ordinary pytest for logic that does not require ROS.
- Use `launch_testing` when assertions require launched nodes, lifecycle, or
  ROS interfaces. Follow the current
  [ROS 2 testing guide](https://docs.ros.org/en/rolling/Tutorials/Intermediate/Testing/Testing-Main.html)
  and [launch_testing README](https://github.com/ros2/launch/blob/rolling/launch_testing/README.md)
  for API details.
- Use a simulator scenario only when the claim depends on physics, sensors,
  time, or closed-loop robot behavior.

## A useful ROS smoke

- Launch the smallest application composition that owns the behavior.
- Wait on the actual readiness boundary rather than a fixed sleep.
- Check the expected node or lifecycle state and the interfaces needed by the
  behavior.
- Drive one bounded action and assert its observable result.
- Capture process exits and perform shutdown assertions so a passing behavior
  does not hide a crashing component.
- Select relevant packages through the project's normal `colcon test` path,
  rather than testing the whole workspace after each edit, and inspect
  `colcon test-result` when it fails.

## Simulation evidence

- Pin the world, robot or model revision, seed, initial state, and simulated
  time behavior.
- Assert task outcomes such as reaching a goal, avoiding an obstacle, or
  completing a manipulation stage. Avoid pixel-perfect or timing-exact goldens
  unless the system actually promises them.
- Separate startup allowance from behavior timeout, and record real-time factor
  when it changes how the result should be interpreted.
- Keep the default scenario small. Longer stress or multi-seed runs can be
  scheduled or manual.

## Headless and platform constraints

- CI simulators should use their supported headless mode instead of assuming a
  display.
- Native ROS 2 and Gazebo CI is Linux-oriented. On macOS, use the project's
  established container or remote environment rather than pretending the same
  native path exists.
- Isaac Sim tests inherit its current NVIDIA GPU and driver requirements. Keep
  them off runners that do not satisfy the verified floor.

## Occupancy-map assertion observed by Robium

In the 2026-07-10 navigation trial, a free-space assertion using
`pixel >= 0.75 * maxval` falsely passed an all-unknown trinary occupancy map.
The observed encoding was free 254, unknown 205, occupied 0. A threshold above
`0.80 * maxval` separated unknown from free in that fixture; 0.9 worked.

Treat those values as evidence for that ROS map encoding and file, not a
universal image rule. Inspect the map format and metadata before reusing the
assertion.
