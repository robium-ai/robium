---
name: rviz2
version: 1.0.1
description: >
  RViz2 visualization for ROS 2: displays, TF frame debugging, markers, saved
  config files, and the common 'nothing shows up' fixes (fixed frame, QoS,
  sim time). Use when: 'rviz', 'rviz2', visualizing ROS topics, TF trees,
  costmaps, or robot models during development. ROS-native desktop debugging
  tool — for remote/web visualization use foxglove; for ML/data-centric
  logging use rerun. Pairs with ros2 and nav2.
---

# rviz2

The local-desktop ROS 2 visualization tool: displays for topics, TF frames,
markers, and robot models, driven by a saved `.rviz` config file per
robot/task. RViz2 ships across every ROS 2 distro back to the earliest
releases through **Lyrical Luth** (current LTS) and Rolling — verified via
direct fetch of `index.ros.org`'s rviz2 package page on 2026-07-10 (the
`docs.ros.org` page returned an access-control error rather than content;
see References) — so nothing in
this skill is distro-gated the way Nav2's binary packages are; the only
distro requirement is that `ROS_DISTRO` matches the sourced workspace. It is
a standard Qt/OpenGL desktop app with no headless or web mode; for a
remote/headless server or sharing a view, use `foxglove` instead (see
Platform gotchas).

## When to use this skill

- Adding or configuring a display (LaserScan, PointCloud2, RobotModel, TF,
  MarkerArray, Path, Costmap, Odometry, ...), debugging why a topic isn't
  rendering, or setting up a saved config for a robot/task.
- The trigger phrases in the description: 'rviz', 'rviz2', visualizing ROS
  topics, TF trees, costmaps, or robot models during development.
- A display is blank/nothing shows up — start here with the checklist in
  Usage patterns before assuming the publishing node itself is broken.
- Cross-references — go to the sibling skill instead when the question is:
  - TF2 concepts themselves (frames, broadcasters, static vs dynamic
    transforms) or QoS concepts (reliability/durability policies, why a
    mismatch drops messages) → `ros2`. This skill only applies those
    concepts as debugging steps (see the nothing-shows-up checklist); it
    does not re-teach them.
  - Nav2-specific behavior-tree/costmap internals (what a costmap layer
    computes, BT Navigator internals) → `nav2`. This skill only lists which
    displays to add for Nav2 debugging, not what the underlying servers do.
  - Remote/headless viewing, sharing a view with someone not at the
    machine, or recording for later → `foxglove`.
  - ML/data-centric logging (policy rollouts, non-ROS sensor pipelines) →
    `rerun`.
  - Choosing which viz tool fits the situation at all → `visualization`
    (routes here once RViz2 is the right choice).

## Key directives

- **Delegation posture: embed.** RViz2's own domain (displays, config files,
  the nothing-shows-up checklist) is small and stable enough to live
  entirely in this skill — there is no large reference tree to split out,
  and no upstream single page covers the debugging checklist as a
  connected whole.
- **Diagnose in order: Fixed Frame, then QoS, then sim time.** These three
  cover the overwhelming majority of "I added a display and nothing
  rendered" reports, in that order of likelihood — see the checklist in
  Usage patterns. Don't jump to restarting nodes or rebuilding the
  workspace before walking it.
- **Never re-teach TF2 or QoS from scratch here.** When the checklist points
  at a broken TF chain or a QoS mismatch, apply the fix (set Fixed Frame,
  flip the display's QoS override) and link to `ros2`'s TF2/QoS references
  for *why* — duplicating that explanation here would drift out of sync.
- **Config files are the unit of reuse, not manual per-session setup.**
  Save a named `.rviz` config per robot/task once the display set is right,
  and launch with it (`-d`) every time rather than rebuilding the display
  list by hand — see Quick start.

## Quick start

**1. Launch RViz2 standalone:**

```bash
ros2 run rviz2 rviz2
```

**2. Add a display** via the "Add" button (bottom-left panel) — by topic
(browses active topics and picks the matching display type) or by display
type (e.g. `RobotModel`, `TF`, `LaserScan`) and set its **Topic** manually.

**3. Set the Fixed Frame** (Global Options panel, top of the Displays
panel) to a frame that actually exists and is being broadcast — usually
`map` or `odom` for a mobile robot, `base_link` for a static/manipulator
view. This is the single most common cause of a display staying empty; see
Usage patterns.

**4. Save the config** once the display set is right: `File > Save Config
As...`, into a path you'll reuse (e.g. `config/<robot>.rviz` in the
project). Reload it next time with `-d` (see Usage patterns) instead of
rebuilding displays by hand.

## Usage patterns

**Launch with a saved config.** Pass `-d <path>.rviz` on the command line or
as a launch-file argument, rather than opening RViz2 bare and re-adding
displays every session:

```bash
ros2 run rviz2 rviz2 -d config/<robot>.rviz
```

In a Python launch file, pass the same flag through `Node`'s `arguments`:
`arguments=['-d', PathJoinSubstitution([pkg_share, 'config', '<robot>.rviz'])]`.
Keep one config per robot/task (nav debugging vs. manipulation vs. sensor
calibration) rather than one config trying to cover everything — a display
list with everything on is slower to render and harder to read than a
focused one.

