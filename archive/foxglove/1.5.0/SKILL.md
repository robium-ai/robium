---
name: foxglove
version: 1.5.0
description: >
  Foxglove for robotics visualization: foxglove_bridge setup for live ROS 2
  robots, layouts, MCAP recording and playback, and remote/web visualization
  of robots running on servers. Use when: 'foxglove', 'mcap', visualizing a
  robot running on a remote server, sharing visualization with others, or
  recording sessions for later analysis. The remote-viz answer in the robium
  stack — key to the local-vs-remote workflow (cross-ref environments). Not
  for: ROS desktop debugging (rviz2) or ML logging (rerun).
---

# foxglove

The remote/web visualization tool for robium: `foxglove_bridge` exposes a
live ROS 2 graph over a WebSocket, and the Foxglove app (desktop or
`app.foxglove.dev` in a browser) connects to it or opens a recorded MCAP
file — the answer `environments` and `gazebo` route to whenever a robot or
sim runs headless/remote and RViz2's local-display requirement doesn't fit.
Two things changed over time and matter for how this skill is used: the
bridge itself (`foxglove_bridge`, MIT-licensed, open source) moved its
active development from `foxglove/ros-foxglove-bridge` (now ROS 1-only,
maintenance mode) to the `foxglove/foxglove-sdk` monorepo, and the *app*
that used to be free/open-source "Foxglove Studio" was discontinued in
February 2024 (last open-source release v1.87.0, MPL-2.0) in favor of the
current closed-source, commercial "Foxglove" 2.x app — which does still
ship a free tier the product page states is "free forever" for local/live
visualization, separate from its paid Data Platform/cloud features. The
bridge migration was confirmed via direct fetch of the
`foxglove/ros-foxglove-bridge` and `foxglove/foxglove-sdk` GitHub repos this
session; the free-tier claim was confirmed via direct fetch of
`foxglove.dev`'s pricing page, while the Studio-to-2.x licensing history was
reconstructed via search-synthesis after the source blog post 404'd on
direct fetch (see References) — re-verify before repeating either claim,
since licensing terms are exactly the kind of thing that drifts.

## When to use this skill

- Setting up `foxglove_bridge` on a robot or sim host, building a layout,
  recording or replaying an MCAP file, or viewing a robot's data from a
  machine that isn't the robot itself.
- The trigger phrases in the description: 'foxglove', 'mcap', visualizing a
  robot running on a remote server, sharing visualization with others,
  recording sessions for later analysis.
- Any time `environments` or `gazebo` has already concluded the target is
  headless/remote and the next question is "how do I actually see it" —
  this skill is that answer.
- Cross-references — go to the sibling skill instead when the question is:
  - Whether headless/remote is the deployment target at all, GPU
    passthrough, or the general local-vs-remote strategy → `environments`
    (load first if not already decided; this skill assumes that decision is
    made and just delivers the viz half of it).
  - Local desktop ROS debugging with a display attached → `rviz2`.
  - ML/data-centric logging outside ROS message types (policy rollouts,
    LeRobot episodes) → `rerun` — though LeRobot dataset episodes can also
    be served straight to the Foxglove app via `lerobot-dataset-viz
    --display-mode foxglove` (invocation is the `lerobot` skill's
    territory; verified 2026-07-12, manip-trial).
  - Choosing which viz tool fits the situation at all → `visualization`
    (routes here once Foxglove is the right choice).

## Key directives

- **Delegation posture: embed + links.** The core mechanics this skill
  exists for — bridging a robot, recording MCAP, connecting the app
  remotely — are embedded here because that's the whole reason
  `environments` and `gazebo` point at this skill by name; anything beyond
  that (panel-by-panel layout editing, the full MCAP CLI, Data Platform
  cloud features) is a link out to Foxglove's own docs, not re-typed here.
- **The bridge runs on the robot/server; the app runs wherever the viewer
  is.** These are two different machines in the remote case, and mixing them
  up is the most common setup mistake — `foxglove_bridge` is a ROS 2 node
  that must be launched *on* the robot or sim host (it needs access to the
  ROS graph), while the Foxglove app connects to it *from* wherever a human
  is looking, local or remote. See Quick start and Usage patterns.
