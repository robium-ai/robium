# SO-arm manipulation on macOS

This card records Robium observations from an SO-arm manipulation build on
Apple Silicon with MuJoCo 3.x, measured on 2026-07-13 through 2026-07-15. They
are diagnostic anchors, not defaults for another robot or scene.

## Runtime and rendering

- `MUJOCO_GL=cgl` was the working macOS offscreen backend and had to be set
  before importing `mujoco`; EGL and OSMesa are Linux paths.
- A 256×256 scene rendered at roughly 84 fps. Physics stepping measured about
  0.012 ms while rendering measured about 11.8 ms, so frame generation, not
  physics, dominated this small scene.
- A target-body camera produced up to 85 least-significant-bit differences from
  call-history-dependent smoothing. A static `xyaxes` look-at camera removed
  that source.
- A new renderer's first complete reset-and-render differed by about 6 LSB from
  later renders. One throwaway full reset, `mj_forward`, scene update, and
  render consumed the cold cycle.
- A renderer created on one thread and first rendered on another could hang in
  CGL `make_current`. Construct the environment and renderer in the thread that
  runs the episode.

## Model and workspace evidence

- MuJoCo Menagerie's current `robotstudio_so101` model states a MuJoCo 3.1.3+
  requirement. Pin and inspect the resolved MuJoCo version when using that
  model; a Gym/Gymnasium environment or another extra may add its own constraint.
- Menagerie provides the SO-101 MJCF and scenes, not a universal Gymnasium task
  or reward contract. In Robium's 2026-07 trial, no suitable off-the-shelf
  SO-101 Gymnasium environment was validated, so the manipulation environment
  was built around the model directly. Re-check the current LeRobot and
  Gymnasium ecosystem before budgeting that work in a new application.
- The trial's default object position near `(0.5, 0, 0.03)` was outside the
  usable mounted-arm workspace.
- Raising the work surface by 6 cm restored the intended envelope and avoided a
  forced roughly 32° downward pitch. This value belongs to that scene geometry.
- With the cube present, one target produced an arm residual near 0.18 with
  joints 1 and 2 saturated; with the cube removed, the residual fell near
  0.0006 with no saturation. This was collision evidence, not an IK tuning
  problem.

## Grasp evidence

- Near-zero wrist roll made the pinch axis about 91% vertical, leaving a 4.2 cm
  aperture unable to span a 6 cm cube. Solving wrist roll separately and then
  re-solving position improved the oracle from 0/10 to 8/10. Adding roll
  directly to that DLS objective diverged.
- A 3 mm grasp-offset change cost 6/10 successes in one sweep. Offset and
  support height were tuned together.
- Raising the first approach waypoint from 0.16 m to 0.20 m prevented a sweep
  through the object and improved that scenario from 2/10 to 10/10.
- The tested gripper was low-control closed and high-control open. Measure both
  actuator endpoints on any other model rather than copying this polarity.

Current upstream starting points:

- [Menagerie `robotstudio_so101`](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101)
- [The Robot Studio SO-101 simulation model](https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation/SO101)
