---
name: ros2
version: 1.6.0
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
- **Always `rosdep install` before building.** <!-- id: rosdep-before-build --> A workspace that hasn't had
  `rosdep install --from-paths src -y --ignore-src` run against it is not
  ready to build — missing system/package dependencies produce confusing
  colcon failures that look like source bugs. Run rosdep first, every time a
  new package or a fresh clone enters the workspace, not just on first setup.
  See `references/workspace-and-packages.md`.
- **QoS compatibility is the first suspect for silent topic failures.** <!-- id: qos-first-suspect --> A
  node that runs cleanly, discovers its peer, and still exchanges zero
  messages is almost always a QoS mismatch (e.g. one side `RELIABLE`, the
  other `BEST_EFFORT`), not a code bug — DDS drops the connection silently
  with no error on either side. Check `ros2 topic info -v` before debugging
  anything else. See `references/interfaces-and-qos.md` and
  `references/debugging.md`.
- **Prefer workspace overlays over editing third-party package source.** <!-- id: workspace-overlays-over-source-edits -->
  When a third-party ROS package needs different behavior, put your changes
  in an overlay package (a new package, or a `COLCON_IGNORE`d fork built on
  top) rather than hand-editing files inside an installed or vendored
  package. Overlays survive `rosdep update`/reinstalls and keep the diff
  visible; in-place edits to third-party source silently rot. See
  `references/workspace-and-packages.md`.
- **Never write distro, tag, or API-surface facts from memory.** <!-- id: no-version-facts-from-memory --> ROS 2's
  distro cadence, package availability, and even some API idioms (e.g. the
  `rclpy.init()` context-manager form) change release to release. Verify
  before repeating a claim in a real project — every example in this skill is
  marked `status: unverified` for exactly this reason.

## Quick start