- **Never re-teach the local-vs-remote/headless decision itself.** That
  decision — and the general "don't default to X11 forwarding" guidance —
  belongs to `environments`; this skill starts from "remote/headless is
  already the answer" and only covers the Foxglove-specific mechanics of
  acting on it.
- **Don't expose the bridge's WebSocket port to the open internet.**
  `foxglove_bridge` has no built-in authentication — reach it over a VPN,
  SSH tunnel, or private network, the same way any other unauthenticated
  service on a robot would be secured, not by opening the port publicly.
  See Platform gotchas.
- **Never write foxglove_bridge's supported-distro list or the app's
  licensing/pricing terms from memory.** Both have changed — the bridge's
  home repo moved, and the app went from open-source to a closed-source
  product with a free tier — verify against `index.ros.org`'s
  `foxglove_bridge` package page and `foxglove.dev`'s own site before
  repeating either claim in a real project.

## Quick start

**1. Install and launch the bridge on the robot/sim host** (verified via
`index.ros.org`'s `foxglove_bridge` package page on 2026-07-10: v3.4.2, MIT
license, released for Humble, Jazzy, Kilted, **Lyrical**, and Rolling — no
distro gap the way Nav2 has):

```bash
sudo apt install ros-$ROS_DISTRO-foxglove-bridge
ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

This starts a WebSocket server on port `8765` (default) that auto-discovers
and exposes every topic currently on the ROS graph.

**2. Connect the Foxglove app.** Open the desktop app or
`app.foxglove.dev` in a browser, and add a connection:
`ws://localhost:8765` if the app runs on the same machine as the bridge, or
`ws://<ROBOT_IP>:8765` over a VPN/tunnel for a remote view (see Platform
gotchas — don't expose this port directly to the internet).

**3. Save a layout** once panels are arranged the way a given task needs
(3D view + a couple of plots + raw topic panels is a common start), so the
next session reopens the same view instead of rebuilding it.

## Usage patterns

**Bridge a live robot.** Launch `foxglove_bridge` on the robot/server as in
Quick start, then connect from the app. All ROS 2 topics are exposed
automatically — no per-topic bridge configuration needed for the common
case; the bridge's own parameters (address, port, topic allow/deny lists)
are set as ROS 2 launch arguments if the defaults need narrowing (e.g.
excluding a high-bandwidth topic from remote viewing).

**Record MCAP.** MCAP is ROS 2's default bag storage format as of recent
distros, so the standard `ros2 bag record` path already writes it:

```bash
ros2 bag record -a -s mcap -o my_session
```

(`-a` records all topics; scope to specific topic names instead for a
large graph.) The resulting `.mcap` file opens directly in the Foxglove
app — drag it onto the window, or `File > Open Local File` — for offline
playback and scrubbing, no bridge or live robot needed. This is the
recording path the `visualization` umbrella's live-vs-recorded directive
points at for ROS 2 data.

**Drive Nav2 from the app (publish goals).** The 3D panel's Publish tool
can send `PoseStamped` goals straight into a running Nav2 stack, but its
Pose-topic default is the ROS 1-era `/move_base_simple/goal` — clicking a
goal publishes into the void with no error (Nav2 subscribes `/goal_pose`).
In the 3D panel settings → Publish, set Pose topic to `/goal_pose`; the
Pose-estimate default `/initialpose` is already right for AMCL. Verified
end-to-end 2026-07-11 (nav-trial: click-to-navigate against Jazzy Nav2
through foxglove_bridge). Note topics only stream when some panel displays
them — a topic missing from the 3D view usually just isn't toggled visible
in the panel's Topics list (latched topics like `/map` arrive on subscribe;
transient-local durability is handled by the bridge).

**Ship a preconfigured layout with the app.** Layouts export/import as
JSON files (Layout menu → Export/Import from file), so an app repo can
commit one that pre-sets the display frame, topic visibility, and the
Publish-tool topics — one import and the robot is drivable by click,
account-persistent thereafter. Verified 2026-07-11 (nav-trial:
`apps/nav-trial/foxglove/nav-trial-layout.json` in robium-applications is a
working sample, incl. `publish: {poseTopic: "/goal_pose"}`).

