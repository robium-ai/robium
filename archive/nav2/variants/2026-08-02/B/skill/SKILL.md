---
name: nav2
version: 1.5.0
description: >
  Nav2 mobile-robot navigation for ROS 2: bringup, behavior trees, costmaps,
  planner/controller servers, localization (AMCL, slam_toolbox), waypoint
  following, and tuning. Use when: 'navigation', 'nav2', 'costmap', 'path
  planning', 'robot won't move to goal', 'localization', 'SLAM', 'AMCL',
  'waypoint', or any autonomous mobile robot task. Load after architect
  selects the ROS nav stack; pairs with ros2 (foundation), gazebo (sim), and
  visualization (debugging). Not for: manipulation (lerobot) or generic
  ROS 2 issues (ros2).
---

# nav2

The nav-vertical core tool skill for robium: bringup, the BT Navigator and
behavior trees, costmap layers, the planner/controller/smoother servers,
localization (AMCL and slam_toolbox), waypoint following, and tuning a
running stack. Nav2 config in this skill targets ROS 2 **Jazzy Jalisco**
(LTS, supported to May 2029) rather than **Lyrical Luth**, the current
overall LTS the `ros2` skill defaults to — Nav2 has not yet shipped binary
packages for Lyrical (tracked in `ros-navigation/navigation2#6123` as of
2026-07). Gazebo Harmonic is Jazzy's paired simulator. Re-check that gap
before starting a new project, and treat picking the distro itself as
`architect`'s call, not this skill's — load this skill once `architect` has
routed you to the navigation vertical.

## When to use this skill

- Any autonomous mobile-robot navigation task: bringing up Nav2, tuning
  costmaps or the planner/controller, adding or debugging a behavior tree,
  choosing between AMCL and slam_toolbox, following waypoints.
- The trigger phrases in the description: 'navigation', 'nav2', 'costmap',
  'path planning', "robot won't move to goal", 'localization', 'SLAM',
  'AMCL', 'waypoint'.
- A robot receives a goal and never moves, or moves erratically — start here
  (see `references/common-failures.md`), not in application logic.
- Cross-references — go to the sibling skill instead when the question is:
  - ROS 2 substrate this stack runs on (workspaces, colcon, packages, nodes,
    QoS, launch syntax, TF2 concepts/broadcasters) → `ros2`. This skill's
    only TF responsibility is verifying the map→odom→base_link chain exists
    and is current before tuning anything else; teaching TF2 itself stays in
    `ros2` — see that skill's interfaces-and-qos and debugging references.
  - Simulating the robot Nav2 drives → the `gazebo` skill.
  - Visualizing costmaps, TF, or BT execution (RViz2, Foxglove) → the
    `visualization` skill.
  - Arm/manipulation tasks, learned policies → `lerobot`. Nav2 is mobile-base
    navigation only.
  - Environment/Docker setup for the ROS 2 + Nav2 + Gazebo stack →
    `environments`.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: embed + links.** The navigation-specific concepts
  (BT Navigator, costmap layers, server roles, AMCL vs slam_toolbox) live in
  this skill and its references in depth, because no single upstream page
  covers them as a coherent whole for a new project — but every parameter
  table and default value is a link back to docs.nav2.org or the
  `navigation2` GitHub repo, not re-typed from memory. See References.
- **Start from the official minimal config, change one subsystem at a
  time.** <!-- id: one-subsystem-at-a-time --> `examples/nav2-params-diffdrive.yaml` is adapted from
  nav2_bringup's own `nav2_params.yaml` (jazzy branch) — begin a new robot
  there, verify it navigates, then change exactly one subsystem (footprint,
  controller plugin, costmap layer) before touching the next. Changing
  costmap, controller, and planner parameters simultaneously makes a
  regression impossible to bisect.
- **`use_sim_time` must be consistent across every node, every time.** <!-- id: use-sim-time-consistency --> In
  simulation, every Nav2 node, the map/odom TF broadcasters, and the sim
  clock source must all agree on `use_sim_time: true` (or all agree on
  `false` on real hardware) — one node left on the wrong value produces TF
  extrapolation errors and rejected goals that look like a planning bug but
  are a clock mismatch. Set it once, globally, in the params file passed to
  every node (see `examples/nav2-params-diffdrive.yaml` and
  `examples/bringup-launch-snippet.py`), not per-node.
