# 2026-08-03 - indoor-navigation (two-flavor demo build)

- [none] figured-out-from-scratch <!-- id: lrn-0803-01 -->
  symptom: `make demo-smoke` fails at the PTY probe with `OSError: Connect call failed ('127.0.0.1', 443)` even though the demo container is healthy on :8765.
  root-cause: tests/pty_probe.py routes bare hostnames to TLS:443 (cloud path) and only uses plaintext when the host argument carries an explicit port; the Makefile invokes it as `pty_probe.py localhost smoke`, so the local gate has been silently broken since that invocation landed. Everything before the probe (WS handshake, claim, ready, intruder guards) passes, which masks it as a "probe network flake".
  fix: invoke as `pty_probe.py localhost:8765 smoke` (check: `make demo-smoke` prints `PTY OK (egress assertion skipped - local)` and `DEMO SMOKE PASS`).
  dead-ends: not a container/port problem; curl against :8765 endpoints all green before the probe line.
  anchors: indoor-navigation-workspace/Makefile demo-smoke target; tests/pty_probe.py host.partition(':') branch.
  source: robium-apps work/indoor-navigation, archiving task of the two-flavor demo plan.

- [live-demo] figured-out-from-scratch <!-- id: lrn-0803-02 -->
  symptom: after adding a viewer redirect on bare GET /, the demo gate failed with `WS HANDSHAKE FAIL` / HTTP 302 from check_ws.sh, though the tunnel worked before.
  root-cause: WebSocket upgrade requests ARE plain GETs to /; any HTTP handler that special-cases `GET /` (redirects, static serving) must exclude `Upgrade: websocket` requests or it hijacks the tunnel handshake.
  fix: gate the redirect on `not is_upgrade` (check: `make demo-smoke` passes; check_ws.sh prints `WS HANDSHAKE OK`).
  anchors: indoor-navigation scripts/demo_gateway.py viewer front-door block.
  source: two-flavor demo build, gateway slimming task.

- [visualization] figured-out-from-scratch <!-- id: lrn-0803-03 -->
  symptom: needed a zero-login, zero-import in-browser viewer for a ROS demo container; skills cover foxglove_bridge + app.foxglove.dev (login wall) but not self-hosting a viewer.
  root-cause: no skill documents that Lichtblick (Foxglove fork, same ws protocol) is trivially embeddable: official image `ghcr.io/lichtblick-suite/lichtblick` ships the built web app at /src (caddy file-server), `index.html` contains the literal `/*LICHTBLICK_SUITE_DEFAULT_LAYOUT_PLACEHOLDER*/` token that can be replaced with a LayoutData JSON (Foxglove-exported layouts work as-is), and `?ds=foxglove-websocket&ds.url=<ws-url>` auto-connects on load (`layoutUrl` also exists but requires absolute http/https URLs). COPY --from that image with `--platform=linux/amd64` works on arm64 hosts since assets are arch-neutral.
  fix: bake the bundle + inject the layout at image build; serve it from the same host:port as the bridge/gateway so everything is same-origin (check: browser opens the viewer, auto-connects, layout shows map/scan, publish tool drives /goal_pose; all verified against a live container 2026-08-03).
  dead-ends: app.foxglove.dev deep link (account wall, layout import friction); website-hosted viewer (breaks the self-contained local flavor).
  anchors: indoor-navigation docker/Dockerfile lichtblick stage; scripts/demo_gateway.py static_file.
  source: two-flavor demo build; facts verified by direct fetch of the Lichtblick Dockerfile, appURLState.ts, FoxgloveWebSocketDataSourceFactory.ts.

- [none] worked-as-documented ✓ <!-- id: lrn-0803-04 -->
  The new local-flavor quickstart ran verbatim from a clean copy outside the
  repo: `make build && make demo`, open http://localhost:8765 (302 to the
  bundled viewer, auto-connect, ready with RTF 0.94 / 21 nodes), one goal
  `TaskResult.SUCCEEDED`, Ctrl-C/`make down` teardown. Also verified
  interactively in Chrome: default layout renders map/scan/costmap, the 3D
  pose-publish tool publishes /goal_pose and the robot drives there.

## End-of-block retro (2026-08-03, two-flavor demo build)

No robium skills loaded during this block: the session's skill list did not
include the robium plugin skills (only the robium:robium-architect agent was
registered), so fired/quiet scoring is not applicable. The block touched
territory that visualization, live-demo, environments, and testing own;
lrn-0803-02 and lrn-0803-03 capture the knowledge those skills lacked
(WS-upgrade-vs-GET-routing, self-hosted Lichtblick bundling). Worth checking
why the plugin's skills were absent from a session launched in the robium
repo before the next app block.
