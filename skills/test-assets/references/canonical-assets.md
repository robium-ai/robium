# Canonical test assets — the verified catalog

Well-known public assets to test robotics apps against: worlds, robot models,
datasets, and recordings. Every entry carries a citation line saying how and
when it was verified — keep that discipline when adding entries (see the end
of this file). Licenses shown were read from the upstream API/card on the
verification date; re-confirm at adoption time before vendoring.

## Worlds

| Asset | Upstream | License | Canonical for | Verified |
|---|---|---|---|---|
| TurtleBot3 House | [ROBOTIS-GIT/turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations) | Apache-2.0 | Indoor/house nav testing; the Nav2-tutorial-canonical world | GitHub API 2026-07-18: 515★, pushed 2025-07-14, SPDX Apache-2.0 |
| Tugbot in Warehouse (OpenRobotics) | [Gazebo Fuel](https://app.gazebosim.org/OpenRobotics/fuel/worlds/Tugbot%20in%20Warehouse) | read from Fuel page at adoption | Industrial/warehouse scenes in modern gz | Fuel API 2026-07-18: 47,114 downloads — most-downloaded warehouse world |
| AWS RoboMaker Small House | [aws-robotics/aws-robomaker-small-house-world](https://github.com/aws-robotics/aws-robomaker-small-house-world) | check repo at adoption | Richer furnished multi-room house — **Gazebo-Classic era: verify modern-gz load before adopting** | GitHub API 2026-07-18: 322★, last pushed 2024-07-26 |
| AWS RoboMaker Small Warehouse | [aws-robotics/aws-robomaker-small-warehouse-world](https://github.com/aws-robotics/aws-robomaker-small-warehouse-world) | check repo at adoption | The most-recognized open warehouse world — **same Gazebo-Classic caveat** | GitHub API 2026-07-18: 487★, last pushed 2024-07-26 |

## Robot models

| Asset | Upstream | License | Canonical for | Verified |
|---|---|---|---|---|
| TurtleBot3 burger/waffle | [ROBOTIS-GIT/turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations) | Apache-2.0 | Mobile-base/Nav2 testing | GitHub API 2026-07-18 (same repo as house world) |
| Unitree Go2 (MJCF) | [google-deepmind/mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie), dir `unitree_go2` | per-model (repo SPDX: NOASSERTION — check the model's own license file) | Quadruped testing in MuJoCo | GitHub API 2026-07-18: dir listing confirms unitree_go2 |
| Unitree Go2/G1 (URDF, ROS) | [unitreerobotics/unitree_ros](https://github.com/unitreerobotics/unitree_ros) | BSD-3-Clause | Official Unitree descriptions for ROS/Gazebo use | GitHub API 2026-07-18: 1,477★, pushed 2026-07-08, SPDX BSD-3-Clause |
| Unitree G1 (MJCF) | mujoco_menagerie dir `unitree_g1`; also [unitreerobotics/unitree_mujoco](https://github.com/unitreerobotics/unitree_mujoco) (BSD-3-Clause) | per-model (Menagerie) | Humanoid testing in MuJoCo | GitHub API 2026-07-18: dir listing confirms unitree_g1; unitree_mujoco 1,089★ |
| SO-101 arm | [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100), `Simulation/SO101/` | Apache-2.0 | The LeRobot-ecosystem arm; upstream source of the SO-101 sim model | GitHub API 2026-07-18: 6,821★, SPDX Apache-2.0, dir listing confirms Simulation/SO101. Note: Menagerie carries only the SO-**100** (`trs_so_arm100`) |

## Datasets

| Asset | Upstream | License | Canonical for | Verified |
|---|---|---|---|---|
| svla_so101_pickplace | [lerobot/svla_so101_pickplace](https://huggingface.co/datasets/lerobot/svla_so101_pickplace) | Apache-2.0 (card tag) | The canonical SO-101 sample: official LeRobot org, SmolVLA-tutorial dataset | HF API 2026-07-18: 42 likes — most-liked SO-101 dataset; every higher-download alternative is a 0-like community upload. Runner-up (sim-MuJoCo shape, inspect before trust): szk1ck/so101-pickplace-sim-mujoco |
| pusht | [lerobot/pusht](https://huggingface.co/datasets/lerobot/pusht) | MIT (card tag) | The CI-sized LeRobot standard for train-smoke tests | HF API 2026-07-18: 18,181 downloads, 54 likes |

## Recordings (replay fixtures)

| Asset | Upstream | License | Canonical for | Verified |
|---|---|---|---|---|
| EuRoC MAV sequences | [ETH ASL dataset page](https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets) | check page at adoption | Canonical VIO/drone rosbags that "just replay" | HTTP 200 on 2026-07-18 — re-verify format/license at adoption |
| TUM RGB-D sequences | [TUM CVG dataset page](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) | check page at adoption | The RGB-D SLAM classic, rosbag downloads | HTTP 200 on 2026-07-18 — re-verify at adoption |
| Foxglove sample MCAPs | [foxglove.dev/examples](https://foxglove.dev/examples) | check page at adoption | Viz-tooling scenarios (foxglove/rerun skills) | HTTP 200 on 2026-07-18 — re-verify at adoption |

## Known gaps

- **No canonical public Nav2/TB3 rosbag exists** — nav regression bags are
  always self-recorded; produce them with a seeded generator script (see the
  sourcing funnel in the skill body) rather than hunting for a download.
- **Drone assets unpicked** — no vertical yet (px4 is future work); the
  matrix row is an honest gap, not an oversight.
- **Legged robots have models here but no robium skill coverage** — Go2/G1
  are test assets awaiting a future legged vertical.

## Adding an entry

1. Verify the asset against its live source (API call, direct fetch) — never
   from memory — and write the citation line with method + date.
2. Read the license from the upstream repo/card at adoption time; an asset
   whose license forbids redistribution stays pointer-mode only.
3. State what the asset is canonical *for* — an entry without a clear
   testing role doesn't belong in the catalog.
