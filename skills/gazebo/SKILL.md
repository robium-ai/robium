---
name: gazebo
version: 1.3.2
description: >
  Modern Gazebo (gz — Harmonic/Ionic line) simulation: SDF worlds and models,
  sensors (lidar, camera, IMU, contact), the ros_gz bridge, spawning robots,
  and headless/server operation. Use when: 'gazebo', 'gz sim', 'ros_gz',
  'simulate the robot', 'add a lidar to the sim', simulating mobile robots or
  sensors in the ROS ecosystem. Pairs with ros2 and nav2; simulator SELECTION
  lives in the simulation skill. Gazebo Classic (11) is EOL — this skill
  covers modern gz only and must never recommend Classic. Not for: Isaac Sim
  (isaac-sim) or non-ROS simulation.
---

# gazebo

The sim half of the robium nav-vertical trial run: modern Gazebo (the `gz`
tools — Gazebo Classic/`gazebo11` is a separate, EOL project and out of scope
everywhere in this skill) for building SDF worlds and models, attaching
sensors, bridging topics to ROS 2 via `ros_gz`, spawning robots, and running
headless. as of 2026-07-10, Gazebo's current named releases are **Jetty**
(LTS, Sep 2025 – May 2031), **Ionic** (standard support, Sep 2024 – Dec 2026),
and **Harmonic** (LTS, Sep 2023 – May 2029) — verified by direct `curl` of
`gazebosim.org/docs/all/releases/` on 2026-07-10, which also lists the older
Fortress LTS (Sep 2021 – May 2027) still inside its support window. Jetty is
now the newest LTS, one release past the Harmonic/Ionic line named in this
skill's description; re-verify the release list before trusting any of this
paragraph in a future session; see `references/worlds-and-models.md`'s
sourcing note. The robium nav vertical (`nav2` skill) targets ROS 2 **Jazzy
Jalisco**, whose paired Gazebo release is **Harmonic** — the `ros_gz`
`jazzy` branch ships prebuilt binaries for that pairing from
packages.ros.org, confirmed by direct fetch of the `ros_gz` README this
session (see References). This skill's nav-facing snippets and examples
target Jazzy + Harmonic for that reason; Ionic (paired with Kilted) is
nearing its Dec 2026 EOL, and Jetty (the newest LTS) pairs with Lyrical or
Rolling, not Jazzy — don't pick either for a new Jazzy-based project without
re-checking the table first.

## When to use this skill

- Building or editing an SDF world or model, adding a sensor (lidar, camera,
  IMU, contact) to a robot, wiring a `ros_gz` bridge, spawning a robot into a
  running simulation, or running Gazebo headless/server-only.
- The trigger phrases in the description: 'gazebo', 'gz sim', 'ros_gz',
  'simulate the robot', 'add a lidar to the sim'.
- Someone mentions Gazebo Classic tutorials, `gazebo11`, or the old
  `libgazebo_ros_*` plugin names — flag that they don't apply here (Classic
  is EOL) and redirect to this skill's modern `gz`/`ros_gz` equivalents.
- Cross-references — go to the sibling skill instead when the question is:
  - **Which simulator to use at all** (Gazebo vs. Isaac Sim vs. something
    else) → the `simulation` skill. This skill assumes Gazebo has
    already been chosen.
  - Generic ROS 2 mechanics the bridge or a spawned robot's launch file rides
    on (workspaces, colcon, launch files, TF2 concepts, QoS) → `ros2`. This
    skill's only TF content is what the `ros_gz` bridge or a sim plugin
    itself publishes.
  - Navigation behavior once sensor data is flowing (costmaps, AMCL,
    behavior trees) → `nav2`. This skill stops at "sensor topics are bridged
    and correctly framed"; what Nav2 does with them is `nav2`'s territory.
  - Isaac Sim specifically → `isaac-sim`.
  - Running `gz`/`ros_gz` inside Docker, GPU passthrough for the *container*,
    or macOS/remote-server environment strategy → `environments`. This
    skill's Platform gotchas section only notes where Docker changes gz's own
    behavior (rendering, display), not how to set the container up.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: embed + links.** SDF anatomy, sensor tags, and the
  `ros_gz` bridge's CLI/YAML syntax live in this skill's references in depth
  — no single upstream page walks through all three as one coherent unit for
  a new project — but every tag, default value, and parameter table links
  back to `gazebosim.org`, the `sdformat` spec, or the `gazebosim/ros_gz`
  GitHub repo rather than being retyped from memory. See References.
