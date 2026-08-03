---
name: visualization
version: 1.0.0
description: >
  Choose and apply robotics visualization: selection guidance for rviz2 vs
  Foxglove vs Rerun, plus best practices — what to visualize at each dev stage,
  live vs recorded, local vs remote. Use when: 'visualize', 'see what the robot
  sees', 'debug visually', 'plot the trajectory', 'dashboard for the robot',
  choosing a viz tool, or recording data for later inspection. Umbrella skill —
  after selecting, load the matching tool skill: rviz2 (ROS-native debugging),
  foxglove (remote/web + MCAP recording), rerun (ML/data-centric logging). Not
  for: tool-specific how-to (the per-tool skills).
---

# visualization

The visualization-selection umbrella for robium. "I can't see what the robot is
doing" is one of the fastest ways a debugging session stalls, and picking the
wrong tool for the context (a local-display tool on a headless server, a
ROS-native tool for a non-ROS ML pipeline) wastes more time than the debugging
itself. This skill decides which of rviz2, Foxglove, or Rerun fits a given
context, and states the cross-cutting practice of *what* to visualize at each
build stage. It does not teach any one tool's UI, panels, or API — that is each
tool's own skill.

## When to use this skill

- A viz tool hasn't been chosen yet for the current context (local desktop,
  headless remote server, or an ML/data pipeline outside ROS).
- The trigger phrases in the description: 'visualize', 'see what the robot
  sees', 'debug visually', 'plot the trajectory', 'dashboard for the robot'.
- Deciding whether to look at data live or record it for later inspection,
  before wiring up either path.
- Cross-references — go straight to the tool skill, skipping this one, once
  the tool is already chosen and the question is tool-specific:
  - RViz2 panel configuration, displays, or plugins on a local Linux desktop →
    `rviz2`.
  - Foxglove layouts, the Foxglove Bridge, or MCAP recording/playback → `foxglove`.
  - Rerun logging API, blueprints, or timeline views for ML/perception data →
    `rerun`.
  - Whether headless/remote is the deployment target at all (as opposed to
    which viz tool to use once it is) → `environments`.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: route + embed the decision logic.** The *selection*
  (which tool, for which context) and the always-visualize checklist live
  here; every tool's actual usage lives in its own skill. Never re-teach
  rviz2/Foxglove/Rerun mechanics in this skill — link to the tool skill.
- **Context picks the tool, not preference.** Local ROS desktop debugging,
  remote/headless or cross-team sharing, and ML-centric rollout inspection
  each have a different right answer — see the selection table in Decision
  guidance. Don't default to whichever tool was used last on an unrelated
  project.
- **Decide live vs recorded up front.** Live viewing is enough for interactive
  debugging in the moment; anything that needs to be compared across runs,
  shared with someone not present, or replayed after a crash needs a recording
  path (rosbag2/MCAP or a Rerun `.rrd` recording) planned before the run
  happens, not reconstructed after the fact from logs.
- **Visualize something concrete at every dev stage, not just "no errors."**
  A stack that builds and runs with no crashes can still be silently wrong —
  see the always-visualize checklist below. Absence of an exception is not
  evidence of correct behavior.
- **Remote/headless defaults to a web-based tool.** Per `environments`'
  general headless-first guidance, don't reach for X11/Wayland display
  forwarding as the default remote-viz path — see Decision guidance.

## Quick start

**1. Answer two questions:** (a) is this ROS 2 data or ML/custom pipeline data,
and (b) is the viewer local-with-a-display or remote/headless/shared? These two
answers select the tool — see the table in Decision guidance.

**2. Load the matching tool skill** (`rviz2`, `foxglove`, or `rerun`) for the
actual setup and usage.

**3. Decide live vs recorded** for this session (see Key directives) before
starting the run, and pick the recording mechanism the chosen tool skill
documents if recording is needed.

**4. Before calling any stage "working," walk the always-visualize checklist**
below — don't rely on "it ran without errors."

## Decision guidance

**Selection table by context:**

| Context | Recommended | Why |
|---|---|---|
| ROS 2, local Linux desktop, interactive debugging | `rviz2` | ROS-native, zero extra infra, richest ROS message-type support out of the box. |
| Remote/headless server, cross-platform team, or need to share a view/recording | `foxglove` | Web-based — works over SSH/remote with no display; MCAP recording is a first-class, shareable artifact. |
| ML rollouts, custom (non-ROS) data pipelines, perception/policy debugging with arbitrary tensors/embeddings | `rerun` | Built for data-centric, timeline-based logging outside the ROS message-type world; the tool `lerobot` itself wraps for episode visualization. |
| ROS 2 data, but the viewer is remote or the team is mixed-platform | `foxglove` | Same ROS data, but rviz2 doesn't work headless — Foxglove Bridge exposes ROS topics to the web client instead. |

When a project spans both worlds (a ROS 2 robot driving a learned policy),
it's normal to use more than one: `rviz2`/`foxglove` for the ROS-side state
(TF, costmaps, sensor topics) and `rerun` for the policy's own inputs/outputs —
pick per-concern, not one tool for the whole project.

**Always-visualize checklist** (walk this at every dev stage before declaring
it working):

- [ ] **TF tree** — every expected frame is present and connected (no gaps
  between `map`/`odom`/`base_link`/sensor frames); a broken TF chain silently
  breaks anything that depends on it (Nav2, a perception node) without a
  visible error elsewhere.
- [ ] **Sensor rates** — each sensor topic is publishing at its expected rate,
  not just "publishing at all"; a lidar or camera silently dropping to a
  fraction of its configured rate degrades downstream behavior without an
  obvious error.
- [ ] **Costmaps / policy actions** — for a navigation stack, the costmap
  layers look sane for the environment (obstacles where they should be, no
  phantom inflation); for a learned policy, the actual actions/trajectory
  overlaid on the scene look purposeful, not just "the eval script exited 0."

## Platform gotchas

- **rviz2 needs a local display.** It is a standard Qt/OpenGL desktop app with
  no headless or web-remote mode — on a remote/headless server, don't try to
  X11-forward it as the default; use `foxglove` instead (see the selection
  table).
- **macOS has no native ROS 2**, so `rviz2` (which links against ROS 2) runs
  inside Docker on a Mac dev machine like the rest of the ROS 2 stack (see
  `environments`' and `ros2`'s macOS gotcha) — `foxglove`'s web client and
  `rerun`'s viewer both run natively on macOS without that constraint.

## Customization

- **Switching tools mid-project:** it's common to debug locally with `rviz2`
  and switch to `foxglove` only when demoing or handing off to a remote
  teammate — this doesn't require re-instrumenting the robot, since both
  consume the same ROS 2 topics; only the viewer changes.
- **Non-ROS projects:** the selection table's ROS-specific rows don't apply;
  `rerun` is the default for any custom data pipeline regardless of local vs
  remote, since its viewer already works both ways.

## References

- Upstream: [RViz2 documentation](https://docs.ros.org/en/jazzy/p/rviz2/),
  [Foxglove documentation](https://docs.foxglove.dev/docs),
  [Rerun documentation](https://rerun.io/docs/getting-started/what-is-rerun),
  [MCAP format](https://mcap.dev/) (the recording format `foxglove` and ROS 2
  tooling both use).
- Sibling skills: `rviz2` (ROS-native local viz mechanics), `foxglove`
  (remote/web viz and MCAP recording mechanics), `rerun` (ML/data-centric
  logging mechanics), `environments` (headless/remote deployment decision this
  skill assumes is already made), `lerobot` (wraps `rerun` for episode
  visualization), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->
