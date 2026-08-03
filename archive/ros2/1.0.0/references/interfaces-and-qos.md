# Interfaces and QoS

A brief map of ROS 2's three communication primitives, then a deep dive on
Quality of Service — the policy set that determines whether a publisher and
subscriber (or client and server) can talk at all — and a short TF2 primer,
since TF2 is itself built on top of these primitives.

Sources: [ros2/ros2_documentation](https://github.com/ros2/ros2_documentation)
(About-Quality-of-Service-Settings.rst, About-Discovery.rst,
Overriding-QoS-Policies-For-Recording-And-Playback.rst, and the TF2 tutorial
set), fetched via ctx7 this session (docs.ros.org was blocked by an anti-bot
page for direct fetch; re-verify there when reachable).

## Topics, services, actions — when to use which

- **Topics** (publish/subscribe): continuous or event streams with no
  request/response coupling — sensor data, state, commands. Many-to-many.
- **Services** (request/response): a single synchronous-feeling call that
  should complete quickly — "give me this value now". One request per call;
  the client blocks (or awaits) until the response arrives.
  `create_publisher`/`create_subscription` become `create_client`/
  `create_service` for services.
- **Actions** (goal/feedback/result): a long-running, preemptible task with
  progress feedback — "navigate to this pose", "pick up this object". Built
  on top of topics and services internally; use when a service would either
  block too long or needs cancel/progress semantics a service can't express.

Custom message/service/action definitions (`.msg`/`.srv`/`.action`) live in
their own `ament_cmake`-typed interface package even in an otherwise
`ament_python` project — Python packages cannot generate interfaces
themselves. This skill doesn't cover writing custom interfaces in depth;
start from an existing type (`std_msgs`, `geometry_msgs`, `sensor_msgs`) when
one fits before reaching for a custom one.

## Quality of Service (QoS): why it exists

ROS 2's transport is built on DDS, and QoS policies are largely inherited
from it. Where ROS 1 had one implicit behavior per primitive, ROS 2 exposes
the underlying knobs — which is more powerful but means two nodes can fail to
connect even though discovery worked and no error was logged on either side.

## The policy set

| Policy | Values | What it controls |
|---|---|---|
| **History** | `keep_last` (N), `keep_all` | How many samples the middleware buffers. `keep_last` + depth is the ROS 1 "queue size" equivalent. |
| **Depth** | integer | The N in `keep_last` — how many samples are buffered before older ones are dropped. |
| **Reliability** | `reliable`, `best_effort` | `reliable` guarantees delivery (retries under the hood); `best_effort` favors throughput/latency and can silently drop samples — the ROS 1 TCPROS vs UDPROS split. |
| **Durability** | `volatile`, `transient_local` | `volatile` (default): late-joining subscribers get nothing published before they connected. `transient_local`: the publisher retains and delivers the last `depth` samples to late joiners — similar to ROS 1's "latched" publishers. |
| **Deadline** | duration | Expected max time between samples; violations are reported, not enforced. No ROS 1 equivalent. |
| **Lifespan** | duration | How long a sample stays valid after publishing — stale samples are dropped instead of delivered. No ROS 1 equivalent. |
| **Liveliness** | `automatic`, `manual_by_topic` | How a node signals "I'm still alive" for this endpoint, paired with a lease duration. No ROS 1 equivalent. |

Not every RMW implementation supports every policy — e.g. `rmw_zenoh_cpp`
does not implement deadline/lifespan. Check the RMW implementation in use
before relying on a less-common policy.

## Compatibility rule — the source of silent failures

**Every QoS policy that affects compatibility must be compatible on both
sides, or no connection is made at all — silently, with no error on either
end.** Discovering each other (nodes see each other in `ros2 node list`) is
not the same as being able to exchange messages. The classic break: a
publisher set to `best_effort` and a subscriber set to `reliable` (a
subscriber can't ask for a stronger guarantee than the publisher offers) —
they discover each other, log nothing, and zero messages cross.

This is why "QoS compatibility is the first suspect" for a node that runs,
discovers its peer, and receives nothing: check `ros2 topic info -v
<topic>` (see `references/debugging.md`) before debugging application logic.

## Preset profiles

Rather than hand-tuning every policy, ROS 2 ships presets for common shapes:

- **Default profile**: `reliable`, `volatile`, `keep_last` depth 10 — the
  right starting point for most topics.
- **Sensor data profile** (`rclpy.qos.qos_profile_sensor_data` /
  `rmw_qos_profile_sensor_data`): `best_effort`, small `keep_last` depth —
  prioritizes the newest sample over guaranteed delivery, appropriate for
  high-rate sensor streams where a dropped frame doesn't matter but latency
  does.
- **Services default profile**: `reliable`, `volatile` — a restarted service
  server shouldn't replay stale requests, so no `transient_local`.
- **Parameters profile**: same shape as services but with a much larger
  queue depth, since parameter-related traffic can burst and shouldn't be
  dropped as readily.

Explicit construction in Python:

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)
publisher = node.create_publisher(String, 'chatter', qos)
```

## Overriding QoS without touching code

`ros2 bag record`/`play` and some tools accept a YAML QoS override file per
topic (history, depth, reliability, durability, deadline, lifespan,
liveliness) — useful for adapting playback QoS to a subscriber's
requirements without re-launching the original publisher. See
`references/debugging.md` for the introspection commands that reveal what a
running topic's actual QoS is, which is the input you need before writing an
override.

## TF2 basics

TF2 is ROS 2's coordinate-frame transform library, itself implemented as
topics (`/tf`, `/tf_static`) under the hood — the same QoS/discovery rules
apply, though TF2's own defaults are tuned for its use case (`/tf_static`
uses `transient_local` so late joiners get static transforms immediately).

Broadcasting a static transform from the CLI (no code needed):

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 1 --yaw 0 --pitch 0 --roll 0 \
  --frame-id world --child-frame-id sensor_link
```

Broadcasting programmatically (`tf2_ros.TransformBroadcaster`) or looking up
a transform (`tf2_ros.Buffer` + `TransformListener`, then
`buffer.lookup_transform(target_frame, source_frame, rclpy.time.Time())`,
wrapped in a try/except for `tf2_ros.TransformException`) follow the same
publish/subscribe shape as any other topic — see
`references/debugging.md` for `tf2_echo`/`view_frames` when a transform
lookup is failing and it's unclear whether the frame exists at all.
