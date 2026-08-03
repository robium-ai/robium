# Setup and requirements

GPU/driver/CPU/RAM/OS/storage requirements, the three install paths
(container, pip, workstation), and headless/livestream networking for Isaac
Sim. Source: `docs.isaacsim.omniverse.nvidia.com`'s System Requirements,
Container Installation, Python (pip) Installation, and livestream-client
pages, fetched directly on 2026-07-10 (method noted per section below).
**Requirements change per release**; re-verify against the live
requirements page before trusting a number here in a real project.

## GPU, driver, CPU, RAM, storage (direct fetch on 2026-07-10)

| Requirement | Minimum | Recommended | Ideal |
|---|---|---|---|
| GPU | GeForce RTX 4080, 16 GB VRAM | GeForce RTX 5080, 16 GB VRAM | RTX PRO 6000 Blackwell, 48 GB VRAM |
| GPU driver (Linux) | 595.58.03+ | – | – |
| GPU driver (Windows) | 595.97+ | – | – |
| CPU | Intel Core i7 (7th gen) / AMD Ryzen 5, 4 cores | Intel Core i7 (9th gen) / AMD Ryzen 7, 8 cores | Intel Core i9 X-series / AMD Ryzen 9 or Threadripper, 16 cores |
| System RAM | 32 GB | 64 GB | 64 GB |
| Storage | 50 GB SSD | 500 GB – 1 TB NVMe | 500 GB – 1 TB NVMe |

Notes:

- **GPUs without RT cores are unsupported regardless of VRAM**: the docs
  call out A100 and H100 explicitly as not supported, since Isaac Sim's
  RTX renderer needs hardware ray-tracing cores that data-center compute
  GPUs lack.
- A GPU with less than 16 GB VRAM may struggle rendering scenes exceeding
  ~16 megapixels per frame, a soft ceiling on top of the hard minimum
  above, worth knowing before sizing a multi-camera synthetic-data scene.
- `aarch64` support is limited to the NVIDIA DGX Spark running DGX OS 7,
  not a general ARM/Jetson path.

**Reconciliation note:** this GPU/RAM floor matches the figures already
recorded in this repo's architect skill (RTX 4080 min / 16 GB VRAM, RTX
5080 recommended, 32 GB RAM min / 64 GB recommended); no discrepancy found
between architect's Platform gotchas and the live requirements page as of
the 2026-07-10 session's fetch.

## Supported operating systems (direct fetch on 2026-07-10)

- **Linux:** Ubuntu 22.04 or 24.04.
- **Windows:** Windows 11 only; **Windows 10 is no longer supported.**
- **macOS:** not supported, on any hardware (see `SKILL.md`'s Platform
  gotchas; this is a hard stop, not a workaround-able gap).

## Three install paths

**1. Container (recommended for reproducibility).** `nvcr.io/nvidia/
isaac-sim:6.0.1` on NGC: the pinned, versioned path that reproduces
identically between a dev machine and a remote GPU server, echoing the
`environments` skill's general local/remote parity goal. Requires Docker
plus the NVIDIA Container Toolkit on the host (Linux only; see
`environments`' GPU-and-remote reference for that generic setup). See
`examples/docker-run-command.md` for the full invocation.

**2. Pip package.** Python 3.12 is required. The `isaacsim` metapackage
provides optional extras for installing components individually or in
bundles (`isaacsim-kernel`, `isaacsim-app`, `isaacsim-core`, and others).
Install with:

```bash
pip install isaacsim[all,extscache]==6.0.1.0 --extra-index-url https://pypi.nvidia.com
```

(`isaacsim[all,extscache]` pulls every component with extension caching for
faster startup; `isaacsim[BUNDLE]` is a smaller bundled alternative without
that cache.) PyTorch with CUDA should be installed first, into an
activated virtual environment. This is the lighter-weight path for an
already-provisioned Linux/Windows workstation; it still needs the same
GPU/driver floor above, but skips the container layer. Prefer the
container path per `SKILL.md`'s Key directives unless this machine is not
going to be redeployed elsewhere. Source: direct fetch of the pip
installation page on 2026-07-10.

**3. Workstation / Omniverse Launcher.** A full local GUI install for
interactive scene authoring on a single machine; same GPU/driver/OS floor
applies. Use this only for local authoring; it is not the reproducible path
for a project that also needs to run headless on a remote server.

## Headless + livestream networking (direct fetch on 2026-07-10)

Running headless: launch with `./runheadless.sh -v` (Linux/container) or
the equivalent Windows batch file; no display is required, which is the
default posture for a remote/cloud GPU box (see `SKILL.md`'s Key
directives on headless-first, not X11).

Livestreaming the viewport uses WebRTC. The host GPU must support NVENC
(hardware video encoding) to stream at all. Two ports must both be
reachable; opening only one is a common half-working setup:

| Port | Protocol | Purpose |
|---|---|---|
| 49100 | TCP | WebRTC signaling |
| 47998 | UDP | WebRTC media stream |

Two client options connect to a running headless instance:

- **Native desktop client**: the Isaac Sim WebRTC Streaming Client,
  available for Windows, macOS, and Linux (the client itself runs
  cross-platform even though Isaac Sim's server side does not run on
  macOS).
- **Browser client**: a Docker Compose deployment serving a browser-based
  interface, reachable from any Chromium-based browser with no local
  install.

For a remote/cloud target reachable over the public internet (not just a
LAN), set the public IP and ports explicitly at launch so the stream
announces the correct endpoint to remote clients:

```
--/exts/omni.kit.livestream.app/primaryStream/publicIp=<PUBLIC_IP>
--/exts/omni.kit.livestream.app/primaryStream/signalPort=49100
--/exts/omni.kit.livestream.app/primaryStream/streamPort=47998
```
