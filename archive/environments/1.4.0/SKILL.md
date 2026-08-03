---
name: environments
version: 1.4.0
description: >
  Virtual-environment-first setup for robotics projects: decide uv/venv vs Docker,
  make local and remote-server runs reproduce identically, handle GPU passthrough
  and headless/display forwarding. Use when: setting up any new robotics project
  environment; 'uv', 'venv', 'virtualenv', 'docker for this project', 'reproducible
  environment', 'works locally but not on the server', 'GPU in container'. Load
  early in any robium build, right after architect. Decision rule of thumb:
  pure-Python ML stacks → uv; anything needing ROS 2 or system deps → Docker. Not
  for: multi-module application Dockerfiles and compose wiring (integration skill).
---

# environments

The environment-strategy umbrella for robium. Every robium build needs an answer
to "how does this run, identically, on my laptop and on whatever server it ends
up on" before the first line of application code is written. This skill decides
uv vs venv vs Docker, and — once Docker is chosen — how to get GPU passthrough
and remote/headless display right. It does not own multi-module application
Dockerfiles or compose wiring across nodes; that's `integration`.

## When to use this skill

- Starting any new robotics project and the environment strategy isn't decided
  yet — this is a required early step, not an optional one.
- The trigger phrases in the description: 'uv', 'venv', 'virtualenv', 'docker
  for this project', 'reproducible environment', 'GPU in container'.
- Debugging "works on my machine but not on the server" — almost always an
  environment-parity bug, not an application bug.
