# When navigation fails

Start with the symptom that is actually present. Move upstream only when the
current link has evidence.

## The stack is unavailable or inactive

- Missing navigation actions point to bringup or lifecycle state, not planner
  tuning.
- If several managed nodes shut down together, find the first node that failed.
  The later transitions are usually fallout.
- If activation waits on a frame, map, or sensor, follow that missing input
  instead of forcing the node active.

## The pose is missing or stale

- Separate a broken transform chain from an old transform. Both can look like
  a missing pose to costmaps and actions.
- Check that every node uses the intended clock and that simulation time is
  advancing. Thread one `use_sim_time` launch value through every participating
  node; copied literals can silently diverge when the launch argument changes.
- Identify who owns each transform. AMCL and SLAM are alternative owners of
  `map -> odom`, not two publishers to run together.
- When `robot_localization` owns `odom -> base_link`, verify that TF publication
  is enabled and that `world_frame` matches the intended continuous odometry
  frame. Do not leave a Gazebo TF bridge publishing the same transform.
- With AMCL, distinguish “no initial pose yet” from a localizer that received a
  pose and still cannot publish one.

## A costmap has no useful data

- An empty global costmap points first to its map and transform inputs.
- An empty local costmap points first to its observation topics, frames,
  freshness, and QoS.
- A costmap full of obstacles points to footprint, inflation, clearing, or
  sensor interpretation. Confirm which layer contributes the cells before
  tuning it.

## A goal is rejected or aborted

- Rejected before planning: inspect action availability, lifecycle state, goal
  frame, and pose validity.
- Aborted without a path: inspect planner feedback and the global costmap.
- Aborted during execution: inspect controller feedback, recovery behavior,
  and the local costmap rather than treating every abort as a planning failure.
- Confirm that the goal is free space in the map frame. A valid world-frame
  coordinate is not automatically a valid map-frame goal.

## A plan exists but the robot does not move

- If no motion command appears, inspect the controller's rejection reason,
  footprint, local costmap, progress checker, and goal checker.
- If commands appear and are then zeroed, trace velocity smoothing, collision
  monitoring, safety, and command arbitration in order.
- A path visible in a viewer proves planning only. It does not prove control or
  actuation.

## Velocity exists but the base remains still

- Compare the publisher and subscriber topic names and message types.
- Follow remaps through every mux, smoother, safety node, bridge, and base
  driver. Do not stop at the first `cmd_vel` topic with traffic.
- Check the base's own state, limits, and stop conditions. Once a valid command
  reaches the driver, the fault is outside Nav2.

## The failure is intermittent

- Compare timeouts with measured publication periods, jitter, and startup load.
  A timeout equal to the nominal period has no margin.
- Correlate lifecycle or bond failures with the first stalled or crashed node,
  not the loudest shutdown log.
- Reproduce one failure at a time. Concurrent simulators or duplicate
  localizers can create convincing but unrelated symptoms.
