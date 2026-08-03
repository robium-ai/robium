# Worlds and models

SDF (Simulation Description Format) world/model anatomy for modern Gazebo
(`gz`), how to spawn a model into a running simulation from ROS 2, and how
to run headless. All tag names, plugin filenames, and CLI flags below were
verified on 2026-07-10 by direct `curl` of the raw source files cited in each
section — re-verify before trusting a specific value in a real project, per
this skill's "never write facts from memory" key directive.

## Release/pairing status (verify before using)

Fetched directly via `curl https://gazebosim.org/docs/all/releases/` this
session (HTML stripped, table read from the rendered text — not AI-summarized
search snippets):

| Codename | Start    | EOL      | Support     |
|----------|----------|----------|-------------|
| Jetty    | Sep 2025 | May 2031 | LTS         |
| Ionic    | Sep 2024 | Dec 2026 | Standard    |
| Harmonic | Sep 2023 | May 2029 | LTS         |
| Fortress | Sep 2021 | May 2027 | LTS         |
| Garden   | Sep 2022 | Nov 2024 | EOL         |

Re-fetch this page before starting a new project — Gazebo ships a new named
release roughly every year, and the "current LTS" answer shifts each time
(Jetty superseded Harmonic/Ionic as the newest LTS after this skill's
frontmatter description was written).

## SDF world structure

An SDF file's root is `<sdf version="...">`, containing one or more
`<world name="...">` elements. A world needs at minimum a physics engine and
the scene-broadcaster system plugin to be usable from the GUI or `gz topic`;
adding *any* `<plugin>` to a world that had none disables Gazebo's implicit
defaults, so an explicit minimal set is required once you add your first
plugin (source: Gazebo's Sensors tutorial, `harmonic/sensors.md`, fetched
directly on 2026-07-10):

```xml
<sdf version="1.9">
  <world name="demo">
    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics" />
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster" />
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands" />
    <!-- add gz-sim-sensors-system if the world has camera/gpu_lidar
         sensors — see references/sensors.md -->
  </world>
</sdf>
```

`<physics name="1ms" type="ignored">` with `<max_step_size>`/
`<real_time_factor>` children controls the simulation step; a
`<light type="directional">` and a static `ground_plane` model are the usual
minimum for a visually sane world (source: `gazebosim/docs`'
`harmonic/tutorials/moving_robot/moving_robot.sdf`, fetched directly this
session).

## Model, link, and joint anatomy

A `<model name="..." canonical_link="...">` contains `<link>` elements
(each with `<inertial>`, `<visual>`, `<collision>`), `<joint>` elements
connecting pairs of links (`<parent>`/`<child>`, an `<axis>` with `<limit>`
for revolute joints), and optional `<frame>` elements for named offset poses
(e.g. where a sensor attaches) without adding an extra link. Poses
(`<pose relative_to="...">`) are relative by default to the model's own
frame unless `relative_to` names another link or frame — this is how a
sensor mounted on `chassis` gets positioned without redundant math. See
`examples/diffdrive-world-snippet.sdf` for a worked single-link example;
the upstream `moving_robot.sdf` (cited above) shows the fuller
chassis+two-wheels+caster pattern this example is adapted from.

## Referencing models with `<include>`

`<include><uri>...</uri></include>` pulls in a model either from a local
path, a Fuel URL
(`https://fuel.gazebosim.org/1.0/<owner>/models/<name>`), or a
`package://<ros_pkg>/<path>` URI once a ROS package exports its model
directory via `package.xml`'s `<export><gazebo_ros
gazebo_model_path="${prefix}/../"/></export>` tag (source: `ros_gz_sim`
README, fetched directly on 2026-07-10 — see the tag's exact semantics
there, including the `${prefix}` expansion to the package's installed share
path).

## The `DiffDrive` system plugin

`gz-sim-diff-drive-system` (`gz::sim::systems::DiffDrive`) is the standard
differential-drive controller. Parameters (source: `gz-sim`'s
`DiffDrive.hh` header comment, fetched directly via raw GitHub this
session — this is the plugin's own doc, not a summary):

| Tag | Default | Notes |
|---|---|---|
| `<left_joint>` / `<right_joint>` | — | required, repeatable for multi-wheel |
| `<wheel_separation>` | 1.0 m | |
| `<wheel_radius>` | 0.2 m | |
| `<odom_publish_frequency>` | 50 Hz | |
| `<topic>` | `/model/<model>/cmd_vel` | set explicitly for a flat, unscoped name |
| `<odom_topic>` | `/model/<model>/odometry` | |
| `<tf_topic>` | `/model/<model>/tf` | publishes `gz.msgs.Pose_V` |
| `<frame_id>` | `<model>/odom` | the odometry/TF parent frame |
| `<child_frame_id>` | `<model>/<link>` | the odometry/TF child frame |
| `<min_velocity>`/`<max_velocity>`, `*_acceleration`, `*_jerk` | unset | optional linear/angular limits, each overridable per-axis |

Setting `<topic>/cmd_vel</topic>`, `<odom_topic>/odom</odom_topic>`,
`<frame_id>odom</frame_id>`, and `<child_frame_id>base_link</child_frame_id>`
explicitly (rather than leaving the model-scoped defaults) is what makes a
single-robot world's gz topics and TF frames line up with what `nav2`
expects (`odom`→`base_link`) without a namespace prefix — see
`examples/diffdrive-world-snippet.sdf`.

## Spawning a robot from SDF/URDF

`ros_gz_sim`'s `create` executable (source: `ros_gz_sim/src/create.cpp`,
fetched directly on 2026-07-10 — flags read from its `gflags::DEFINE_*`
declarations, not inferred) spawns an entity via a ROS 2 process rather than
a raw Gazebo Transport service call:

```bash
ros2 run ros_gz_sim create -world default -file /path/to/model.sdf \
  -name my_robot -x 0 -y 0 -z 0.1
```

Flags: `-world`, `-file` (path or Fuel URL), `-param` (load XML from a ROS
parameter), `-string` (load XML from a literal string), `-topic` (subscribe
to a latched `std_msgs/msg/String` publisher — the pattern for spawning a
URDF that `robot_state_publisher` already published to
`/robot_description`), `-name`, `-allow_renaming`, and `-x`/`-y`/`-z`/`-R`/
`-P`/`-Y` for the initial pose. `ros2 run ros_gz_sim create --helpshort`
prints the live flag list — check it against a specific `ros_gz` version
before scripting around it.

## Running headless

`gz sim -s -r <world>.sdf` — `-s` runs the server only ("headless mode",
overriding `-g` if also given) and `-r` starts the simulation running
immediately rather than paused. Add `-v 4` for debug-level console output,
`--headless-rendering` if the world has GPU-rendered sensors and there is no
display (see `references/sensors.md`), and `--record` (or
`--record-path <dir>`) to log state for later playback. Source: `gz-sim`'s
own CLI help text, `src/cmd/cmdsim.rb.in`, fetched directly via raw GitHub
on 2026-07-10 — this is the authoritative flag list, not a tutorial's subset
of it.