- **Never recommend Gazebo Classic (`gazebo11`).** <!-- id: never-recommend-classic --> It reached end-of-life;
  its plugin names (`libgazebo_ros_*`), world format quirks, and tutorials do
  not carry over to modern `gz`. If a search result or an old tutorial
  mentions Classic, say so explicitly and translate to the modern
  equivalent rather than silently using Classic syntax.
- **Bridge every topic explicitly, via a config file, not ad-hoc CLI
  bridges.** <!-- id: bridge-config-file --> A one-off `ros2 run ros_gz_bridge parameter_bridge
  /topic@ros_type@gz_type` per topic is fine for a five-minute test, but a
  real project's bridge set (clock, cmd_vel, odom, tf, every sensor) belongs
  in one YAML config file passed via the `config_file` parameter — it's the
  single reviewable place that states exactly what's bridged, in which
  direction, and at what QoS, and it survives a robot rename without hunting
  down scattered `ros2 run` invocations. See
  `examples/ros-gz-bridge-config.yaml` and
  `references/ros2-bridge.md`.
- **Sensor rates and frames must match the real target robot, not simulator
  defaults.** <!-- id: sensor-rates-match-real --> A lidar simulated at the tutorial's default rate/FOV, or a
  camera with the wrong resolution, produces a stack that "works in sim" and
  then behaves differently the moment it meets real sensor data or a
  downstream consumer (Nav2's costmap update rate, a perception model's
  expected input size) tuned for the real hardware's datasheet. Pull the
  real sensor's rate/FOV/range/frame from its datasheet before simulating it
  — this is the `simulation` skill's correctness-checklist territory;
  this skill only supplies the SDF tags to encode whatever numbers
  that check produces.
- **Never write gz release numbers, EOL dates, or ROS 2/Gazebo pairings from
  memory.** <!-- id: no-release-facts-from-memory --> They change with every named release (Jetty's arrival moved
  Harmonic and Ionic down a rung since this skill's description was
  written). Verify against `gazebosim.org/docs/all/releases/` and the
  `gazebosim/ros_gz` README's compatibility table before repeating a claim
  in a real project — every example in this skill is marked `status:
  unverified` for exactly this reason, and each reference states how its
  claims were checked on 2026-07-10.

## Quick start

**1. Confirm the gz release paired with your ROS 2 distro.** <!-- id: confirm-gz-ros2-pairing --> Check the
compatibility table in `references/ros2-bridge.md` (sourced from the
`gazebosim/ros_gz` README) before installing anything — for the Jazzy-based
nav vertical this skill targets, that's Gazebo **Harmonic**:

```bash
sudo apt-get install ros-jazzy-ros-gz
```

**2. Write or copy a world.** Start from
`examples/diffdrive-world-snippet.sdf` (a minimal differential-drive robot
with lidar and IMU sensors) and see `references/worlds-and-models.md` for
SDF anatomy.

**3. Run it headless and bridge topics.** See the two usage patterns below —
"Run a world headless" and "Bridge sensor topics to ROS 2" — using
`examples/ros-gz-bridge-config.yaml` as the bridge's `config_file`.

**4. Verify data is flowing** <!-- id: verify-data-flowing --> with `ros2 topic echo /scan` (or `/imu`,
`/odom`) before wiring anything downstream (Nav2, a perception node) to it.

## Usage patterns