**The nothing-shows-up checklist.** Walk these in order before assuming the
publisher is broken:

1. **Fixed Frame wrong or not broadcasting.** Global Options → Fixed Frame
   must name a frame that's actually present in the TF tree *right now* — a
   red/orange warning next to a display, or the display simply staying
   empty, both point here first. Confirm the frame exists and is current
   with `ros2 run tf2_ros tf2_echo <fixed_frame> <a_frame_the_data_uses>`
   (see `ros2`'s TF2 reference for what a stale vs. missing transform looks
   like) — don't touch anything else until this returns clean data.
2. **QoS mismatch between the display and the publisher.** Each display has
   a **Topic** section with a QoS override (Reliability: Reliable/Best
   Effort, Durability: Volatile/Transient Local) that must be *compatible*
   with the publisher's own QoS, not merely "set to something" — a sensor
   publishing Best Effort with a display left on the default Reliable will
   silently receive nothing, no error dialog. Check the publisher's actual
   QoS (`ros2 topic info <topic> --verbose`) and match the display's
   override to it; see `ros2`'s QoS reference for the compatibility rules
   themselves.
3. **`use_sim_time` mismatch or a stalled `/clock`.** In simulation, if
   RViz2 (and the nodes publishing the data it's trying to show) don't
   agree on `use_sim_time`, or the sim's `/clock` has stalled/paused,
   timestamps stop advancing and time-sensitive displays (TF, anything with
   a message filter) stay empty even though the topic is technically
   publishing. Confirm `ros2 topic echo /clock` is advancing and every
   relevant node was launched with the same `use_sim_time` value — see
   `nav2`'s sim-time directive for why this has to be set globally, not
   per-node.

**Nav2 debugging display set.** For debugging a navigation stack, add (on
top of `TF` and `RobotModel`): `Map` (topic `/map`), two `Costmap`
displays — one on `/global_costmap/costmap`, one on
`/local_costmap/costmap` — a `Path` display for the planned path, a
`Polygon` display for the robot footprint, `LaserScan`/`PointCloud2` for the
raw sensor(s) feeding the costmaps, and a `MarkerArray` for behavior-tree/
planner debug markers if the stack publishes them. Send goals with the
"Nav2 Goal" tool in the toolbar. See the `nav2` skill's common-failures
reference for what each display should look like when the stack is healthy
vs. broken (e.g. a costmap with no obstacles where there should be some).

## Platform gotchas

- **No headless or web mode.** RViz2 needs a local X11/Wayland display —
  there is no server-side/remote flag. On a headless or remote box, don't
  attempt X11 forwarding as the default; use `foxglove` (see the
  `visualization` umbrella's selection table).
- **macOS has no native ROS 2**, so RViz2 (which links against ROS 2) runs
  inside Docker on a Mac dev machine along with the rest of the ROS 2 stack
  — see `environments`' and `ros2`'s macOS gotcha for the container/display
  setup; this is not an RViz2-specific workaround.
- **A stale config referencing a display plugin that isn't installed**
  (e.g. a Nav2-specific display plugin missing from a minimal install) fails
  that one display silently or with a small error banner, not a hard crash
  — the rest of the config still loads. Check the Displays panel for a
  greyed-out/errored entry if a saved config "loses" one display after
  moving to a different machine.

## Customization

- **New robot, same task:** copy the closest existing `.rviz` config,
  update the `RobotModel`'s topic/description source and any frame-specific
  display settings (e.g. a `LaserScan` topic name) to the new robot's
  namespace, then re-save under a new filename rather than overwriting a
  config that other tasks still reference.
- **Multi-robot/namespaced setups:** each display's **Topic** field needs
  the fully-namespaced topic (e.g. `/robot1/scan`), and Fixed Frame needs
  the namespaced frame if TF is also namespaced — a config built for a
  single-robot setup will silently show nothing when pointed at a
  namespaced one until every topic/frame field is updated.

## References

- Upstream: [RViz2 documentation](https://docs.ros.org/en/jazzy/p/rviz2/)
  (direct fetch attempted on 2026-07-10; the page returned an access-control
  error rather than content — cross-check against the live page before
  relying on exact UI wording), [rviz2 package page,
  index.ros.org](https://index.ros.org/p/rviz2/) (fetched directly this
  session — source of the distro-coverage claim above, used in place of the
  `docs.ros.org` page which did not return content),
  [ros2/rviz GitHub repo](https://github.com/ros2/rviz) (source of the
  plugin/display implementations; fetched directly on 2026-07-10 — CLI flag
  documentation was not present in the README itself, so the `-d` flag
  above was confirmed via search-synthesis of ROS community docs, e.g.
  [ROS Answers on loading a specific config
  file](https://answers.ros.org/question/76864/rviz-start-specific-config-file/)
  and [The Construct's RViz config-file
  walkthrough](https://www.theconstruct.ai/gazebo-in-5-minutes-010-how-to-launch-rviz-using-a-configuration-file/)
  — re-verify against `rviz2 --help` before depending on it in a script).
  Sibling skills: `ros2` (TF2/QoS foundations this skill applies but does
  not re-teach), `nav2` (costmap/BT internals behind the Nav2 debugging
  display set), `foxglove` (remote/web viewing), `rerun` (ML/data-centric
  logging), `visualization` (umbrella, routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
