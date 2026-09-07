# ROS 2 failures

Use this router to identify the broken layer before applying a fix.

- **`ros2` or a package is not found**
  - Check the underlay, then the overlay, were sourced in this shell.
  - Confirm the requested package exists in the selected distro and workspace.
  - A ROS setup script may read unset variables; source it before enabling
    shell `set -u`.

- **The workspace does not build**
  - Run dependency resolution before changing code.
  - Identify the first package that fails; downstream `colcon` failures may be
    consequences.
  - Separate absent system dependencies from package metadata and compile
    errors.

- **Nodes cannot see each other**
  - Compare `ROS_DOMAIN_ID`, RMW implementation, namespace, and network reach.
  - Domain ID `0` is shared by default. Unrelated stacks may silently cross-talk.
  - For containers or multiple hosts, move to `integration` once the local ROS
    graph is healthy; DDS discovery must be designed at that boundary.

- **Endpoints exist but no messages arrive**
  - Compare message types and the offered/requested QoS policies on both ends.
  - Use best-effort when inspecting a best-effort publisher; a reliable CLI
    subscriber can otherwise appear healthy while receiving nothing.
  - Check that simulation time and `/clock` advance before changing callbacks.

- **Transforms are unavailable or stale**
  - Find the first missing edge in the TF chain, not merely the final lookup.
  - Compare frame spelling, namespace, timestamp, and static versus dynamic
    ownership.

- **A container ignores shutdown**
  - `ros2 launch` as PID 1 may not follow the expected SIGTERM path. Use an init
    shim or the shutdown signal the launch process handles, and verify an orderly
    exit rather than waiting for the container runtime's forced kill.

Use [the detailed debugging guide](references/debugging.md) for concrete graph,
topic, node, TF, and dependency probes. Confirm command flags with the current
CLI help because distro surfaces change.
