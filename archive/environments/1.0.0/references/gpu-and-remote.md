# GPU passthrough and remote/headless environments

How to get an NVIDIA GPU into a Docker container, and how to think about
display/visualization once the project is running on a headless or remote
machine. Sources: [NVIDIA Container Toolkit
docs](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
(install guide + sample workload page), fetched directly — re-verify package
versions before use, they move frequently.

## GPU passthrough: nvidia-container-toolkit (Linux only)

GPU access inside a Docker container requires the **NVIDIA Container
Toolkit** installed on the *host* — this is a Linux-only requirement (the
official install guide covers Ubuntu/Debian, RHEL/CentOS/Fedora, and
OpenSUSE/SLE; there is no first-party macOS or bare-Windows host path). See
the Platform gotchas in `SKILL.md`.

**Install (Ubuntu/Debian host, apt):**

```bash
# 1. Configure NVIDIA's package repository (see the current install guide
#    for the exact repo-setup commands — they change; don't hardcode a key
#    URL from memory).
# 2. Install the toolkit:
sudo apt-get install -y nvidia-container-toolkit
# 3. Wire it into the Docker daemon:
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

**Verify it works:**

```bash
sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

If `nvidia-smi` prints the host's GPU(s) from inside the container, the
toolkit is wired up correctly. Do this verification step on any *new* remote
host before assuming GPU workloads will just work there — it's a common
source of "works locally, fails on the server" when the toolkit is missing
or the Docker daemon wasn't restarted after configuration.

**Running a GPU workload:**

```bash
docker run --rm --gpus all my-gpu-image
```

`--gpus all` is the flag that matters day to day; `--runtime=nvidia` above is
mainly for the one-time verification (once `nvidia-ctk runtime configure`
has run, `--gpus` works without needing to also set `--runtime` explicitly on
every invocation, but check current NVIDIA docs if you see different
behavior on a given Docker version).

**CUDA base image, host driver compatibility:** the CUDA toolkit version
baked into the container image must be supported by the host's installed GPU
driver. Check the host's supported CUDA version with `nvidia-smi` (top-right
of its output) before picking a CUDA base image tag — this is one of the
sharpest local/remote parity failure modes: a dev laptop with a newer driver
building an image whose CUDA version the remote server's older driver can't
run. See `examples/Dockerfile.gpu-ml` for a concrete base-image example
(marked `status: unverified` — re-check the tag against
[hub.docker.com/r/nvidia/cuda](https://hub.docker.com/r/nvidia/cuda) before
using it in a real project).

**WSL2 note:** the official install guide referenced above documents Linux
distributions only and doesn't cover WSL2 specifically; if a remote/dev
target is Windows+WSL2, verify the current WSL2-specific GPU support path
against NVIDIA's docs separately rather than assuming the Linux steps apply
unchanged.

## Headless / remote display strategy

The instinct when a container needs to show something is X11 forwarding
(`-e DISPLAY=$DISPLAY`, mounting `/tmp/.X11-unix`, `xhost +local:docker`).
That works for **local-Linux-only, single-user** development, but it breaks
down fast:

- It doesn't work at all from a headless remote server with no X server.
- It's fragile over SSH (needs `-X`/`-Y` forwarding, a working X client
  chain, and generally poor performance for anything beyond simple 2D UI).
- It doesn't work from macOS/Windows hosts without extra tooling (XQuartz,
  VcXsrv) that itself isn't containerized or reproducible.

**Default instead to headless containers + web-based visualization.** Run
the container with no display requirement at all, and expose whatever needs
visualizing over a web UI that any browser (local or remote, any OS) can
reach. This is exactly what the `foxglove` skill covers — route to it
instead of building out X11 forwarding, especially for:

- Any remote/cloud GPU server (the common case for training or
  Isaac Sim work).
- Cross-platform teams where not everyone is on Linux.
- CI or automated runs where no display exists at all.

Reserve X11/Wayland forwarding for a narrow case: local Linux development,
one user, and a tool that genuinely has no web-based alternative — and treat
it as a local-dev convenience, not something the deployed/remote environment
depends on.

## Local vs remote parity for GPU + display

- **Don't let "works on my GPU laptop" silently mean "works on the remote
  GPU server."** Confirm both the CUDA-version-vs-driver compatibility above
  and that `nvidia-container-toolkit` is actually installed and configured
  on the remote host — it's easy to develop for weeks locally without ever
  hitting this gap.
- **Don't build the visualization story around a display that only exists
  locally.** If any part of the workflow assumes a local X server, it will
  silently fail (or need a completely different setup) the moment the
  project moves to a remote/headless host. Default to `foxglove` from the
  start so there's nothing to redo.
