# Remote viewport over WebRTC

Use this card when a headless Isaac Sim instance needs an interactive or
view-only viewport. The observations were measured on a RunPod pod running Go2
on Isaac Lab image 3.0.0-beta2-post1 (driver 580.159.04, Python 3.12.13) on
2026-07-27/28. Isaac Sim owns the streaming protocol; `runpod` owns provider
port exposure, mapping, and proxy mechanics.

## Use a supported client

NVIDIA's current remote-viewport path is WebRTC. In the tested pod,
VNC/VirtualGL connected but could not carry Kit's Vulkan RTX viewport and
showed black or software output. Preserve that as a failure signature for that
stack, not a claim that every remote-desktop product or future renderer fails.

- The native **Isaac Sim WebRTC Streaming Client** is available for supported
  Windows, macOS, and Linux client platforms and suits local or trusted
  networks.
- NVIDIA also documents a separate Docker Compose web client for Chromium-based
  browsers and recommends it for cloud or remote deployments. It runs beside
  Isaac Sim; it is not bundled into the Isaac Sim NGC container.
- The streaming endpoints provide neither authentication nor encryption. Keep
  them on a trusted network or add an authenticated TLS boundary.

Use the current [NVIDIA livestream client guide](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html)
for the native and browser deployments.

## Start the stream and prove both paths

- Use the launch command for the installed distribution. Current documented
  forms include `isaac-sim.streaming.sh`, container `runheadless.sh`, and the
  full-streaming pip application; re-check before scripting one.
- WebRTC needs signaling and media. In the current NVIDIA guide these are TCP
  49100 and UDP 47998. Re-check them for the selected release and open both.
- For a public endpoint, pass the public IP and advertised ports through the
  current Kit settings. Do not expose the unauthenticated service directly.
- In the tested RunPod setup, the client used the pod public IP and externally
  mapped ports. Verify current provider behavior with `runpod`; do not copy that
  mapping to another provider.
- A reachable TCP port proves signaling only. Confirm media, a loaded stage,
  and a changing frame before debugging the application.

The current container guide requires host networking for the native WebRTC
path; Docker port publishing is not equivalent. The official web-client Compose
deployment owns its own networking shape.

## Black, grainy, or slow output

- Compare the server render size with the client's selected resolution. The
  native client tested in 2026-07 offered 720p, 1080p, 1440p, and 4K choices; a
  mismatch produced a black screen and a resolution-difference error.
- Pass renderer dimensions through current Kit settings. In the tested Isaac
  Lab launcher, generic `--width` and `--height` flags were not accepted.
- In that client, grainy output tracked render resolution rather than an
  exposed bitrate control. Slow output tracked pod distance. Recheck the
  current client before carrying either diagnosis to another release.

## Separate viewing from control

- Bare Isaac Lab scripts with livestreaming produced video but did not load the
  full editor's input extensions in the tested image, so the stream was
  view-only.
- The full editor was interactive, but its timeline fought the running Isaac
  Lab policy's `env.step()` and invalidated the physics tensor view in that
  image.
- The reliable choices in that trial were headless policy execution with a
  view-only stream, or editor control without policy stepping. Retest this
  limitation on the selected Isaac Sim/Lab pair; do not state it as a permanent
  product constraint.
