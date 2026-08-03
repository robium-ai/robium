# Remote GUI over WebRTC livestream

Getting a full Isaac Sim viewport out of a headless cloud pod, with the
traps that cost real time. Battle-tested on a RunPod pod running go2 on the
prebuilt Isaac Lab image (Isaac Lab image 3.0.0-beta2-post1, driver
580.159.04, Python 3.12.13), 2026-07-27/28. These are Isaac-specific facts;
the general pod port-exposure mechanics belong to the `environments` skill's
GPU-and-remote reference; reference it, don't re-derive it here.

## The only working answer is WebRTC (VNC/VirtualGL is a dead end)

A full Isaac Sim GUI from a headless pod = a **WebRTC livestream**. Do not
reach for VNC/VirtualGL: Kit's RTX viewport renders with **Vulkan**, and
VirtualGL only intercepts GLX/OpenGL, so you get a black or software
viewport. Only GPU-Vulkan-aware protocols work: WebRTC (built in),
NoMachine, or DCV.

## Client

Client = the **Isaac Sim WebRTC Streaming Client** (macOS aarch64 `.dmg`).
Headless install (no Finder):

```bash
hdiutil attach <client>.dmg
cp -R "/Volumes/<mounted>/<Client>.app" /Applications/
xattr -dr com.apple.quarantine "/Applications/<Client>.app"
```

There is **no in-page browser WebRTC client on the NGC image**: it ships
the native client and the server extension but not a browser/JS WebRTC
client (NVIDIA's web viewer is a separate Docker-Compose piece). If you need
an in-page view, embed **MJPEG** instead (`env.render()` → `<img src=/stream>`):
that is the real Isaac render, just JPEG rather than H.264/RTX.

## Enabling the stream

- Via AppLauncher: `--livestream 1` (public) or `--livestream 2` (private),
  plus `PUBLIC_IP=<ip>`.
- Or run `/isaac-sim/isaac-sim.streaming.sh`.

**Ports:** TCP **49100** (signaling) and UDP **47998** (media). Opening only
the TCP port is insufficient; WebRTC media needs the UDP port too, and a
TCP-only setup is a common half-working state. On RunPod the ports are
**remapped**, so in the client set the Signal/Stream fields to the
**external mapped ports** and Server to the **pod public IP**. Pod
port-exposure mechanics: the `environments` skill's GPU-and-remote reference.

## Resolution must match a client dropdown option

The client offers fixed resolutions (720 / 1080 / 1440 / 4K). If the server
renders at anything else you get a **black screen** plus:

```
Cannot stream video frame with resolution AxB that differs from CxD
```

Force a matching render resolution through Kit args (AppLauncher itself has
**no `--width`/`--height` flags**; passing them yields
`error: unrecognized arguments`):

```
--kit_args "--/app/window/width=1920 ... --/app/renderer/resolution/height=1080"
```

Other symptoms: **"grainy"** is render resolution, not bitrate (there is no
bitrate setting; it is adaptive). **"Slow/laggy"** is pod distance:
geolocate the pod IP (e.g. `ip-api.com/json`) and pick a closer datacenter.

## Input forwarding is split, and the interactive combo can't run a policy

- **Bare Isaac Lab scripts** (`create_empty.py`, `play.py`) with
  `--livestream` stream **video but not input**: the interaction extensions
  never load, so the view is read-only.
- **The full editor** (`isaac-sim.streaming.sh` /
  `isaacsim.exp.full.streaming.kit`) loads those extensions, so it is
  interactive, **but it cannot run an Isaac Lab policy.** The editor
  timeline fights `env.step()`; the env never finishes reset and hangs
  (~12 min) with:

  ```
  omni.physx.tensors: All physics information was deleted while being used
  by a tensor view class ... simulationView invalidated
  ```

**Consequence:** {trained policy + interactive WebRTC + keyboard} cannot all
coexist. Pick two: a policy running headless with a view-only stream, or an
interactive editor with no policy stepping.
