# tb4-teleop — Orin web console (design)

**Status:** design approved in brainstorming (2026-07-24); ready for `writing-plans`.
**Supersedes:** the earlier minimal-launcher draft of this file — this expands the Orin
console to a real teleop console (webcam + on-page controls + a Foxglove launch button).
**Companion to:** `docs/superpowers/specs/2026-07-24-tb4-teleop-design.md` (Phase 1, nav —
done) and `apps/tb4-teleop/docs/architecture-brief.md`.

> **New phase of the existing `tb4-teleop` app — do NOT create a separate app.** Phase 1
> (drive a real TurtleBot 4 from Foxglove via `foxglove_bridge`) is complete and
> human-verified. This phase adds an **NVIDIA Jetson Orin** serving a web console with
> three things: **(1) on-page teleop controls, (2) a live USB-webcam view (webcam on the
> Orin — not the OAK-D), (3) an "Open in Foxglove" button.** Robot/bridge facts you need
> are recapped in §10. Next step: `writing-plans`, then build under `apps/tb4-teleop/orin/`.

---

## 1. Goal

An Orin-served web console that is the operator's front door to teleop:
- **drive the robot** from on-page controls (buttons + keyboard),
- **see a live webcam** feed from a USB camera on the Orin,
- **launch Foxglove** pre-wired to the robot's bridge (one click, no manual connect/import),

and — a second driver stated by the user — **package it so the same image runs on other
platforms and on server instances with simulators**: Dockerized and repointable at any
`foxglove_bridge`, not just this robot.

## 2. Architecture

```
Operator browser
  │  http://<orin>:8080          ── nginx: console page + env.js (static)
  │  <img src http://<orin>:8081/stream>   ── ustreamer: MJPEG webcam
  │
  │  ws://192.168.0.100:8765  (Foxglove WebSocket protocol, foxglove.sdk.v1)
  │      page CLIENT-PUBLISHES /cmd_vel (Twist) and /teleop/{dock,undock} (Empty)
  ▼
Robot foxglove_bridge ──localhost DDS──▶ TurtleBot 4 ROS graph   (unchanged from Phase 1)

  "Open in Foxglove (web)" button → app.foxglove.dev deep-link (ds.url=ws://robot:8765)
```

**The Orin only serves the console + the webcam.** Every robot command goes
**browser → robot's `foxglove_bridge`**, exactly as Phase 1's Foxglove Teleop panel does.
Consequences:
- **No ROS on the Orin** (this phase) — it's nginx + a webcam streamer.
- **Repointable:** aim the whole console at a different bridge (a sim's `foxglove_bridge`
  on a server) by changing one env var.
