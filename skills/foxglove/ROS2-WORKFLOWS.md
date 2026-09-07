# Foxglove WebSocket and ROS 2 workflows

Verify commands and launch arguments against the installed bridge. The package
and SDK surfaces have changed across releases.

## Live bridge

- Run `foxglove_bridge` on the robot or ROS host so it discovers the local
  graph. The normal case does not require one bridge declaration per topic.
- Connect the client to that WebSocket over a private network, VPN, or tunnel.
  A typical local bridge has used port `8765`, but treat the live configuration
  as authoritative.
- Use the bridge's allow/deny or topic-selection controls when a remote link
  cannot carry the whole graph.

## Record and replay

ROS 2 can record MCAP through `ros2 bag`; confirm the storage plugin and current
CLI flags for the selected distro. Record only the needed topics for a large
graph, while retaining `/tf`, `/tf_static`, and `/clock` when they explain the
data. The resulting MCAP can be opened without a live bridge.

## Navigation goals and layouts

- In Robium's 2026-07-11 Jazzy Nav2 trial, the 3D Publish tool's ROS 1-era
  pose-topic default sent goals to `/move_base_simple/goal`, while Nav2 consumed
  `/goal_pose`. Setting the Pose topic to `/goal_pose` made click-to-navigate
  work; `/initialpose` was correct for AMCL in that setup.
- Topic and action names remain application contracts. Inspect the live graph
  instead of copying those names universally.
- Export and commit one focused layout per task. Robium's navigation layout
  preserved the pose topic and useful displays so a new session did not depend
  on manual configuration.

## Teleoperation and actions

- The Teleop panel publishes `geometry_msgs/Twist`; set conservative linear and
  angular values and verify the actual command topic and message type before
  moving physical hardware.
- In the 2026-07-24 TurtleBot 4 trial, topic publishing and service calls were
  available but ROS 2 action calls were not. A small robot-side node translated
  trigger topics into dock/undock action goals. Re-check current client
  capability before preserving that adapter in a new app.
- Persist both the bridge and any control adapter as supervised services. In
  the 2026-07-26 trial, both disappeared after a Pi reboot until separate
  `systemd` units with restart policies were installed.

## Custom WebSocket clients

In Robium's 2026-07-25 live-hardware test, bridge 3.4.2 accepted the
`foxglove.sdk.v1` subprotocol. A publisher advertised a channel in JSON and
sent binary client-message frames containing the channel ID and CDR payload.
Older `foxglove.websocket.v1` examples were rejected. This is exact evidence
for that bridge build; use the current
[Foxglove SDK](https://github.com/foxglove/foxglove-sdk) protocol documentation
before implementing or testing a hand-rolled client.
