# When Isaac Sim fails

Route by the first layer that lacks evidence.

## The runtime will not start

- Compare the host GPU, ray-tracing capability, driver, OS, and memory with the
  requirements for the exact Isaac Sim release.
- Confirm GPU passthrough in a small container before debugging Isaac Sim.
- Separate an unsupported host from a bad image tag, cache permission, EULA, or
  container-user problem.
- A container carries a CUDA runtime, not the host kernel driver. An old host
  driver can surface as a renderer or startup failure.

## Python imports or scene startup fail

- In standalone scripts, construct `SimulationApp` before importing other
  Isaac Sim modules. The import path itself is release-sensitive.
- Compare the code and extension names with the installed release rather than a
  tutorial for another major version.
- Reduce to a minimal stage before diagnosing robot or sensor assets.

## The remote viewer is black or unreachable

- Confirm both signaling and media paths. A reachable TCP port does not prove
  UDP media is reaching the client.
- Compare server render resolution with a resolution accepted by the client.
  Robium observed a mismatch producing a black screen with an explicit
  resolution error.
- In Robium's 2026-07 Isaac Lab/RunPod trial, VNC or VirtualGL connected while
  Kit's Vulkan RTX viewport remained unusable. Compare that signature, then use
  a streaming path supported by the selected Isaac Sim release.
- On a remapped cloud host, distinguish internal service ports from the public
  ports entered in the client.

## ROS 2 sees no useful data

- Verify the bridge supports or has been proven against the project's ROS 2
  distro and operating system.
- Confirm the bridge extension, shared ROS context, simulation clock, topic
  names, types, QoS, and frame IDs before debugging downstream ROS nodes.
- Generic discovery, QoS, TF, and launch issues cross into ROS 2 guidance only
  after the bridge boundary is producing evidence.

## Policy stepping and interactive streaming conflict

- A view-only stream from a headless training script and an interactive editor
  are different applications.
- Robium's Isaac Lab trial observed the full editor timeline invalidating the
  policy's physics tensor view while `env.step()` ran. Choose headless policy
  execution with view-only streaming, or interactive editor control without
  policy stepping, unless the current release provides a proven integration.
