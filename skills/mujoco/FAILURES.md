# When a MuJoCo manipulation sim fails

Find the first physical link whose measurement disagrees with the command.

## The arm does not reach the target

- If the environment already exposes end-effector or operational-space
  control, use it before copying an IK loop. Record the resulting joint targets
  only when the application's action contract requires joint-space data.
- Report the pose residual and saturated joints; do not treat returned joint
  positions as convergence.
- Probe the task footprint and lift heights independently. One reachable point
  does not validate the workspace.
- Remove or move the object and repeat the same target. A result that succeeds
  without the object identifies obstruction rather than kinematics.
- When actuator force is already at its range, more settle steps are unlikely
  to help.

## The arm reaches but the grasp fails

- Measure the world-frame pinch axis and fingertip gap at the attempted pose.
  Position-only IK can leave a wrist rotation that makes the object impossible
  to span.
- Sweep grasp offset and support height together. Recalibrate after changing
  wrist orientation; grasp offset is pose-dependent.
- Measure the fingertip/object contact height relative to the TCP site. The
  physical pinch point may sit millimeters away from the site even when the TCP
  reaches the object's center.
- Inspect the approach trajectory, not only its endpoint. A joint-space servo
  can sweep through the object on the way to a valid pose.
- Resolve gripper geoms by body membership when mesh geoms are unnamed.
- Drive the gripper through both actuator limits and measure which end is open.
- Calibrate a stable hold command as well as open/closed polarity. A
  position-controlled gripper held at its fully closed limit can eject an
  object, so more squeeze time or slower carrying is not automatically safer.

## The scene looks wrong

- Compare the world surface, robot mount, object spawn, and camera against the
  intended real setup. A generic asset can make valid task poses unreachable.
- Check collision geometry separately from visual geometry. A convincing mesh
  can hide an unsuitable contact model.

## Rendering hangs or changes between identical resets

- Confirm the platform render backend was selected before importing MuJoCo.
- Create and use the renderer on the same thread. On macOS CGL, first use from
  another thread can deadlock silently.
- Replace target-tracking cameras with a static camera when repeated calls
  change an otherwise identical frame.
- Warm the renderer with one throwaway full reset, forward, scene update, and
  render before recording comparisons.
- Interactive-viewer failures are separate from offscreen rendering. On macOS,
  check the current `mjpython` requirement and its compatibility with the
  environment runner.
