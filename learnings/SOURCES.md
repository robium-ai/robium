# Robium — Sample Repos to Learn & Distill

A living list of example repositories — framework usages, sample robot apps, vendor example collections, and community projects — that Robium skills can learn from and distill. The goal: mine these for real patterns, gotchas, and reference material to harden skills (same spirit as the learnings loop, but sourced from the ecosystem instead of our own trials).

**How to use:** add candidates under the right category with a one-line "why". When we actually explore one, change its status and capture what was distilled (which skill(s) it fed, link to the learnings entry or skill changelog). Statuses: `todo` (not yet explored) → `exploring` → `distilled` (fed into a skill) or `dropped` (not worth it — say why, so we don't re-triage it). A distilled repo that has moved on far past the commit we crawled gets `recheck`.

**Crawl records (engine-maintained):** when a repo reaches `exploring` or beyond, its row gains a crawl record in the Notes column or a sub-bullet: `crawled: YYYY-MM-DD @ <short-sha> → fed: <skill(s) / observation ids>`. Re-crawls diff the repo against the recorded SHA — only what changed since gets re-mined, and distillations whose source lines changed upstream get flagged for re-verification (the external analog of the staleness sweep).

*Started 2026-08-01. All repos verified to exist as of that date unless marked (unverified).*

## ROS 2 core & patterns

| Repo | What / why | Status |
|---|---|---|
| [ros2/examples](https://github.com/ros2/examples) | Canonical minimal examples for every core API (pub/sub, services, actions, launch) in C++/Python. The "official idiom" baseline for the ros2 skill. `crawled: 2026-08-02 @ 90a5b64 → fed: obs-ros2-001, obs-ros2-002, obs-ros2-003, obs-ros2-004` | distilled |
| [ros2/demos](https://github.com/ros2/demos) | Official demos one level up from examples: QoS, composition, lifecycle, intra-process. Good source of "when to use which" judgment. | todo |
| [ros-controls/ros2_control_demos](https://github.com/ros-controls/ros2_control_demos) | Vendor example set for ros2_control: hardware interfaces, controllers, simulation integration. Robium currently has no controls-specific skill — good probe for whether one is needed. | todo |
| [alsora/ros2-code-examples](https://github.com/alsora/ros2-code-examples) | Community tutorial/example collection — useful contrast between official idiom and how people actually write ROS 2. | todo |

## Navigation & mobile robots

| Repo | What / why | Status |
|---|---|---|
| [ros-navigation/navigation2](https://github.com/ros-navigation/navigation2) | Nav2 itself; `nav2_bringup` inside is the reference launch/bringup pattern everyone copies. Primary source for the nav2 skill. | todo |
| [ros-navigation/navigation2_tutorials](https://github.com/ros-navigation/navigation2_tutorials) | Official tutorial code: custom planners/controllers/behaviors, SLAM integration. Maps directly onto nav2 skill "usage patterns". `crawled: 2026-08-02 @ 050a2d6 → fed: obs-nav2-001, obs-nav2-002, obs-nav2-003, obs-nav2-004`. License varies per package (no top-level LICENSE): most cited packages BSD-3-Clause, Apache-2.0 (sam_bot pkg verified). | distilled |
| [ROBOTIS-GIT/turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations) | The flagship-platform sim stack nav-trial was built around — worth mining for what we did differently and why. `crawled: 2026-08-02 @ 9be186f (main branch) → fed: obs-gazebo-001, obs-gazebo-002, obs-gazebo-004, obs-ros2-005, obs-simulation-002` (obs-simulation-001 renumbered obs-ros2-005; obs-simulation-003 renumbered obs-gazebo-004 — post-review re-placement, see task-9 report). License: Apache-2.0 (repo root LICENSE + per-package `<license>` tags, confirmed). Notes: comparison set: tb3-sim + tb4-sim (run 2026-08-02). | distilled |
| [linorobot/linorobot2](https://github.com/linorobot/linorobot2) | Popular community full-stack AMR (2WD/4WD/mecanum): URDF → ros2_control → Nav2, sim + real hardware. A complete "someone's real robot app" specimen. | todo |
| [husarion/rosbot_ros](https://github.com/husarion/rosbot_ros) | Vendor robot stack (ROSbot) — Docker-first ROS 2 setup from a company that leans hard into containerized robotics, close to our own compose-profile approach. | todo |
| [turtlebot/turtlebot4_simulator](https://github.com/turtlebot/turtlebot4_simulator) | Clearpath's TurtleBot 4 sim — the "modern successor" bringup style vs TB3; useful A/B for the environments + nav2 skills. **URL corrected 2026-08-02**: the org is `turtlebot`, not `turtlebot4` — the previously-listed `turtlebot4/turtlebot4_simulator` does not exist (`git clone` returned "Repository not found"; confirmed via GitHub search). `crawled: 2026-08-02 @ b7d0f3b (jazzy branch, repo's default — no main/master exists) → fed: obs-gazebo-001, obs-gazebo-002, obs-gazebo-003, obs-gazebo-004, obs-ros2-005, obs-simulation-002` (obs-simulation-001 renumbered obs-ros2-005; obs-simulation-003 renumbered obs-gazebo-004 — post-review re-placement, see task-9 report). License: Apache-2.0 (repo root LICENSE + per-package `<license>` tags, confirmed). Notes: comparison set: tb3-sim + tb4-sim (run 2026-08-02). | distilled |
| [open-rmf/rmf_demos](https://github.com/open-rmf/rmf_demos) | Multi-robot fleet coordination demos (Open-RMF). Beyond current catalog scope — park until a multi-robot skill is on the table. | todo |

## Manipulation

| Repo | What / why | Status |
|---|---|---|
| [moveit/moveit2_tutorials](https://github.com/moveit/moveit2_tutorials) | Official MoveIt 2 tutorial code — motion planning, pick/place, servoing. Robium has no moveit skill yet; this is the evidence base for whether/what to build. | todo |
| [moveit/mujoco_ros2_control](https://github.com/moveit/mujoco_ros2_control) | New official bridge: MuJoCo as a ros2_control sim backend. Directly relevant to plugin issue #1 (mujoco skill) — connects MuJoCo world to ROS 2 world. | todo |
| [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) | The SO-100/SO-101 arm hardware repo (what vla-trial simulates). Source of truth for models, assembly, calibration conventions. | todo |

## Simulation

| Repo | What / why | Status |
|---|---|---|
| [gazebosim/ros_gz](https://github.com/gazebosim/ros_gz) | The ROS 2 ↔ Gazebo bridge, including `ros_gz_sim_demos` — canonical patterns for the gazebo skill's bridge guidance. | todo |
| [google-deepmind/mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie) | Curated, quality-graded MJCF models of real robots (incl. SO-101 family). Both a resource to point users at and a model-quality rubric worth stealing for test-assets. | todo |
| [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) | MuJoCo itself — sample tasks and python bindings examples under `python/` and `model/`. Feeds the future mujoco skill (issue #1). | todo |

## NVIDIA Isaac stack

| Repo | What / why | Status |
|---|---|---|
| [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) | The robot-learning framework on Isaac Sim; `source/standalone` + task suites are the reference examples for the isaac-lab skill. | todo |
| [isaac-sim/IsaacSim](https://github.com/isaac-sim/IsaacSim) | Isaac Sim is now open-source on GitHub — standalone python examples + extension examples. Check what the isaac-sim skill says about install paths vs this repo's current story. | todo |
| [NVIDIA-ISAAC-ROS/isaac_ros_common](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common) | Entry point to the Isaac ROS GEM ecosystem (nvblox, cuMotion, VSLAM…) — NVIDIA's opinionated Docker/dev-container workflow is itself worth distilling. | todo |
| [NVIDIA-Omniverse/IsaacSim-ros_workspaces](https://github.com/NVIDIA-Omniverse/IsaacSim-ros_workspaces) | Official Isaac Sim ↔ ROS 2 workspace glue — the "connect the two worlds" reference. | todo |

## Robot learning & VLA

| Repo | What / why | Status |
|---|---|---|
| [huggingface/lerobot](https://github.com/huggingface/lerobot) | Already central to manip/vla trials — but its `examples/` tree (incl. SmolVLA tutorials) keeps evolving; periodic re-mining should feed the lerobot skill. | todo |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | Open π0/π0.5 VLA models + fine-tuning recipes — the other major open VLA codebase besides SmolVLA; good comparative source for VLA-related guidance. | todo |
| [NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) | GR00T N1.x humanoid foundation model — NVIDIA's take on the VLA fine-tune/eval loop, bridges the Isaac and learning sides of the catalog. | todo |
| [openvla/openvla](https://github.com/openvla/openvla) | The original open VLA reference implementation — older but the pattern-setter many downstream repos copy. Lower priority than openpi. | todo |

## Visualization

| Repo | What / why | Status |
|---|---|---|
| [foxglove/examples](https://github.com/foxglove/examples) | Official Foxglove code examples — layouts, websocket bridges, custom panels. Direct feed for the foxglove skill. | todo |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | Rerun's `examples/` include several robotics ones (URDF, datasets, live streams) — direct feed for the rerun skill. | todo |

## Complete platforms & full-stack apps (bigger bites)

| Repo | What / why | Status |
|---|---|---|
| [hello-robot/stretch_ros2](https://github.com/hello-robot/stretch_ros2) | A commercial mobile manipulator's full ROS 2 stack — rare public example of nav + manip integrated on one real product. (unverified today) | todo |
| [f1tenth/f1tenth_gym](https://github.com/f1tenth/f1tenth_gym) | Autonomous racing gym used by a large academic community — compact, well-tested sim app outside the Nav2 mold. (unverified today) | todo |
| [autowarefoundation/autoware](https://github.com/autowarefoundation/autoware) | The biggest open ROS 2 application in existence (self-driving). Not a distill target per se — a place to study how a huge ROS 2 system is organized when a user asks "how do the pros structure this". | todo |

## Meta / discovery (where to find more)

- [fkromer/awesome-ros2](https://github.com/fkromer/awesome-ros2) — the standing ROS 2 awesome list; re-sweep occasionally.
- [jslee02/awesome-robotics-libraries](https://github.com/jslee02/awesome-robotics-libraries) — broader library-level curation.
- GitHub topics worth periodic sweeps: [nav2](https://github.com/topics/nav2), [moveit2](https://github.com/topics/moveit2), [mujoco](https://github.com/topics/mujoco?o=desc&s=updated), [smolvla](https://github.com/topics/smolvla) — sort by recently-updated to catch new community sample apps.

## Triage inbox

New candidates land here first, one line each, before earning a category row. (empty)
