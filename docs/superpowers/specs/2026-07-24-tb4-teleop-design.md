# tb4-teleop — browser teleoperation of a real TurtleBot 4

**Status:** design approved (brainstorming) — 2026-07-24
**App dir:** `apps/tb4-teleop/`
**Vertical:** Classical ROS · real hardware · teleoperation
**Phase 1 scope:** navigation only (drive + live scan + status). Camera (OAK-D) and
SLAM mapping are explicitly deferred to later phases.

## 1. Purpose & what makes this app different

Drive a **physical TurtleBot 4** (not a simulator) from a **browser** over Wi-Fi, with
live sensor feedback. This is the repo's first **real-hardware** app — every prior app
(nav-trial, manip-trial, vla-trial) runs in simulation. The Mac stays **ROS-free**: all
control and visualization happen in a browser talking to a bridge that runs *on the
robot*.

Phasing (only Phase 1 is in scope for this spec):
- **① Navigation (this spec):** teleop drive, live `/scan`, battery/dock/hazard status.
- **② Camera:** stream the OAK-D (`/oakd/rgb/image_raw`) into the browser.
- **③ Mapping:** SLAM (slam_toolbox) to build/save a map while teleop-driving.

## 2. The hardware (verified 2026-07-24)

| Fact | Value |
| --- | --- |
| Platform | TurtleBot 4 (iRobot Create 3 base + Raspberry Pi 4 + RPLIDAR + OAK-D) |
| OS / arch | Ubuntu 22.04.4 (jammy), aarch64 |
| ROS | **Humble** (`/opt/ros/humble`) |
| Middleware | CycloneDDS, `ROS_DOMAIN_ID=0`, no namespace |
| Robot IP | `192.168.0.100` (wlan0, RobotWiFi Wi-Fi, `autoconnect: yes`, persists reboots) |
| Mac IP | `192.168.0.101` (en5 wired into router LAN1) |
| Router | `192.168.0.1` (RobotWiFi, isolated LAN — no internet uplink) |
| SSH | `ubuntu@192.168.0.100`, key installed; sudo password `turtlebot4` |
| mDNS | avahi **inactive** — `ubuntu.local` does NOT resolve; use the IP |
| `/cmd_vel` type | **`geometry_msgs/msg/Twist`** (plain Twist — Foxglove Teleop default) |

**Split-DDS caveat:** the Create 3 base runs its own FastDDS on `usb0`; the Pi runs
CycloneDDS on `wlan0`. So `ros2 topic info /cmd_vel` reports **0 subscribers** even
though the base is listening — the base's subscription lives in a different DDS realm,
invisible to Pi-side introspection. **Movement can only be confirmed empirically** (drive
and watch the wheels), never by subscriber count.

Live topics available to the bridge (24): `/scan /cmd_vel /tf /tf_static /battery_state
/imu /joint_states /wheel_status /dock_status /hazard_detection /joy /robot_description
/ip /oakd/rgb/image_raw` (+ preview/camera_info).

## 3. Architecture (Phase 1)

```
[ Browser on Mac ]                         [ TurtleBot 4 (192.168.0.100) ]
 Foxglove Studio                            foxglove_bridge  (ROS node)
  - Teleop panel  --publishes /cmd_vel-->    :8765 WebSocket  <--localhost DDS--> ROS topics
  - 3D/LaserScan  <--subscribes /scan-----                                          |
  - Indicators    <--battery/dock/hazard--                              Create 3 base (drives)
        |                                                               RPLIDAR (/scan)
        +-------------- ws://192.168.0.100:8765 (TCP) --------------------+
```

- **On the robot:** `ros-humble-foxglove-bridge` runs as a node exposing a WebSocket on
  `:8765`. It sees ROS topics over localhost DDS — no cross-host DDS multicast, which is
  exactly why this design avoids the macOS Docker-DDS problem.
- **In the browser:** Foxglove (`app.foxglove.dev` or the desktop app) connects to
  `ws://192.168.0.100:8765` and loads a **committed layout** (`foxglove/tb4-teleop-layout.json`):
  - **Teleop panel** → topic `/cmd_vel`, type `geometry_msgs/Twist`, with conservative
    speed limits (see §5).
  - **3D panel** → `/scan` (LaserScan), `/tf` + `/tf_static`, `/robot_description`.
  - **Indicator/Raw-message panels** → `/battery_state`, `/dock_status`,
    `/hazard_detection`.
- **Mac:** browser only. No ROS, no Docker, no native install.