- Cross-references — go to the sibling skill instead when the question is:
  - Wiring multiple app modules together, Dockerfiles for a multi-node app, or
    compose files spanning services → `integration` (this skill covers a
    *single* environment's shape; `integration` covers the app that runs in it).
  - Remote visualization once headless is decided → `foxglove`.
  - ROS 2-specific package/build questions once Docker + ROS 2 is chosen →
    `ros2`.
  - Picking a manipulation/training framework once the env is settled →
    `lerobot`.
  - The whole-stack decision this feeds into → `architect` (load that first if
    you haven't; it routes here).

## Key directives

- **Delegation posture: embed.** The decision logic (uv vs venv vs Docker) and
  the concrete patterns (pyproject.toml shape, Dockerfile shape, GPU/display
  flags) live in this skill and its references — this is a foundational,
  every-build concern, not a thin pointer to someone else's docs.
- **Environment before code.** Decide and record the environment strategy
  before writing application code. An undecided environment is an open risk,
  not a detail to fix later.
- **Preflight the machine before deciding.** Run `npx robium-ai doctor --json`
  (the robium CLI, npm package robium-ai) at the start of an environment
  decision and read the report — platform/Apple Silicon, Docker daemon state,
  GPU, free disk, python3/uv — instead of re-deriving those facts with ad-hoc
  shell probes. `npx robium-ai doctor` is the human-readable variant. If npx
  is unavailable, fall back to probing manually; the decision logic below is
  unchanged either way.
- **Never `pip install` into the system Python.** Not on the host, not inside
  a container's base image. Every install goes into a project-scoped uv
  environment (`uv sync`, `uv run`) or, inside Docker, a venv managed the same
  way. The only sanctioned exception is a deliberate, explicit `--system`
  flag (or `UV_SYSTEM_PYTHON=1`) inside a container build stage that is itself
  disposable — see `references/uv-patterns.md`.
- **Every project states its env strategy in the architecture brief.** If
  you're routed here from `architect`, write the choice (uv / venv / Docker,
  and why) into `docs/architecture-brief.md`'s env-strategy section before
  moving on — don't let it live only in your head or in a Dockerfile no one
  reads.
- **Local == remote is the acceptance test.** An environment strategy isn't
  done until you can state, concretely, why the same commands produce the
  same result on a laptop and on a headless remote server (same base image
  digest or lockfile, same Python/CUDA versions, no host-only assumptions). If
  you can't state that, the strategy isn't finished — see the parity
  checklist in `references/docker-patterns.md`.
- **Never write image tags or version numbers from memory.** Verify current
  uv usage against [docs.astral.sh/uv](https://docs.astral.sh/uv/), current
  ROS 2 image tags against
  [hub.docker.com/_/ros](https://hub.docker.com/_/ros), and NVIDIA Container
  Toolkit steps against
  [docs.nvidia.com](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
  before committing them to a real project. Every example in this skill is
  marked `status: unverified` for exactly this reason — treat it as a
  starting shape to re-check, not a pinned truth.

## Quick start

**1. Answer one question: does this project need ROS 2 or other system-level
dependencies (apt packages, native libs, a specific OS)?**

- **No — pure-Python (ML training/inference, data tooling, a plain script):**
  use **uv**. `uv init`, define dependencies in `pyproject.toml`, commit
  `uv.lock`, run everything through `uv run`. See
  `references/uv-patterns.md` and `examples/pyproject-uv.toml`.
- **Yes — ROS 2, system packages, or a robot's exact host OS matters:**
  use **Docker**, built on an official ROS 2 image, with uv installed inside
  for any pure-Python pieces of the workspace. See
  `references/docker-patterns.md` and `examples/Dockerfile.ros2`.
- **Both — ROS 2 in one place, a heavy pure-Python ML stack in another:**
  still Docker, but run uv *inside* the container for the Python side rather
  than fighting the container's system Python. See
  `references/docker-patterns.md`.

**2. If Docker, and the project needs a GPU (training, Isaac Sim, CUDA
inference):** confirm `nvidia-container-toolkit` is installed on the host
(Linux only), and run with `docker run --gpus all …`. See
`references/gpu-and-remote.md` and `examples/Dockerfile.gpu-ml`.

**3. If the project runs on a headless/remote server:** don't reach for X11
forwarding as the default — route visualization to `foxglove` (web-based,
works over SSH/remote with no display). Reserve X11/Wayland forwarding for
local-Linux-only, single-user cases. See `references/gpu-and-remote.md`.

**4. Record the decision.** Write the chosen strategy (and why) into
`docs/architecture-brief.md`'s environment-strategy section.

## Decision guidance

```
Does the project need ROS 2, system apt packages, or a specific OS?
│
├─ No → pure-Python stack
│   └─ uv
│       - `uv init`, pyproject.toml + uv.lock (commit the lock file)
│       - `uv run <cmd>` for everything — never activate-and-forget
│       - `uv venv` only if you need a venv without full project management
│       - See references/uv-patterns.md
│
├─ Yes, and it's ROS 2 / system deps only → Docker
│   └─ Base on an official ROS 2 image (hub.docker.com/_/ros); add a project
│      venv with uv inside only if there's Python glue code beyond ROS 2 nodes.
│      See references/docker-patterns.md, examples/Dockerfile.ros2.
│
└─ Yes, mixed: ROS 2/system deps AND a heavy pure-Python ML stack → Docker
    └─ Docker for the system layer, uv for the Python layer *inside* the
       container (multi-stage build: uv resolves deps in a builder stage, the
       runtime stage copies the resulting venv). Do not `pip install` into
       the container's system Python even though you're already in Docker.
       See references/docker-patterns.md, examples/Dockerfile.gpu-ml.
```

**Local vs remote parity checklist** (the acceptance test from Key
directives — walk this before calling an environment strategy done):

- [ ] Base image is pinned to a specific tag (and ideally digest), not
  `latest` — so "remote" can't silently drift from "local".
- [ ] `uv.lock` (or the container image itself) is the single source of
  truth for dependency versions — no "just pip install X" steps documented
  as a workaround anywhere.
- [ ] GPU projects: the CUDA version baked into the image matches what the
  remote host's driver supports (see `references/gpu-and-remote.md`) — don't
  assume the dev laptop's CUDA matches the server's.
- [ ] No hardcoded local paths, display assumptions, or "run this manual step
  first" instructions that only work on one machine.
- [ ] The same `docker run` / `uv run` invocation (modulo GPU flags) is
  documented for both local and remote use.
- [ ] "Clean-room" claims name what was actually cold: `docker compose down
  --rmi local` removes the image but NOT the buildx layer cache, so a
  rebuild-and-pass after it proves the committed build definition works —
  not that a cold host (fresh apt downloads) reproduces it. A truly cold
  check additionally needs `docker builder prune`. Verified 2026-07-11
  (nav-trial).

## Platform gotchas

- **macOS has no native ROS 2.** There is no supported native ROS 2 install
  on macOS/Apple Silicon — any ROS 2 project on a Mac dev machine goes
  straight to Docker, even for local development. Don't try to install ROS 2
  natively on macOS as a shortcut. If plain Docker Desktop performance or
  networking is a problem, Lima (a lightweight Linux VM manager for macOS)
  is a solid alternative for running Docker/containers, and falling back to
  a Linux machine (local or remote) is always an option too.
- **GPU containers need `nvidia-container-toolkit`, and it's Linux-only.**
  GPU passthrough into Docker (`--gpus all`) requires the NVIDIA Container
  Toolkit installed on the *host*, and NVIDIA's own install guide covers
  Linux distributions only (Ubuntu/Debian/RHEL/Fedora/SUSE) — there is no
  first-party Windows/macOS host path. A remote Linux GPU server is the
  reliable target for GPU workloads; a local macOS dev machine cannot run
  GPU containers at all. See `references/gpu-and-remote.md`.
- **Docker on macOS cannot see MPS — for ML/VLA on Apple Silicon this is a
  latency decision, not a preference.** Docker containers on macOS run in a
  Linux VM with no Metal/MPS passthrough, so any policy inference inside a
  macOS Docker container falls back to CPU — and so does Cloud Run, which is
  CPU-only regardless of host. Measured on SmolVLA: 0.55s/forward pass on
  MPS-native (uv) vs ~9s/forward pass under CPU (Docker or Cloud Run) —
  roughly 17x. For an ML policy on Apple Silicon, the number that decides
  "can I containerize this" is CPU inference latency, not whether Docker
  itself works (seen 2x: manip-trial, vla-trial).
- **X11/Wayland forwarding vs headless + web viz.** Forwarding a display out
  of a container (X11 sockets, `DISPLAY` env, `xhost`) works for local-Linux
  development but breaks down over SSH to a remote server and doesn't work
  from macOS/Windows hosts without extra tooling. For anything remote or
  cross-platform, default to headless containers plus web-based
  visualization — route that to the `foxglove` skill rather than fighting
  display forwarding.
- **A Mac wired to a no-internet robot LAN loses internet — reorder network
  services.** macOS ranks a wired (USB-Ethernet) service above Wi-Fi, so when
  you cable a Mac into a robot's private router (common for a real-robot bring
  -up), the default route goes down that dead-end LAN and the browser goes
  offline — including `app.foxglove.dev`, which needs internet to *load* even
  though the robot WebSocket rides the LAN. Fix: System Settings → Network →
  ⋯ → Set Service Order → drag Wi-Fi above the USB LAN. The directly-connected
  robot subnet still routes out the cable regardless of default-route order.
  Verified 2026-07-24 (tb4-teleop).

## Customization

- **Different Python version:** pin it explicitly — `uv python pin
  <version>` for uv projects, or the base image tag for Docker (e.g. the
  Python tag on the official ROS 2 / `python` images) — rather than relying
  on whatever the environment happens to have.
- **Different ROS 2 distro:** swap the base image tag in
  `examples/Dockerfile.ros2` (e.g. `jazzy` ↔ `lyrical`); re-verify the tag
  exists on [hub.docker.com/_/ros](https://hub.docker.com/_/ros) first —
  see `architect`'s Platform gotchas for the current distro
  recommendation (Lyrical Luth generally; Jazzy Jalisco for the Nav2
  vertical).
- **Different GPU / CUDA version:** swap the `nvidia/cuda` base tag in
  `examples/Dockerfile.gpu-ml` to match the target host's driver-supported
  CUDA version — check with `nvidia-smi` on that host, don't assume.
- **Adding system packages to a uv-only project:** that's the signal to
  graduate from uv to Docker, not to reach for `pip install --system` or
  host-level `apt install` as a workaround — see the decision tree above.
  Exception (verified 2026-07-12, manip-trial): a single trivial host
  package (e.g. `ffmpeg` for dataset video decode) on a macOS ML project,
  where Docker would forfeit the MPS accelerator — a ~17x inference-latency
  hit, per Platform gotchas — document the one `brew install` step in the
  project README and stay on uv.

## References

- `references/uv-patterns.md` — pyproject.toml shape, `uv sync`/`uv run`,
  lockfiles, dependency groups, and when to graduate to Docker.
- `references/docker-patterns.md` — multi-stage Docker builds with uv inside,
  official ROS 2 image tags and variants, local/remote parity mechanics.
- `references/gpu-and-remote.md` — NVIDIA Container Toolkit setup, `--gpus
  all`, headless/remote display strategy and the handoff to `foxglove`.
- `examples/pyproject-uv.toml` — minimal pure-Python uv project (status:
  unverified).
- `examples/Dockerfile.ros2` — ROS 2 workspace container with uv for the
  Python-glue layer (status: unverified).
- `examples/Dockerfile.gpu-ml` — GPU-enabled multi-stage uv build for an ML
  training/inference container (status: unverified).
- Upstream: [uv docs](https://docs.astral.sh/uv/), [uv + Docker
  guide](https://docs.astral.sh/uv/guides/integration/docker/), [official ROS
  2 images](https://hub.docker.com/_/ros), [NVIDIA Container Toolkit
  docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/).
  Sibling skills: `architect` (routes here early), `integration`
  (multi-module app Dockerfiles/compose — not duplicated here), `foxglove`
  (remote/headless visualization), `ros2`, `lerobot`.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.4.0 (2026-07-24): tb4-teleop absorption — Platform gotchas gains the
  macOS network-service-order gotcha: a Mac cabled to a no-internet robot LAN
  routes its default (internet) down the dead-end LAN unless Wi-Fi is ordered
  above the USB LAN.

- 1.3.0 (2026-07-18): Key directives gains the machine-preflight bullet:
  run `npx robium-ai doctor --json` (robium CLI 0.1.0, shipped 2026-07-18)
  before the env decision instead of ad-hoc shell probes.
- 1.2.0 (2026-07-15): vla-trial absorption — Platform gotchas gains the
  quantified Docker-macOS-MPS latency gotcha (0.55s MPS vs ~9s CPU, ~17x),
  generalizing the manip-trial exception into an ML/VLA containerization
  decision rule (seen 2x).
- 1.1.1 (2026-07-12): manip-trial absorption — uv-vs-Docker graduation
  rule gains the macOS/MPS exception (one trivial host dep, e.g. ffmpeg,
  doesn't justify losing the accelerator to Docker).
- 1.1.0 (2026-07-11): nav-trial absorption — parity checklist gains the
  buildx-cache caveat (`down --rmi local` ≠ cold rebuild; add `docker
  builder prune` for a true cold check). Dockerfile.ros2 shape exercised
  successfully via adaptation in a real arm64 build (not verbatim, so the
  example stays unverified).
