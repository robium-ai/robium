# indoor-navigation two-flavor demo - design

**Date:** 2026-08-03 · **Status:** approved (brainstorming session)
**Surfaces:** robium-internal-apps (`indoor-navigation/`, new `indoor-navigation-workspace/`) + robium-website (demo page, self-hosted Lichtblick, orchestrator config)

## Purpose

Replace the IDE-workspace demo experience with two complementary flavors of
the same navigation demo:

1. **Try it live (browser):** a Docker container on our servers, presented
   through Foxglove directly - an embedded Lichtblick viewer, auto-connected,
   zero login, zero layout import.
2. **Run it locally:** the visitor clones the app and runs the *same*
   container on their own machine - and gets the *same* viewer: the image
   bundles the Lichtblick web build, so `http://localhost:8765` IS the demo.

The point is "show what they can achieve": the artifact driving the live
demo is byte-identical to the artifact they download, viewer included -
self-contained, no Foxglove account, no layout import, nothing to install
beyond Docker.

## Decisions (from brainstorming)

1. **Viewer: Lichtblick** (open-source Foxglove fork, same WebSocket
   protocol), **bundled in the demo image and served by the gateway** -
   both flavors get it from the container itself. Rejected: deep link to
   app.foxglove.dev (login wall + manual layout import - v1's accepted
   friction, no longer acceptable); website-hosted viewer (would make the
   local flavor depend on our site or the visitor's own Foxglove - not
   self-contained, not the same demo).
2. **Local viz: the bundled Lichtblick, not RViz.** RViz options (X11
   passthrough, noVNC) rejected - cross-platform friction (XQuartz
   flakiness, extra container weight) for no experience gain.
3. **One container, two front doors - viewer included.** The `demo`
   compose profile (demo.launch.py + slim gateway + bundled viewer) is the
   canonical artifact both flavors run, unchanged between them. Local =
   `make demo`, then open `http://localhost:8765`; live = the orchestrator
   spawns the same image and the demo page iframes the instance-served
   viewer at its host.
4. **Distribution: build in robium-internal-apps now; promote to the public
   robium-apps showcase when done.** README written promotion-ready
   (promotion = copy, not rewrite). Prebuilt-image handout deferred to
   promotion time.
5. **Archive the IDE flavor as a sibling app** `indoor-navigation-workspace/`
   with its own registry card. It stays runnable (its `make demo-smoke`
   must pass) but is **shelved: not routed on robium.ai**. Side effect:
   the public interactive shell (PTY/fs, the unverified-egress abuse
   surface) leaves prod.
6. **Keep the session gateway, slimmed** (Approach 1). The WS tunnel with
   claim/hijack-guard, `/start`, `/status` (boot log ring, RTF, countdown),
   `/shutdown`, `/logs`, CORS all stay; `/pty` and `/fs/*` are deleted.
   Rejected: bridge-direct with no gateway (loses session claim, boot
   status UX, graceful shutdown - re-derives encoded battle scars).

## Architecture

```
robium.ai/demos/nav-trial (rebuilt page, two paths)
├── "Try it live"
│     Start → orchestrator createInstance('nav-trial', session)
│           → poll GET /status?session= (boot log ring, RTF, countdown)
│           → ready: iframe https://<instance-host>/?session=…
│             (the instance serves its own viewer; it auto-connects to
│              wss://<same-host>?session=… - same origin; nav layout
│              preloaded; goals clicked via /goal_pose)
│     Stop / beforeunload beacon → orchestrator deleteInstance
└── "Run it locally"
      git clone … && cd indoor-navigation && make demo
      → same container on the visitor's Docker
      → open http://localhost:8765 - same viewer, same demo

Container (identical in both flavors):
  demo.launch.py - foxglove_bridge (:8766) first, gz sim headless,
  Nav2 on saved map + AMCL, demo_init (auto /initialpose, RTF measure,
  status file, boot-race watchdog), demo_gateway.py on :8765:
    WS upgrade        → tunnel to bridge (claim/hijack-guard)
    /start /status /shutdown /logs → session API
    any other GET     → static Lichtblick web build (baked into the image)
                        with the nav layout as its default
```

Serving the viewer from the gateway makes both flavors same-origin
(viewer page and its WebSocket share one host:port) - no CORS for the
viewer, no Safari `ws://localhost`-from-https block in the local flavor.

The orchestrator stays lifecycle-only and out of the data path (existing
design fact, unchanged).

## Changes - robium-internal-apps

