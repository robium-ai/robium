# Project History — Two Eras

## Era 1: The Original Vision ("Robotics Development Studio", legacy)

The project began as an ambitious **web-based robotics development studio IDE**
(preserved in `archive/legacy/` of the old repo, PRD at `archive/legacy/scripts/PRD.md`).

Target users: robotics developers, educators, students, hobbyists.

Core idea: solve the pain of setting up, wiring, and debugging ROS2 projects by
providing:

- A **curated catalog of ROS2 modules/algorithms** organized by task category
  (mapping, localization, planning, person tracking, arm control, voice control, …),
  each with task definition, input/output relations, and ROS package lists.
- A **global colcon workspace** containing all supported packages, baked into a
  **unified Docker base image** — every project container builds FROM this image,
  guaranteeing compatibility and fast per-project builds.
- **Per-project isolated Docker containers** with persistent host-mounted workspaces,
  strict volume/network isolation, automated lifecycle (naming: `robium_{user}_{project}`),
  resource limits, and idle cleanup.
- **One-click execution**: launch all nodes, per-node logs, live RViz, embedded Gazebo
  with predefined worlds, rosbag playback — all in the browser.
- **Auth + ownership**: private projects per user, admin role.
- **Future**: LLM assistant for task curation and wiring suggestions, component
  marketplace, real-time collaboration.

The legacy backend got fairly far: WebSocket server with heartbeat, container
lifecycle service, Dockerfile generation from templates, log streaming, workspace
mounting, caching, automated cleanup, Postgres→SQLite migration, 9 SQL migrations,
module/ros_package database schemas with dependency graphs.

## Era 2: The Redesign (final state of the repo)

At some point (commit `dd70ab1 chore(archive): move legacy to archive/legacy and seed
redesign root`) the whole legacy codebase was archived and a **much smaller MVP** was
rebuilt from scratch, defined in `docs/PRD_REDESIGN.md`:

> "Robium is a focused web platform to create and manage robotics project
> configurations and generate Dockerfiles from templates."

In scope: Auth (JWT), Projects/Templates CRUD (single table with `is_template` flag),
on-demand Dockerfile generation, GitHub repo creation + scaffold push on project
create/clone, Hugging Face–style chip-filter sidebar, admin panel.

**Explicitly out of scope** (quote): "ROS packages/modules, datasets, execution
workspace, WebSocket features, container lifecycle."

The redesign shipped: 22/22 Taskmaster tasks done, all UI-level (filter management,
admin panel fixes, template dialogs, profile editing). Final commits were filter
management polish.

## The trajectory in one sentence

The project drifted from **"a place where robots run"** to **"a place where robot
project metadata is managed"** — the robotics execution core was designed, partially
built, then cut for scope, leaving a well-executed but generic CRUD platform whose
only remaining robotics DNA was the Dockerfile generator and the vocabulary of the
filters (robots, capabilities, simulators, use cases).

## Development process notes

- Built primarily with **Cursor** + **Taskmaster AI** (task-driven development,
  `.taskmaster/tasks/tasks.json`, cursor rules in `.cursor/rules/*.mdc`).
- Project rule: commit after every subtask.
- CI workflow in `.github/workflows`, husky pre-commit hooks in legacy era.