**Run a world headless.** <!-- id: gz-sim-headless-flags --> `gz sim -s -r <world>.sdf` starts the simulation
server only (`-s`, "headless mode" — overrides `-g` if present) with the
simulation already playing (`-r`, "run simulation on start"); add
`--headless-rendering` (requires OGRE2, the default render engine) when the
world has camera or lidar sensors and there's no X server — see Platform
gotchas. The server alone (`-s`) is not enough for those sensors: Gazebo's lidar
is a render-based `gpu_lidar` sensor, so even a headless server still needs a
working render engine — a GPU, or in a GPU-less container an EGL or llvmpipe
(software rasterizer) backend — or the sensor silently produces nothing. This is
the mode a CI job or a remote/cloud run should use; source
verified from the `gz-sim` CLI's own help text
(`src/cmd/cmdsim.rb.in`, fetched directly on 2026-07-10). See
`references/worlds-and-models.md`.

**Spawn a robot from SDF/URDF.** <!-- id: spawn-robot-create --> Launch Gazebo, then use `ros_gz_sim`'s
`create` executable rather than hand-rolling a Gazebo Transport service call:
`ros2 run ros_gz_sim create -world <world_name> -file <path/to/model.sdf>
-name <robot_name> -x 0 -y 0 -z 0.1` for a file on disk (or a Fuel URL), or
`-topic <topic>` to spawn from a latched `std_msgs/msg/String` publisher —
the pattern for spawning a URDF that a `robot_state_publisher` node already
published to `/robot_description`. See `references/worlds-and-models.md`.

