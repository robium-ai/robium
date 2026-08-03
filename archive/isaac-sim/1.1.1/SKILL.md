---
name: isaac-sim
version: 1.1.1
description: >
  NVIDIA Isaac Sim: installation and container setup, GPU/driver requirements, USD
  scenes, robots and sensors, the ROS 2 bridge, and headless/livestream operation
  for remote servers. Use when: 'isaac sim', 'omniverse', GPU photorealistic
  simulation, synthetic data generation, or NVIDIA robotics ecosystem work. State
  the GPU requirement BEFORE recommending Isaac Sim — if the user lacks an
  RTX-class NVIDIA GPU, route to gazebo instead. Simulator selection lives in the
  simulation skill. Not for: RL training workflows (isaac-lab) or lightweight
  simulation needs (gazebo).
compatibility: Requires NVIDIA RTX-class GPU and recent drivers; Linux or Windows; no macOS support.
---

# isaac-sim

The NVIDIA-ecosystem entry point for robium: installing and containerizing
Isaac Sim, meeting its GPU/driver floor, building USD scenes, adding robots
and sensors, bridging to ROS 2, and running headless with livestreaming on a
remote server. Isaac Sim is a GPU-gated tool, not a default — the very first
thing this skill does, every time, is check whether the target machine can
run it at all. as of 2026-07-10 the current release is **Isaac Sim
6.0.1** (the `nvcr.io/nvidia/isaac-sim` container tag and the `isaacsim`
PyPI package version track together), verified by direct fetch of
`docs.isaacsim.omniverse.nvidia.com` and the NGC catalog page on 2026-07-10 —
see `references/setup-and-requirements.md` for exactly how each fact below
was checked. GPU/driver/OS requirements change per release; re-verify before
trusting a number here in a future session.

## When to use this skill

- Installing or containerizing Isaac Sim, checking whether a machine meets
  its GPU/driver floor, building or loading a USD scene, adding a robot or
  sensor, wiring the ROS 2 bridge, or running headless/livestreamed on a
  remote box.
- The trigger phrases in the description: 'isaac sim', 'omniverse', GPU
  photorealistic simulation, synthetic data generation, NVIDIA robotics
  ecosystem work.
- Someone asks "should I use Isaac Sim or Gazebo?" before a GPU has been
  confirmed — answer the GPU question first (see Key directives), don't
  assume Isaac Sim is available.
- Cross-references — go to the sibling skill instead when the question is:
  - **Whether to use Isaac Sim at all vs. Gazebo or something else** →
    the `simulation` skill (the architect skill's stack-selection
    reference carries the same decision tree). This skill assumes Isaac
    Sim has already been chosen.
  - **No RTX-class GPU available** → `gazebo`. Don't try to make Isaac Sim
    work without the GPU floor; route away instead (see Key directives).
  - **RL training at scale on top of Isaac Sim** (parallel GPU
    environments, policy training loops) → `isaac-lab`. This
    skill stops at "the sim is running, a robot and sensors are in it, and
    data can be produced" — training loops are `isaac-lab`'s territory.
  - **Generic Docker/GPU-container mechanics** (NVIDIA Container Toolkit
    install, `--gpus all`, CUDA-driver version matching, headless-display
    strategy in general) → `environments`. This skill's container guidance
    assumes that groundwork is already in place and covers only what's
    Isaac-Sim-specific on top of it.
  - **Synthetic-data STRATEGY** — which datasets/sources to combine, how
    much synthetic vs. real data a project needs → the `data` umbrella
    skill. This skill owns the *mechanics*
    of generating synthetic data inside Isaac Sim (Replicator, writers,
    output formats) — see Usage patterns.
  - **ROS 2 mechanics beyond the bridge itself** (workspaces, colcon,
    launch files, TF2, QoS) → `ros2`. This skill's ROS 2 content is limited
    to what the bridge extension publishes/subscribes.
  - **Lightweight simulation, or a sim that doesn't need a GPU** → `gazebo`.
  - The whole-stack decision this feeds into → `architect` (routes here,
    gated on the GPU floor).

## Key directives