**Teleop-drive and fire actions from the app.** The Teleop panel publishes
`geometry_msgs/Twist` to `/cmd_vel` — hold-to-drive a real base straight from
the browser, no ROS on the client; set conservative per-button linear/angular
values (the panel default is unbounded). Foxglove can publish topics and call
services but CANNOT call ROS 2 **actions**, so dock/undock and any other
action-only command need a tiny robot-side helper node that subscribes to a
trigger topic (`std_msgs/Empty`) and forwards the goal to the action — a
Publish panel then becomes the button. Verified 2026-07-24 (tb4-teleop: a real
TurtleBot 4 driven + docked/undocked from the browser via a `teleop_actions.py`
helper and Publish-panel buttons; layout at
`apps/tb4-teleop/foxglove/tb4-teleop-layout.json`).

**Share a view via a launcher deep-link.** For a free, no-self-hosting way to
hand someone a preconfigured connection, use a launcher deep-link rather than a
self-hosted viewer (which now needs a paid plan — see Customization):
`https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://<host>:<port>&layoutId=<uuid>`
opens the web app already pointed at the bridge — but `layoutId` must reference a
layout already imported into the org (there is no arbitrary-layout-by-URL
parameter). The secure https origin may refuse the insecure `ws://` connection
(same mixed-content class as the Safari gotcha below); the desktop form
`foxglove://open?ds=...` sidesteps that block but fails silently if the desktop
app isn't installed. Verified 2026-07-24 (tb4-teleop).

**Publish from a hand-rolled WS client (no Foxglove app).** The bridge's
client-publish path can be driven directly from a custom WebSocket client —
useful for a scripted teleop or a CI smoke check with no viewer. Connect with
subprotocol `foxglove.sdk.v1` (see Platform gotchas), send a JSON `advertise`,
then push binary client-message frames `[0x01][channelId little-endian][CDR
payload]` (e.g. a 52-byte `geometry_msgs/Twist`, a 4-byte `std_msgs/Empty`).
Verified 2026-07-25 (tb4-teleop: against a live `foxglove_bridge` 3.4.2 at
`ws://<robot>:8765` on real hardware — serverInfo received, channels advertised,
client-publish works).

**View remotely in the web app.** Point `app.foxglove.dev` (no desktop
install needed) at `ws://<ROBOT_IP>:8765` over a VPN/SSH tunnel/tailnet —
this is the answer `environments`' headless-first guidance and `gazebo`'s
headless-operation section both defer to: a teammate or a CI dashboard can
watch a robot or sim running on a server with no display attached, using
only a browser. The same connection works for a temporary SSH port-forward
(`ssh -L 8765:localhost:8765 robot-host`) if a persistent VPN isn't set up
for a one-off debugging session.

## Platform gotchas

- **No built-in auth on the bridge's WebSocket.** Treat `8765` like any
  other unauthenticated robot service — reachable only over a VPN, SSH
  tunnel, or private network, never bound to a public interface.
- **The desktop app and the web app (`app.foxglove.dev`) are the same
  product, different delivery** — either works for the same
  live-bridge-or-MCAP-file workflow; the web app needs nothing installed
  and is the lower-friction choice for a teammate who just needs to look
  once.
- **The bridge itself is open source (MIT); the app is not.** Don't assume
  Foxglove's viewer code is inspectable/forkable the way it was under the
  old "Foxglove Studio" — that ended February 2024. The bridge running on
  the robot is unaffected by this; only the client app's license changed.
- **Safari can't open `ws://localhost` from the https web app.** The
  mixed-content block yields a generic "check that the WebSocket server is
  reachable" even when the bridge is healthy — use Chrome (which exempts
  localhost), the desktop app, or Lichtblick. Verified 2026-07-11
  (nav-trial).
