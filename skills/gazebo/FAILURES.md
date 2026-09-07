# Gazebo failures

Use the symptom to locate the failed simulation contract.

- **`gz` is not found in a ROS image**
  - Some ROS packages vendor the CLI beneath `/opt/ros/<distro>`; check that the
    ROS environment is sourced before installing another Gazebo.
  - `gz stats` belongs to Gazebo Classic. For modern Gazebo, inspect the world's
    stats topic and confirm syntax with the current CLI help.

- **The server runs but camera or lidar data is absent**
  - Camera and `gpu_lidar` depend on the render engine even in server-only mode.
  - Check OGRE2/EGL or the software renderer and use the current headless-
    rendering option when no display is present.
  - Physics or odometry continuing does not prove render-backed sensors work.

- **A vendor demo always opens a GUI**
  - Some vendor top-level launch files hardcode a client or do not expose
    headless arguments. In Robium's 2026-07-11 TurtleBot3/Jazzy trial and a
    2026-08-02 TurtleBot4 source review, this happened through two different
    launch structures.
  - Compose the upstream Gazebo server launch with explicit headless arguments
    and reuse the vendor's parameterized spawn, state-publisher, and bridge
    sub-launches rather than copying the entire top-level file.

- **Gazebo topics exist but ROS topics do not**
  - Compare the exact Gazebo topic, ROS topic, message types, direction, and
    bridge configuration.
  - Treat `/clock` separately; without a healthy clock, downstream nodes using
    simulation time can look like bridge or TF failures.

- **Clients repeat `Requesting list of world names.`**
  - Gazebo Transport discovery uses UDP multicast; cloud sandboxes, container
    networks, and some VPNs may drop it.
  - On a same-host deployment, Robium's 2026-07-12 Cloud Run trial restored
    unicast discovery with `GZ_RELAY=127.0.0.1` and `GZ_IP=127.0.0.1`.
    Multi-host setups require a real peer address and a network design.
  - That trial also found a sticky per-boot `SO_REUSEPORT` race: relayed
    announcements reached one of several local sockets and a failed boot did
    not recover. A roughly 120-second no-data watchdog that recycled the
    instance was more effective than an in-process retry loop. These values are
    evidence from those Cloud Run conditions, not universal defaults.

- **It works natively on macOS but not with ROS**
  - Gazebo itself may have a native macOS package; the `ros_gz` path still
    requires a ROS 2 environment, which normally means Linux or a container.

For exact headless flags and bridge fields, use the current CLI help and the
official documentation linked from the main skill.
