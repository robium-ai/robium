<!-- status: unverified -->
<!-- A filled architecture brief for a hypothetical robot, illustrating the
     brief-template. Not from a real trial run — promote to verified once an
     actual app is built from a brief like this. -->

# Architecture Brief — WarehouseBot (diff-drive warehouse navigator)

**Date:** 2026-07-10   **Status:** draft
**Author:** robium-architect subagent

## 1. Requirements

- **Robot type:** differential-drive mobile base (~40 cm footprint), 2D lidar +
  wheel odometry, no manipulator.
- **Task:** navigate autonomously between named pick/drop stations in a
  warehouse, avoiding dynamic obstacles (people, carts).
- **Hardware:** none yet — **sim-first**; a real base is a later phase.
- **Sim vs real:** MVP must run entirely in simulation.
- **GPU:** *assumed none* on the dev machine (laptop). **Assumption** — not
  confirmed; feeds open risks.
- **Local vs remote:** developed on a macOS laptop, so the stack runs in Docker;
  a headless workstation is a possible later target.

## 2. Chosen stack + reasoning

| Layer | Choice | Version | Why (and what was rejected) |
|---|---|---|---|
| Middleware | ROS 2 | Jazzy Jalisco | LTS to 2029; standard nav ecosystem. Lyrical Luth (newer LTS, to 2031) rejected for now — Nav2 has no released binaries for it yet. Kilted rejected — non-LTS, ends 2026. |
| Simulator | Gazebo | Harmonic | Officially paired with Jazzy; no GPU needed. Isaac Sim rejected — GPU-gated, overkill for a lidar nav demo. |
| Navigation | Nav2 | (Jazzy release) | The standard ROS 2 nav stack; costmaps + planners + BT out of the box. Rolling our own rejected — no reason to. |
| Visualization | RViz2 (dev) + Foxglove (remote) | — | RViz2 locally for quick checks; Foxglove for the eventual headless workstation. Rerun rejected — not needed for classical nav. |
| Environment | Docker | Jazzy base image | Dev machine is macOS, which can't run the native ROS 2 + Gazebo desktop cleanly; Docker gives identical local/remote repro. uv rejected — this is a compiled ROS 2 workspace, not pure Python. |

Decisions trace to the architect trees: middleware → ROS 2 (mobile multi-node
system); simulator → Gazebo (no GPU); no training framework (classical nav).

## 3. Module breakdown

- **warehousebot_description** — URDF/xacro of the diff-drive base, lidar + wheel
  frames, meshes. Publishes the robot model. In/out: none / `robot_description`,
  TF.
- **warehousebot_sim** — Gazebo world (warehouse layout, shelves, spawn points)
  and spawn glue. In/out: `robot_description` / simulated `/scan`, `/odom`, TF.
- **warehousebot_navigation** — Nav2 config: costmaps (lidar-based obstacle
  layer + inflation), NavFn/Smac planner, DWB/MPPI controller, behavior tree,
  saved warehouse map. In/out: `/scan`,`/odom`,`/map`,goal / `/cmd_vel`.
- **warehousebot_bringup** — top-level launch (sim + nav + viz) and params.
  In/out: launch args / the running system.

## 4. Comms plan

Standard ROS 2 topics, single robot, all in-process for the MVP.

| Topic | Type | Rate | Producer → Consumer |
|---|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | ~10 Hz | Gazebo lidar → Nav2 costmap |
| `/odom` | `nav_msgs/Odometry` | ~30 Hz | Gazebo diff-drive → Nav2, TF |
| `/cmd_vel` | `geometry_msgs/Twist` | ~20 Hz | Nav2 controller → base |
| `/map` | `nav_msgs/OccupancyGrid` | latched | map_server → Nav2 |
| goal | `nav2` action (`NavigateToPose`) | on demand | app → Nav2 BT |

No cross-host transport needed for the MVP. If the fleet grows to multiple
robots later, revisit with the `integration` skill (namespacing, DDS discovery).

## 5. Environment strategy

Docker, single `Dockerfile` on a ROS 2 Jazzy base plus Gazebo Harmonic and Nav2
from ROS vendor packages; a `compose.yaml` running sim + nav + viz. macOS dev
uses an X/Wayland forward or Foxglove for viewing. The same image runs on the
headless workstation later — identical repro is the reason Docker was chosen
over a native workspace. No GPU passthrough (none required). Detail: route to
the `environments` skill.

## 6. Data plan

No learned components → no datasets. Data artifacts are: the saved warehouse
occupancy `map` (built once via SLAM in sim, then reused), Nav2 param YAMLs, and
recorded rosbags for regression. Rosbags and maps are versioned in-repo; large
bags gitignored. No Hub involvement.

## 7. Robium skills per build phase

| Phase | Skill(s) |
|---|---|
| Environment setup | environments |
| Robot model + bringup | ros2 |
| Simulation world | gazebo |
| Mapping + navigation | nav2 |
| Visualization | visualization → rviz2 (local), foxglove (remote) |
| Smoke/regression tests | testing |

## 8. Open risks

- **GPU availability unconfirmed** — the design assumes no GPU and stays on
  Gazebo, which is fine. Blocks nothing for this app, but confirm before any
  future perception/learning phase that might want Isaac. *Resolve:* check
  `nvidia-smi` on the dev/target machine.
- **Dynamic-obstacle avoidance in sim ≠ real** — Gazebo pedestrians are scripted;
  real warehouse traffic is messier. Blocks confidence in the avoidance tuning.
  *De-risk:* keep the costmap/controller params in `warehousebot_navigation`
  easy to retune; plan a hardware validation phase.
- **macOS + Gazebo rendering** — GUI rendering under Docker on macOS can be slow
  or flaky. Blocks smooth local dev. *De-risk:* prefer Foxglove/headless sim for
  day-to-day; use RViz2 sparingly, or move dev to the Linux workstation early.
- **ROS 2 Jazzy version pins** — Nav2/Gazebo package versions assumed compatible
  on the Jazzy line but not yet built. *Resolve:* stand up the Docker image
  first and confirm `colcon build` is clean before writing app code.
