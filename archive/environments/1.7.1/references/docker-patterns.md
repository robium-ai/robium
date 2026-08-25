# Docker patterns

How to shape a Docker image for a robium project that needs ROS 2 or other
system-level dependencies: the "Yes" branch of the decision tree in
`SKILL.md`. This covers a *single environment's* Dockerfile shape; wiring
multiple app modules together with compose is the `integration` skill's job;
don't duplicate that here, cross-reference it.

Sources: official ROS 2 images at
[hub.docker.com/_/ros](https://hub.docker.com/_/ros) (fetched directly, not
from memory: tags below were current at authoring time; re-verify before
using), and the uv + Docker integration guide at
[docs.astral.sh/uv/guides/integration/docker](https://docs.astral.sh/uv/guides/integration/docker/).

## Official ROS 2 image tags

The official `ros` image on Docker Hub publishes, per distro, three variant
tiers plus an OS-codename-suffixed form:

- `ros:<distro>-ros-core`: minimal ROS 2 install.
- `ros:<distro>-ros-base`: adds basic tools/libraries (the usual starting
  point for an application image).
- `ros:<distro>-perception`: adds perception-related packages.
- Each of the above also has an explicit OS-codename form, e.g.
  `ros:jazzy-ros-base-noble` / `ros:lyrical-ros-base-resolute`; prefer the
  explicit form when you want to pin the Ubuntu base as well as the ROS
  distro, for the strongest local/remote parity guarantee.

Currently published distros include `jazzy` (Ubuntu Noble base) and
`lyrical` (Ubuntu Resolute base, current LTS), among others (`humble`,
`kilted`, `rolling`). Confirm the current set and exact tags at
[hub.docker.com/_/ros](https://hub.docker.com/_/ros) before pinning one; this
list changes as distros reach EOL and new ones ship. Desktop-variant images
are not part of the official minimal set (kept lean/secure); if you need a
desktop image, that's a deliberate, separate choice.

There is no official `ros-desktop` reason to reach for the OSRF-hosted
`osrf/ros2` images for a headless application container: official + minimal
is the default; only deviate with a stated reason.

## Base pattern: ROS 2 image + uv for the Python layer

Even inside a ROS 2 container, keep the "never pip install into system
Python" directive: if the workspace has pure-Python glue code (a bridge
script, a data-processing node, an ML inference node) with its own
dependencies, manage those with uv rather than `pip install`ing them into the
image's system Python.

```dockerfile
FROM ros:jazzy-ros-base

# Install uv by copying the binary from the official distroless image;
# no pip/curl needed for this step.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /workspace
COPY ./src ./src
COPY pyproject.toml uv.lock ./

# Python-side deps for glue code, isolated in a project venv, not the
# container's system Python.
RUN uv sync --locked

# ROS 2 workspace build (colcon ships in ros-base; add
# python3-colcon-common-extensions via apt if a variant lacks it).
RUN . /opt/ros/jazzy/setup.sh && colcon build --symlink-install
```

See `examples/Dockerfile.ros2` for the full, runnable-shape version
(non-root user, entrypoint that sources both the ROS 2 and workspace
overlays).

## Multi-stage builds with uv (mixed / heavy-Python case)

When the Python side is heavy (a training or inference stack with large
dependencies like torch), use a proper multi-stage build so the final image
doesn't carry uv's cache or build-only tooling:

```dockerfile
FROM python:3.12-slim-trixie AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM python:3.12-slim-trixie
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY . /app
CMD ["python", "train.py"]
```

The `--mount=type=cache` on `/root/.cache/uv` speeds up rebuilds without
baking the cache into any image layer; the two-step `sync` (deps first,
then the project) maximizes Docker layer-cache hits when only application
code changes. See `examples/Dockerfile.gpu-ml` for the GPU-base variant of
this same shape.

## Non-root users

Run the final container as a non-root user; it's both a security default and
a parity aid (file permissions on mounted volumes behave the same locally and
remotely):

```dockerfile
RUN groupadd --system --gid 1000 robium \
 && useradd --system --gid 1000 --uid 1000 --create-home robium
USER robium
```

## Local == remote parity, the Docker half

This is the mechanical half of the checklist in `SKILL.md`:

- **Pin tags, not `latest`.** `ros:jazzy-ros-base-noble`, not `ros:jazzy`;
  ideally pin a digest (`@sha256:...`) for anything long-lived.
- **`.dockerignore` your `.venv`, `build/`, `install/`, `log/`** (ROS 2
  colcon artifacts); building on a clean tree locally and remotely avoids
  "works because of stale local build state" bugs.
- **Bake the lockfile in, don't `COPY` a `requirements.txt` generated
  ad-hoc.** `uv.lock` (or the ROS 2 `rosdep`-resolved package list) is the
  single source of truth referenced from both local and CI/remote builds.
- **Build the same image for local dev and remote deployment**: a `docker
  build` + volume-mount for live-editing locally, the same image pushed and
  run remotely, rather than two divergent Dockerfiles.
- **Compose/multi-service wiring is out of scope here**: once you have more
  than one container that needs to talk to each other, hand off to
  `integration` for the compose file and inter-node comms plan.
