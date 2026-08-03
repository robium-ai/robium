---
name: integration
version: 1.2.1
description: >
  Glue robotics modules into one running system: choose module boundaries,
  pick inter-module communication (ROS 2 topics/services/actions, zenoh,
  gRPC, REST, shared memory), and write solid Dockerfiles and docker-compose
  for robotics workloads. Use when: wiring components together; 'containerize
  this', 'dockerfile', 'docker compose', 'how should these modules talk',
  'connect the planner to the controller', multi-process or multi-container
  robotics systems. Load after architect chose the stack and environments
  set the env strategy. Not for: choosing the overall stack (architect) or
  single-project env setup (environments).
---

# integration

The glue-layer umbrella for robium. Once `architect` has picked a stack and
`environments` has decided how a single module runs reproducibly, something
has to decide how the *modules* find and talk to each other, and how they're
packaged so the whole system starts up as one thing. This skill owns three
tightly related decisions: where the module boundaries are, what comms
crosses each boundary, and how Dockerfiles/docker-compose package and wire
the result. It does not decide the stack (`architect`) or a single module's
env reproducibility (`environments`) — it decides how already-chosen modules
become a running system.

## When to use this skill

- Wiring two or more components together and the question is "how should
  these talk" — a planner to a controller, a perception node to a policy, a
  sim to an app container.
- The trigger phrases in the description: 'containerize this', 'dockerfile',
  'docker compose', 'how should these modules talk', 'connect the planner to
  the controller'.
- Any multi-process or multi-container robotics system, even a simple
  two-container sim+app pair.
- Cross-references — go to the sibling skill instead when the question is:
  - The overall stack hasn't been chosen yet → `architect` (load first; it
    routes here once the stack and modules are known).
  - A single module's reproducibility (uv vs Docker, GPU passthrough, base
    image) rather than how modules talk to *each other* → `environments`.
    This skill assumes each module's own environment is already decided and
    focuses on cross-module wiring.
  - ROS 2 package/node/launch-file internals within one module → `ros2`.
  - Remote visualization transport (Foxglove bridge, rosbridge) →
    `foxglove`.

## Key directives

- **Delegation posture: embed.** Module-boundary heuristics, the comms
  decision table, and Dockerfile/compose patterns for robotics workloads
  live in this skill and its references — this is core, every-multi-module-
  build content, not a thin pointer elsewhere.
- **Prefer ROS 2 native comms inside a ROS system.** <!-- id: prefer-native-ros2-comms --> If two modules are both
  ROS 2 nodes in the same system, use topics/services/actions over DDS by
  default. Reach for a non-ROS transport (zenoh, gRPC, REST, shared memory)
  only when crossing a *system* boundary — a non-ROS peer, another team's
  service, a cloud endpoint, or a boundary DDS genuinely can't cross without
  extra config. Don't introduce a second transport inside a single ROS
  system "just in case."
- **One process per container, unless there's a stated reason.** <!-- id: one-process-per-container --> Each
  container should run one supervisable unit (one ROS 2 node, or one tightly
  coupled node group that only makes sense together). Bundling unrelated
  nodes into one container to save a Dockerfile hides failures and blocks
  independent scaling/restart — if you do it anyway, write down why in the
  compose file or brief.
- **DDS discovery across containers must be configured explicitly, never
  assumed.** <!-- id: dds-discovery-explicit-config --> Docker's default bridge network does not forward the multicast
  UDP traffic DDS's default discovery relies on — "it worked when I ran both
  nodes on the host" does not imply it will work in compose. Pick and state
  one discovery mechanism (host networking, a Discovery Server, static
  peers, or a zenoh router) — see `references/compose-patterns.md`. This is
  the single most common integration bug in robium builds; treat an
  unconfigured discovery setup as a defect, not a "works on my machine" risk
  to defer.
