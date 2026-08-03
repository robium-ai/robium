# Dockerfile guide (multi-module build quality)

How to write a Dockerfile for **one module** in a multi-container robotics
system. This is a different concern from the `environments` skill's
docker-patterns.md reference: that reference is about a *single
environment's* reproducibility (uv inside a ROS 2 image, GPU base tags,
local/remote parity). This reference is about *build quality* for a module
that's going to run as one service among several in compose — image size,
build-cache efficiency, and container-runtime behavior (signals, one
process). Read both; they compose, they don't duplicate.

## One process per container

Restated from the key directive because it's a Dockerfile-shape decision,
not just a compose one: a Dockerfile that `CMD`s a single `ros2 launch` (or
a single node executable) is the default shape. If a Dockerfile's `CMD`
starts multiple unrelated long-running processes (a supervisor script
backgrounding several nodes), that's the signal to split into multiple
Dockerfiles/services instead — supervisord-in-a-container patterns exist,
but they trade away independent restart/scaling and should be a stated
exception, not a default reach.

## Multi-stage: builder vs runtime

A ROS 2 module's build toolchain (colcon, compilers, `-dev` apt packages,
rosdep-resolved build dependencies) is large and mostly irrelevant at
runtime. Split it:

```dockerfile
# Stage 1: build — full toolchain, discarded after this stage.
# (re-verify `jazzy-ros-base-noble` against hub.docker.com/_/ros and the
# current default distro before using this tag in a real project)
FROM ros:jazzy-ros-base-noble AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3-colcon-common-extensions build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY ./src ./src
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --merge-install --install-base /opt/module_install

# Stage 2: runtime — only the built install/ tree and runtime deps.
FROM ros:jazzy-ros-base-noble
COPY --from=builder /opt/module_install /opt/module_install
# runtime-only apt deps (no compilers, no -dev packages) go here if needed
ENTRYPOINT ["/bin/bash", "-c", \
  "source /opt/ros/jazzy/setup.bash && source /opt/module_install/setup.bash && exec \"$@\"", "--"]
CMD ["ros2", "launch", "my_module", "my_module.launch.py"]
```

The runtime stage never sees `build-essential`, colcon, or the raw `src`
tree — smaller image, smaller attack surface, and a build-cache boundary
that keeps "recompile" and "ship" concerns separate. See
`examples/Dockerfile.multistage-ros2` for the complete, runnable-shape
version this pattern is drawn from, and cross-reference `environments`'
Dockerfile.gpu-ml example for the same technique applied to a heavy-Python
(uv/torch) build instead of colcon.

## Layer-cache ordering

Order instructions from least-to-most frequently changing, same as any
Docker build: apt packages and other system-level deps first, then
dependency manifests (`package.xml`, `pyproject.toml`/`uv.lock` for any
Python glue), then source code last. Changing one line of application code
should not force a full apt-get/colcon-dependency-resolution re-run.

## Signal handling for `ros2 launch`

`ros2 launch` and the nodes it starts need to receive `SIGINT`/`SIGTERM`
cleanly for graceful shutdown (lifecycle transitions, clean DDS
participant teardown). Two things commonly break this in containers:

- **Use exec form, not shell form, for the final `CMD`/`ENTRYPOINT` step**
  so the launched process is PID 1 (or receives signals directly) rather
  than being a child of an untracked shell that swallows the signal. The
  `ENTRYPOINT` pattern above uses `exec "$@"` for exactly this reason —
  without `exec`, the sourced-setup shell stays PID 1 and `docker stop`
  has to wait out the full timeout before SIGKILL.
- **`docker compose stop`'s default timeout (10s)** may not be enough for a
  ROS 2 graph with several lifecycle nodes to shut down cleanly — raise
  `stop_grace_period` in compose for modules with real shutdown work to do,
  rather than accepting SIGKILL as the normal path.

## Non-root runtime user

Same guidance as `environments`' `docker-patterns.md` — run the runtime
stage as a non-root user for a security default and permission parity with
mounted volumes:

```dockerfile
RUN useradd --create-home --uid 1000 robium && \
    chown -R robium:robium /opt/module_install
USER robium
```

## `.dockerignore`

Exclude colcon build artifacts (`build/`, `install/`, `log/`) and any local
venv from the build context — same reasoning as the single-environment case
in `environments`, and it matters more here because a multi-module repo's
build context is larger and slower to send to the daemon if left unfiltered.
