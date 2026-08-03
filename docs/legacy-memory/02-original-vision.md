# The Original Vision (Legacy PRD, condensed)

Source: `robium-old/archive/legacy/scripts/PRD.md`

## Product definition

"Robium is a web-based robotics development studio IDE that enables users to create,
simulate, and run robotics applications by connecting modular ROS2 components."

Value proposition: accelerate robotics development, reduce setup/wiring/debugging
errors, make advanced robotics accessible to a broader audience.

## Core features (as specified)

1. **Global colcon workspace + unified base image**
   - All supported ROS packages maintained and integration-tested in ONE global
     colcon workspace.
   - Docker base image built from this workspace supports every package; project
     containers build FROM it. Guarantees compatibility, kills per-project build pain.
   - User projects copy only the packages their selected tasks require.

2. **ROS algorithm suite with task categories**
   - Meta-categories → task categories (actuator, camera, remote control, arm control,
     voice control, mapping, localization, planning, person tracking, person
     recognition, character animation, …).
   - Each category holds multiple solution alternatives; each solution has a task
     definition, IO relations, and its ROS package list.
   - Modularity + swappable solutions per task was a central design principle.

3. **Containerized project environments**
   - One isolated Docker container per project, FROM the base image (ROS 2 Humble).
   - Persistent host-mounted workspace volume (`/workspace`) → versioning, backup,
     local portability.
   - Strict isolation: volume scoping, network isolation, security policies,
     non-root users, least-privilege capabilities, resource limits, vulnerability
     scanning, automated idle cleanup. Naming: `robium_{user_id}_{project_id}`.

4. **Project configuration system**
   - Standardized JSON/YAML schema: metadata, ROS2 dependencies, env vars,
     simulation settings.
   - Automated Dockerfile + docker-compose generation from configs.

5. **Execution and debugging**
   - One-click run: launch all nodes, per-node logs, live RViz, embedded Gazebo
     (predefined worlds, object spawning, sensor emulation), rosbag playback,
     web terminal.

6. **Auth & ownership**: signup/login, private per-user projects, admin sees all.

7. **Minimal backend**: metadata APIs, rosbag hosting, LLM proxy, WebSocket sync.

## Planned future enhancements (never built)

- LLM assistant: intelligent task curation, solution suggestions, project structure
  guidance, guided wiring/parameter editing.
- MCP ("Mission Control Plane") server for centralized container/project management.
- Multi-user real-time collaboration.
- Component marketplace/library.
- Learning-based recommendations, analytics.

## Key user flow (as designed)

1. Create project → Docker/ROS2 workspace initialized from base image.
2. Configure settings → dependencies, env vars, simulation settings.
3. Add tasks/algorithms via UI forms, code, or LLM assistant.
4. Inspect/edit component code, adjust parameters.
5. Click "Run" → nodes launch; view logs, RViz, Gazebo in browser.
6. Share/export project or run it locally.

## Risks identified at the time

- ROS2 + Docker + web integration complexity.
- Container security/isolation.
- Resource management for many user containers.
- MVP scope creep (this one materialized — the response was to cut the robotics core).
- Base image maintenance overhead.
