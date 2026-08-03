# Common failures: the "robot won't move" diagnostic checklist

Nav2 does not have one official "why won't my robot move" troubleshooting
page as of 2026-07-10 — a guessed URL
(`docs.nav2.org/troubleshooting/index.html`) 404s, and a site-scoped web
search for one surfaced only a *build* troubleshooting guide plus one
useful runtime note (quoted and cited below). This checklist is this
skill's own synthesis, built from the architecture facts in
`references/nav2-architecture.md` (each individually direct-fetched from
docs.nav2.org or the `navigation2` GitHub repo on 2026-07-10 — see that
file's Sources line) plus the one runtime note found via web search:
docs.nav2.org's build-troubleshooting guide states "If you see errors on
startup about map or odom frame not existing, remember to activate drivers
(or gazebo for simulation) and set an initial pose in map frame, as
Costmap2D will block activation until a full TF tree is available" — found
via a search-engine result snippet, not a direct fetch of that exact
sentence in context; re-verify against
`https://docs.nav2.org/development_guides/build_docs/build_troubleshooting_guide.html`
directly before treating it as gospel.

Work through these in order — each step assumes the previous ones passed.
This mirrors the "verify TF before tuning" key directive in `SKILL.md`:
most "won't move" reports are environment/wiring problems, not planner or
controller bugs.

## 1. Are all lifecycle nodes actually active?

```bash
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
```

- **Stuck at `unconfigured` or `inactive`**: the `lifecycle_manager` never
  activated it. Check `autostart` — the raw `lifecycle_manager` node
  defaults `autostart` to `false` (nav2_bringup's launch files override
  this to `true`, but a custom launch setup may not); check that the node
  is actually listed in the relevant `lifecycle_manager`'s `node_names`.
- **Nodes activate, then the whole stack transitions back down together
  a few seconds later**: a `bond_timeout` failure — one managed node
  stopped responding (crashed, deadlocked, or is just slow to start under
  load) and the lifecycle manager tore down every node in response, not
  just the failed one. Check that node's own log for the actual crash/error
  first, don't chase the ones that were torn down as a side effect.
- **Bringup aborted (`Failed to bring up all requested nodes. Aborting
  bringup`)**: most often the global costmap timed out (~60 s) waiting for
  `map`→`base_link` because no initial pose was published yet (AMCL silent
  — step 2 below), and the manager then leaves every later node
  (`planner_server`, `bt_navigator`, …) permanently `inactive` even after
  localization recovers. Prevent it by publishing `/initialpose`
  immediately after launch. Recover without a restart by walking the
  remaining nodes manually in manager order — `ros2 lifecycle set /<node>
  configure` (if unconfigured) then `activate` — because re-calling
  `manage_nodes {command: 0}` re-aborts on the already-active nodes.
  Verified 2026-07-11 (nav-trial).

## 2. Is the TF tree complete: map → odom → base_link?

```bash
ros2 run tf2_ros tf2_echo map base_link
```

- **"could not find a connection"**: the chain is broken somewhere. Check
  each hop separately (`tf2_echo map odom`, `tf2_echo odom base_link`) to
  find which link is missing — `map`→`odom` comes from AMCL or
  slam_toolbox, `odom`→`base_link` comes from the robot's own odometry
  source (wheel odometry node, or `robot_localization` if fused with an
  IMU — that fusion setup is the `ros2`/robot-description side, not this
  skill's).
- **`map`→`odom` specifically missing, AMCL is running**: AMCL has not
  received an initial pose yet. This is silent, not an error — set one via
  RViz's "2D Pose Estimate" tool or by publishing to `/initialpose`. See
  `references/nav2-architecture.md`'s localization section.
- **Costmaps never finish activating even though other lifecycle nodes
  did**: Costmap2D blocks its own activation until it sees a complete TF
  tree — this is the same underlying cause as the missing-initial-pose case
  above, just observed from the costmap side instead of directly from
  `tf2_echo`.

## 3. Does every node agree on `use_sim_time`?

```bash
ros2 param get /controller_server use_sim_time
ros2 param get /planner_server use_sim_time
ros2 param get /bt_navigator use_sim_time
# ...repeat for every Nav2 node and any TF broadcaster (robot_state_publisher, etc.)
```

In simulation, `/clock` must be publishing (confirm Gazebo is actually
running and unpaused) and every one of these must read `true`; on real
hardware every one must read `false`. A single node left on the wrong
value produces TF timestamps that look like they're from the future or the
past relative to the rest of the system — action goals get rejected and
costmaps refuse to update, which presents identically to a broken TF chain
from step 2. Rule this out explicitly rather than re-checking TF a second
time.

## 4. Is the costmap actually seeing obstacles?

```bash
ros2 topic hz /scan               # or whatever topic observation_sources points at
ros2 topic echo /local_costmap/costmap --once
```

- **No messages on the sensor topic**: the sensor driver (or Gazebo sensor
  plugin) isn't running, or `observation_sources`'s configured topic name
  in `examples/nav2-params-diffdrive.yaml` doesn't match the sensor's real
  topic name (a remap mismatch, not a Nav2 bug).
- **Costmap is entirely "unknown" or entirely "free" with real obstacles
  nearby**: check `static_layer`'s `map_subscribe_transient_local` is set
  (so it actually receives the map, which is published transient-local) and
  that the sensor's `data_type`/topic in the relevant costmap's
  `observation_sources` block is correct.

## 5. Is a goal actually being accepted?

```bash
ros2 action list -t | grep navigate
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{...}"
```

- **Action not listed**: `bt_navigator` isn't active — back to step 1.
- **Goal accepted, then immediately aborted**: check the BT Navigator's log
  for which BT node failed — a missing/misconfigured default BT XML path,
  or a downstream server (planner/controller) rejecting the request, is far
  more common than the BT logic itself being wrong.
- **Goal accepted but nothing happens, no abort**: likely `general_goal_checker`
  already considers the goal satisfied (`xy_goal_tolerance`/`yaw_goal_tolerance`
  too loose for the actual distance) or the controller is silently producing
  zero-velocity trajectories — see step 6.

## 6. Is `cmd_vel` actually being published, and is the base listening?

```bash
ros2 topic hz /cmd_vel
ros2 topic echo /cmd_vel
```

- **Nothing published**: the controller isn't producing a trajectory it
  considers valid — check `controller_server`'s log for "no valid
  trajectory found" (often a footprint/costmap problem from step 4, not the
  controller itself) or for `min_x_velocity_threshold`/
  `min_theta_velocity_threshold` zeroing out a legitimately small commanded
  velocity near the goal.
- **`cmd_vel` publishing non-zero values but the robot doesn't move**:
  this is no longer a Nav2 problem — check `velocity_smoother`'s output
  topic actually matches what the robot's base controller subscribes to
  (a remap mismatch between `cmd_vel_smoothed`/`cmd_vel` is a common one),
  and that the base driver itself is running and not e-stopped.
