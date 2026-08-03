# Sensors

SDF sensor tags for IMU, contact, lidar, and camera, the system plugins each
depends on, and the shared `<noise>` element. All tags below were verified
on 2026-07-10 by direct `curl` of the raw source files cited per section —
re-verify before trusting a specific default in a real project.

## Shared pattern

Every sensor is a `<sensor name="..." type="...">` element inside a
`<link>`, with common tags `<always_on>` (update per `<update_rate>` if
true), `<update_rate>` (Hz), `<visualize>` (show in the GUI), and `<topic>`
(the gz topic data is published on — set explicitly for a flat, predictable
name rather than relying on the model-scoped default). Source: Gazebo's
Sensors tutorial (`harmonic/sensors.md`, `gazebosim/docs` repo, fetched
directly on 2026-07-10 — the tutorial that ships with the Harmonic release
this skill's nav-facing examples target).

## IMU

Requires the `gz-sim-imu-system` world plugin (`gz::sim::systems::Imu`).
Outputs `orientation` (quaternion), `angular_velocity`, and
`linear_acceleration`:

```xml
<!-- under <world> -->
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu" />

<!-- under a <link> -->
<sensor name="imu_sensor" type="imu">
  <always_on>1</always_on>
  <update_rate>100</update_rate>
  <visualize>true</visualize>
  <topic>imu</topic>
</sensor>
```

No GPU/render engine dependency — IMU is computed directly from the physics
engine's link state.

## Contact

Requires `gz-sim-contact-system`. Reports when a named collision touches
another:

```xml
<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact" />

<sensor name="sensor_contact" type="contact">
  <contact>
    <collision>collision</collision>
  </contact>
</sensor>
```

Commonly paired with `gz-sim-touchplugin-system` (fires when a named
`<target>` model touches the sensor's owner, publishing to
`<namespace>/touched`) and `gz-sim-triggered-publisher-system` (publishes a
configured message when an input topic matches a pattern — e.g. stop the
robot on contact). No GPU dependency.

## Lidar

Use the current preferred type/tag `type="gpu_lidar"` with a `<lidar>`
element — `type="ray"`/`type="gpu_ray"` with a `<ray>` element are legacy
aliases, structurally identical but flagged for eventual deprecation in the
SDF spec (source: `sdformat`'s `sensor.sdf` schema file, fetched directly
on 2026-07-10: "It is preferred to use ... 'lidar', 'gpu_lidar' ... since
'ray', 'gpu_ray' ... will be deprecated"). Requires the `gz-sim-sensors-
system` world plugin with an explicit render engine (GPU-rendered, unlike
IMU/contact):

```xml
<!-- under <world> -->
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>

<!-- under a <link> -->
<sensor name="gpu_lidar" type="gpu_lidar">
  <topic>scan</topic>
  <update_rate>10</update_rate>
  <lidar>
    <scan>
      <horizontal>
        <samples>640</samples>
        <resolution>1</resolution>
        <min_angle>-1.396263</min_angle>
        <max_angle>1.396263</max_angle>
      </horizontal>
      <vertical>
        <samples>1</samples>
        <resolution>0.01</resolution>
        <min_angle>0</min_angle>
        <max_angle>0</max_angle>
      </vertical>
    </scan>
    <range>
      <min>0.08</min>
      <max>10.0</max>
      <resolution>0.01</resolution>
    </range>
    <noise>
      <type>gaussian</type>
      <mean>0.0</mean>
      <stddev>0.01</stddev>
    </noise>
  </lidar>
  <always_on>1</always_on>
  <visualize>true</visualize>
</sensor>
```

`<samples>`/`<resolution>` under `<horizontal>`/`<vertical>` control ray
count and interpolation; `<range>` bounds each ray's min/max distance and
linear resolution. Source: Gazebo's Sensors tutorial for the `<lidar>`
child tags, `sdformat`'s `lidar.sdf` schema file for the authoritative
element list including `<noise>` (both fetched directly on 2026-07-10; the
tutorial itself still shows the legacy `<ray>` tag — this reference
recommends `<lidar>` per the schema's own deprecation note above).

## Camera

Also requires `gz-sim-sensors-system` (GPU-rendered):

```xml
<sensor name="camera" type="camera">
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image>
      <width>640</width>
      <height>480</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>100</far>
    </clip>
  </camera>
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <visualize>true</visualize>
  <topic>camera</topic>
</sensor>
```

Source: `gz-sim`'s `examples/worlds/camera_sensor.sdf`, fetched directly via
raw GitHub on 2026-07-10. Camera images bridge to ROS through `ros_gz_image`
(unidirectional, `image_transport`-based) or `ros_gz_bridge`'s
`sensor_msgs/msg/Image` mapping — see `references/ros2-bridge.md`. The
bridge's `override_frame_id` parameter is the documented way to point a
bridged `Image`/`CameraInfo` message's `frame_id` at a proper z-forward
optical frame (REP-103), since Gazebo's own camera frame convention differs
from ROS's.

## Noise (shared element)

The `<noise type="...">` element (`sdformat`'s `noise.sdf` schema, fetched
directly on 2026-07-10) is the general form used across sensor types beyond
the lidar-specific block shown above:

| Tag | Applies to `type="gaussian*"` |
|---|---|
| `<mean>` | mean of the sampled noise value |
| `<stddev>` | standard deviation of the sampled noise value |
| `<bias_mean>` / `<bias_stddev>` | a per-run constant bias, itself drawn from a Gaussian |
| `<dynamic_bias_stddev>` / `<dynamic_bias_correlation_time>` | slow bias drift over time (e.g. IMU gyro drift) |

`type="gaussian_quantized"` additionally rounds outputs to a `<precision>`
step. A sensor left at the tutorial/example defaults (frequently zero
noise) will not expose the same failure modes a downstream consumer will hit
against the real sensor — set noise from the real sensor's datasheet, per
this skill's sensor-correctness key directive.

## GPU dependency and headless rendering

IMU and contact sensors have no render-engine dependency. Camera and
`gpu_lidar` sensors do, via `gz-sim-sensors-system`'s render engine (OGRE2
by default) — see this skill's Platform gotchas for headless-rendering and
GPU-vs-software-rendering guidance when running these sensor types without
a display or GPU.
