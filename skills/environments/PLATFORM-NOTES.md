# Environment platform notes

These observations explain choices that can look arbitrary without their
measured conditions. They are evidence, not universal performance claims.

- **ROS 2 on macOS:** use Linux or a container for the normal supported ROS 2
  workflow. Gazebo by itself may run natively, but the full ROS integration
  inherits this boundary.

- **Apple Silicon acceleration:** Docker Desktop does not pass Metal/MPS into a
  Linux container. In Robium's `manip-trial` and `vla-trial`, SmolVLA inference
  measured about 0.55 seconds per forward pass with host-native MPS and about 9
  seconds on CPU in Docker or Cloud Run, roughly a 17x difference. For an ML
  policy on a Mac, measure CPU latency before choosing Docker. A trivial host
  dependency such as `ffmpeg` may be a better documented exception than losing
  the accelerator.

- **arm64 slim images:** a dependency without an arm64 manylinux wheel falls
  back to a source build. In the 2026-07-15 `manip-trial`, `pymunk` required a
  compiler and failed with `gcc` absent. Install the build toolchain in a build
  stage or choose a base that contains it; do not assume all architectures have
  the same wheels.

- **GPU containers:** NVIDIA Container Toolkit is a Linux-host dependency.
  Docker on macOS cannot create an NVIDIA accelerator path. Some applications,
  including Isaac Sim/Lab and CUDA-heavy training, therefore use the Mac only
  as an SSH/browser client and run on a compatible remote GPU machine.

- **Cold rebuild claims:** `docker compose down --rmi local` removes local
  images but not the BuildKit/buildx layer cache. Robium's 2026-07-11
  `nav-trial` used an additional builder-cache prune to test a genuinely cold
  build. Cache removal is destructive to build performance, so use it only when
  the test explicitly needs that evidence.

- **Mac plus private robot LAN:** in the 2026-07-24 `tb4-teleop` setup, macOS
  preferred a wired no-internet robot LAN over Wi-Fi for the default route.
  Moving Wi-Fi above the USB LAN in Network Service Order restored internet
  while the robot subnet continued over the cable. Read
  [robot networking](references/robot-networking.md) before generalizing that
  topology.