1. **`indoor-navigation-workspace/` (new):** verbatim copy of today's
   `indoor-navigation/`, then registry quick-index row + card ("IDE-workspace
   flavor - file tree, editor, PTY terminal; runnable/deployable, not routed").
   Done bar: its `make demo-smoke` passes post-copy.
2. **`indoor-navigation/` slimmed + viewer-bundled:**
   - `scripts/demo_gateway.py`: delete `pty_bridge`, `/pty`, `/fs/*`,
     `safe_path`, `WORKSPACE_ROOT`. Keep tunnel/claim semantics, `/start`,
     `/status`, `/shutdown`, `/logs`, CORS, fleet stub. Add: non-API GET
     paths serve the Lichtblick static build (index.html fallback, correct
     content-types, no directory traversal outside the assets dir).
   - Dockerfile: bake the Lichtblick web build into the image (multi-stage
     node build from the Lichtblick repo, or a vendored prebuilt web
     bundle - decided at implementation after de-risk task #1), plus the
     committed nav layout as the viewer's default.
   - `Makefile demo-smoke`: drop PTY probe + fs steps; add "GET / returns
     the viewer HTML"; keep WS handshake, claim, budget, ready, intruder
     409/403, nav goal via send_goals, shutdown, teardown.
   - `tests/pty_probe.py`: moves with the workspace app; deleted here.
   - README: "Run it locally" quickstart becomes the headline - prereqs
     Docker + a browser, `make build && make demo`, open
     `http://localhost:8765`, click goals. Framed as the same container
     the live demo runs. Written as the future public README.
   - Registry card updated (two-flavor story, workspace sibling noted).
   - Unchanged: compose, all launch files, params, map, `make smoke`,
     cloudbuild.
3. **Learnings** captured throughout to `learnings/2026-08-03-indoor-navigation.md`
   (robium repo), per the two-hats rule.

## Changes - robium-website

1. **No website-hosted viewer** - the instance serves its own. The live
   page iframes `https://<instance-host>/?session=…` once `/status` says
   ready. Fallback presentation if iframe embedding fights us
   (CSP/service-worker quirks): "open viewer in new tab" with the same URL.
2. **`/demos/nav-trial` page rebuilt:** drops the Workspace IDE component;
   two paths as in Architecture. Boot phase shows the gateway's log ring +
   RTF + session countdown; ready phase swaps in the viewer iframe. Stop
   button + beacon cleanup as today.
3. **Orchestrator:** logic untouched. `demo-orchestrator/src/demos/nav-trial.json`
   updated to the post-rename names (image `indoor-navigation:latest`,
   package `indoor_nav_bringup`) - fixes a live stale reference.
4. **Workspace components** (`Workspace.tsx`, FileTree, Editor, Terminal,
   WorkTabs) remain - manip/vla demo pages still use them. Only the
   nav-trial page stops.

## Error handling (mostly inherited, verified in the existing app)

- gz-discovery boot race: in-container watchdog SIGINTs PID 1; page keeps
  polling and rides the restart.
- Busy instance: tunnel 503 → visitor's retry lands on a fresh instance;
  orchestrator budget (`maxInstances`) caps the fleet; page states limits.
- Session guards: foreign-session `/status` 409, `/shutdown` 403; claim
  takeover only when no live tunnel (reload semantics).
- 30-min reaper unchanged; countdown shown on the page.
- New: viewer connect failure after `ready` → reconnect affordance
  (Lichtblick retries its WS; page offers manual retry).
- Local flavor README troubleshooting: port 8765 collisions, cold
  `make build` time. (The old Safari `ws://localhost`-from-https issue
  disappears: viewer and WebSocket are same-origin plain http locally.)

## Testing

- **Apps:** `make smoke` unchanged (app pass bar). Slimmed `make demo-smoke`
  (demo bar): removed surfaces must be *gone* (assert `/fs/list` and `/pty`
  return 404/close, not 200) and the viewer must be *there* (GET / returns
  the Lichtblick HTML). Workspace sibling: full original `make demo-smoke`
  passes there.
- **Website:** site smoke extended - demo page contains both paths and the
  instance-viewer iframe wiring; orchestrator unit tests + `e2e.sh` pass
  with the updated demo config.
- **Local-flavor honesty check:** execute the README quickstart from a
  clean clone exactly as written, on the Mac host, before calling it done.

## Out of scope (deferred)

- Promotion to public robium-apps (explicit follow-up once this lands).
- Prebuilt public image handout (`docker run` no-clone path) - promotion-time
  decision.
- manip/vla demo pages migrating off the Workspace IDE - separate efforts.
- Cloud Run vs orchestrator hosting changes; egress verification (#6 in
  robium-website's tracker) - unchanged by this work, though shelving the
  workspace route removes the exposed PTY from prod.

## Open risks

1. **Lichtblick web-bundle acquisition (de-risk task #1).** Lichtblick's
   repo has a web target, but whether a prebuilt web bundle is published
   (vs. multi-stage `npm` build in our Dockerfile, vs. vendoring a built
   bundle) is unverified - as are its auto-connect URL parameters
   (upstream Foxglove supported `?ds=foxglove-websocket&ds.url=…`) and
   default-layout injection. Verify against current Lichtblick docs/source
   before anything else. Mitigation: we serve and control index.html, so
   connect/layout defaults can be injected at the serving layer if URL
   params fall short.
2. **Iframe embedding constraints** (service worker, COOP/COEP or CSP
   requirements) - fallback is new-tab presentation from the same URL.
3. **Image weight & build time** - a node build stage must not bloat the
   runtime image (copy only the built static assets; expected tens of MB
   on a 5.4 GB image).
