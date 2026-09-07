# Gazebo and ROS 2 on Cloud Run

This compatibility card records Robium's Gazebo Harmonic, ROS 2, and Nav2
deployment observations from 2026-07-12/13. It does not define defaults for
other simulator, middleware, or bridge versions.

## Discovery boundary

- Cloud Run provided no usable UDP multicast for Gazebo transport or DDS
  discovery.
- The tested single-container stack used `GZ_RELAY=127.0.0.1` and
  `GZ_IP=127.0.0.1` for Gazebo transport, and
  `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` to avoid Fast DDS shared-memory errors.
- Verify current environment-variable behavior against the
  [Gazebo transport relay documentation](https://gazebosim.org/api/transport/14/relay.html)
  and the middleware version actually installed.

## Sticky Gazebo boot failures

- With more than two Gazebo processes, Robium observed a per-boot unicast relay
  race: a boot either discovered the world or never recovered.
- The failure signature was repeated `Requesting list of world names.` with no
  Gazebo output, odometry, or scan data.
- A status node watched for first simulator data and terminated PID 1 after
  roughly 120 seconds without it. A fresh instance could then boot on reconnect.
- The trial lost roughly half of affected boots. Preserve the watchdog as a
  bounded recovery for this tested topology, then re-measure it for another
  Gazebo process layout.

## Process and readiness behavior

- The tested `ros2 launch` process running as PID 1 shut down correctly on
  `SIGINT`; assuming `SIGTERM` caused the container to remain alive. Verify the
  actual entrypoint rather than generalizing this signal choice.
- Readiness meant simulator data, required ROS nodes, and an application metric
  such as real-time factor, not merely an open HTTP port.
- A 2.5 GB ROS image added about 30 to 90 seconds on a fresh node during the
  measured deployment. State a measured cold-start window on the public page.

## Session isolation

- Concurrent ROS stacks on a shared host need distinct discovery domains.
  Robium's local orchestrator assigned a free `ROS_DOMAIN_ID` for each
  instance; a fixed domain merged graphs and produced backward-time transform
  warnings.
- Cloud Run instance isolation does not replace application-level access
  control when the demo requires it. Keep first-claim coordination and real
  authorization distinct.
