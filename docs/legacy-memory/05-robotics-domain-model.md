# Robotics Domain Model (the most valuable IP of the old project)

The robotics-specific knowledge lived almost entirely in the **legacy era**
(`archive/legacy/packages/shared/`). This is the part most worth carrying forward
conceptually, regardless of stack.

## Module catalog format

Modules were JSON files organized by category
(`modules/{navigation,vision,robots,communication,gui,debug}/`). Real example
(`navigation/nav2-core.json`):

```json
{
  "id": "navigation2",
  "title": "Navigation2 Core",
  "description": "ROS 2 Navigation Stack - path planning, localization, navigation",
  "category": "navigation",
  "version": "1.0.0",
  "rosDistros": ["humble", "foxy", "iron"],
  "dependencies": [],
  "apt": ["ros-humble-nav2-core", "ros-humble-nav2-bt-navigator", "..."],
  "pip": [],
  "env": { "NAV2_USE_SIM_TIME": "true" },
  "setupCommands": [],
  "expose": [11311],
  "bashrcAliases": ["alias nav2='ros2 launch nav2_bringup bringup_launch.py'"]
}
```

The Dockerfile generator consumed these: module selection → apt/pip installs, env
vars, exposed ports, aliases, setup commands composed into a Dockerfile.

Catalog at time of archive: `nav2-core`, `depthai-oakd` (vision),
`turtlebot4` (robots), `rmw-cyclonedds` (communication), `x11-gui`,
`debug-tools`. Small but the format was proven.

## Database-backed module/package model (legacy)

Modules and ROS packages were later moved from JSON files into DB tables with:

- **modules**: name, version, category, type (core/advanced/custom), packages[],
  dependencies[], tags[], algorithms[], is_active/is_public/is_default.
- **ros_packages**: full ROS package metadata including build/runtime/test
  dependencies, build_type (ament_cmake), **published_topics, subscribed_topics,
  advertised_services, called_services** (IO relations — key for future wiring
  validation/visualization), source paths.
- Dependency edge tables with type (required/optional/conflicts, build/runtime/test)
  and version constraints.

Example modules seeded: `localization` (amcl, kalman_filter),
`navigation` (depends on localization; nav2), `person_tracking` (opencv, pcl).

## Project templates (legacy)

`templates/{navigation,manipulation,perception,custom}-project.json` — pre-baked
project configs aligned with the shared JSON schemas.

## JSON Schemas (legacy shared package)

`project-config`, `environment-config`, `project-metadata`, `ros2-package`,
`simulation-config` — validation-first configuration was a core principle.

## Base image strategy

- One global colcon workspace, integration-tested, baked into a single base image
  (ROS 2 Humble) hosted in a registry.
- Project containers: `FROM robium-base` + copy only selected packages.
- Rationale: compatibility guaranteed centrally, project builds stay fast and small.
- Known cost: base image gets huge; maintenance overhead acknowledged as a risk.

## Filter taxonomy (final era — the surviving robotics vocabulary)

Projects/templates were faceted by: **use_cases, capabilities, robots, simulators,
tags** — dynamically manageable via the admin panel. This taxonomy is the final
era's residue of the original task-category system.

## Scaffold generated for GitHub publishing (final era)

Dockerfile (Ubuntu 22.04 dev container), docker-compose.yml, .gitignore,
.dockerignore, README, `scripts/dev-{start,shell,stop}.sh`, `src/.keep`.
Notably: the generated scaffold was generic Ubuntu, not even ROS-based — evidence
of how far the robotics core had receded by the end.