**1. Confirm the workspace exists and rosdep is current:** <!-- id: rosdep-update-workspace -->

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
rosdep update
rosdep install --from-paths src -y --ignore-src
```

**2. Build and source the overlay:** <!-- id: colcon-build-source -->

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

**Create a package → build → run.** <!-- id: pkg-create-workflow -->
`ros2 pkg create --build-type ament_python --license Apache-2.0 --node-name
<node> <package>` scaffolds `package.xml`, `setup.py`, `setup.cfg`, the
resource marker, and a starter node. Fill in `package.xml`'s
`<description>`/`<maintainer>`, add real dependencies, `colcon build
--symlink-install` from the workspace root, `source install/setup.bash`, then
`ros2 run <package> <executable>`. See `references/workspace-and-packages.md`
and `examples/package-ament-python/`.

**Add a dependency.** <!-- id: add-dependency-rosdep --> Declare it in `package.xml` as `<exec_depend>` (runtime)
or `<build_depend>` (build-time C++), then re-run `rosdep install --from-paths
src -y --ignore-src` before rebuilding — adding the tag alone does not install
the underlying apt/pip package. See `references/workspace-and-packages.md`.

**Write a launch file.** <!-- id: python-launch-default --> Python launch files are the default choice (XML/YAML
exist but are thinner and less composable): `generate_launch_description()`
returning a `LaunchDescription` of `Node` actions, with
`DeclareLaunchArgument`/`LaunchConfiguration` for anything that should be
overridable from the command line, and the launch directory registered in
`setup.py`'s `data_files` plus `<exec_depend>launch</exec_depend>` /
`<exec_depend>launch_ros</exec_depend>` in `package.xml`. See
`references/launch-patterns.md` and
`examples/package-ament-python/launch/talker.launch.py`.

**Bridge two third-party packages (remap + relay).** <!-- id: remap-relay-bridge --> When two existing
packages almost line up but use different topic names or message shapes,
prefer wiring them at the launch/CLI layer over patching either package's
source: `remappings=[('from_topic', 'to_topic')]` on a `Node` action (or
`<remap>` in XML) for a straight rename, and `ros2 run topic_tools relay
<in> <out>` (or `relay_field` for a field-level republish) when the fix
needs to live as its own running node rather than a launch-time rename. This
stays inside one ROS 2 system — crossing to a non-ROS peer is `integration`'s
call, not this pattern. See `references/launch-patterns.md`.

**Parameterize a node.** <!-- id: declare-parameter-pattern --> Call `self.declare_parameter('name', default)` in
the node's `__init__`, read it with `self.get_parameter('name').value` (or
the typed `.get_parameter_value()` accessors), and feed it from a launch
file's `parameters=[{...}]` list, a YAML params file, or `--ros-args -p
name:=value` on the CLI — don't hardcode values a launch file should own. See
`references/interfaces-and-qos.md` and
`examples/package-ament-python/ros2_example_pkg/talker_node.py`.
**Test a launched process with launch_testing.** <!-- id: launch-testing-launched-process -->
`launch_testing` tests a process (a plain `ExecuteProcess` or a
`launch_ros.actions.Node`) through its real launch file rather than
mocking it: `generate_test_description()` returns a `LaunchDescription`
ending in `launch_testing.actions.ReadyToTest()`; an undecorated
`unittest.TestCase` runs while the process is alive
(`@launch_testing.markers.keep_alive` on the launched action keeps it
running through the active-test phase instead of exiting immediately),
asserting via `proc_output.assertWaitFor(...)` (or `get_node_names()`
for a launched node); a second `unittest.TestCase` decorated
`@launch_testing.post_shutdown_test()` asserts the exit code with
`launch_testing.asserts.assertExitCodes(proc_info)`. This closes the
gap the `testing` skill's `ros2-pytest-vs-launch-testing-split` anchor
already names — "needs a running node or launch file" tests route
here, but this skill previously had no such pattern. Confirmed
2026-08-02 against the `rolling`-branch `ros2/examples` repo; re-verify
the decorator/assertion API surface against this skill's default
distro (Lyrical Luth) before copying verbatim.
**Control callback concurrency with executors + callback groups.** <!-- id: callback-group-executor-concurrency -->
Concurrency under a `MultiThreadedExecutor` is scoped per callback
group, not per executor: passing a `MutuallyExclusiveCallbackGroup()`
instance as `callback_group=` to `create_timer`/`create_subscription`/
etc. serializes only that group's own callbacks — other callbacks on
the same node (or in a different group) can still run concurrently.
Without an explicit group, a node's callbacks share one implicit
`MutuallyExclusiveCallbackGroup` by default, so a bare
`MultiThreadedExecutor(num_threads=N)` alone does not parallelize a
single node's own callbacks. Use `ReentrantCallbackGroup` instead when
a callback should run concurrently with itself rather than being
serialized. Confirmed 2026-08-02 against the `rolling`-branch
`ros2/examples` repo; re-verify the callback-group API surface against
this skill's default distro before relying on exact signatures.

## Platform gotchas

- **macOS has no native ROS 2 — Docker only.** <!-- id: macos-no-native-ros2 --> There is no supported native
  ROS 2 install on macOS/Apple Silicon; every ROS 2 workflow on a Mac dev
  machine runs inside Docker, even for local iteration. Don't try to `pip
  install`/homebrew a native ROS 2 as a shortcut. See the `environments`
  skill's Docker patterns and its ROS 2 base-image guidance.
- **`ROS_DOMAIN_ID` collisions are silent.** <!-- id: domain-id-collision --> All ROS 2 nodes default to
  domain ID `0`; two unrelated ROS 2 systems on the same network segment with
  the same domain ID will discover and cross-talk with each other with no
  error. Export a project-unique `ROS_DOMAIN_ID` (`export
  ROS_DOMAIN_ID=<n>`) in every shell/container that runs this project's
  nodes, the same way you'd pick a non-default port.
- **Shell sourcing order matters.** <!-- id: sourcing-order --> Source the underlay (`/opt/ros/<distro>/
  setup.bash`) before the workspace overlay (`install/setup.bash`) — each
  `setup.bash` only extends the environment the previous one built, so
  sourcing the overlay alone (or in the wrong order) silently drops the
  underlay's paths. A fresh shell that skips sourcing entirely is the most
  common "package not found" / "command not found: ros2" report — check this
  before anything else.
- **`set -u` before sourcing a ROS setup script kills the script.** <!-- id: set-u-breaks-source --> ROS's
  own `setup.bash` reads unset variables, so a strict-mode wrapper
  (`set -euo pipefail` at the top, then `source /opt/ros/<distro>/
  setup.bash`) aborts with an unbound-variable error from inside ROS's
  script — an alarming failure that has nothing to do with your code. Order
  it the other way: source first, *then* `set -u`. Verified 2026-07-11
  (nav-trial).
- **`ros2 launch` as container PID 1 ignores SIGTERM.** <!-- id: launch-pid1-sigterm --> The kernel drops
  unhandled signals to PID 1, and launch installs no SIGTERM handler — so
  the normal teardown path (`docker stop`, or an in-container
  `os.kill(1, SIGTERM)`) is a silent no-op and the container sits there
  until the 10 s timeout escalates to SIGKILL, taking the sim down hard.
  **SIGINT** hits launch's real shutdown path (clean exit 0, nodes
  shut down in order — verified in-container 2026-07-12, nav-trial demo).
  Either send SIGINT, or don't run launch as PID 1: an init shim
  (`docker run --init`, `tini`) reaps and forwards signals properly and is
  the better default for any launch-as-entrypoint image.
- **TurtleBot 4 with zero ROS topics? Check Wi-Fi before blaming DDS.** <!-- id: tb4-wifi-dds -->
  `ros2 topic list` empty *and* `turtlebot4.service` FAILED with `rcl node's
  rmw handle is invalid, at ./src/rcl/node.c:415` means node creation itself
  failed for lack of a DDS network interface — not a ROS bug or a QoS issue.
  Root cause (2026-07-24, tb4-teleop): the robot never joined Wi-Fi (`wlan0`
  DOWN) while `/etc/turtlebot4/cyclonedds_rpi.xml` binds CycloneDDS to `wlan0`
  only, so DDS had no interface to bind and every node's rmw handle came up
  invalid. Fix: bring `wlan0` up (join the network), then `systemctl restart
  turtlebot4.service` → topics return (24 in that session). Verified 2026-07-24
  (tb4-teleop).
- **TurtleBot 4: when the Create 3 base is invisible to the Pi, restart the
  base's *application* — the Pi-side config is almost never the problem.** <!-- id: create3-restart-app -->
  Symptom: `ros2 node list` shows no `/motion_control`, no `/battery_state`,
  and `/cmd_vel` reaches nothing (the robot won't drive), yet the base pings on
  `usb0` (`192.168.186.2`). `/scan` keeps streaming because the RPLIDAR is a
  Pi-local node, which masks the break completely — seeing the scan proves
  nothing about the base link. The same wedge also follows a Pi reboot or a
  network flip (signature then: `/motion_control` node count 0, only
  `/robot_state_publisher` left, no `/wheel_status` or `/battery_state`; seen 3×+,
  tb4-teleop). The cause is the Create 3's **ROS 2 application getting stuck**,
  and it's fixed **on the base, not the Pi**. Prefer the scriptable endpoint
  over clicking the web UI:
  `curl -X POST -H "Content-Type: application/json" -d '{}' http://192.168.186.2/api/restart-app`
  — the endpoint REQUIRES a JSON body, so a bare `curl -X POST` hangs (curl exit
  28 / HTTP 000). ~30 s later `/motion_control` returns and `/cmd_vel`'s
  subscription count goes 0→1, so this one-liner can back a self-healing
  watchdog. Related base endpoints: `/api/reboot`, `/api/forget-wifi`,
  `/api/restart-ntpd`. Equivalent by hand: the Create 3 web UI →
  **Application → Restart application**.
  Reach the web UI headlessly by tunneling it off the Pi-only `usb0` net:
  `ssh -L 8888:192.168.186.2:80 ubuntu@<robot>` → `http://localhost:8888` →
  Application → Configuration (confirm `RMW_IMPLEMENTATION`, ROS_DOMAIN_ID, and
  namespace all match the Pi — they usually already do) and Restart application.
  **Dead-ends — ~10 Pi-side attempts across two builds, none worked:** editing
  `CYCLONEDDS_URI` (unset / explicit `usb0` / unicast `<Peers>` to the base),
  FastDDS discovery-server mode, matching Pi/base clocks, `POST
  http://192.168.186.2/api/reboot`, and a full physical power-cycle
  (storage-mode → dock). A `CYCLONEDDS_URI` edit that once *seemed* to fix this
  did **not** reproduce — the DDS interface config and the clock are red
  herrings. Verified 2026-07-25 (tb4-teleop): after Restart application,
  `/motion_control` back, `/battery_state` → 0.97, robot drove.
