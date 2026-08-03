# Debugging

The ROS 2 CLI introspection toolkit, and how to tell apart the handful of
failure signatures that account for most "it doesn't work" ROS 2 reports.

Sources: [ros2/ros2_documentation](https://github.com/ros2/ros2_documentation)
(About-Command-Line-Tools.rst, About-Discovery.rst,
Configuring-ROS2-Environment.rst, Installation-Troubleshooting.rst, the TF2
tutorial set), fetched via ctx7 on 2026-07-10 (docs.ros.org was blocked by an
anti-bot page for direct fetch; re-verify there when reachable).

## First: is the environment actually sourced and configured?

Before touching application-level debugging, rule out environment problems —
they produce error messages that look unrelated to the real cause:

```bash
echo $ROS_DISTRO           # empty or wrong distro → underlay not sourced
ros2 doctor --report       # broad environment/health report in one command
```

- **Empty/wrong `$ROS_DISTRO`, "command not found: ros2"**: the underlay
  wasn't sourced, or was sourced in the wrong shell. `source
  /opt/ros/lyrical/setup.bash` (underlay) then `source install/setup.bash`
  (overlay), in that order, every new shell — see
  `references/workspace-and-packages.md`.
- **Package builds but `ros2 run`/`ros2 pkg list` doesn't see it**: the
  overlay (`install/setup.bash`) wasn't re-sourced after the last build, or
  the package name in `package.xml` doesn't match what you're typing.
- **Two unrelated ROS 2 systems interfering with each other** (nodes you
  didn't start showing up in `ros2 node list`, or traffic from another
  project): a `ROS_DOMAIN_ID` collision — every ROS 2 system defaults to
  domain `0`. `export ROS_DOMAIN_ID=<project-unique-int>` in every shell/
  container for this project.

## Node and topic introspection

```bash
ros2 node list                 # every running node
ros2 node info /my_node        # a node's subs/pubs/services/actions

ros2 topic list                # every active topic
ros2 topic info -v /my_topic   # publisher/subscriber count AND their QoS
ros2 topic echo /my_topic      # print messages as they arrive
ros2 topic hz /my_topic        # measured publish rate
ros2 topic pub /my_topic <type> "<yaml>"   # publish one-off test messages
```

`ros2 topic info -v` is the single most useful command for the QoS-mismatch
failure mode: it prints each publisher's and subscriber's actual QoS profile
side by side, so an incompatible pairing (e.g. one `RELIABLE`, one
`BEST_EFFORT`) is visible directly instead of inferred from silence.

## Diagnosing "node not receiving messages"

Work through these in order — this is the concrete version of the "QoS
compatibility is the first suspect" directive:

1. **Do both nodes appear in `ros2 node list`?** If not, it's a discovery
   problem (domain ID mismatch, network/multicast blocked — see the
   `integration` skill's DDS-across-containers gotchas if this is a
   multi-container setup), not a QoS problem.
2. **Does the topic appear in `ros2 topic list` with both a publisher and a
   subscriber count ≥ 1 in `ros2 topic info -v`?** If either count is 0, the
   node isn't actually creating the publisher/subscription you think it is
   (check the topic name for a typo or an unintended remap) — not a QoS
   problem yet.
3. **Are the QoS profiles shown by `ros2 topic info -v` compatible?**
   Reliability: a subscriber set to `reliable` will not connect to a
   publisher set to `best_effort`. Durability: this only affects *late
   joiners* — a `volatile` publisher won't have delivered anything published
   before a late-joining subscriber connected. Mismatches here produce zero
   messages with no error on either side — this is usually the actual cause
   once steps 1–2 pass. See `references/interfaces-and-qos.md`.
4. **Only after 1–3 check out**, look at application logic (callback errors,
   message filtering, executor not spinning).

## Build and dependency failures

- **`colcon build` fails with a missing header or `ModuleNotFoundError`**:
  almost always an unresolved dependency — run `rosdep install --from-paths
  src -y --ignore-src` before assuming it's a source bug. See
  `references/workspace-and-packages.md`.
- **A package isn't found by colcon at all**: confirm it's actually under
  `src/` and has a valid `package.xml`; a malformed or missing `package.xml`
  makes colcon skip the directory silently rather than erroring loudly.
- **Rebuilding a Python-only change has no effect**: confirm the workspace
  was built with `--symlink-install` — without it, Python file edits require
  a rebuild to take effect, not just a re-source.

## TF2-specific debugging

```bash
ros2 run tf2_ros tf2_echo <source_frame> <target_frame>   # live transform values
ros2 run tf2_tools view_frames                             # renders the current TF tree to a PDF
```

`tf2_echo` failing with "could not find a connection" almost always means
either the broadcaster node isn't running, or the frame names don't match
exactly (case-sensitive, no leading slash in modern TF2) — `view_frames`
shows the whole tree at once, which is faster than guessing frame names one
`tf2_echo` at a time when the tree has more than two or three frames.

## rosdep troubleshooting

- **`rosdep: command not found` / "no such key"**: `sudo rosdep init &&
  rosdep update` hasn't been run on this machine, or the rosdep index is
  stale relative to a newly-released package — `rosdep update` again.
- **A specific key won't resolve**: check it's spelled exactly as it appears
  upstream (rosdep keys are case-sensitive and package-specific, not always
  the same as the apt package name) and that the OS/distro combination is
  actually supported by that package's rosdep rule.
