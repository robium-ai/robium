# Compose patterns

How to wire multiple robotics-module containers together with
docker-compose, and — the part that actually breaks in practice — how to
make DDS discovery work across that boundary. Checked 2026-07 against
[Docker Compose networking docs](https://docs.docker.com/compose/how-tos/networking/)
and a worked cross-host example at [Husarnet's ROS 2 + Docker
writeup](https://husarnet.com/blog/ros2-docker) — the Husarnet writeup was
fetched directly. The [Fast DDS Discovery Server
docs](https://fast-dds.docs.eprosima.com/en/latest/fastdds/ros2/discovery_server/ros2_discovery_server.html)
page loaded but didn't render past its table of contents, so the
`ROS_DISCOVERY_SERVER` details in option 2 below rest on WebSearch
corroboration rather than a full direct read — re-verify before relying on
them.

## The core problem: multicast doesn't cross Docker's default network

By default, `docker compose` puts services on a bridge network. Most DDS
implementations' default discovery (Simple Discovery Protocol) uses
multicast UDP (traditionally `239.255.0.1:7400` and neighboring ports) to
find peers. Docker's default bridge network does not forward multicast
between containers, so two ROS 2 nodes in separate compose services will
**not** discover each other with a bare `services:` block and no other
config — this is the failure mode the "DDS discovery must be configured
explicitly" key directive exists to prevent.

There are three sound fixes; pick one per project and state which:

### 1. Host networking (same host, Linux, simplest)

```yaml
services:
  sim:
    network_mode: host
    environment:
      - ROS_DOMAIN_ID=42
  app:
    network_mode: host
    environment:
      - ROS_DOMAIN_ID=42
```

Containers share the host's network namespace, so multicast discovery
works exactly as it would for two processes run directly on the host — no
DDS config changes needed. Linux-only in practice (Docker Desktop on
macOS/Windows does not give a real host network namespace — see `SKILL.md`
Platform gotchas), and it gives up Docker's port-mapping isolation, which
is usually fine for a closed robotics stack but worth noting. This is the
mechanism the compose example (`examples/docker-compose.ros2-app.yml`)
uses, because it targets the common same-host Linux dev/deploy case.

### 2. Fast DDS Discovery Server (cross-host, or containers without host networking)

Runs a small discovery-server process; participants register as clients
instead of relying on multicast:

```yaml
environment:
  - ROS_DISCOVERY_SERVER=discovery-server-host:11811
```

set on every participant, plus a `discovery-server` service (or an
external process) actually running the server. Reduces discovery traffic
too, which matters at fleet scale, not just for the multicast problem. See
the Fast DDS docs linked above for the full super-client/server role
config — this is Fast-DDS-specific (the RMW must be Fast DDS, the distro
default in several ROS 2 releases; confirm before relying on it if a
project has pinned a different RMW).

### 3. Static peers with multicast disabled (CycloneDDS, cross-host)

Mount a `cyclonedds.xml` pointing at explicit peer addresses and turn
multicast off:

```xml
<CycloneDDS>
  <Domain>
    <General><AllowMulticast>false</AllowMulticast></General>
    <Discovery><Peers><Peer address="sim-host"/><Peer address="app-host"/></Peers></Discovery>
  </Domain>
</CycloneDDS>
```

```yaml
environment:
  - CYCLONEDDS_URI=file:///config/cyclonedds.xml
```

This is the pattern in the Husarnet writeup above (there applied across a
VPN, but the peers/no-multicast shape is the same for any cross-host
compose deployment where host networking isn't an option).

### (Alternative to all three) rmw_zenoh

Switching the whole system's RMW to `rmw_zenoh_cpp` sidesteps multicast
entirely via its router-based gossip discovery — but it's a bigger decision
than a compose-networking tweak (it changes the RMW for the whole system;
see `references/comms-selection.md`). If chosen, the router is its own
compose service:

```yaml
services:
  zenoh-router:
    image: eclipse/zenoh:latest
    command: ["-l", "tcp/[::]:7447"]
  app:
    environment:
      - RMW_IMPLEMENTATION=rmw_zenoh_cpp
      - ZENOH_ROUTER_CHECK_ATTEMPTS=5
    depends_on:
      - zenoh-router
```

Don't assume a node will start the router itself — it's a shared
dependency, model it as one.

## `ROS_DOMAIN_ID`

Set it explicitly, per project, on every service that should discover each
other, and treat it like a port number: unique enough that this project's
containers don't cross-talk with another ROS 2 system running on the same
host-network segment (default `0` is exactly the collision risk called out
in `SKILL.md`'s Platform gotchas).

The constant in this file (`42`) is right for the shape compose models: one
copy of the stack per host. It is **wrong for concurrent copies** — if
something spawns N containers from this image at once, they all land on
domain 42, their graphs merge, and you get two `/clock` publishers and a
`Moved backwards in time, re-publishing joint transforms!` flood rather
than an honest error. Concurrent-instance spawners assign a per-instance
domain ID (lowest free in 1–200) at start time; see the `ROS_DOMAIN_ID`
gotcha in `SKILL.md`.

## `depends_on` and healthchecks

`depends_on` alone only waits for the dependency's container to *start*,
not for its ROS 2 graph to be ready (a sim that takes 10s to load a world
before publishing `/clock` is a common case). Pair it with a healthcheck
that reflects actual readiness, not just process liveness:

```yaml
services:
  sim:
    healthcheck:
      test: ["CMD", "ros2", "topic", "list"]
      interval: 5s
      timeout: 3s
      retries: 10
  app:
    depends_on:
      sim:
        condition: service_healthy
```

A bare `ros2 topic list` is a weak healthcheck (it only proves the ROS 2
CLI can reach the graph, not that the sim published anything useful) —
tighten it to check for a specific expected topic/service in a real
project rather than copying this as-is.

## Compose sharp edges (all three hit in one real build — nav-trial, 2026-07-11)

- **Profile-gated `build` is a silent no-op.** With every service behind a
  `profiles:` key (the one-image/one-service-per-profile shape), bare
  `docker compose build` exits 0 with `No services to build` and builds
  NOTHING — a Makefile/CI `build` target wrapping it "succeeds" without
  producing an image. Name a service explicitly (`docker compose build
  <svc>` auto-activates its profile) or pass `--profile "*"`.
- **YAML merge keys are shallow.** Declaring `environment:` on a service
  that merges an `x-` anchor (`<<: *app`) REPLACES the anchor's whole
  environment map — silently dropping every var the anchor set — rather
  than merging into it. Redeclare the anchor's vars alongside the new one,
  and leave a comment on the anchor warning the next editor.
- **`docker compose exec` bypasses the image ENTRYPOINT** (unlike
  `compose run`), so an entrypoint that sources the ROS env doesn't run and
  in-container commands fail with unsourced-env symptoms
  (`ModuleNotFoundError: rclpy`, `command not found: ros2`). Prefix
  manually: `docker compose exec <svc> /entrypoint.sh <cmd>`.

## Volumes

Mount shared config (a `cyclonedds.xml`, a shared parameters file) and any
persistent data (bags, logs) as named volumes or explicit host binds,
scoped to what actually needs to be shared — don't bind-mount an entire
workspace into a container that only needs one config file, and don't rely
on a shared writable volume as an IPC mechanism (that's what topics/
services are for; see `references/comms-selection.md`).
