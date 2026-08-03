# Nav2 architecture

How Nav2's pieces fit together: the BT Navigator and default behavior trees,
the task servers it delegates to, the two costmaps, the lifecycle manager
that brings the whole stack up in order, localization (AMCL vs
slam_toolbox), and the Python commander API for driving it programmatically.

Sources: [docs.nav2.org](https://docs.nav2.org/) — `concepts/index.html`,
`configuration/packages/configuring-lifecycle.html`,
`configuration/packages/configuring-costmaps.html`,
`tutorials/docs/navigation2_with_slam.html`, and
`commander_api/index.html`, all fetched directly this session. Plugin/class
names and default BT XML filenames cross-checked against the comments in
`ros-navigation/navigation2`'s `nav2_bringup/params/nav2_params.yaml`
(jazzy branch), fetched directly via raw GitHub URL this session — see
`examples/nav2-params-diffdrive.yaml` for that file's full content. Re-verify
before repeating any of this in a real project; Nav2's defaults have shifted
release to release (the controller default alone moved from DWB to MPPI).

## The BT Navigator

The BT Navigator is Nav2's top-level orchestrator: instead of a fixed state
machine, it executes an XML-defined **behavior tree** (action nodes,
condition nodes, control-flow nodes like `PipelineSequence`/`RoundRobin`,
and decorators) that decides, moment to moment, which server to call next —
compute a path, follow it, recover from a stall, replan. It exposes
`navigate_to_pose` and `navigate_through_poses` action servers
(`nav2_bt_navigator::NavigateToPoseNavigator` /
`NavigateThroughPosesNavigator`), each backed by a default BT XML shipped in
the `nav2_bt_navigator` package —
`navigate_to_pose_w_replanning_and_recovery.xml` and
`navigate_through_poses_w_replanning_and_recovery.xml` — which can be
overridden per-navigator in the params file or via a launch-time YAML
rewrite. Custom BT nodes are added through `plugin_lib_names`; Nav2's
built-in nodes are registered automatically. See
`examples/nav2-params-diffdrive.yaml`'s `bt_navigator` block.

## The task servers

The BT Navigator delegates real work to a set of independently
lifecycle-managed servers, each a plugin host:

- **Planner server** (`planner_server`) — computes a global path from robot
  pose to goal on the global costmap. Plugin examples: `NavfnPlanner`
  (grid-based, the long-standing default), `SmacPlanner2D`/`SmacPlannerHybrid`/
  `SmacPlannerLattice` (kinematically-aware variants), `ThetaStarPlanner`.
- **Controller server** (`controller_server`) — tracks the global path,
  producing `cmd_vel` at `controller_frequency` Hz on the local costmap.
  Plugin examples: `MPPIController` (model-predictive path integral, the
  current upstream default as of the jazzy-branch params file fetched this
  session), `DWBController` (Dynamic Window Approach, configurable via
  trajectory "critics"), `RegulatedPurePursuitController`, `GracefulController`,
  plus a `RotationShimController` wrapper for in-place-rotation-first
  behavior.
- **Smoother server** (`smoother_server`) — optional post-processing pass
  over a computed path (e.g. `SimpleSmoother`) to reduce sharp-angle
  artifacts before the controller tracks it.
- **Behavior server** (`behavior_server`) — recovery behaviors invoked by
  the BT on failure: `Spin`, `BackUp`, `DriveOnHeading`, `Wait`,
  `AssistedTeleop`.
- **Waypoint follower** (`waypoint_follower`) — sequences multiple
  `navigate_to_pose` calls for a waypoint list, with a
  `waypoint_task_executor_plugin` (e.g. `WaitAtWaypoint`) run at each stop.

Servers communicate with the BT Navigator over ROS 2 actions (long-running,
cancelable, feedback-bearing — path execution, spins, waypoint sequences)
and services (short request/response — costmap clearing, map save). This is
the same actions/services distinction the `ros2` skill covers generically;
Nav2 just fixes which interface each server exposes.

## Costmap 2D: two costmaps, layered

Nav2 maintains **two independent costmaps**, each a stack of layer plugins
combined into one occupancy-with-cost grid:

- **Global costmap** — covers the whole known map (`global_frame: map`),
  feeds the planner server. Typical layers: `static_layer` (the loaded map),
  `obstacle_layer` (2D obstacles from a laser/sensor), `inflation_layer`
  (cost gradient around obstacles so the planner prefers clearance).
- **Local costmap** — a smaller, robot-centered rolling window
  (`global_frame: odom`, `rolling_window: true`), feeds the controller
  server for reactive obstacle avoidance. Typical layers: `voxel_layer`
  (3D-aware obstacle marking/clearing from a range sensor, collapsed to 2D
  for costing) or `obstacle_layer`, plus its own `inflation_layer`.

Both costmaps share the same layer *types* (`nav2_costmap_2d::StaticLayer`,
`ObstacleLayer`, `VoxelLayer`, `InflationLayer`) but are configured, sized,
and updated independently — see
`examples/nav2-params-diffdrive.yaml`'s `local_costmap`/`global_costmap`
blocks and `references/tuning-guide.md` for the parameters that matter most.
Costmap2D will not finish activating until a complete TF tree is available
to it — this is the mechanism behind the "verify TF before tuning" key
directive in `SKILL.md`.

## Lifecycle manager

Every Nav2 server is a ROS 2 **managed lifecycle node**
(`unconfigured` → `inactive` → `active`, with `finalized` on shutdown). A
`lifecycle_manager` node owns an ordered `node_names` list and drives every
listed node through `configure` then `activate` in sequence at startup
(when `autostart: true` — the raw `lifecycle_manager` node defaults this to
`false`, but `nav2_bringup`'s launch files pass `autostart: true` by
default) and back down in reverse on shutdown. It also holds a `bond` to
each managed node; if a node stops responding within `bond_timeout`
(default 4.0 s, minimum recommended 0.3 s), the manager treats it as failed
and transitions the **entire** managed set back down rather than continuing
with a partially-alive stack. A server stuck at `inactive` (never reaching
`active`) is the most common lifecycle symptom — see
`references/common-failures.md`.

## Localization: AMCL vs slam_toolbox

Nav2 needs the `map`→`odom` half of the TF chain from somewhere; two
mutually-exclusive sources ship in the standard bringup:

- **AMCL** (`nav2_amcl`) — particle-filter localization **against a
  pre-built, static map** loaded by `nav2_map_server`. This is the default
  path (`slam:=false` in `bringup_launch.py`). AMCL does not publish
  `map`→`odom` until it has an initial pose estimate — set one via RViz's
  "2D Pose Estimate" tool or by publishing to `/initialpose` immediately
  after launch, every time.
- **slam_toolbox** (`online_async_launch.py`) — builds the map **online**
  while the robot drives, publishing both `/map` and the `map`→`odom`
  transform itself. Launched *instead of* `nav2_map_server` + `nav2_amcl`
  (`slam:=true` in `bringup_launch.py`, which conditionally skips the
  localization include) — running both localization sources at once is a
  conflict, not a redundancy. Use this to explore an unmapped space, then
  save the result with `nav2_map_server`'s `map_saver_cli` and switch back
  to AMCL for repeat runs. See the "SLAM-then-navigate" usage pattern in
  `SKILL.md`.

## The Simple Commander API

`nav2_simple_commander`'s `BasicNavigator` (Python) wraps the BT Navigator's
action interfaces so application code doesn't have to manage `ActionClient`
boilerplate directly:

```python
# status: unverified — method names confirmed via direct fetch of
# docs.nav2.org/commander_api/index.html this session; re-verify exact
# signatures/imports against that page before use.
from nav2_simple_commander.robot_navigator import BasicNavigator

nav = BasicNavigator()
nav.waitUntilNav2Active()          # blocks until the stack is active
nav.goToPose(goal_pose_stamped)    # non-blocking
while not nav.isTaskComplete():
    feedback = nav.getFeedback()
result = nav.getResult()
```

`goToPose()`/`goThroughPoses()`/`followWaypoints()` are all non-blocking, so
a single-threaded script can poll `isTaskComplete()` and react to feedback
without a separate executor thread. See the "send goals programmatically"
usage pattern in `SKILL.md`.