- **No mixed-content problem for the page's own teleop:** the console is served over plain
  **http**, so its `ws://` connection to the robot is allowed (the https `app.foxglove.dev`
  path is the one that can hit the https→ws block; that's a Foxglove-side concern, not the
  custom page's).

**Network assumption / deployment (see §10 for the board facts):** for the console to work,
the operator's browser must reach **both** the Orin (`:8080/:8081`) and the robot bridge
(`ws://192.168.0.100:8765`). The clean deployment is the Orin on **RobotWiFi Wi-Fi**
alongside the robot and the operator's Mac. But RobotWiFi has **no internet**, and the Orin
only gets online via a **metered iPhone hotspot** — so the flow is: **pull/build the (small)
image while the Orin is on the hotspot, then serve on RobotWiFi.** During development the
Orin is also reachable from this Mac over its **USB link at `192.168.55.1`** (that path is
Mac-only, not a general LAN address). Keep images small (nginx:alpine ~20 MB is fine; the
metered link rules out multi-GB pulls).

## 3. Decisions locked in brainstorming

- **Teleop path:** browser → robot `foxglove_bridge` (client-publish). *Rejected:* ROS 2 +
  rosbridge on the Orin (heavier, re-inherits the CycloneDDS discovery gotchas from Phase 1,
  ties the console to a ROS network instead of a portable bridge URL); a browser→Orin→robot
  relay (extra hop, no gain).
- **Webcam:** MJPEG via **ustreamer**. *Deferred:* WebRTC (lower latency, much more
  plumbing — a later upgrade; keep the page's video panel swappable so it can drop in).
- **On-page teleop input:** on-screen directional buttons **and** keyboard (WASD/arrows),
  both **hold-to-drive**.
- **Dock/undock:** yes, on the page too (publish `std_msgs/Empty` to `/teleop/{dock,undock}`;
  the Phase-1 `teleop_actions.py` helper already turns those into Create 3 actions).
- **Foxglove launch:** **web-only** button (`app.foxglove.dev` deep-link). Desktop
  `foxglove://` button deferred.
- **`FOXGLOVE_LAYOUT_ID`:** ship **empty** for now (operator picks the imported layout;
  connection still auto-wires). Wire the id later.
- **Realization for the Foxglove launcher:** deep-link (free, full Foxglove incl. Teleop).
  *Rejected:* self-hosted `@foxglove/embed` viewer — **requires a paid Foxglove plan** (user
  confirmed; see `learnings/2026-07-24.md`).

## 4. Components (each a focused, testable unit)

**`orin/web/` — console page (static, vanilla JS, no framework):**
- `index.html` — webcam panel (large) + teleop panel (d-pad, dock/undock, "Open in
  Foxglove") + a connection-status dot + a settings row (robot host/port, prefilled from
  `env.js`, edits persisted to `localStorage`).
- `foxglove-ws.js` — minimal Foxglove WebSocket client: connect (`foxglove.sdk.v1`),
  serverInfo/advertise handshake, **client-advertise** `/cmd_vel`
  (`geometry_msgs/msg/Twist`) and `/teleop/{dock,undock}` (`std_msgs/Empty`), send
  CDR-encoded message frames. Exposes `connect()`, `publishTwist(lin, ang)`,
  `publishEmpty(topic)`, and a status callback. Main unit-test target.
- `teleop.js` — input → velocity. Buttons + keyboard (WASD/arrows). **Hold-to-drive:**
  keydown/pointerdown starts a ~10 Hz publish of a fixed Twist; keyup/pointerup/**window
  `blur`** publishes a **zero** Twist (dead-man). Speed caps match Phase 1 (linear ≤0.15,
  angular ≤0.4).
- `env.js` — emitted at container boot from env vars (§6).

**Webcam:** `ustreamer` reads `/dev/video0` and serves MJPEG on `:8081`; the page shows it
via `<img>`. Its device/resolution/fps are env-configurable.

**Docker (`orin/docker/`):** `nginx:alpine` (multi-arch arm64 + amd64) serves the static
page on `:8080`; `entrypoint.sh` runs `envsubst` on `web/env.js.tmpl` → `env.js`;
`compose.yaml` brings up nginx + ustreamer together (ustreamer needs `--device /dev/video0`).

## 5. Publishing over the Foxglove WS protocol (the one non-obvious bit)

`foxglove_bridge` accepts client-published topics — this is literally how Phase 1's Foxglove
Teleop panel drives `/cmd_vel`. From raw JS it needs a small **CDR encoder**:
- **Twist:** 4-byte little-endian CDR encapsulation header (`00 01 00 00`) + six `float64`
  LE (linear x/y/z, angular x/y/z), 8-aligned from the body start → **52 bytes**.
- **Empty:** the 4-byte encapsulation header (exact length — some RMWs pad — is **verified
  against the live bridge at build time**; the real check is that publishing to
  `/teleop/undock` fires the helper and the robot undocks).

`encodeTwist()`, `encodeEmpty()`, and `buildFoxgloveUrl()` are pure functions with
known-output unit tests.

## 6. Config / reuse (runs-anywhere)

`entrypoint.sh` runs `envsubst` at container start to emit `env.js`, so one image repoints
with no rebuild:

| Env var | Default | Purpose |
| --- | --- | --- |
| `ROBOT_HOST` | `192.168.0.100` | robot bridge host |
| `ROBOT_WS_PORT` | `8765` | bridge ws port |
| `WEBCAM_STREAM_URL` | `http://<orin-host>:8081/stream` | MJPEG source; **blank ⇒ hide the webcam panel** (e.g. a camera-less sim server) |
| `FOXGLOVE_LAYOUT_ID` | *(empty)* | optional org layout id for one-click layout |

Point it at the real TB4 today; at a sim's `foxglove_bridge` on a server later — same image.
The webcam is Orin-hardware-specific (needs `/dev/video0`); on a camera-less host, leave
`WEBCAM_STREAM_URL` blank and the panel hides.

## 7. Suggested shape (fits the existing app)

```
apps/tb4-teleop/
  orin/                       # new — the Orin web console
    web/index.html
    web/foxglove-ws.js        # WS client + CDR encoders (buildFoxgloveUrl lives here or app.js)
    web/teleop.js             # input → hold-to-drive publish
    web/app.js                # wiring, settings/localStorage, status
    web/env.js.tmpl           # envsubst → env.js at boot
    docker/Dockerfile         # nginx:alpine, multi-arch
    docker/compose.yaml       # nginx + ustreamer
    entrypoint.sh
    tests/                    # unit tests (URL builder, CDR encoders) + container serve check
  Makefile                    # add: orin-build, orin-serve, orin-smoke, orin-down (leave bridge/teleop/smoke)
  foxglove/tb4-teleop-layout.json   # reused unchanged
```

## 8. Testing / pass bar (honestly scoped — "our artifact")

`make orin-smoke`:
1. Orin container serves the page (HTTP 200 + an expected marker in the HTML).
2. `buildFoxgloveUrl({host, port, layoutId})` returns the exact expected deep-link
   (`ds=foxglove-websocket`, correct `ds.url`, layoutId present/absent).
3. `encodeTwist()` / `encodeEmpty()` produce the known CDR byte sequences.
4. `foxglove/tb4-teleop-layout.json` is valid JSON and still contains the Teleop panel on
   `/cmd_vel` (guards against layout drift).

The registry card states plainly that Orin-phase smoke covers the **console contract**, not
an end-to-end drive: the live webcam and live drive stay the **human HIL bar** (no
camera/robot in CI). Phase-1 `make smoke` (HIL bridge/scan/cmd_vel) is unchanged.

## 9. Phasing & out-of-scope

`apps/tb4-teleop/orin/` · **infra Phase 2** (a prerequisite host; camera → 3, mapping → 4 in
the brief's roadmap). **Out (this phase):** WebRTC, image processing, the Orin joining the
ROS graph, any auth, the desktop `foxglove://` button, a wired `FOXGLOVE_LAYOUT_ID`.

## 10. Robot facts recap (so you don't rediscover them)

From `apps/tb4-teleop/README.md` + architecture brief (verified 2026-07-24):
- Robot: **TurtleBot 4** (Create 3 + RPi 4 + RPLIDAR; OAK-D present but **unused here**),
  **ROS 2 Humble**, IP **`192.168.0.100`** on RobotWiFi Wi-Fi.
- Bridge: **`foxglove_bridge` 3.4.2 on `:8765`**, WS subprotocol **`foxglove.sdk.v1`**.
- **`/cmd_vel` is `geometry_msgs/msg/Twist` (plain Twist, NOT TwistStamped).**
- Dock/undock = `std_msgs/Empty` on `/teleop/{dock,undock}`, bridged by
  `robot/teleop_actions.py` to Create 3 actions (the helper runs via `make bridge`).
- Working layout already in the Foxglove org: `foxglove/tb4-teleop-layout.json`.
- The Orin is arm64 (Jetson) → keep the image multi-arch (`nginx:alpine` qualifies;
  ustreamer builds for arm64).

**Orin board facts (stood up 2026-07-24, from `learnings/2026-07-24.md`):**
- Hardware: **Jetson Orin Nano (Super) 8 GB** — 6 CPU cores, ~7.4 GiB RAM, ~783 GB NVMe free.
- Software: **JetPack 6.2** (L4T R36.4.3), Ubuntu 22.04.5, **arm64**.
- **Docker GPU-ready out of the box:** Docker 26.1.3, default runtime already `nvidia`,
  nvidia-container-toolkit 1.16.2, operator in the `docker` group (relevant to camera/
  image-proc phases; **not** needed for this nginx+ustreamer phase).
- **SSH:** `ssh robium@192.168.55.1` (USB link) — keyless from this Mac is configured;
  username `robium`, hostname `ubuntu`. **`sudo` needs the operator's password** (not in
  this repo — some steps, e.g. `nmcli` Wi-Fi joins or `--device` access, need it).
- **Headless access:** USB-C data port → serial console `/dev/cu.usbmodem*` @ 115200 8N1,
  and USB device-mode Ethernet (Orin `192.168.55.1`, Mac `192.168.55.100` on `en6`).
- **Networking:** Wi-Fi `wlP1p1s0` (currently joined to the metered iPhone hotspot for
  internet; auto-reconnects), Ethernet `enP8p1s0`. Two default routes coexist (hotspot =
  internet, USB link = stable SSH) — expected, don't "fix" it. Getting it onto RobotWiFi to
  serve is a deployment step (§2).

## 11. Deep-link facts (fetched from docs.foxglove.dev via ctx7 `/websites/foxglove_dev`, 2026-07-24)

Re-verify at build time. Web (hosted) connect + optional layout:
`https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://<host>:<port>&layoutId=<uuid>`
— `layoutId` refers to a layout **already imported into the user's Foxglove org**; there is
**no** arbitrary-layout-URL param. Omit `layoutId` when `FOXGLOVE_LAYOUT_ID` is empty and the
connection still auto-wires. (Desktop `foxglove://open?ds=foxglove-websocket&ds.url=...`
exists but the desktop button is deferred.)

---

*Provenance: brainstorming session (superpowers:brainstorming) 2026-07-24; expands the
minimal-launcher draft after the user scoped in on-page teleop + a USB webcam on the Orin.
Foxglove deep-link/self-hosting facts fetched via ctx7 `/websites/foxglove_dev` and logged in
`learnings/2026-07-24.md`. Key decisions: browser→bridge teleop (no ROS on Orin), MJPEG via
ustreamer, deep-link launcher (self-hosted viewer ruled out as paid-plan-gated).*