- **`foxglove_bridge` ≥3.x speaks the subprotocol `foxglove.sdk.v1`, not
  `foxglove.websocket.v1`.** The 3.x line (e.g. `ros-jazzy-foxglove-bridge`
  3.4.1) is built on the Foxglove SDK and rejects the classic subprotocol
  with `HTTP 400 "Missing expected sec-websocket-protocol header"` — a
  misleading message, since the header *is* present, just not with the
  value it wants. The viewer apps negotiate this for you; anything
  hand-rolled (a health probe, a CI smoke check, a custom client) must send
  the new value. Confirm what a given build expects by grepping the shared
  object for the literal: `strings $(ros2 pkg prefix
  foxglove_bridge)/lib/libfoxglove.so | grep foxglove\.` — that's how this
  was pinned down (2026-07-12, nav-trial demo, after ruling out curl header
  formatting with a raw-socket handshake).
- **"Bridge unreachable" usually isn't the bridge.** Before debugging
  foxglove_bridge, check the container runtime/host is actually up (a
  stopped Docker Desktop presents as a closed socket in the app) and that
  the port is reachable (`nc -z <host> 8765`) — the bridge has no failure
  mode that looks like a silently closed listener while its process runs.
- **A high topic/message rate can saturate a remote link.** Over a slow or
  high-latency connection (a robot on cellular, a distant VPN hop), narrow
  the bridge to the topics actually needed for the session (bridge launch
  arguments, or a scoped `ros2 bag record` topic list) rather than
  streaming the full graph and fighting lag in the viewer.
- **Restarting the bridge over SSH: kill it by port, not by name.** A
  `pkill -f foxglove_bridge` in the same command that runs
  `ros2 launch foxglove_bridge …` self-matches the launch shell's own command
  line and kills the SSH session (it exits 255, the bridge never starts). Free
  the port instead: `fuser -k 8765/tcp`. Verified 2026-07-24 (tb4-teleop
  `start_bridge.sh`).
- **Persist the robot-side teleop stack as services, or a reboot silently kills
  it.** `foxglove_bridge` AND the action-helper node (the dock/undock forwarder
  above) together are the entire browser-teleop path on the robot — launched by
  hand or a one-shot `start_bridge.sh`, a robot reboot leaves the console
  connecting to nothing with no error surfaced: the base is healthy, the page
  just does nothing. Install each as a `systemd` unit that sources the robot's
  own env and sets `Restart=always`; on a TurtleBot 4:
  `ExecStart=/bin/bash -c 'source /etc/turtlebot4/setup.bash && exec ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765'`
  with `After=turtlebot4.service`, then `systemctl enable --now` — and the same
  for the helper (`… && exec python3 …/teleop_actions.py`). Verified 2026-07-26
  (tb4-teleop: both died on a Pi reboot — bridge, then dock/undock, seen 2× —
  fixed by twin units; is-active/is-enabled + `/teleop/dock` subscription 1).

## Customization

- **Different topic scope per session:** override `foxglove_bridge`'s
  launch arguments (e.g. an allow-list) when a remote link can't carry the
  full graph, rather than always bridging everything and filtering in the
  app — filtering upstream saves bandwidth, filtering in the app only saves
  screen space.
- **Self-hosted vs. `app.foxglove.dev`:** the web app is a hosted client
  pointed at whatever WebSocket URL is given to it — no project files here
  assume the hosted URL specifically. The self-hosting story changed: the old
  open-source foxglove/studio Docker image is gone, and the current self-host
  path is the @foxglove/embed FoxgloveViewer dropped into your own page — but
  that self-hosted viewer asset requires a **paid** Foxglove plan
  (user-confirmed, tb4-teleop 2026-07-24; verified via
  docs.foxglove.dev/docs/embed/self-hosted, fetched 2026-07-24). For a free
  self-directed path, prefer launcher deep-links (see Usage patterns) over a
  self-hosted viewer. Either way the connection mechanics (`ws://` URL, VPN/
  tunnel) are unchanged.
- **Layouts per task:** keep a saved layout per debugging task (nav
  debugging vs. sensor calibration vs. a demo view) the same way `rviz2`
  keeps a config per task, rather than one layout trying to cover every
  use case.

