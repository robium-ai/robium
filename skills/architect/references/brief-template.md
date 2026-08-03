# Architecture brief template

The required structure of `docs/architecture-brief.md`: the living architecture
contract that lives in every robium application repo. The `robium-architect`
subagent writes the first version; all later refinement happens in the main
conversation with the `architect` skill loaded, editing this same file.

**Every section below is required.** Depth scales with the project (a one-robot
sim demo has a short comms plan; a fleet has a real one), but no section is
omitted; an empty section is a signal that a decision hasn't been made yet.
Copy the skeleton, fill each section, keep it current as the build proceeds.

---

## Skeleton

```markdown
# Architecture Brief: <app name>

**Date:** <YYYY-MM-DD>   **Status:** <draft | active | superseded>
**Author:** <robium-architect subagent | main agent refinement>

## 1. Requirements

The inputs this design answers to. Robot type, task, hardware, sim-vs-real,
GPU availability, local-vs-remote. Mark any assumed (not confirmed) input
explicitly; assumptions also feed section 8.

## 2. Chosen stack + reasoning

The decisions and why. One row per component with the alternative rejected.

| Layer | Choice | Version | Why (and what was rejected) |
|---|---|---|---|
| Middleware | ROS 2 / none | Jazzy | … |
| Simulator | Gazebo / Isaac / LeRobot-sim | Harmonic | … |
| Nav / learning | Nav2 / LeRobot / … | … | … |
| Visualization | rviz2 / foxglove / rerun | … | … |
| Environment | uv / Docker | … | … |

Tie each choice back to a branch in the architect stack-selection trees.

## 3. Module breakdown

The system decomposed into modules/packages/nodes, each with its
responsibility and its inputs/outputs. Mirrors the scaffold layout.

## 4. Comms plan

How modules talk. For ROS 2: the key topics/services/actions and their
message types and rates. For cross-process or remote boundaries: the
transport (topics vs zenoh vs gRPC). Sensor rates and frames that matter go
here. (The `integration` skill owns the detail.)

## 5. Environment strategy

Reproducibility. uv/venv vs Docker and why; base image or Python version;
GPU passthrough if any; how local and remote stay identical. (The
`environments` skill owns the detail.)

## 6. Data plan

Where data comes from and where it goes. Offline datasets vs sim-generated
vs teleop-collected; Hub datasets/models pulled or pushed; storage and
gitignore boundaries. For non-learning apps this may be short (maps, logs).
(The `data` and `huggingface` skills own the detail.)

## 7. Robium skills per build phase

The routing plan: which skill the builder loads at each phase, in order.
Example:

| Phase | Skill(s) |
|---|---|
| Env setup | environments |
| Robot model + bringup | ros2 |
| Simulation | gazebo |
| Navigation | nav2 |
| Visualization | visualization → foxglove |
| Testing | testing |

## 8. Open risks

Every unverified assumption and known unknown, stated plainly. GPU
availability, sim-to-real gap, hardware you can't inspect, version pins you
haven't confirmed, performance concerns. Each risk: what it is, what it
blocks, and how you'd resolve or de-risk it. This section is never empty;
if you think it is, you haven't looked hard enough.
```

---

## Filling notes

- **Section 2 is the heart.** A reader should be able to reconstruct why the
  stack is what it is without asking. Always name the rejected alternative.
- **Section 7 makes the brief actionable**: it is the routing table from the
  architect skill, narrowed to this app and ordered by build phase.
- **Section 8 protects the project.** The architect directive is to surface
  risks, not bury them. GPU availability is the most common one for the
  manipulation path; the sim-to-real gap for anything targeting real hardware.
- Keep **Status** current: `draft` while being written, `active` once the build
  is proceeding from it, `superseded` when a re-architecture pivot produces a
  new version (the subagent is relaunched only for genuine pivots).

See `examples/architecture-brief-example.md` for a filled instance.
