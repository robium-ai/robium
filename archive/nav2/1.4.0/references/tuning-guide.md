# Tuning guide

How to move a Nav2 stack from "navigates in the demo" to "navigates
reliably on your robot" — in the order that avoids un-bisectable regressions.
Follow the key directive from `SKILL.md`: change one subsystem at a time,
starting from `examples/nav2-params-diffdrive.yaml`, and re-verify the
map→odom→base_link TF chain before touching any of this.

Sources: [docs.nav2.org](https://docs.nav2.org/) — `tuning/index.html`,
`configuration/packages/configuring-costmaps.html`,
`setup_guides/algorithm/select_algorithm.html`, and
`setup_guides/footprint/setup_footprint.html`, all fetched directly this
session. The tuning index page is itself explicit that it's an evolving,
community-contributed document ("a perpetual work in progress") rather than
a closed spec — treat specific numeric recommendations below as informed
starting points to re-verify, consistent with every example in this skill
being marked `status: unverified`.

## Tuning order

1. **Footprint / robot_radius first.** Nothing else means anything if the
   costmap thinks the robot is a different size or shape than it is.
2. **Costmap resolution and update rates.** Get obstacle sensing correct and
   responsive before asking the planner/controller to react to it well.
3. **Planner plugin and its parameters.** A global path that's already bad
   (too close to walls, unnecessarily long) can't be fixed downstream by
   controller tuning.
4. **Controller plugin, velocity/acceleration limits, and critics/weights.**
   Tune last, against a costmap and global path you already trust.

Skipping this order — e.g. tuning controller critics against a costmap
that's still wrong — produces changes that "fix" a symptom of an upstream
problem and then need to be re-tuned again once the real cause is found.

## Footprint vs robot_radius

`robot_radius` (a single float) is the simplest option — fast, but
pessimistic for any non-circular robot, since obstacle clearance is
computed against the largest circle that contains the robot. An explicit
`footprint` (a polygon of `[x, y]` points in the robot's frame) costs more
to compute but lets a long, narrow, or non-symmetric base pass through
gaps a circular approximation would reject. Set this identically in both
`local_costmap` and `global_costmap` — a mismatch between the two makes the
planner and controller disagree about whether a path is even valid. See
`examples/nav2-params-diffdrive.yaml`'s `robot_radius: 0.22` (adapted from
nav2_bringup's TurtleBot 3 default) as the starting point to replace with
your robot's actual footprint.

## Costmap resolution and update/publish rates

- **`resolution`** (meters/cell): smaller cells give finer obstacle
  representation at higher CPU/memory cost. `0.05` (5 cm) is
  nav2_bringup's default and a reasonable starting point for an
  indoor robot; don't go finer than your sensor's actual angular
  resolution can support.
- **`update_frequency`** (how often the costmap recomputes from sensor
  data) vs **`publish_frequency`** (how often it's published for
  consumers like RViz or the controller): the local costmap generally
  needs both higher than the global costmap (nav2_bringup:
  `update_frequency: 5.0` / `publish_frequency: 2.0` local vs `1.0` / `1.0`
  global) since the local costmap drives reactive obstacle avoidance at
  `controller_frequency`, while the global costmap only needs to be fresh
  enough for periodic replanning.
- **`inflation_layer`**: `inflation_radius` sets how far the cost gradient
  extends from an obstacle; `cost_scaling_factor` sets how steeply cost
  falls off within that radius (higher = steeper falloff, paths hug
  obstacles more closely; lower = gentler falloff, paths stay farther
  away). Tune these together — a wide `inflation_radius` with a low
  `cost_scaling_factor` can make the planner treat a narrow doorway as
  fully blocked.

## Planner plugin selection

- **`NavfnPlanner`** (`nav2_navfn_planner::NavfnPlanner`): Dijkstra/A*-style
  grid planner, no kinematic constraints, the long-standing simple default
  — fine for most differential-drive and holonomic robots where any
  reasonably short path is trackable.
- **Smac Planner family** (`nav2_smac_planner::SmacPlanner2D` /
  `SmacPlannerHybrid` / `SmacPlannerLattice`): adds kinematic feasibility
  (Hybrid-A*, or a custom motion-primitive lattice) — reach for these when
  the robot has real turning-radius constraints (e.g. Ackermann/car-like
  steering) that a kinematics-blind planner will produce infeasible paths
  for.
- **`ThetaStarPlanner`**: any-angle planning for straighter, more
  direct paths than a strictly grid-aligned planner, at extra compute cost.

Switching planners means swapping `planner_server.<plugin_id>.plugin` and
supplying that plugin's own parameter block — plugin identifiers are not
interchangeable, verify the exact class name against docs.nav2.org's
configuration guide before writing it into a params file.

## Controller plugin selection

- **`MPPIController`** (`nav2_mppi_controller::MPPIController`): model
  predictive path integral control — samples many candidate trajectories
  per cycle and scores them against a set of "critics" (goal distance, path
  alignment, obstacle cost, etc., each with its own `cost_weight`). This is
  nav2_bringup's current default as of the jazzy-branch params file fetched
  on 2026-07-10; tuning it means adjusting critic weights, not a small fixed
  parameter set — start by adjusting `CostCritic`/`PathAlignCritic` weights
  before touching the sampling parameters (`batch_size`, `time_steps`).
- **`DWBController`**: the older Dynamic Window Approach controller,
  also critic-based but with a different critic set and simpler cost model;
  still widely used, more predictable to reason about than MPPI at the cost
  of less sophisticated obstacle handling.
- **`RegulatedPurePursuitController`**: a simpler, kinematically-motivated
  pure-pursuit tracker with speed regulation near obstacles/curvature —
  lower compute cost than MPPI, a reasonable choice for a well-mapped,
  mostly-static environment.
- **`RotationShimController`**: not a full controller — a wrapper that
  forces an in-place rotation toward the path before handing off to the
  wrapped controller, useful when a robot needs to face its direction of
  travel before starting to drive (the "Rotate in Place" tuning topic on
  docs.nav2.org).

## Velocity and acceleration limits

Two places bound speed, and they must agree:

- The active controller plugin's own `vx_max`/`vx_min`/`wz_max` (etc. —
  field names vary per plugin).
- `velocity_smoother`'s `max_velocity`/`min_velocity`/`max_accel`/
  `max_decel` — a final smoothing/clamping stage between the controller and
  the robot's `cmd_vel` input, which also rate-limits acceleration so
  commanded velocity jumps don't exceed what the base can actually track.

A robot that "hits its speed limit and jerks" usually has these two set
inconsistently (e.g. a controller allowed to command a `vx` above what
`velocity_smoother`'s `max_accel` can ramp to smoothly) rather than a
control-law problem. Also check `controller_server`'s
`min_x_velocity_threshold`/`min_theta_velocity_threshold` — a threshold set
too high causes small commanded velocities to be zeroed out entirely,
which can look like the robot refusing to move at low speed near a goal.
