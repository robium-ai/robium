# Foxglove and Lichtblick failures

- **The client says the bridge is unreachable**
  - Confirm the robot, container runtime, and bridge process are actually up.
  - Prove the configured port is listening and reachable from the client host.
  - Check VPN, tunnel, firewall, and address binding before changing ROS code.

- **The web client cannot open a local `ws://` connection**
  - An HTTPS page may block insecure WebSockets as mixed content. In Robium's
    2026-07-11 test Safari blocked `ws://localhost` while the bridge was healthy.
    A desktop client, compatible browser, secure proxy, or Lichtblick may avoid
    that browser-origin policy.

- **A custom client receives HTTP 400 about a missing subprotocol**
  - Bridge 3.x builds may expect `foxglove.sdk.v1` rather than the older
    `foxglove.websocket.v1`. Inspect the installed build and current protocol
    documentation; the viewer applications negotiate this automatically.

- **The connection works but panels stay blank**
  - Prove the topic locally, then compare namespace, message schema, QoS, frame,
    and time.
  - Some topics stream only while a panel subscribes. A topic absent from a 3D
    view may simply be disabled in that panel.

- **Remote viewing is laggy**
  - Measure topic and message rates. Limit high-bandwidth streams at the bridge
    or recording source; panel filtering changes display, not network traffic.

- **Restarting the bridge over SSH kills the session**
  - In the 2026-07-24 TurtleBot 4 trial, `pkill -f foxglove_bridge` also matched
    the launch command being started and terminated the SSH shell. Freeing the
    configured listening port targeted the old process more safely. Resolve the
    exact process or port before killing anything.

- **Teleop moves nothing or a button cannot call an action**
  - Confirm the panel's topic, message type, scale, and the robot-side
    subscription.
  - If the client cannot invoke the required ROS action, use a narrowly scoped
    robot-side adapter and prove the trigger-to-action path; see
    [ROS 2 workflows](ROS2-WORKFLOWS.md).

The bridge normally has no application-level authentication. Do not expose it
directly to the public internet as a workaround for reachability.