**Why not the alternatives** (recorded so we don't relitigate): native ROS 2 on macOS has
no good build; Docker Desktop's VM breaks DDS multicast to the physical LAN; a custom
FastAPI/rclpy gateway is more code than a first teleop needs. `foxglove_bridge` +
Foxglove panels is the shortest path and reuses nav-trial's proven foxglove pattern. A
custom session-gateway (the nav/manip/vla demo shape) remains a *later* option for a
public demo, out of scope here.

## 4. Environment & reproducibility (real hardware)

nav-trial's env is a Docker image; **this app's "environment" is the robot itself plus a
scripted, reproducible bring-up of the bridge.** Reproducibility means: anyone can bring
the teleop path up from a clean robot with committed artifacts.

Robot-side artifacts (committed in the app):
- **Install:** `ros-humble-foxglove-bridge` via apt (one-time; see §7).
- **Launch:** a committed launch file (or documented `ros2 launch foxglove_bridge
  foxglove_bridge_launch.xml port:=8765`) plus, optionally, a **systemd unit** so the
  bridge starts on boot. Phase 1 may start with a manual/`ssh` launch and add the
  systemd unit once validated.
- **Layout:** `foxglove/tb4-teleop-layout.json` — import once into Foxglove.

No container on the Pi for Phase 1 (a Pi-4 arm64 image for one bridge node is not worth
the weight); if a container is later justified it is an additive change, not a
requirement.

## 5. Safety model (a real robot moves)

- **Speed caps** set in the Foxglove Teleop panel (start low, e.g. linear ≤ 0.15 m/s,
  angular ≤ 0.4 rad/s; raise after first successful drive).
- **Supervised first drive:** undock onto clear floor, human watching, ready to
  power-off / e-stop the base.
- **Status awareness:** `/hazard_detection` and `/dock_status` visible in the layout;
  the Create 3 base has its own bump/cliff safety that will stop motion.
- The bridge is on an **isolated LAN** (RobotWiFi has no internet), so exposure is
  limited to the local network — acceptable for Phase 1.

## 6. Testing — hardware-in-the-loop smoke

Chosen approach: **HIL only** (no simulator fallback in Phase 1). The smoke test is run
with the robot **powered and on RobotWiFi**; it is not CI-runnable without the robot,
and that is an accepted, documented limitation.

`make smoke` asserts, from the Mac:
1. **Robot reachable:** `ping`/SSH `192.168.0.100` succeeds.
2. **Bridge up:** the `:8765` WebSocket accepts a connection (a small
   foxglove-websocket / websocket client handshake, or a scripted check).
3. **Topics flowing:** the bridge advertises `/scan` and it is publishing (non-zero
   message rate within a timeout).
4. **Command path accepts input:** publishing a **zero** `Twist` to `/cmd_vel` through
   the bridge is accepted without error (zero velocity = safe, robot does not move).

**Definitive manual pass bar (the real bar):** *a human drives the real robot from the
Foxglove Teleop panel in a browser and the robot moves as commanded.* The HIL smoke is
the automated proxy; the manual drive is the truth. The registry card records the
manual-verified date.

Test scripts live in `apps/tb4-teleop/tests/`. The smoke client must speak the
**Foxglove WebSocket protocol** (the `foxglove-websocket` Python package), NOT the
rosbridge protocol — `foxglove_bridge` and `rosbridge_server` are wire-incompatible, and
we chose `foxglove_bridge`. (If a rosbridge-style client like `roslibpy` is ever wanted,
it requires switching the robot to `rosbridge_server`.) Exact client pinned in the
implementation plan.

## 7. One-time bridge install (chosen: cable + Internet Sharing)

The bridge is not yet installed and RobotWiFi has no internet. One-time procedure:
1. Re-cable robot↔Mac (direct Ethernet).
2. macOS **Internet Sharing**: share Wi-Fi (iPhone hotspot) → to the USB LAN adapter.
3. On the robot: `sudo apt update && sudo apt install -y ros-humble-foxglove-bridge`.
4. Unplug; robot returns to RobotWiFi Wi-Fi. Package is now cached permanently.

(During install the Mac is on the WAN/NAT side and won't see ROS topics — that's fine,
we're only running apt. Topic access resumes once back on the LAN.)

## 8. Repo integration (bootstrap + registry)

- Bootstrap structure/conventions from **nav-trial** (foxglove layout pattern, Makefile
  shape, README, `docs/architecture-brief.md`).
- `docs/architecture-brief.md` written by the `robium-architect` agent at kickoff.
- **Registry:** add a `tb4-teleop` quick-index row + card in the **same commit** the app
  reaches its pass bar. Card notes: first real-hardware app, HIL smoke, foxglove_bridge
  reuse, split-DDS caveat, the network/creds facts, and phase roadmap.
- Battle scars to encode: split-DDS invisible subscriptions; TB4 "zero topics" =
  wlan0-down/DDS-bound-to-wlan0 chain; DDS-does-not-cross-NAT (LAN vs WAN); local clock
  sync without NTP. (Already in `learnings/2026-07-24.md`.)

## 9. Out of scope (Phase 1)

- OAK-D camera streaming (Phase 2).
- SLAM / mapping (Phase 3).
- Autonomous Nav2 goal-sending (this is *teleop*, not autonomy).
- Public/remote demo (Cloud Run session gateway) — local-network only for now.
- systemd auto-start may be deferred to after the first validated manual drive.
