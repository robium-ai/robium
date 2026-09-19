# Scaffold patterns

Optional repo shapes after selecting adaptation, partial reuse, or a fresh
build. Do not scaffold for a try-only request or copy an entire app merely
because one component fits. Follow the chosen [reuse path](reuse-paths.md),
then prune anything the first working slice does not need.

The `tests/` directories below are optional. Reuse existing checks; add automated
coverage for meaningful risk or repeatable regressions, not to fill the tree.

Keep tiny-demo decisions inline; applications with meaningful architecture
choices can use a concise `docs/architecture-brief.md`.
Learning capture belongs to Robium's sibling `learnings/` tree and hooks rather
than an application-local ritual.

The env layer (Dockerfile vs `pyproject.toml`) is decided by the `environments`
skill; both trees below show the common case.

## ROS 2 application (navigation golden path)

For a mobile robot navigating in Gazebo with Nav2. A ROS 2 workspace with a
`src/` colcon layout, one package per concern.

```
my-nav-robot/
├── docs/
│   └── architecture-brief.md        # concise decision record
├── docker/
│   ├── Dockerfile                   # selected ROS 2 base + deps (environments skill)
│   └── compose.yaml                 # sim + nav + viz services
├── src/                             # colcon workspace source
│   ├── my_robot_description/        # URDF/xacro, meshes: the robot model
│   │   ├── urdf/
│   │   ├── meshes/
│   │   └── launch/                  # spawn/description launch
│   ├── my_robot_bringup/            # top-level launch + params, ties it together
│   │   ├── launch/                  # bringup.launch.py (sim + nav + viz)
│   │   └── config/                  # nav2_params.yaml, ros2 params
│   ├── my_robot_navigation/         # Nav2 config: costmaps, planners, BT
│   │   ├── config/
│   │   ├── behavior_trees/
│   │   └── maps/
│   └── my_robot_sim/                # Gazebo worlds + spawn glue
│       ├── worlds/
│       └── models/
├── tests/                           # smoke + launch tests (testing skill)
└── README.md
```

**What each dir holds**
- `*_description`: the robot's URDF/xacro, meshes, and the launch that
  publishes the model. One source of truth for the robot's geometry/frames.
- `*_bringup`: the composition layer; the launch file that starts sim + Nav2 +
  visualization together, plus the parameter YAMLs. Where a new user starts.
- `*_navigation`: everything Nav2 (`navigation` skill): costmap configs, planner and
  controller params, behavior trees, saved maps.
- `*_sim`: Gazebo (`gazebo` skill): world files, spawn models, sim-only glue.
- `docker/`: the reproducible environment (`environments` skill): a
  compatibility-checked ROS 2 base image and a compose file wiring services.
- `tests/`: smoke and launch tests (`testing` skill): "does the robot reach a
  goal in sim" as a regression.

## LeRobot application (manipulation golden path)

For training and evaluating a manipulation policy. A Python project managed by
`uv` (no colcon), organized around the data → train → eval loop.

```
my-arm-policy/
├── docs/
│   └── architecture-brief.md        # concise decision record
├── pyproject.toml                   # uv-managed deps (environments skill)
├── uv.lock
├── src/
│   └── my_policy/
│       ├── configs/                 # policy + training configs (ACT, Diffusion, SmolVLA…)
│       ├── datasets/                # LeRobotDataset prep / loading glue (lerobot)
│       ├── train.py                 # training entry point (lerobot)
│       ├── eval.py                  # in-sim evaluation entry point
│       └── env/                     # sim/hardware env wrappers
├── data/                            # local datasets / cache (gitignored; data skill)
├── outputs/                         # checkpoints, logs, eval videos (gitignored)
├── notebooks/                       # exploration (optional)
├── tests/                           # smoke tests: dataset loads, 1-step train runs
└── README.md
```

**What each dir holds**
- `src/my_policy/configs`: training and policy hyperparameter configs; which
  policy family (ACT / Diffusion / SmolVLA / π0) and its settings.
- `src/my_policy/datasets`: LeRobotDataset preparation, loading, transforms,
  and recording glue belong to `lerobot`; Hub authentication and transfers go
  through `huggingface`, and sourcing strategy through `data`.
- `src/my_policy/{train,eval}.py`: the `lerobot` training and evaluation
  entry points; keep them thin, config-driven.
- `src/my_policy/env`: wrappers around the sim (or, later, real hardware).
  Add `isaac-sim`/`isaac-lab` here **only if the GPU floor is met**; otherwise
  LeRobot's own sim.
- `data/` and `outputs/`: large, regenerable, git-ignored.
- `pyproject.toml` + `uv.lock`: the reproducible env (`environments` skill);
  uv is the default for the manipulation path since much of it is CPU-friendly
  Python and doesn't need the full ROS 2 Docker apparatus.

## Adapting

- A real-hardware version of either app keeps the tree and swaps the `*_sim` /
  `env` directory for a hardware-driver package/module.
- A hybrid (learned policy running inside a ROS 2 system) starts from the ROS 2
  tree and adds a `my_policy` package that wraps the LeRobot inference.
- Prune aggressively for an MVP; a single-package ROS 2 demo doesn't need four
  packages. Add `docs/architecture-brief.md` only when the application has
  meaningful decisions worth retaining beyond an inline explanation.
