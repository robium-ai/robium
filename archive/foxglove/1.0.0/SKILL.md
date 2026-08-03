---
name: foxglove
version: 1.0.0
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
    LeRobot episodes) → `rerun`.
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
`index.ros.org`'s `foxglove_bridge` package page this session: v3.4.2, MIT
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
- **A high topic/message rate can saturate a remote link.** Over a slow or
  high-latency connection (a robot on cellular, a distant VPN hop), narrow
  the bridge to the topics actually needed for the session (bridge launch
  arguments, or a scoped `ros2 bag record` topic list) rather than
  streaming the full graph and fighting lag in the viewer.

## Customization

- **Different topic scope per session:** override `foxglove_bridge`'s
  launch arguments (e.g. an allow-list) when a remote link can't carry the
  full graph, rather than always bridging everything and filtering in the
  app — filtering upstream saves bandwidth, filtering in the app only saves
  screen space.
- **Self-hosted vs. `app.foxglove.dev`:** the web app is a hosted client
  pointed at whatever WebSocket URL is given to it — no project files here
  assume the hosted URL specifically; swap in a self-managed deployment if
  that's the team's policy, the connection mechanics (`ws://` URL, VPN/
  tunnel) are unchanged either way.
- **Layouts per task:** keep a saved layout per debugging task (nav
  debugging vs. sensor calibration vs. a demo view) the same way `rviz2`
  keeps a config per task, rather than one layout trying to cover every
  use case.

## References

- Upstream: [Foxglove documentation](https://docs.foxglove.dev/docs)
  (primary source for app/bridge usage), [foxglove_bridge package page,
  index.ros.org](https://index.ros.org/p/foxglove_bridge/) (fetched
  directly this session — source of the distro-coverage and
  version/license facts above; re-check before a new install), [foxglove/
  foxglove-sdk](https://github.com/foxglove/foxglove-sdk) (current home of
  bridge development; fetched directly this session), [foxglove/
  ros-foxglove-bridge](https://github.com/foxglove/ros-foxglove-bridge)
  (older repo, now ROS 1-only/maintenance — fetched directly this session,
  confirms the move), [Foxglove pricing
  page](https://foxglove.dev/pricing) and ["Foxglove vs. Foxglove Studio:
  Two Years On"](https://foxglove.dev/blog/foxglove-vs-foxglove-studio-two-years-on)
  (source of the open-source-to-closed-source history above — the pricing
  page was fetched directly this session; the Studio-transition history was
  confirmed via search-synthesis of Foxglove's own blog posts and should be
  re-verified by reading that post directly before repeating the exact
  dates in a real project), [MCAP format](https://mcap.dev/) (fetched
  directly this session). Sibling skills: `environments` (headless/remote
  decision this skill assumes is already made), `rviz2` (local desktop
  debugging), `rerun` (ML/data-centric logging), `visualization` (umbrella,
  routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->
