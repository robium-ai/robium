# nav-trial — Design

Date: 2026-07-10
Status: approved

## Purpose

First application in the robium proving ground: autonomous mobile-robot navigation
in simulation (`apps/nav-trial`). Dual purpose per CLAUDE.md — build the app honestly
using robium's skills, and capture every skill interaction as QA data in `learnings/`.

## Requirements

- **Simulation only.** No real robot. TurtleBot-class off-the-shelf robot (e.g. TurtleBot 3/4)
  with existing Gazebo model and Nav2 params — final pick is the robium-architect agent's call.
- **SLAM included.** The robot builds its own map (drive around, map, save), then navigates
  autonomously on that saved map. Not a known-map-only shortcut.
- **Runs in Docker on macOS.** ROS 2 + Nav2 + Gazebo headless in containers on this Mac.
  Browser-based visualization (Foxglove expected). No native RViz dependency.
- **Stack decisions deferred to robium.** ROS distro, Gazebo version, SLAM package, container
  layout: decided by the robium-architect agent and downstream robium skills, not pre-empted here.

## Milestones

1. **Bringup** — dockerized env; robot spawns in a standard world; drivable (teleop or
   scripted); sensor data visible in Foxglove.
2. **SLAM** — robot driven around the world; map built and saved as a file committed to the app.
3. **Navigate** — Nav2 localizes on the saved map; goals sent programmatically; robot reaches
   them while avoiding obstacles.

## Testing (definition of done)

- **Smoke test** (pass bar): one command launches the full stack headless, loads the saved map,
  sends nav goal(s), asserts arrival within a timeout. No GUI required.
- **SLAM check**: lighter assertion that a map file is produced and non-trivial.
- Per README: app is not done until the smoke test passes and the robium skills visibly drove
  the stack decisions.

## Process

- Kickoff: launch the `robium-architect` agent with the requirements above; it writes
  `apps/nav-trial/docs/architecture-brief.md`. Refinement happens with the `architect` skill
  in the main session.
- Build follows robium skill routing (expected: environments, ros2, gazebo, nav2, foxglove,
  integration, testing).
- Learnings captured in `learnings/2026-07-10.md` at the moment they happen, per the
  CLAUDE.md taxonomy; end-of-block retro per skill.

## Out of scope

- Real-robot deployment, remote-server runs (may come later per README reproducibility bar),
  multi-robot, custom robot models, SOTA navigation performance.