**Bridge sensor topics to ROS 2.** <!-- id: bridge-sensor-topics --> Pass a single YAML file to
`parameter_bridge` rather than one CLI arg per topic (see Key directives):

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=examples/ros-gz-bridge-config.yaml
```

`examples/ros-gz-bridge-config.yaml` bridges `/clock`, `/cmd_vel`, `/odom`,
`/tf`, `/scan`, and `/imu` for the robot in
`examples/diffdrive-world-snippet.sdf` — the gz-side topic names in that
world and the `gz_topic_name`s in the bridge config are kept in sync
deliberately; renaming one without the other silently breaks the bridge for
that topic. See `references/ros2-bridge.md`.

**Add sensor noise.** <!-- id: sdf-sensor-noise --> Every SDF sensor type accepts a `<noise>` element
(`type="gaussian"`, with `<mean>`/`<stddev>`, plus `<bias_mean>`/
`<bias_stddev>` for slowly-varying sensor bias) — for a lidar it sits inside
`<lidar>` alongside `<scan>`/`<range>`, for IMU/camera it sits inside the
relevant axis/noise block. A sensor with zero noise is a common source of a
perception or localization stack that "works perfectly in sim" and then
struggles on the real sensor's actual noise floor — pull real numbers from
the target sensor's datasheet, per the sensor-rates-and-frames key directive
above. See `references/sensors.md`.

## Platform gotchas

- **GPU vs. software rendering.** <!-- id: gpu-vs-software-rendering --> Camera and `gpu_lidar` sensors go through
  Gazebo's render engine (OGRE2 by default); with a GPU and a display, this
  just works. Headless or GPU-less, use `--headless-rendering` (EGL-backed,
  OGRE2-only) rather than trying to get X11 forwarding working for a
  render-heavy sim — and if there's no GPU at all, OGRE2 falls back to
  software rendering, which works but is markedly slower for camera/lidar-
  heavy worlds. Source: `gazebosim.org`'s Headless Rendering page, fetched
  directly on 2026-07-10. See `references/sensors.md`.
- **Upstream robot-demo launch files often can't run headless as-is.** <!-- id: vendor-launch-not-headless -->
  Vendor demo launches commonly hardcode a gz GUI client and
  non-overridable server `gz_args` (verified 2026-07-11, nav-trial: Jazzy
  `turtlebot3_gazebo`'s `turtlebot3_world.launch.py` unconditionally adds a
  `-g` client and exposes no argument to inject `--headless-rendering`).
  Don't fight the top-level file — include `ros_gz_sim`'s
  `gz_sim.launch.py` yourself with headless `gz_args` (`-r -s
  --headless-rendering`) and reuse the vendor's *sub*-launches (spawn,
  robot_state_publisher, bridge config), which are usually cleanly
  parameterized. Second official-repo witness (confirmed 2026-08-02):
  `turtlebot4_simulator`'s `turtlebot4_gz_bringup/launch/sim.launch.py`
  builds `gz_args` from `world` + `-r` + `-v 4` + `--gui-config` — no
  `-s`/`-g` split, no launch arg to skip the GUI — the same
  no-headless-by-default outcome via a structurally different
  mechanism (one combined launch vs. TB3's two split ones).
- **On a ROS 2 system the `gz` CLI is vendored and needs a sourced env.** <!-- id: gz-cli-vendored-sourced-env -->
  Packages like `ros-jazzy-gz-tools-vendor` install `gz` under
  `/opt/ros/<distro>`, so it's not on PATH until the ROS setup is sourced —
  a bare `gz ...` in a fresh container shell fails with "command not
  found". Also note `gz stats` is a Gazebo Classic command that no longer
  exists; read the real-time factor from `gz topic -e -t
  /world/<world>/stats` instead. Verified 2026-07-11 (nav-trial).
- **gz-transport discovery is UDP multicast — it dies on networks that
  don't carry it.** <!-- id: gz-transport-udp-multicast --> Cloud sandboxes (Cloud Run, many k8s CNIs, some VPNs)
  drop multicast, and the failure is silent-looking: every gz-transport
  client loops `Requesting list of world names.` forever while the server
  prints nothing at all. Fix: unicast relay — `GZ_RELAY=127.0.0.1` plus
  `GZ_IP=127.0.0.1` (same-host processes only; a real multi-host setup
  points `GZ_RELAY` at the peer). Two follow-on facts, both verified live
  (2026-07-12, nav-trial demo on Cloud Run): the relay loses a **sticky
  per-boot race** when several gz-transport processes share a host —
  `SO_REUSEPORT` flow-hashing pins relayed announcements to one socket, so
  a boot either works fully or never recovers (~50/50), which means any
  unattended deployment needs a **boot watchdog** (no sim data within
  ~120 s → kill and let the client reconnect to a fresh instance) rather
  than a retry loop inside the boot. Ruled out along the way: gen1-vs-gen2
  execution environment (no effect) and CPU-throttled boot (a held-open
  connection kept CPU allocated and it still stalled).
- **Running `gz` in Docker.** A ROS 2 + Gazebo + `ros_gz` stack in a
  container needs the same GPU-passthrough and headless-rendering
  considerations as any other GPU-using container workload — that setup
  (`--gpus all`, the NVIDIA Container Toolkit, choosing headless vs. a
  forwarded display) is the `environments` skill's territory, not
  duplicated here; see that skill's Docker and GPU/remote guidance,
  including its example ROS 2 Dockerfile, before building a gz-in-Docker
  image from scratch.
- **macOS status.** <!-- id: macos-gz-native-but-bridge-needs-docker --> `gz sim` itself ships native Jetty binaries for macOS
  via Homebrew (`brew install gz-jetty`, Ventura/Sonoma — verified via
  direct fetch of `gazebosim.org`'s macOS binary-install page on 2026-07-10),
  so Gazebo alone is not Docker-only the way ROS 2 is. But the `ros_gz`
  bridge links against ROS 2, and ROS 2 has no native macOS install (see the
  `ros2` skill's Platform gotchas) — so the full ROS 2 + `gz` + bridge stack
  this skill assumes still needs Docker on a Mac dev machine, even though a
  gz-only world with no ROS integration could run natively there.

## Customization

- **Different gz release / ROS 2 distro pairing:** swap the install command
  and the world/plugin filenames' implicit release assumptions (plugin
  filenames like `gz-sim-diff-drive-system` are stable across releases, but
  package names and binary availability are not) — re-check
  `references/ros2-bridge.md`'s pairing table against the live `ros_gz`
  README first; don't assume the Jazzy/Harmonic pairing this skill defaults
  to still applies once the project moves to a different ROS 2 distro.
- **Different robot / sensor set:** start from
  `examples/diffdrive-world-snippet.sdf`, keep the `DiffDrive` plugin's
  `<frame_id>`/`<child_frame_id>` (`odom`/`base_link`) and the sensors'
  `<topic>` names in sync with whatever bridge config you copy alongside it
  — see `references/worlds-and-models.md` and `references/sensors.md`.
- **Different bridge topic set:** add or remove entries in
  `examples/ros-gz-bridge-config.yaml`; each entry is independent, but a
  removed `gz_topic_name` must also be removed (or renamed together with)
  the SDF side that publishes it, per the Usage patterns note above.

## References

- `references/worlds-and-models.md` — SDF world/model/link/joint anatomy,
  default world plugins, `<include>`/Fuel model references, the `DiffDrive`
  plugin's parameters, and spawning with `ros_gz_sim`'s `create` executable.
- `references/sensors.md` — IMU, contact, lidar (`<lidar>`, the current
  preferred tag over the legacy `<ray>` alias), and camera sensor tags, the
  render-engine-backed `Sensors` system, and the shared `<noise>` element.
- `references/ros2-bridge.md` — `parameter_bridge` CLI syntax, the YAML
  config-file format (every field), the ROS↔gz message-type table, `/clock`
  bridging, and `frame_id`/`override_frame_id` overrides.
- `examples/diffdrive-world-snippet.sdf` — a minimal differential-drive
  robot world with lidar and IMU sensors (status: unverified — file header
  states the exact upstream sources and the deviations made).
- `examples/ros-gz-bridge-config.yaml` — the matching bridge config for the
  world above; topic names are kept in sync between the two files
  deliberately (status: unverified — file header states sourcing).
- Upstream: [Gazebo documentation](https://gazebosim.org/docs/) and
  [Gazebo releases](https://gazebosim.org/docs/all/releases/) (both reached
  via direct fetch on 2026-07-10), [gazebosim/ros_gz
  repo](https://github.com/gazebosim/ros_gz) (bridge source and
  compatibility table, fetched directly on 2026-07-10),
  [gazebosim/gz-sim](https://github.com/gazebosim/gz-sim) (world examples
  and system-plugin sources), [sdformat
  spec](https://sdformat.org/spec/1.12/sensor/) (sensor/noise element
  definitions). Sibling skills: `ros2` (foundation, load alongside), `nav2`
  (consumes this skill's bridged topics), `simulation` (simulator selection),
  `isaac-sim` (GPU photorealistic alternative), `environments`
  (Docker/GPU/remote setup), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->


- 1.3.2 (2026-08-02): annotate vendor-launch-not-headless [reasons: obs-gazebo-001] (applied by apply_deltas)
- 1.3.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.3.0 (2026-07-31): nav-trial finding — clarified the "Run a world headless"
  pattern: lidar is a render-based `gpu_lidar` sensor, so even `gz sim -s`
  server-only still needs a render engine (a GPU, or an EGL/llvmpipe software
  rasterizer in a GPU-less container) or the sensor silently produces nothing.

- 1.2.0 (2026-07-13): nav-trial demo absorption — gz-transport discovery
  is UDP multicast and stalls on networks that drop it (`Requesting list
  of world names.` loop, silent server); documented the `GZ_RELAY`/`GZ_IP`
  unicast fix, its sticky per-boot `SO_REUSEPORT` race, and the boot
  watchdog that makes it survivable. Knowledge previously lived only in
  `live-demo`; placement rule puts the gz fact here.

- 1.1.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.

- 1.1.0 (2026-07-11): nav-trial absorption — headless gotchas: upstream
  demo launches hardcode GUI clients (compose gz_sim.launch.py directly),
  vendored `gz` CLI needs a sourced env, `gz stats` is Classic-era (use
  `gz topic -e -t /world/<world>/stats`). Headless-rendering guidance
  itself confirmed under real GPU-less arm64 load (lidar rendered, RTF≈1).
