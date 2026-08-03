# Scaffold patterns

Starting repo layouts for the two golden paths. Copy the tree, rename packages
to your app, prune directories you don't need. Two invariants hold for every
robium app regardless of stack:

- `docs/architecture-brief.md` — the living architecture contract. Fixed
  location; every build phase and the `robium-architect` subagent expect it here.
- `learnings/YYYY-MM-DD.md` — dated friction notes captured during building,
  later absorbed back into robium skills by `skill-author`.

The env layer (Dockerfile vs `pyproject.toml`) is decided by the `environments`
skill; both trees below show the common case.

## ROS 2 application (navigation golden path)

For a mobile robot navigating in Gazebo with Nav2. A ROS 2 workspace with a
`src/` colcon layout, one package per concern.

```
my-nav-robot/
├── docs/
│   └── architecture-brief.md        # the contract (required)
├── learnings/                       # dated friction notes for skill-author
├── docker/
│   ├── Dockerfile                   # ROS 2 Jazzy base + deps (environments skill)
│   └── compose.yaml                 # sim + nav + viz services
├── src/                             # colcon workspace source
│   ├── my_robot_description/        # URDF/xacro, meshes — the robot model
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
- `*_description` — the robot's URDF/xacro, meshes, and the launch that
  publishes the model. One source of truth for the robot's geometry/frames.
- `*_bringup` — the composition layer: the launch file that starts sim + Nav2 +
  visualization together, plus the parameter YAMLs. Where a new user starts.
- `*_navigation` — everything Nav2 (`nav2` skill): costmap configs, planner and
  controller params, behavior trees, saved maps.
- `*_sim` — Gazebo (`gazebo` skill): world files, spawn models, sim-only glue.
- `docker/` — the reproducible environment (`environments` skill): a Jazzy base
  image and a compose file wiring the services.
- `tests/` — smoke and launch tests (`testing` skill): "does the robot reach a
  goal in sim" as a regression.

## LeRobot application (manipulation golden path)

For training and evaluating a manipulation policy. A Python project managed by
`uv` (no colcon), organized around the data → train → eval loop.

```
my-arm-policy/
├── docs/
│   └── architecture-brief.md        # the contract (required)
├── learnings/                       # dated friction notes for skill-author
├── pyproject.toml                   # uv-managed deps (environments skill)
├── uv.lock
├── src/
│   └── my_policy/
│       ├── configs/                 # policy + training configs (ACT, Diffusion, SmolVLA…)
│       ├── datasets/                # dataset prep / loading glue (huggingface delegation)
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
- `src/my_policy/configs` — training and policy hyperparameter configs; which
  policy family (ACT / Diffusion / SmolVLA / π0) and its settings.
- `src/my_policy/datasets` — glue for fetching and shaping datasets; Hub
  pulls/pushes go through the `huggingface` delegation, sourcing strategy
  through the `data` skill.
- `src/my_policy/{train,eval}.py` — the `lerobot` training and evaluation
  entry points; keep them thin, config-driven.
- `src/my_policy/env` — wrappers around the sim (or, later, real hardware).
  Add `isaac-sim`/`isaac-lab` here **only if the GPU floor is met**; otherwise
  LeRobot's own sim.
- `data/` and `outputs/` — large, regenerable, git-ignored.
- `pyproject.toml` + `uv.lock` — the reproducible env (`environments` skill);
  uv is the default for the manipulation path since much of it is CPU-friendly
  Python and doesn't need the full ROS 2 Docker apparatus.

## Adapting

- A real-hardware version of either app keeps the tree and swaps the `*_sim` /
  `env` directory for a hardware-driver package/module.
- A hybrid (learned policy running inside a ROS 2 system) starts from the ROS 2
  tree and adds a `my_policy` package that wraps the LeRobot inference.
- Prune aggressively for an MVP — a single-package ROS 2 demo doesn't need four
  packages. But never move `docs/architecture-brief.md`.