## References

- Upstream: [Foxglove documentation](https://docs.foxglove.dev/docs)
  (primary source for app/bridge usage), [foxglove_bridge package page,
  index.ros.org](https://index.ros.org/p/foxglove_bridge/) (fetched
  directly on 2026-07-10 — source of the distro-coverage and
  version/license facts above; re-check before a new install), [foxglove/
  foxglove-sdk](https://github.com/foxglove/foxglove-sdk) (current home of
  bridge development; fetched directly on 2026-07-10), [foxglove/
  ros-foxglove-bridge](https://github.com/foxglove/ros-foxglove-bridge)
  (older repo, now ROS 1-only/maintenance — fetched directly on 2026-07-10,
  confirms the move), [Foxglove pricing
  page](https://foxglove.dev/pricing) and ["Foxglove vs. Foxglove Studio:
  Two Years On"](https://foxglove.dev/blog/foxglove-vs-foxglove-studio-two-years-on)
  (source of the open-source-to-closed-source history above — the pricing
  page was fetched directly on 2026-07-10; the Studio-transition history was
  confirmed via search-synthesis of Foxglove's own blog posts and should be
  re-verified by reading that post directly before repeating the exact
  dates in a real project), [MCAP format](https://mcap.dev/) (fetched
  directly on 2026-07-10). Sibling skills: `environments` (headless/remote
  decision this skill assumes is already made), `rviz2` (local desktop
  debugging), `rerun` (ML/data-centric logging), `visualization` (umbrella,
  routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.5.0 (2026-07-31): tb4-teleop absorption — self-hosting story corrected (the
  old open-source foxglove/studio Docker image is gone; current self-host = the
  @foxglove/embed FoxgloveViewer, which requires a paid plan — prefer free
  launcher deep-links); new usage patterns for app.foxglove.dev /
  `foxglove://` deep-links (layoutId must already be in the org; https origin may
  block insecure ws://) and for publishing from a hand-rolled `foxglove.sdk.v1`
  WS client (binary `[0x01][channelId][CDR]` frames, verified against
  foxglove_bridge 3.4.2 on real hardware).

- 1.4.0 (2026-07-26): tb4-teleop absorption — gotcha: persist the robot-side
  teleop stack (foxglove_bridge + the dock/undock action-helper) as systemd
  units with Restart=always; hand-launched, both silently die on a robot reboot
  and teleop fails with no error (hit both components in one session — bridge,
  then dock/undock).

- 1.3.0 (2026-07-24): tb4-teleop absorption — usage pattern for
  teleop-driving a real base from the Teleop panel and firing action-only
  commands (dock/undock) via a helper node + Publish-panel buttons (Foxglove
  can't call ROS 2 actions); gotcha: restart the bridge over SSH by killing
  the port (`fuser -k`), not `pkill -f foxglove_bridge` (self-kills the launch
  shell, SSH 255). (3.4.2 re-confirmed the existing `foxglove.sdk.v1` gotcha.)

- 1.2.0 (2026-07-13): nav-trial demo absorption — gotcha: foxglove_bridge
  >=3.x (SDK-based) requires the `foxglove.sdk.v1` WebSocket subprotocol
  and rejects the classic `foxglove.websocket.v1` with a misleading HTTP
  400; added the `libfoxglove.so` grep that identifies the expected value.
  Bites every hand-rolled client and health probe.

- 1.1.2 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.

- 1.1.1 (2026-07-12): manip-trial absorption — rerun cross-ref notes the
  LeRobot bridge (`lerobot-dataset-viz --display-mode foxglove` serves
  episodes to the Foxglove app directly).
- 1.1.0 (2026-07-11): nav-trial absorption — new usage patterns: publishing
  Nav2 goals from the app (ROS1-default `/move_base_simple/goal` →
  `/goal_pose` fix) and committing a layout JSON per app repo; gotchas:
  Safari ws://localhost mixed-content block, "unreachable ≠ broken, check
  the container runtime". Quick-start bridge flow confirmed ✓ under real
  load (browser + headless arm64 container).