- **Check GPU/driver compatibility first, always — before recommending
  Isaac Sim.** <!-- id: gpu-floor-check-first --> State the requirement out loud before suggesting Isaac Sim
  for a project: minimum **RTX 4080-class GPU with 16 GB VRAM** (GPUs
  without RT cores, e.g. A100/H100, are unsupported regardless of VRAM),
  32 GB system RAM, Linux (Ubuntu 22.04/24.04) or Windows 11 — **no macOS
  support at all**. If the user hasn't confirmed a qualifying GPU, don't
  design the project around Isaac Sim — route to `gazebo` and log the GPU
  question as an open risk, the same posture `architect` takes. See
  `references/setup-and-requirements.md` for the full table and how it was
  verified on 2026-07-10, and re-check it against the live requirements page
  before repeating a number in a real project — these change per release.
- **Delegation posture: embed + links.** No upstream skill or plugin wraps
  Isaac Sim as a coherent whole for a new robium project — the GPU floor,
  container invocation, USD/robot/sensor basics, and ROS 2 bridge live in
  this skill's references in depth, but every claim links back to
  `docs.isaacsim.omniverse.nvidia.com`, the NGC catalog, or
  `github.com/isaac-sim` rather than being retyped from memory. See
  References.
- **Prefer the official container for reproducibility.** <!-- id: prefer-official-container --> `nvcr.io/nvidia/
  isaac-sim` is the pinned, versioned way to get an identical Isaac Sim
  across a dev laptop and a remote GPU server — the same local/remote
  parity goal `environments` states generally. Reach for the `isaacsim` pip
  package only for a lightweight, already-provisioned Linux/Windows
  workstation that isn't going to be redeployed elsewhere; reach for the
  full Omniverse Launcher/workstation install only for interactive GUI
  authoring on a single machine. See Quick start and
  `references/setup-and-requirements.md`.
