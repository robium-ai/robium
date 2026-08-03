---
name: ros2
version: 1.0.1
description: >
  Core ROS 2 usage: workspaces, colcon builds, packages (ament_python/ament_cmake),
  nodes, topics/services/actions, QoS, launch files, parameters, TF2, rosdep, and
  gluing third-party packages together. Use when: any ROS 2 development or
  debugging; 'ros2', 'colcon', 'launch file', 'package.xml', 'QoS mismatch', 'TF',
  'node not receiving messages', 'rosdep'. Foundation skill for the ROS vertical —
  load alongside nav2, gazebo, rviz2. ROS 2 only; ROS 1 is EOL and out of scope.
  Not for: navigation specifics (nav2), simulation (gazebo), or visualization
  (rviz2/foxglove).
---

# ros2

The foundation tool skill for the robium ROS vertical. Everything that touches
ROS 2 itself — workspaces, colcon, package anatomy, nodes, topics/services/
actions, QoS, launch files, parameters, TF2, rosdep, and gluing third-party ROS
packages together — lives here. `nav2`, `gazebo`, and `rviz2` all assume this
skill's content and cross-reference it rather than re-explaining ROS 2 basics;
load this skill alongside any of them. This skill is ROS 2 only — ROS 1 reached
end-of-life with Noetic Ninjemys and is out of scope everywhere in robium.

## When to use this skill

- Any ROS 2 development or debugging task: creating a package, building a
  workspace, writing nodes, wiring topics/services/actions, writing launch
  files, setting parameters, working with TF2, resolving dependencies.
- The trigger phrases in the description: 'ros2', 'colcon', 'launch file',
  'package.xml', 'QoS mismatch', 'TF', 'node not receiving messages', 'rosdep'.
- A ROS 2 node isn't receiving messages it should be — start here (QoS is the
  first suspect), not in application logic.
- Cross-references — go to the sibling skill instead when the question is:
  - Autonomous navigation specifics (costmaps, planners, controllers,
    behavior trees, AMCL/localization) → `nav2`. This skill covers the ROS 2
    substrate Nav2 runs on, not navigation algorithms.
  - Simulating a ROS 2 robot → `gazebo`.
  - Visualizing ROS 2 data → `rviz2` (local display) or `foxglove` (remote/
    headless).
  - Choosing uv vs Docker, or macOS/GPU environment setup → `environments`.
  - Module boundaries, non-ROS transports at a system boundary, Dockerfiles/
    compose for a multi-module app → `integration`. This skill's "bridge two
    third-party packages" pattern below is intra-system (still ROS 2 topics);
    crossing to a non-ROS peer is `integration`'s call.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: embed.** No good upstream "how do I use ROS 2" skill
  exists to point to — this content lives here, in depth, not as a thin
  pointer to docs.ros.org. Link out only for exact version/tag facts that
  change release-to-release.
- **Always `rosdep install` before building.** A workspace that hasn't had
  `rosdep install --from-paths src -y --ignore-src` run against it is not
  ready to build — missing system/package dependencies produce confusing
  colcon failures that look like source bugs. Run rosdep first, every time a
  new package or a fresh clone enters the workspace, not just on first setup.
  See `references/workspace-and-packages.md`.
- **QoS compatibility is the first suspect for silent topic failures.** A
  node that runs cleanly, discovers its peer, and still exchanges zero
  messages is almost always a QoS mismatch (e.g. one side `RELIABLE`, the
  other `BEST_EFFORT`), not a code bug — DDS drops the connection silently
  with no error on either side. Check `ros2 topic info -v` before debugging
  anything else. See `references/interfaces-and-qos.md` and
  `references/debugging.md`.
- **Prefer workspace overlays over editing third-party package source.**
  When a third-party ROS package needs different behavior, put your changes
  in an overlay package (a new package, or a `COLCON_IGNORE`d fork built on
  top) rather than hand-editing files inside an installed or vendored
  package. Overlays survive `rosdep update`/reinstalls and keep the diff
  visible; in-place edits to third-party source silently rot. See
  `references/workspace-and-packages.md`.
