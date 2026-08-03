# The ros_gz bridge

`ros_gz_bridge`'s `parameter_bridge` exchanges messages between ROS 2 topics/
services and Gazebo Transport topics/services. Everything below is sourced
directly from the `gazebosim/ros_gz` repo's `ros_gz_bridge/README.md`
(`ros2` branch), fetched via raw GitHub `curl` on 2026-07-10; the CLI
syntax, the YAML field list, and the message-type table are copied from that
file's own examples, not reconstructed from memory or search snippets.

## ROS 2 / Gazebo pairing (verify before installing)

From the same repo's top-level `README.md`, fetched directly on 2026-07-10:

| ROS 2 | Gazebo | Binaries |
|---|---|---|
| Jazzy | Harmonic | packages.ros.org (`jazzy` branch) |
| Jazzy | Garden | source only; Garden is EOL |
| Kilted | Ionic | packages.ros.org |
| Lyrical | Jetty | packages.ros.org |
| Lyrical | Harmonic / Ionic | source only |
| Rolling | Jetty | packages.ros.org |
| Rolling | Harmonic / Ionic | source only |

The robium nav vertical (`nav2` skill) targets Jazzy, so this skill's
nav-facing examples use the Jazzy/Harmonic row with prebuilt binaries
(`sudo apt-get install ros-jazzy-ros-gz`). Re-fetch this table before
picking a pairing for a different ROS 2 distro; it changes with every new
named Gazebo or ROS 2 release.

## Ad-hoc CLI bridging (one-off use only)

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /chatter@std_msgs/msg/String@gz.msgs.StringMsg
```

The `@` syntax is bidirectional; `[` (ROS→GZ dropped, i.e. GZ→ROS only) or
`]` (ROS→GZ only) replace the middle `@` for a unidirectional bridge, e.g.
`/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock` for the one-way `/clock`
bridge Gazebo itself recommends (see below). This skill's key directives
reserve ad-hoc CLI bridges for quick tests; a real project's bridge set
belongs in a YAML config file (below).

## YAML config file (the recommended approach)

Pass a YAML file via the `config_file` ROS parameter:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=path/to/bridge.yaml
```

The file is a YAML array of maps, one per bridge. Every field below is
copied from the README's own "Example 5" (`ros_gz_bridge/test/config/
full.yaml`'s documented shape):

```yaml
- ros_topic_name: "ros_chatter"
  gz_topic_name: "gz_chatter"
  ros_type_name: "std_msgs/msg/String"
  gz_type_name: "gz.msgs.StringMsg"
  subscriber_queue: 5       # default 10 if qos_profile is empty
  publisher_queue: 6        # default 10 if qos_profile is empty
  lazy: true                # default false; only bridge while someone's subscribed
  direction: BIDIRECTIONAL  # or GZ_TO_ROS / ROS_TO_GZ
  qos_profile: SENSOR_DATA  # default: a default-constructed QoS
  frame_id: "map"           # optional: override the ROS message header's frame_id
```

`topic_name` sets both sides at once if `ros_topic_name`/`gz_topic_name`
aren't given separately. `direction` defaults to `BIDIRECTIONAL`; sensor
data and `/clock` should be `GZ_TO_ROS`, and command topics like `/cmd_vel`
should be `ROS_TO_GZ`; see `examples/ros-gz-bridge-config.yaml`.

YAML config does not support launch-time substitutions (e.g. a
parametrized world/robot name); use the XML or Python launch-file forms
(`<ros_gz_bridge>` tags, or a `parameter_bridge` `Node` with
`bridges.<name>.<setting>` parameters) instead when that's needed; both are
documented in the same README ("Example 6"/"Example 7") and can be combined
with a YAML `config_file` on the same bridge instance.

## Message type table (subset relevant to this skill)

Full table is much longer (services, geometry, actuator types); this is the
subset this skill's examples use, copied verbatim from the README:

| ROS type | Gazebo Transport type |
|---|---|
| `rosgraph_msgs/msg/Clock` | `gz.msgs.Clock` |
| `geometry_msgs/msg/Twist` | `gz.msgs.Twist` |
| `nav_msgs/msg/Odometry` | `gz.msgs.Odometry` |
| `tf2_msgs/msg/TFMessage` | `gz.msgs.Pose_V` |
| `sensor_msgs/msg/LaserScan` | `gz.msgs.LaserScan` |
| `sensor_msgs/msg/Imu` | `gz.msgs.IMU` |
| `sensor_msgs/msg/Image` | `gz.msgs.Image` |
| `sensor_msgs/msg/CameraInfo` | `gz.msgs.CameraInfo` |

See the upstream README for the complete table (batteries, GPS, point
clouds, detections, and more) before bridging a type not listed here.

## `/clock` needs special handling

If Gazebo detects another `/clock` publisher at startup, it falls back to a
fully-qualified `/world/<world>/clock` topic instead, so bridge `/clock`
explicitly and unidirectionally (`GZ_TO_ROS`) so Gazebo stays the sole
`/clock` source: every `use_sim_time:=true` node (Nav2 included; see the
`nav2` skill's Platform gotchas) depends on this topic actually publishing,
or every TF/action timestamp check hangs waiting for a clock that never
arrives.

## `frame_id` / `override_frame_id`

Two related mechanisms, both from the README: the YAML config's `frame_id`
field (shown above) overrides any bridged message's header `frame_id`. The
bridge node's `override_frame_id` ROS parameter does the same thing for a
single ad-hoc CLI-bridged topic, e.g.
`--ros-args -p override_frame_id:=my_optical_frame`. Cameras are the most
common case: Gazebo's camera frame convention isn't ROS's z-forward
optical-frame convention (REP-103), so bridged `Image`/`CameraInfo` topics
typically need this set to whatever optical frame a static transform
publishes.

## Other bridge parameters

`subscription_heartbeat` (default 1000 ms; how often the bridge checks for
new subscribers on `lazy` bridges) and `expand_gz_topic_names` (default
`false`; apply the bridge node's ROS namespace to the Gazebo-side topic
name too, needed when spawning multiple namespaced robots in one world).