- **Verify the TF tree — map→odom→base_link — before tuning anything
  else.** <!-- id: tf-tree-before-tuning --> Costmap2D blocks activation until a full TF tree is available, and
  AMCL will not publish `map`→`odom` until it has an initial pose (from
  RViz's "2D Pose Estimate" or the `/initialpose` topic). A robot that
  "won't move" is, more often than a bad planner or controller parameter, a
  broken or incomplete TF chain — check this first with `ros2 run tf2_ros
  tf2_echo map base_link` every time, before touching costmap or controller
  tuning. See `references/common-failures.md`.
- **Never write Nav2 parameter defaults, plugin names, or version/status
  claims from memory.** <!-- id: no-param-facts-from-memory --> They change release to release (the controller
  default alone has moved from DWB to MPPI upstream). Verify against
  docs.nav2.org or the `navigation2` GitHub repo before repeating a claim in
  a real project — every example in this skill is marked `status:
  unverified` for exactly this reason, and each reference states how its
  claims were checked on 2026-07-10.

## Quick start

**1. Confirm the ROS 2 substrate is ready.** <!-- id: confirm-ros2-substrate --> A sourced Jazzy workspace with
Nav2 installed (`sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup`
— re-verify the package name against `docs.nav2.org`'s install page before
running it) — see the `ros2` skill if the workspace itself isn't set up yet.

**2. Bring up Nav2 with the example config.** <!-- id: bringup-example-config --> Copy
`examples/nav2-params-diffdrive.yaml` and `examples/bringup-launch-snippet.py`
into your project, keeping the params filename the launch snippet expects
(or updating both together — see Customization), then:

```bash
ros2 launch ./bringup-launch-snippet.py map:=/path/to/your_map.yaml use_sim_time:=true
```

**3. Verify before tuning.** <!-- id: verify-before-tuning --> Confirm every managed node is active
(`ros2 lifecycle get /controller_server` etc.) and the TF chain is complete
(`ros2 run tf2_ros tf2_echo map base_link`) — see
`references/common-failures.md` if either check fails.

**4. Send a goal** through RViz2's "Nav2 Goal" tool, or programmatically —
see the "send goals programmatically" usage pattern below.

## Usage patterns

**Bringup with an existing map.** <!-- id: bringup-existing-map --> Pass a saved map YAML and leave `slam`
false — Nav2 launches `nav2_map_server` + `nav2_amcl` for localization
against that static map. Set the robot's initial pose (RViz "2D Pose
Estimate" or publish to `/initialpose`) immediately after launch; AMCL does
not publish `map`→`odom` until it has one. See
`examples/bringup-launch-snippet.py` (`map:=` argument) and
`references/nav2-architecture.md`'s localization section.

**SLAM-then-navigate.** <!-- id: slam-then-navigate-single-instance --> Pick exactly ONE of two combinations — on Jazzy
(observed 2026-07-10, nav-trial) nav2_bringup's `slam:=True` ALREADY
launches its own `online_sync_launch.py`, so *also* including slam_toolbox's
`online_async_launch.py` alongside spawns two slam_toolbox nodes whose
lifecycle managers fight and every goal fails (0/9: "Unable to start
transition 1 from current state inactive", "Timed out while waiting for
action server to acknowledge goal request for compute_path_to_pose").
Either (a) bring up with `slam:=True` and NO extra slam include, or (b)
launch `navigation_launch.py` plus your own `online_async_launch.py` — never
both. Either way pass no `map:=` argument; a SLAM node publishes `/map` and
the `map`→`odom` transform in place of `nav2_map_server`/`nav2_amcl`.
slam_toolbox's Jazzy `online_async` already ships `base_frame:
base_footprint` and `scan_topic: /scan` — only `use_sim_time: true` needs
adding, and any guidance to edit `base_frame` is stale for Jazzy. Drive the
robot to explore, then save the resulting map with `nav2_map_server`'s
`map_saver_cli` (see
`map_saver`'s params in `examples/nav2-params-diffdrive.yaml`) once mapping
is done, so the next run can go back to AMCL-on-a-fixed-map. Mind the frame
convention: the SLAM `map` frame's origin is the robot's mapping **start
pose**, not the world/sim origin — goals written in world coordinates are
silently offset by the spawn pose, and the saved map inherits the same
origin (convert `goal_map = goal_world − start_pose`, or pick goals off the
live map in a viewer). Verified 2026-07-11 (nav-trial). See
`references/nav2-architecture.md`.

**Launch Nav2 servers directly (without nav2_bringup's launch).** <!-- id: direct-server-launch --> Three
Jazzy-verified reasons a project outgrows `bringup_launch.py` (all hit in
one real build, 2026-07-11 nav-trial): `slam:=True` starts its own
*synchronous* slam_toolbox, so also launching `online_async_launch.py`
alongside yields two SLAM nodes; `navigation_launch.py` hard-codes its
lifecycle-manager params, so `bond_timeout` can't be adjusted; and a params
file containing `$(find-pkg-share ...)` substitutions reaches the nodes as
literal strings. When launching servers as plain `Node`s yourself: wrap the
params file in `launch_ros.parameter_descriptions.ParameterFile(path,
allow_substs=True)`, replicate `navigation_launch.py`'s remappings (the
`cmd_vel` → `cmd_vel_nav` → smoother chain), and list every server in your
own lifecycle manager — set `bond_timeout: 0.0` on it (the only way to
change it, since `navigation_launch.py` hard-codes the value; see the
Docker-stall gotcha). To override a single param the `ParameterFile` gets
wrong (e.g. TB3 `burger.yaml`'s relative `yaml_filename: "map.yaml"`, which
makes `map_server`'s `LoadMap` fail), append a plain dict AFTER the
`ParameterFile` in the node's `parameters=` list — later entries win:
`parameters=[ParameterFile(params_yaml, allow_substs=True), {'yaml_filename':
abs_map_path}]`. yaml_filename fix observed 2026-07-10 (nav-trial).

**Send goals programmatically.** <!-- id: basic-navigator-api --> Use `nav2_simple_commander`'s
`BasicNavigator` Python class rather than hand-rolling `NavigateToPose`
action clients: `goToPose()` / `goThroughPoses()` for single/multi-pose
goals, `followWaypoints()` for a waypoint list, and non-blocking
`isTaskComplete()`/`getResult()` polling for feedback in a single-threaded
script. See `references/nav2-architecture.md`'s commander-API section for a
minimal snippet shape.

**Tune for a new robot footprint/speed.** <!-- id: tune-footprint-speed --> Start from
`examples/nav2-params-diffdrive.yaml`'s `local_costmap`/`global_costmap`
`robot_radius` (switch to an explicit `footprint` polygon for a non-circular
base), then the controller's velocity/acceleration limits and
`velocity_smoother`'s `max_velocity`/`max_accel`/`max_decel` — change these
before touching planner or BT internals, since a wrong footprint or speed
limit makes every downstream navigation attempt look broken. See
`references/tuning-guide.md`.

**Author a custom global planner plugin.** <!-- id: custom-global-planner-plugin -->
A global-planner plugin subclasses `nav2_core::GlobalPlanner` and
implements `configure(parent, name, tf, costmap_ros)` / `cleanup()` /
`activate()` / `deactivate()` / `createPlan(...)` — the `costmap_ros`
argument handed to `configure()` is how the plugin reaches the same
costmap `references/nav2-architecture.md`'s planner-server section
already documents. Registration needs exactly two pieces, not three:
`PLUGINLIB_EXPORT_CLASS(<YourClass>, nav2_core::GlobalPlanner)` in the
.cpp, and the CMakeLists.txt's
`pluginlib_export_plugin_description_file(nav2_core <plugin>.xml)`
call, which installs the plugin-description XML and writes the
ament-index marker pluginlib's `ClassLoader` queries at runtime — a
`package.xml` `<export>` tag for the same XML is a ROS 1 carryover
some tutorials still ship and is not load-bearing in ROS 2, per
search-synthesis of ament_cmake/pluginlib docs (re-verify on next docs
pass). Treat the exact `configure()`/`createPlan()` parameter list as
a conceptual pattern, not a pinned signature — confirmed 2026-08-02
against the `rolling`-branch `navigation2_tutorials` repo (no
Jazzy/Humble/Iron branch exists there to check directly); re-verify
against this skill's target distro (Jazzy Jalisco) before writing a
plugin from it.

**Author a custom costmap layer plugin.** <!-- id: custom-costmap-layer-plugin -->
A costmap layer plugin subclasses `nav2_costmap_2d::Layer` and
overrides `onInitialize()` (parameter declaration + one-time state),
`updateBounds(robot_x, robot_y, robot_yaw, min_x, min_y, max_x,
max_y)` (grows the costmap's dirty-bounds window), and
`updateCosts(master_grid, min_i, min_j, max_i, max_j)` (writes cost
values into that window) — plus `reset()`, `onFootprintChanged()`, and
`isClearable()`. Registration mirrors the planner-plugin pattern's
load-bearing half only (see the custom-global-planner-plugin pattern
above): `PLUGINLIB_EXPORT_CLASS(<YourClass>, nav2_costmap_2d::Layer)`
in the .cpp, paired with CMakeLists.txt's
`pluginlib_export_plugin_description_file(nav2_costmap_2d
<layer>.xml)` — the macro's first argument is `nav2_costmap_2d` here,
not `nav2_core` as in the planner case; it is pluginlib's
resource-index key, not a string a params file's `plugins:` list
names directly. Cross-references `references/nav2-architecture.md`'s
Costmap 2D section (which names the shared layer types — StaticLayer,
ObstacleLayer, VoxelLayer, InflationLayer — but not how to author a
new one). Confirmed 2026-08-02 against the `rolling`-branch
`navigation2_tutorials` repo; the `Layer` virtual-method set has been
stable across recent distros per search-synthesis, but re-verify
before absorbing a parameter list verbatim.

## Platform gotchas

- **Jazzy, not Lyrical, until Nav2 ships Lyrical binaries.** <!-- id: jazzy-not-lyrical --> See the intro
  paragraph above; this is a binding, repo-wide fact (`architect` and
  `ros2` both reference it) — don't silently "upgrade" a nav2 project to
  Lyrical without re-checking `ros-navigation/navigation2#6123` first.
- **AMCL is silent, not erroring, without an initial pose.** <!-- id: amcl-silent-no-initial-pose --> A freshly
  launched AMCL-based stack with no `/initialpose` published will sit idle —
  no error, just no `map`→`odom` transform and a costmap that never
  activates. This looks identical to a hung launch; check for a missing
  initial pose before debugging anything else. Between bringup and the first
  goal, `global_costmap` and AMCL spam transform/pose warnings every
  ~0.5–2 s ("Timed out waiting for transform from base_link to map ...
  Invalid frame ID map", "AMCL cannot publish a pose ... Please set the
  initial pose") — this is benign, the `map` frame doesn't exist until AMCL
  gets its initial pose, so don't chase it. See
  `references/common-failures.md`.
- **Composed (`use_composition:=true`) vs standalone nodes change crash
  behavior.** <!-- id: composition-vs-standalone --> nav2_bringup defaults to component-container composition; a
  crash inside one composed node can take down the whole container process,
  whereas standalone nodes (`use_composition:=false`, with
  `use_respawn:=true`) restart independently. Prefer standalone + respawn
  while iterating on a new robot; composition is a later performance
  optimization, not a default to fight while still debugging.
- **`/cmd_vel` may be `TwistStamped`, not `Twist`.** <!-- id: cmd-vel-twiststamped --> Modern gz robot
  integrations (TB3 on Jazzy among them) subscribe `TwistStamped`; a plain
  `Twist` publisher never matches — no error, `ros2 topic pub` just waits
  forever for a matching subscription — and the robot silently ignores
  Nav2. Check with `ros2 topic info -v /cmd_vel`, and set
  `enable_stamped_cmd_vel: true` in every cmd_vel-publishing section
  (`controller_server`, `velocity_smoother`, `behavior_server`,
  `collision_monitor`, `docking_server`). TB3 Jazzy's `burger.yaml` already
  pre-sets `enable_stamped_cmd_vel: true` in all five of those sections, so
  this trap only bites configs started from nav2_bringup's `nav2_params.yaml`.
  This wire-format toggle is a separate fact from the controller plugin
  API: `nav2_core::Controller::computeVelocityCommands()` always returns
  `geometry_msgs::msg::TwistStamped` regardless of `enable_stamped_cmd_vel`
  — a plugin returning `TwistStamped` does NOT imply `/cmd_vel` is
  published as `TwistStamped`; that inference is not valid.
  `controller_server` converts/republishes the plugin's `TwistStamped`
  according to this parameter, not according to the plugin's return type.
  Verified 2026-07-11 (nav-trial); plugin-API decoupling confirmed
  2026-08-02 against `navigation2_tutorials` (rolling branch).
- **On TB3 Jazzy, start from `turtlebot3_navigation2`'s `burger.yaml`, not
  nav2_bringup's `nav2_params.yaml`.** <!-- id: tb3-burger-yaml-start --> It is TB3-tuned and carries 13 of
  nav2_bringup's 14 sections; it ships no `use_sim_time` keys and relies on
  `RewrittenYaml` to inject them. Observed 2026-07-10 (nav-trial).
- **TB3 `burger.yaml`'s `collision_monitor` `source_timeout` is too tight
  for its own lidar.** <!-- id: tb3-collision-monitor-timeout --> The scan source ships `source_timeout: 0.2`, but the
  burger lidar publishes at 5 Hz (a 0.2 s period), so ordinary jitter makes
  `collision_monitor` reject the source and zero `cmd_vel` — the robot won't
  move even with a healthy stack ("Latest source and current collision
  monitor node timestamps differ on 0.2xx seconds. Ignoring the source.",
  "Robot to stop due to invalid source"). Set `source_timeout` above the
  sensor period (1.0 worked). Observed 2026-07-10 (nav-trial).
- **On Docker Desktop/macOS the container stalls ~8 s at Nav2 activation and
  the first goal, so the default `bond_timeout: 4.0` self-destructs the
  stack** <!-- id: docker-desktop-bond-timeout --> ("CRITICAL FAILURE: SERVER controller_server IS DOWN after not
  receiving a heartbeat for 4000 ms"). Jazzy's `navigation_launch.py`
  hard-codes the `lifecycle_manager` params, so `bond_timeout` cannot be set
  through `params_file`/`RewrittenYaml`; the only fix is to launch the
  servers under your own `lifecycle_manager` node with `bond_timeout: 0.0`
  (see the direct-server-launch usage pattern). Observed 2026-07-10
  (nav-trial).
- **In live SLAM, an unreachable goal corrupts the map.** <!-- id: slam-goal-corrupts-map --> A goal in unknown
  space that fails to plan triggers a spin/backup recovery loop that smears
  the live SLAM map until every subsequent plan fails ("Failed to create
  plan with tolerance of: 0.500000", "Goal ... was outside bounds"). Check
  waypoints against actual world geometry and keep them ≥0.4 m from
  obstacles — e.g. `turtlebot3_world` has pillars of r=0.15 at {-1.1, 0,
  1.1}² (grep the SDF pillar poses); an octagon route of r=1.7 lands inside
  them. Observed 2026-07-10 (nav-trial).
- **Gazebo Harmonic's `/clock` must actually be publishing** <!-- id: clock-must-be-publishing --> before any node
  with `use_sim_time:=true` will progress — a paused or not-yet-started
  Gazebo world leaves every Nav2 node waiting on TF timestamps that never
  arrive, which looks like a Nav2 hang rather than a sim issue.

## Customization

- **Different robot footprint or drive type:** swap `robot_radius` for an
  explicit `footprint` polygon in both `local_costmap` and `global_costmap`
  in `examples/nav2-params-diffdrive.yaml`, and change `FollowPath`'s
  `motion_model` (e.g. `"DiffDrive"` → `"Omni"`) if the base isn't
  differential-drive — see `references/tuning-guide.md`.
- **Different controller/planner plugin:** the params file's
  `controller_server.FollowPath.plugin` and
  `planner_server.GridBased.plugin` fields select the algorithm; swapping
  requires the matching plugin name and its own parameter block (e.g.
  `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController` or
  `nav2_smac_planner::SmacPlannerHybrid`) — verify exact plugin/class names
  against `docs.nav2.org`'s configuration guide before writing them, they
  are not interchangeable strings. See `references/tuning-guide.md`.
- **Different params filename or launch structure:**
  `examples/bringup-launch-snippet.py`'s `params_file` default and
  `examples/nav2-params-diffdrive.yaml`'s own filename must be kept in sync
  if you rename either — the launch snippet resolves the params path
  relative to itself, so a silent rename of one without the other produces a
  "params file not found" failure at launch, not a subtle runtime bug.
- **Reverting to Lyrical Luth:** once Nav2 ships Lyrical binaries (re-check
  `ros-navigation/navigation2#6123`), swap `jazzy` for `lyrical` in every
  install command and Docker base image in the `environments` skill's
  Dockerfile.ros2 example; nothing in this skill's params/launch content itself is
  distro-specific beyond the install step.

## References

- `references/nav2-architecture.md` — the BT Navigator and default behavior
  trees, the planner/controller/smoother/behavior/waypoint-follower servers,
  costmap 2D layers (global vs local), the lifecycle manager, AMCL vs
  slam_toolbox, and the `nav2_simple_commander` API.
- `references/tuning-guide.md` — costmap resolution/update-rate/inflation
  tuning, footprint vs radius, controller/planner plugin selection,
  velocity/acceleration limits, and the "one subsystem at a time" workflow.
- `references/common-failures.md` — the "robot won't move" diagnostic
  checklist: lifecycle state, TF tree, `use_sim_time` consistency, costmap
  obstacle sourcing, goal rejection, and `cmd_vel` not reaching the base.
- `examples/nav2-params-diffdrive.yaml` — adapted from nav2_bringup's
  official minimal diff-drive `nav2_params.yaml` (status: unverified — file
  header states the exact source and the deviations made).
- `examples/bringup-launch-snippet.py` — a project launch file that includes
  nav2_bringup's own `bringup_launch.py`, pointed at this skill's example
  params file (status: unverified — file header states the exact source).
- Upstream: [Nav2 documentation](https://docs.nav2.org/) (primary source for
  this skill, reachable via direct fetch on 2026-07-10), [navigation2 GitHub
  repo, jazzy branch](https://github.com/ros-navigation/navigation2/tree/jazzy)
  (source of the params/launch examples, fetched directly via raw GitHub
  URLs on 2026-07-10), [nav2_simple_commander
  docs](https://docs.nav2.org/commander_api/index.html), [slam_toolbox
  GitHub](https://github.com/SteveMacenski/slam_toolbox). Sibling skills:
  `ros2` (foundation, load alongside), `gazebo` (sim),
  `visualization` (debugging), `environments` (Docker/env
  setup), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->



- 1.5.0 (2026-08-02): update cmd-vel-twiststamped [reasons: obs-nav2-003] (applied by apply_deltas)
- 1.4.0 (2026-08-02): annotate SKILL.md; update custom-costmap-layer-plugin [reasons: obs-nav2-001, obs-nav2-002] (applied by apply_deltas)
- 1.3.0 (2026-08-02): add Usage patterns; add Usage patterns [reasons: obs-nav2-001, obs-nav2-002] (applied by apply_deltas)
- 1.2.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.2.0 (2026-07-31): nav-trial absorption (Jazzy/TB3, observed 2026-07-10) — corrected SLAM-then-navigate (bringup slam:=True already runs a slam_toolbox node; a second online_async is double-SLAM), added Docker-stall bond_timeout:0.0 fix, TB3 burger.yaml starting point + pre-set enable_stamped_cmd_vel + collision_monitor source_timeout, benign costmap/AMCL log storm, live-SLAM recovery map corruption + waypoint clearance, and map_server yaml_filename override.

- 1.1.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.

- 1.1.0 (2026-07-11): nav-trial absorption — TwistStamped cmd_vel gotcha,
  SLAM map-origin-at-start-pose convention, direct-server launch pattern
  (allow_substs / double-SLAM / bond_timeout), bringup-abort recovery added
  to common-failures.