- **Never write distro, tag, or API-surface facts from memory.** ROS 2's
  distro cadence, package availability, and even some API idioms (e.g. the
  `rclpy.init()` context-manager form) change release to release. Verify
  before repeating a claim in a real project — every example in this skill is
  marked `status: unverified` for exactly this reason.

## Quick start

**1. Confirm the workspace exists and rosdep is current:**

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
rosdep update
rosdep install --from-paths src -y --ignore-src
```

**2. Build and source the overlay:**

```bash
colcon build --symlink-install
source install/setup.bash
```

**3. Run something.** The `examples/package-ament-python/` directory in this
skill is a minimal, internally-consistent ament_python package (one
parameterized publisher node, one launch file) — copy it into `src/`, rebuild,
and run with `ros2 run ros2_example_pkg talker` or `ros2 launch
ros2_example_pkg talker.launch.py`.

For any step beyond this, see the matching usage pattern below and the
references it points to.

## Usage patterns

**Create a package → build → run.**
`ros2 pkg create --build-type ament_python --license Apache-2.0 --node-name
<node> <package>` scaffolds `package.xml`, `setup.py`, `setup.cfg`, the
resource marker, and a starter node. Fill in `package.xml`'s
`<description>`/`<maintainer>`, add real dependencies, `colcon build
--symlink-install` from the workspace root, `source install/setup.bash`, then
`ros2 run <package> <executable>`. See `references/workspace-and-packages.md`
and `examples/package-ament-python/`.

**Add a dependency.** Declare it in `package.xml` as `<exec_depend>` (runtime)
or `<build_depend>` (build-time C++), then re-run `rosdep install --from-paths
src -y --ignore-src` before rebuilding — adding the tag alone does not install
the underlying apt/pip package. See `references/workspace-and-packages.md`.

**Write a launch file.** Python launch files are the default choice (XML/YAML
exist but are thinner and less composable): `generate_launch_description()`
returning a `LaunchDescription` of `Node` actions, with
`DeclareLaunchArgument`/`LaunchConfiguration` for anything that should be
overridable from the command line, and the launch directory registered in
`setup.py`'s `data_files` plus `<exec_depend>launch</exec_depend>` /
`<exec_depend>launch_ros</exec_depend>` in `package.xml`. See
`references/launch-patterns.md` and
`examples/package-ament-python/launch/talker.launch.py`.

**Bridge two third-party packages (remap + relay).** When two existing
packages almost line up but use different topic names or message shapes,
prefer wiring them at the launch/CLI layer over patching either package's
source: `remappings=[('from_topic', 'to_topic')]` on a `Node` action (or
`<remap>` in XML) for a straight rename, and `ros2 run topic_tools relay
<in> <out>` (or `relay_field` for a field-level republish) when the fix
needs to live as its own running node rather than a launch-time rename. This
stays inside one ROS 2 system — crossing to a non-ROS peer is `integration`'s
call, not this pattern. See `references/launch-patterns.md`.

**Parameterize a node.** Call `self.declare_parameter('name', default)` in
the node's `__init__`, read it with `self.get_parameter('name').value` (or
the typed `.get_parameter_value()` accessors), and feed it from a launch
file's `parameters=[{...}]` list, a YAML params file, or `--ros-args -p
name:=value` on the CLI — don't hardcode values a launch file should own. See
`references/interfaces-and-qos.md` and
`examples/package-ament-python/ros2_example_pkg/talker_node.py`.

## Platform gotchas

- **macOS has no native ROS 2 — Docker only.** There is no supported native
  ROS 2 install on macOS/Apple Silicon; every ROS 2 workflow on a Mac dev
  machine runs inside Docker, even for local iteration. Don't try to `pip
  install`/homebrew a native ROS 2 as a shortcut. See the `environments`
  skill's Docker patterns and its ROS 2 base-image guidance.
- **`ROS_DOMAIN_ID` collisions are silent.** All ROS 2 nodes default to
  domain ID `0`; two unrelated ROS 2 systems on the same network segment with
  the same domain ID will discover and cross-talk with each other with no
  error. Export a project-unique `ROS_DOMAIN_ID` (`export
  ROS_DOMAIN_ID=<n>`) in every shell/container that runs this project's
  nodes, the same way you'd pick a non-default port.
- **Shell sourcing order matters.** Source the underlay (`/opt/ros/<distro>/
  setup.bash`) before the workspace overlay (`install/setup.bash`) — each
  `setup.bash` only extends the environment the previous one built, so
  sourcing the overlay alone (or in the wrong order) silently drops the
  underlay's paths. A fresh shell that skips sourcing entirely is the most
  common "package not found" / "command not found: ros2" report — check this
  before anything else.

## Customization

- **Different ROS 2 distro:** this skill's commands are written against
  **Lyrical Luth**, the current LTS. Swap `lyrical` for another distro name
  in `/opt/ros/<distro>/setup.bash` and in the example package's dependency
  versions; re-verify package availability for that distro first. The
  ROS 2 + Nav2 + Gazebo navigation vertical currently defaults to **Jazzy
  Jalisco** instead, because Nav2 has not yet shipped binaries for Lyrical —
  see `nav2`'s and `architect`'s Platform gotchas for the current status
  before picking a distro for that path.
- **ament_cmake instead of ament_python:** the workspace/colcon/rosdep/launch
  mechanics in this skill are build-type-agnostic; only package internals
  differ (a `CMakeLists.txt` build/install pipeline instead of
  `setup.py`/`setup.cfg`, with `find_package`/`ament_target_dependencies`
  instead of Python imports). See `references/workspace-and-packages.md` for
  both anatomies side by side.
- **Different node/topic names in the example package:** `package.xml`'s
  `<name>`, `setup.py`'s `package_name`/console-script entry point, and the
  launch file's `package=`/`executable=` must all agree — rename all four
  places together (see `examples/package-ament-python/`) rather than
  drifting one and hitting a confusing `ros2 run`/`ros2 launch` "not found".

## References

- `references/workspace-and-packages.md` — workspace layout, colcon build
  mechanics, underlay/overlay sourcing, ament_python vs ament_cmake package
  anatomy, rosdep workflow, adding dependencies.
- `references/launch-patterns.md` — Python launch files in depth: Node
  actions, launch arguments, parameter files, remapping, includes, and the
  remap+relay bridging pattern.
- `references/interfaces-and-qos.md` — topics/services/actions overview, the
  full QoS policy set, compatibility rules, preset profiles, and TF2 basics.
- `references/debugging.md` — the `ros2 doctor`/`ros2 topic`/`ros2 node`
  introspection toolkit, common failure signatures (unsourced shell, domain
  ID collision, QoS mismatch, missing rosdep install) and how to tell them
  apart.
- `examples/package-ament-python/` — a minimal, internally-consistent
  ament_python package: `package.xml`, `setup.py`, `setup.cfg`, one
  parameterized publisher node, one launch file (status: unverified — each
  file links its own upstream source).
- Upstream: [ROS 2 documentation](https://docs.ros.org/) (blocked for direct
  fetch on 2026-07-10 — verified via the `ros2/ros2_documentation` GitHub
  repo through ctx7 instead; re-check docs.ros.org directly when it's
  reachable), [colcon documentation](https://colcon.readthedocs.io/),
  [ros2/launch](https://github.com/ros2/launch),
  [ros-tooling/topic_tools](https://github.com/ros-tooling/topic_tools).
  Sibling skills: `nav2`, `gazebo`, `rviz2` (load alongside), `environments`
  (macOS/Docker setup), `integration` (cross-boundary comms, compose),
  `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