- **Inspecting Create 3 (best-effort) topics from the CLI.** <!-- id: create3-qos-cli --> `ros2 topic echo`
  defaults to RELIABLE QoS and silently receives nothing from the base's
  best-effort publishers — pass `--qos-reliability best_effort`. And
  `ros2 topic pub --once /cmd_vel …` HANGS on "Waiting for at least 1 matching
  subscription" because the base subscribes in a separate DDS realm invisible
  to the publisher (so `ros2 topic info /cmd_vel` also shows 0 subscribers
  even when working) — add `-w 0` to publish without waiting. For a base-alive
  check, echo a *fast* topic (`/imu`, `/wheel_status`) with `--once`, not
  `/battery_state` — the battery publishes slowly, so `--once` on it returns
  nothing even on a healthy base and reads as a false "base dead". Verified
  2026-07-24 and 2026-07-26 (tb4-teleop).
- **TurtleBot 4 / Create 3 stops obeying *backward* commands — it's a safety
  reflex, not your teleop.** <!-- id: create3-safety-override --> The cliff sensors face forward only, so the base
  limits reverse travel (it can't see a cliff behind it) and silently drops back
  commands after a short distance. The `motion_control` node's `safety_override`
  string parameter controls it: `none` (default, full safety) / `backup_only`
  (removes the back-up limit, KEEPS cliff safety — usually what you want) /
  `full` (all safety off). Runtime: `ros2 param set /motion_control
  safety_override backup_only` (resets on base-app restart). Persist via the
  Create 3 web UI → Application → "Application ROS 2 Parameters File" (raw YAML,
  unvalidated): `/motion_control: {ros__parameters: {safety_override:
  "backup_only"}}`, then Restart application. Verified 2026-07-26 (tb4-teleop:
  get `none` → set → `backup_only`); docs
  `iroboteducation.github.io/create3_docs/api/safety/`.

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


- 1.6.0 (2026-08-02): add Usage patterns; add Usage patterns [reasons: obs-ros2-001, obs-ros2-003] (applied by apply_deltas)
- 1.5.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.5.0 (2026-07-31): tb4-teleop absorption — new gotcha: TB4 zero topics +
  `turtlebot4.service` "rcl node's rmw handle is invalid (node.c:415)" = Wi-Fi
  down (`wlan0`) while cyclonedds_rpi.xml binds DDS to `wlan0` only (bring up
  Wi-Fi, restart the service → 24 topics); and UPGRADED the Create 3 base-app
  restart from a web-UI click to the scriptable
  `curl -X POST .../api/restart-app` one-liner (requires a JSON body or it hangs,
  exit 28 / HTTP 000; ~30 s to recover; enables a self-healing watchdog).

- 1.4.0 (2026-07-26): tb4-teleop absorption — two Create 3 gotchas: reverse
  commands silently dropped by the base backup-limit reflex → set
  `motion_control` `safety_override=backup_only` (persist via the base web-UI
  ROS 2 Parameters YAML); and base-alive checks should echo a fast topic
  (`/imu`, `/wheel_status`), not the slow `/battery_state` (false "base dead").

- 1.3.0 (2026-07-25): tb4-teleop — CORRECTS the 1.2.0 base-invisible fix. The
  real, reliable fix is the base's web-UI **Application → Restart application**
  (the Create 3 ROS 2 app gets stuck); the Pi-side `CYCLONEDDS_URI` edit was
  coincidental and did NOT reproduce (~10 Pi-side attempts failed across two
  builds). Added the `ssh -L` tunnel for reaching the base web UI headlessly.

- 1.2.0 (2026-07-24): tb4-teleop absorption — two TurtleBot 4 / Create 3
  gotchas that cost ~7 failed resets: the stock `CYCLONEDDS_URI` interface
  restriction blocks base discovery over `usb0` (robot won't drive; `/scan`
  masks it — disable the export), and Create 3 base topics need
  `--qos-reliability best_effort` to echo plus `-w 0` to `ros2 topic pub`
  (split-DDS hides the subscriber). Clock-skew ruled out as a red herring.

- 1.1.0 (2026-07-13): nav-trial absorption — two container/shell gotchas
  that cost real debugging time: `set -u` before sourcing a ROS setup
  script aborts on ROS's own unset vars (source first, then set -u), and
  `ros2 launch` as PID 1 ignores SIGTERM (kernel drops unhandled signals to
  PID 1) so teardown must use SIGINT or an init shim. Both were previously
  captured only in demo-specific notes.

- 1.0.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
