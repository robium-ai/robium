# Comms selection

The full decision behind the comms-choice table in `SKILL.md`: what each
transport is, when it's the right default, and what was actually verified
about current status (vs. carried from memory) as of this writing (2026-07).

## ROS 2 native: topics, services, actions

Inside one ROS 2 system, these three are the default; don't reach for
anything else without a reason.

- **Topics**: one-to-many, continuous streams, no response expected
  (sensor data, robot state, odometry). Publisher/subscriber, decoupled in
  time and space.
- **Services**: one request, one response, synchronous-feeling, no
  progress feedback. Right for short, bounded operations ("get current
  pose", "trigger a reset").
- **Actions**: request with progress feedback, a result, and cancellation,
  for anything that takes a meaningful amount of time (navigate to a pose,
  run a manipulation trajectory). Built on topics + services under the
  hood; use it instead of a service when the caller needs to track progress
  or cancel.

Source: [ROS 2 Topics vs Services vs
Actions](https://docs.ros.org/en/rolling/How-To-Guides/Topics-Services-Actions.html);
a direct fetch of this docs.ros.org page was blocked by an anti-bot
challenge, so this rests on WebSearch snippet synthesis (consistent across
Rolling/Jazzy/Humble in those snippets) rather than a full-text read;
re-verify directly before relying on distro-specific details.

All three ride on DDS by default (the RMW layer is swappable; see below).
Inside one host or one un-firewalled network, default DDS discovery (Simple
Discovery Protocol, multicast-based) works with zero config. Crossing a
container or host boundary is where discovery needs explicit setup; that's
a docker-compose concern, covered in `compose-patterns.md`, not a reason to
switch transports.

## rmw_zenoh: an alternative RMW, opt-in, not the default

**Status checked 2026-07.** The [ros2/rmw_zenoh
README](https://github.com/ros2/rmw_zenoh) was fetched and verified
directly. The [docs.ros.org Zenoh
page](https://docs.ros.org/en/rolling/Installation/RMW-Implementations/Non-DDS-Implementations/Working-with-Zenoh.html)
could not be fetched directly (blocked by an anti-bot challenge) and is
corroborated only via WebSearch snippet synthesis; re-verify it directly
before relying on distro-support specifics:

- rmw_zenoh has been available since **ROS 2 Jazzy Jalisco** (it does not
  support Humble or earlier). It is **opt-in, not the default RMW**: you
  must explicitly set `RMW_IMPLEMENTATION=rmw_zenoh_cpp` (default RMWs
  remain the DDS-based implementations, e.g. Fast DDS / CycloneDDS,
  distro-dependent).
- Install: `sudo apt install ros-<DISTRO>-rmw-zenoh-cpp`.
- It requires a running **Zenoh router**
  (`ros2 run rmw_zenoh_cpp rmw_zenohd`) reachable by all participants;
  discovery is gossip-based through that router rather than multicast. This
  is *why* it's attractive for containerized/cross-host setups (no
  multicast dependency), but it is an extra process to run and wire in,
  not a drop-in replacement with no setup cost.
- It claims shared-memory (SHM) optimization for messages passing through
  it, transparently interoperating with non-SHM/remote nodes.
- Do not claim rmw_zenoh is "the new default" in a real project without
  re-checking the current docs; this status has moved before (zenoh
  support itself only landed in early 2025) and may move again.

A related, distinct tool: **zenoh-plugin-ros2dds**
([eclipse-zenoh/zenoh-plugin-ros2dds](https://github.com/eclipse-zenoh/zenoh-plugin-ros2dds))
bridges a *standard DDS-based* ROS 2 system to Zenoh at the edge, rather
than replacing the RMW. Reach for this when the ROS 2 side should stay on
its normal DDS RMW and only the boundary to a non-ROS/remote Zenoh peer
needs bridging; it fits the "cross-boundary to a non-ROS peer" row of the
comms table better than swapping the whole system's RMW to rmw_zenoh.

## gRPC and REST: for non-ROS boundaries only

Use these when the peer on the other side doesn't speak ROS 2/DDS at all:
another team's microservice, a cloud API, a mobile app, a system that will
never run ROS 2:

- **gRPC**: typed contracts (protobuf), efficient binary encoding,
  supports streaming. Prefer it when both sides can adopt a shared `.proto`
  schema and the extra tooling is worth it (higher throughput, lower
  latency than REST, native streaming for continuous data crossing the
  boundary).
- **REST**: simplest, most universally interoperable (any HTTP client),
  best when the peer is unknown/heterogeneous, low-frequency, or a human/UI
  is in the loop.

Do not run either of these *inside* one ROS 2 system in place of native
topics/services/actions; that's the anti-pattern the "prefer ROS 2 native
comms" key directive exists to block. The boundary case is the exception,
not the template for internal wiring.

## Shared memory

Two forms come up in robium builds:

- **ROS 2 intra-process comms / loaned messages**: when publisher and
  subscriber are in the same process (composed nodes in one executor),
  rclcpp/rclpy can avoid a serialize/deserialize round-trip entirely. This
  only applies within one process; it is not a cross-process IPC
  mechanism.
- **rmw_zenoh's SHM path**: if already on rmw_zenoh, same-host
  cross-process messages can use Zenoh's shared-memory transport
  transparently, without changing application code.

Adopt either only when profiling shows serialization/copy cost is the
actual bottleneck (large images, point clouds, high-rate large messages).
Don't reach for shared memory as a first move; the comms-choice table's
default for same-host ROS 2 nodes is still plain topics/services/actions.

## Discovery across containers/hosts (comms-selection summary)

This reference covers *which transport*; the *how do containers on that
transport find each other* mechanics (Discovery Server, static peers, host
networking, the zenoh router as a compose service) live in
`compose-patterns.md`; the two are deliberately split so this file stays
about picking a transport and that one stays about wiring it into compose.
