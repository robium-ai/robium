# TurtleBot3 + ROS 2 Jazzy + Gazebo Harmonic

Use this card only when the robot, ROS distribution, and simulator all match.
Treat every value below as observed evidence, not a default to copy blindly.

## Start from the matching platform

- Use the model-specific parameters from `turtlebot3_navigation2` before the
  generic `nav2_bringup` parameters. The tested Jazzy package carried
  TurtleBot-specific kinematics, footprint, collision monitoring, and velocity
  settings that the generic file did not.
- Keep the simulation model, bridge configuration, robot description, and Nav2
  parameters matched to the same TurtleBot model.
- Inspect the installed package before relying on filenames or defaults. The
  upstream TurtleBot repositories use distribution branches and continue to
  evolve.

Official starting points:

- [TurtleBot3 e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/)
- [ROBOTIS TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3)
- [ROBOTIS TurtleBot3 simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations)
- [Nav2 documentation](https://docs.nav2.org/)

## Interface contract observed by Robium

- Gazebo publishes `/clock`; every node participating in navigation uses that
  clock.
- The tested Burger bridge subscribed to `/cmd_vel` as
  `geometry_msgs/msg/TwistStamped`. A plain `Twist` publisher had no matching
  subscriber and did not move the robot.
- The tested TurtleBot navigation parameters already enabled stamped velocity
  output in each command-producing Nav2 section. Starting from generic Nav2
  parameters lost that alignment.
- Burger Cam and Waffle Pi preserved the application's movement, odometry, TF,
  lidar, IMU, and camera interfaces when their matching model, bridge, and
  description were selected together.
- The tested Waffle Pi profile used a `0.15 m` Nav2 robot radius. Re-read the
  matching installed profile before applying that value to another model.

## Proven gotchas

- **Command type:** on the tested Jazzy Burger stack,
  `geometry_msgs/msg/TwistStamped` moved the robot and plain `Twist` did not.
  Trace the live publisher/subscriber types before changing Nav2 output.
- **Collision-source freshness:** the tested Burger lidar published at `5 Hz`
  while collision monitoring used `source_timeout: 0.2`. Normal jitter made
  scans stale and commands were zeroed. `1.0` worked in that run; the reusable
  rule is to measure the source and leave real margin above its period.
- **Duplicate SLAM:** Jazzy `nav2_bringup` with `slam:=True` already launched
  `slam_toolbox` in the tested package. Starting another SLAM launch produced
  competing lifecycle owners and immediate navigation failures. Inspect the
  actual launch graph before adding a localizer.
- **Container stalls:** on a constrained Docker Desktop host, an approximately
  `8 s` activation stall exceeded a `4 s` lifecycle bond timeout and shut the
  stack down. Setting `bond_timeout: 0.0` allowed that experiment to run but
  disabled bond failure detection; fix resource pressure or measure startup
  behavior before accepting that tradeoff.
- **Launch substitutions:** the tested TurtleBot parameter file contained
  `$(find-pkg-share ...)` behavior-tree paths. A custom launch passing the YAML
  directly left those expressions literal; loading it through a substitution-
  aware `ParameterFile` resolved them.
- **Map coordinates:** goals authored from Gazebo world coordinates did not
  automatically match the SLAM map frame. Use TF or select goals from the map;
  do not generalize the tested spawn-offset arithmetic to rotated frames.
- **Goal clearance:** several failed waypoints were inside or too near world
  geometry. Confirm clearance against the map and footprint before changing
  planner tolerances.

## Model and application evidence

- The original Burger/Jazzy/Harmonic run (nav-trial, 2026-07-10) completed
  mapping and two saved-map Nav2 goals with stamped velocity output.
- A later Waffle Pi application (indoor-navigation, 2026-08-14) preserved the
  TurtleBot sensor and control contract across several Gazebo worlds.
- The renamed Robot Navigation application (2026-08-16) completed the full
  chain from Gazebo lidar through mapping, map save, AMCL, and a Nav2 return
  goal.

Re-check the upstream packages whenever the ROS distribution, TurtleBot model,
simulator, or installed package version changes. Add another platform card only
after that combination completes a real navigation run.