- **Never write RMW/DDS/zenoh version or default-status claims from memory.** <!-- id: no-rmw-facts-from-memory -->
  These have changed release-to-release (zenoh support, discovery-server
  defaults). Verify against [docs.ros.org](https://docs.ros.org/) and the
  [ros2/rmw_zenoh](https://github.com/ros2/rmw_zenoh) repo before repeating
  a claim in a real project — see `references/comms-selection.md` for what
  was verified and when.

## Quick start

**1. Confirm the prerequisites are settled.** `docs/architecture-brief.md`
should already record the chosen stack (`architect`) and each module's env
strategy (`environments`). If either is missing, route back there first.

**2. Decide module boundaries.** Split by **rate + failure domain** — see
Decision guidance below. Write the resulting module list into the brief's
module-breakdown section.

**3. Pick comms per module pair.** Use the comms-choice table in Decision
guidance; the default inside one ROS 2 system is native topics/services/
actions. See `references/comms-selection.md` for the full picture including
zenoh, gRPC, REST, and shared memory.

**4. Write one Dockerfile per module.** <!-- id: multistage-dockerfile-per-module --> Multi-stage: a build stage with the
full toolchain (colcon, compilers, apt build deps), a slim runtime stage
that copies only the built `install/` output and runtime deps. See
`references/dockerfile-guide.md` and `examples/Dockerfile.multistage-ros2`.
This is a different concern from `environments`' Dockerfile.ros2 example
(single-environment reproducibility) — this one is about build quality for
a module that ships as part of a multi-container system.

**5. Wire modules with docker-compose.** <!-- id: compose-explicit-domain-discovery --> One service per container, explicit
network mode, explicit `ROS_DOMAIN_ID`, and an explicit DDS discovery
mechanism. See `references/compose-patterns.md` and
`examples/docker-compose.ros2-app.yml`.

**6. Verify discovery, not just that containers start.** <!-- id: verify-discovery-not-just-start --> `docker compose up`
succeeding is not proof nodes can see each other — run `ros2 topic list` /
`ros2 node list` from inside each container (or `ros2 doctor --report`) and
confirm cross-container topics actually appear before calling the wiring
done.

## Decision guidance

### Comms-choice table

| Relationship | Default choice | Why / when to deviate |
|---|---|---|
| Same process, same language | Direct call / shared object, no IPC | Don't wrap this in ROS 2 messaging "for consistency" — it adds serialization cost and a node boundary for no isolation benefit. |
| Same-host, both ROS 2 nodes | ROS 2 topics/services/actions (default RMW, default DDS discovery) | Native; multicast discovery works unmodified on the host network or a single non-networked process. This is the default — deviate only for a stated reason. |
| Cross-host or cross-container, both ROS 2 (one system) | Still ROS 2 topics/services/actions, but with discovery **explicitly** configured — host networking, a Fast DDS Discovery Server, static CycloneDDS peers, or rmw_zenoh with a router | Multicast usually doesn't cross container/host boundaries by default. Don't reach for a non-ROS transport just because discovery needs setup — fix discovery, keep the transport native. See `references/comms-selection.md`. |
| Cross-boundary to a non-ROS peer (another team's service, a cloud API, a system that doesn't speak ROS/DDS) | gRPC (typed, streaming-capable, low overhead) or REST (simplest, most interoperable) at the boundary | This is the one case where a non-ROS transport is the *default*, not the exception — don't leak DDS/RMW specifics across an org or system boundary. |
| High-throughput same-host data (large images, point clouds, mostly within one host) | Shared memory: ROS 2 intra-process comms / loaned messages, or zenoh's SHM path if already on rmw_zenoh | Adopt only when profiling shows serialization/copy overhead is the actual bottleneck — not a default starting point. |

### Module-boundary heuristics: split by rate + failure domain

- **Rate mismatch** <!-- id: rate-mismatch-split --> → split. A 1 kHz control loop and a 10 Hz planner have
  no business sharing a process/executor; bundling them risks the slow one
  starving the fast one (or the fast one wasting the slow one's CPU budget).
  Each rate tier gets its own node/process so it can be scheduled and
  rate-limited independently.
- **Failure domain** <!-- id: failure-domain-split --> → split. If module A crashing should not take down
  module B (a perception model that OOMs shouldn't kill the safety
  controller; a sim shouldn't kill the app that drives it), they're separate
  processes/containers so a restart policy can target just the failed one.
- **Neither applies** <!-- id: neither-applies-keep-together --> → keep together. Two tightly coupled pieces with the
  same rate and no independent failure story (e.g., a filter and the node
  that owns it, with no reason either would run or fail alone) add pure
  comms overhead if split — one node, one container, is the simpler and
  correct default.
- Write the resulting boundary list, and the rate/failure reasoning behind
  each split, into the brief's module-breakdown section — an undocumented
  boundary decision gets silently re-litigated by the next person.

## Platform gotchas

- **Docker's default bridge network drops DDS multicast.** <!-- id: docker-bridge-drops-dds-multicast --> The default
  Simple Discovery Protocol most DDS implementations use relies on
  multicast UDP, and Docker's default bridge network does not forward it
  between containers — two ROS 2 nodes in separate `docker compose`
  services will not discover each other with zero extra config. Use
  `network_mode: host` (Linux only) for the simplest fix, or an explicit
  discovery mechanism (Discovery Server, static peers, zenoh router) when
  host networking isn't available. See `references/compose-patterns.md`.
- **`network_mode: host` is Linux-only in the way this skill means it.** <!-- id: network-mode-host-linux-only -->
  Docker Desktop on macOS/Windows does not give containers the host's real
  network namespace the way Linux does — don't rely on host networking as
  the discovery fix on a macOS/Windows dev machine (consistent with
  `environments`' "macOS has no native ROS 2" gotcha: Mac ROS 2 dev is
  already inside a VM/Docker layer). Use an explicit CycloneDDS peers list,
  a Discovery Server, or rmw_zenoh instead in that case; [this Husarnet
  writeup](https://husarnet.com/blog/ros2-docker) has a worked example of
  disabling multicast and pointing CycloneDDS at static peers.
- **rmw_zenoh needs its own router process.** <!-- id: zenoh-needs-router-process --> Switching `RMW_IMPLEMENTATION`
  to `rmw_zenoh_cpp` doesn't work standalone — it requires a Zenoh router
  (`ros2 run rmw_zenoh_cpp rmw_zenohd`) running and reachable, or peer-to-
  peer config if deliberately skipping the router. In compose, that's its
  own service, not an assumption baked into one node's entrypoint. See
  `references/comms-selection.md`.
- **`ROS_DOMAIN_ID` collisions are silent.** <!-- id: ros-domain-id-collision-silent --> Two unrelated ROS 2 systems on
  the same host-network segment with the same (default `0`) domain ID will
  discover and cross-talk with each other. Set an explicit, project-unique
  `ROS_DOMAIN_ID` in the compose file for every robium project, the same way
  you'd pick a non-default port. **But a pinned constant is a
  one-stack-per-host assumption** — the moment something runs *concurrent
  copies* of the same stack (an orchestrator spawning a container per
  visitor, a parallel test matrix, several sims on one CI box), that shared
  constant merges every copy's ROS graph into one. The symptom is not a
  discovery error but physics nonsense: two Gazebo `/clock` publishers on
  one graph, and
  `[robot_state_publisher] Moved backwards in time, re-publishing joint
  transforms!` flooding forever. Whatever spawns the instances must assign
  a **per-instance domain ID** (lowest free in 1–200, recorded on the
  container so it can be excluded while in use) instead of inheriting the
  project constant. Verified 2026-07-13 (nav-trial demo orchestrator).

## Customization

- **Fewer/more than two services:** the compose example is a minimal
  two-service (sim + app) shape; extend the same pattern — one service per
  module, shared `ROS_DOMAIN_ID`, one explicit discovery mechanism — for
  additional nodes rather than inventing a different wiring style per
  service.
- **Adding a non-ROS peer:** add the boundary transport (gRPC/REST) as its
  own service or sidecar rather than piping it through the DDS network; keep
  the ROS-internal comms native per the key directive.
- **Swapping the discovery mechanism:** `references/compose-patterns.md`
  covers host networking, Fast DDS Discovery Server, static CycloneDDS
  peers, and rmw_zenoh — pick one per project based on whether it's
  same-host (host networking is simplest) or cross-host/cross-network
  (Discovery Server or zenoh scale better); don't mix mechanisms within one
  project.
- **Heavier build (large ML deps in one module):** extend
  `examples/Dockerfile.multistage-ros2`'s builder/runtime split rather than
  collapsing back to a single stage — see `references/dockerfile-guide.md`
  and cross-reference `environments`' Dockerfile.gpu-ml example for the
  GPU-specific multi-stage shape.

## References

- `references/comms-selection.md` — the full comms decision: ROS 2
  topics/services/actions in depth, rmw_zenoh and zenoh-plugin-ros2dds
  status and setup, gRPC/REST for non-ROS boundaries, shared memory, with
  verified sources.
- `references/dockerfile-guide.md` — Dockerfile quality for a robotics
  module: multi-stage build/runtime split, one-process-per-container,
  layer-cache ordering, signal handling for `ros2 launch`.
- `references/compose-patterns.md` — docker-compose wiring: network modes,
  `ROS_DOMAIN_ID`, DDS discovery mechanisms across containers/hosts,
  `depends_on`/healthchecks, volumes.
- `examples/docker-compose.ros2-app.yml` — minimal two-service (sim + app)
  ROS 2 compose file with explicit DDS discovery config (status:
  unverified).
- `examples/Dockerfile.multistage-ros2` — multi-stage build/runtime split
  for one ROS 2 module, complementary to `environments`'
  Dockerfile.ros2 example (status: unverified).
- Upstream: [ROS 2 Topics vs Services vs
  Actions](https://docs.ros.org/en/rolling/How-To-Guides/Topics-Services-Actions.html),
  [rmw_zenoh](https://github.com/ros2/rmw_zenoh), [Fast DDS Discovery
  Server](https://fast-dds.docs.eprosima.com/en/latest/fastdds/ros2/discovery_server/ros2_discovery_server.html),
  [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/).
  Sibling skills: `architect` (routes here), `environments` (single-module
  env strategy — not duplicated here), `ros2` (node/launch internals),
  `foxglove` (remote viz transport).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.2.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.2.0 (2026-07-13): nav-trial demo absorption — corrected the
  `ROS_DOMAIN_ID` directive, which prescribed a pinned project constant
  unconditionally. That is a one-stack-per-host assumption; concurrent
  copies of a stack (orchestrator-per-visitor, parallel CI sims) merge
  their graphs on the shared constant and surface as duplicate `/clock`
  publishers + a `Moved backwards in time` flood. Spawners must assign a
  per-instance domain ID. Same nuance added to compose-patterns.md, whose
  examples hardcode 42.

- 1.1.0 (2026-07-11): nav-trial absorption — "Compose sharp edges" section
  in compose-patterns.md (profile-gated `build` no-op, shallow YAML merge
  keys dropping anchor env vars, `exec` bypassing ENTRYPOINT). macOS
  DDS-multicast gotcha confirmed load-bearing in a real build (drove a
  one-container-per-scenario design, verified end-to-end).