- **Headless + livestream for remote work — WebRTC only, not X11 or VNC.** <!-- id: webrtc-only-headless --> A
  remote GPU server has no display; run Isaac Sim with `runheadless.sh` and
  stream the viewport over WebRTC to the native client rather than fighting
  X11/Wayland forwarding, echoing `environments`' general headless-first
  guidance. VNC/VirtualGL is a dead end here — Kit's RTX viewport renders
  with Vulkan and VirtualGL only intercepts GLX/OpenGL, so it yields a black
  viewport; only Vulkan-aware protocols (WebRTC built-in, NoMachine, DCV)
  work. See `references/webrtc-livestream.md` for the full remote-GUI
  workflow (client install, port remapping, the resolution black-screen
  trap, and why an interactive stream can't also run a trained policy),
  Usage patterns, and Platform gotchas.
- **Never write GPU/driver/version numbers, container tags, or ROS 2 distro
  support from memory.** <!-- id: no-gpu-facts-from-memory --> Isaac Sim's requirements and supported ROS 2
  distros change with nearly every release, and the officially supported
  ROS 2 distro list is narrower than robium's general default — see
  `references/ros2-integration.md`. Every claim in this skill states how
  it was checked on 2026-07-10 (direct fetch vs. search synthesis) —
  re-verify against `docs.isaacsim.omniverse.nvidia.com` before repeating a
  number in a real project.

## Quick start

Source: `docs.isaacsim.omniverse.nvidia.com`'s installation and container
pages, fetched directly on 2026-07-10.

**1. Confirm the GPU floor first** <!-- id: confirm-gpu-floor-step --> (see Key directives) — `nvidia-smi` on
the target machine, checked against `references/setup-and-requirements.md`.
If it doesn't meet the floor, stop here and route to `gazebo`.

**2. Pull and run the official container:** <!-- id: pull-official-container -->

```bash
docker pull nvcr.io/nvidia/isaac-sim:6.0.1
```

See `examples/docker-run-command.md` for the full `docker run` invocation
(GPU flags, cache-volume mounts, EULA/privacy env vars) — copy it rather
than retyping the flags from memory, and re-verify the tag against the NGC
catalog first.

**3. Inside the container, launch headless and confirm it starts:** <!-- id: launch-headless-runheadless -->

```bash
./runheadless.sh -v
```

**4. Connect a viewport** <!-- id: connect-viewport-client --> with the Isaac Sim WebRTC Streaming Client (native,
Windows/macOS/Linux) or the browser-based client, per
`references/setup-and-requirements.md`'s livestream section.

**5. Load a scene, add a robot and sensors, enable the ROS 2 bridge, and
generate data** — see Usage patterns below and
`references/scenes-and-sensors.md` / `references/ros2-integration.md`.

## Usage patterns

**Run the container.** <!-- id: run-container-flags --> `docker run --gpus all --network=host -e
"ACCEPT_EULA=Y" -e "PRIVACY_CONSENT=Y" <cache-mounts>
nvcr.io/nvidia/isaac-sim:6.0.1` — `--network=host` matters here beyond the
usual GPU-container concerns because WebRTC livestreaming needs it; the
cache-volume mounts persist Omniverse's shader/asset cache across container
restarts so a second run isn't a cold start. See
`examples/docker-run-command.md` (full command, sourced and status-marked)
and the `environments` skill for the generic GPU-container groundwork this
builds on.

**Load a scene.** <!-- id: load-scene-usd --> Open or author a USD stage — either through the GUI Asset
Browser (backed by NVIDIA's Nucleus asset library) or the standalone Python
`SimulationApp` workflow, which starts the app before any other Isaac Sim
import can run. See `references/scenes-and-sensors.md`.

**Add a robot + sensors.** <!-- id: add-robot-sensors --> Import a robot via the URDF or MJCF importer (or
start from a Nucleus-hosted asset), then attach camera, RTX (lidar/radar),
or physics-based sensors (IMU, contact) through the Robot Setup tooling
(Robot Inspector, Robot Assembler, Joint Inspector). See
`references/scenes-and-sensors.md`.

**Enable the ROS 2 bridge.** <!-- id: enable-ros2-bridge --> The `isaacsim.ros2.bridge` extension exposes
OmniGraph nodes (`ROS2Context`, `ROS2PublishClock`, and other
publish/subscribe nodes per message type) that publish/subscribe ROS 2
topics from the running scene — wire them via an Action Graph in the GUI or
`omni.graph.core`'s `Controller.edit()` in a standalone script. See
`references/ros2-integration.md` for the supported-distro table (narrower
than robium's general ROS 2 default — read this before assuming Lyrical
Luth works out of the box) and a worked clock-publisher example.

**Generate synthetic data.** <!-- id: generate-synthetic-data-replicator --> `omni.replicator.core` (Replicator) drives
domain randomization (poses, lighting, textures, physics properties) plus
annotators and writers that export labeled data (COCO and other formats) —
this is the mechanics half of synthetic data generation; *what* data a
project actually needs is the `data` umbrella skill's call, not this
skill's. See `references/scenes-and-sensors.md`.

## Platform gotchas

- **Driver/CUDA mismatches are the sharpest failure mode.** <!-- id: driver-cuda-mismatch --> The container
  bundles its own CUDA runtime, but the *host* GPU driver must still meet
  Isaac Sim's minimum version (Linux: 595.58.03+; Windows: 595.97+ as of
  2026-07-10) — an older host driver produces cryptic renderer/launch
  failures rather than a clear version error. Check `nvidia-smi`'s reported
  driver version against `references/setup-and-requirements.md` before
  assuming a GPU-passing machine can actually run this release.
- **X11/GUI vs. headless.** <!-- id: x11-vs-headless --> The full workstation/GUI install wants a local
  display; a remote or cloud GPU box has none. Don't try to X11-forward the
  Isaac Sim GUI over SSH — use `runheadless.sh` + WebRTC livestreaming
  instead (see Usage patterns), which needs NVENC support on the GPU and
  both TCP 49100 (signaling) and UDP 47998 (media) reachable — opening only
  the TCP port is a common half-working setup. See
  `references/setup-and-requirements.md`.
- **WebRTC black screen / resolution mismatch.** <!-- id: webrtc-resolution-mismatch --> The Streaming Client only
  accepts fixed resolutions (720/1080/1440/4K); if the server renders at
  anything else you get a black screen plus "Cannot stream video frame with
  resolution AxB that differs from CxD". Force a matching render resolution
  through `--kit_args` — AppLauncher has no `--width`/`--height` flags. On a
  remapped-port host (e.g. RunPod) point the client's Signal/Stream fields
  at the external mapped ports, Server at the pod public IP. Full workflow
  and the interactive-vs-policy limitation:
  `references/webrtc-livestream.md`; general pod port-exposure mechanics
  belong to the `environments` skill.
- **Windows vs. Linux differences.** <!-- id: windows-vs-linux-differences --> Windows 11 is supported (Windows 10 is
  not); the officially tested ROS 2 bridge distro on Windows is narrower
  than on Linux (Humble only, vs. Humble and Jazzy on Ubuntu) — see
  `references/ros2-integration.md`. The NVIDIA Container Toolkit path
  `environments` documents for GPU-in-Docker is Linux-host only, so a
  Windows dev machine running the container needs WSL2 with GPU support
  configured — re-verify the current WSL2-specific steps rather than
  assuming the Linux host steps apply unchanged.
- **No macOS support, full stop.** <!-- id: no-macos-support --> Not the GUI, not the container, not the
  pip package — there is no code path that runs Isaac Sim on macOS/Apple
  Silicon. A macOS dev machine needs a remote Linux or Windows GPU host;
  don't spend time chasing a local macOS workaround.

## Customization

- **Different robot / sensor set:** swap the URDF/MJCF import target and
  the sensors attached via Robot Setup tooling; keep sensor rates/frames
  matched to the real hardware's datasheet, the same correctness principle
  `gazebo`'s sibling skill states for its own sensors. See
  `references/scenes-and-sensors.md`.
- **Different ROS 2 distro:** check
  `references/ros2-integration.md`'s supported-distro table first —
  Isaac Sim's bridge is officially tested only against a narrower distro
  set than robium's general ROS 2 default, and experimental support for
  other natively-installed distros works differently (no prebuilt bridge
  package; it sources whatever ROS 2 is already on the host).
- **No local GPU:** provision a remote Linux GPU host (cloud or on-prem)
  meeting the floor in `references/setup-and-requirements.md`, run the
  container there, and use headless + livestreaming (Usage patterns) rather
  than trying to run any part of Isaac Sim locally.
- **Workstation GUI instead of container:** the Omniverse Launcher /
  workstation install path is documented on the same requirements page as
  the container — same GPU floor applies, but pick it only for local,
  single-machine interactive authoring, not for anything that needs to
  reproduce on a different box later.

## References

- `references/setup-and-requirements.md` — the full GPU/driver/CPU/RAM/OS/
  storage requirements table, container vs. pip vs. workstation install
  paths, and headless/livestream networking details, each with how it was
  verified on 2026-07-10.
- `references/ros2-integration.md` — the `isaacsim.ros2.bridge` extension,
  officially supported ROS 2 distros per platform, the OmniGraph node
  pattern for publish/subscribe, and a worked clock-publisher example.
- `references/webrtc-livestream.md` — the remote-GUI-over-WebRTC workflow
  from a headless cloud pod: native client install (macOS), enabling the
  stream, the signaling/media ports and RunPod port remapping, the
  resolution black-screen trap, the VNC/VirtualGL dead end, the MJPEG
  in-page fallback, and why a trained policy + interactive stream + keyboard
  cannot all coexist.
- `references/scenes-and-sensors.md` — USD stage/scene basics, the
  standalone `SimulationApp` Python workflow, robot import (URDF/MJCF),
  sensor types (camera, RTX lidar/radar, IMU, contact), and the Replicator
  synthetic-data pipeline (randomization, annotators, writers).
- `examples/docker-run-command.md` — the full `docker run` invocation for
  `nvcr.io/nvidia/isaac-sim:6.0.1` with GPU, network, and cache-mount flags
  (status: unverified — file header states the exact source).
- Upstream: [Isaac Sim
  documentation](https://docs.isaacsim.omniverse.nvidia.com/) (primary
  source for this skill, fetched directly on 2026-07-10), [Isaac Sim NGC
  container
  catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim)
  (image tags), [github.com/isaac-sim](https://github.com/isaac-sim)
  (source repos, examples). Sibling skills: `simulation` (simulator
  selection), `isaac-lab` (RL training on top of this
  skill), `gazebo` (no-GPU / lightweight alternative),
  `environments` (generic Docker/GPU-container setup), `ros2` (ROS 2
  mechanics beyond the bridge), `data` (synthetic-data strategy),
  `architect` (routes here, GPU-gated).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.1.0 (2026-07-31): hardened from the go2 RunPod livestream run (2026-07-27/28) — added the webrtc-livestream reference (remote-GUI workflow, resolution black-screen trap, VNC/VirtualGL dead end, MJPEG fallback, policy-vs-interactive limitation) and surfaced the WebRTC-only / resolution-mismatch gotchas in the body.
- 1.0.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
