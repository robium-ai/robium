# indoor-navigation two-flavor demo — design

**Date:** 2026-08-03 · **Status:** approved (brainstorming session)
**Surfaces:** robium-internal-apps (`indoor-navigation/`, new `indoor-navigation-workspace/`) + robium-website (demo page, self-hosted Lichtblick, orchestrator config)

## Purpose

Replace the IDE-workspace demo experience with two complementary flavors of
the same navigation demo:

1. **Try it live (browser):** a Docker container on our servers, presented
   through Foxglove directly — an embedded, self-hosted Lichtblick viewer on
   the robium.ai demo page, auto-connected, zero login, zero layout import.
2. **Run it locally:** the visitor clones the app and runs the *same*
   container on their own machine, viewing it with Foxglove/Lichtblick
   pointed at `ws://localhost:8765`.

The point is "show what they can achieve": the artifact driving the live
demo is byte-identical to the artifact they download.

## Decisions (from brainstorming)

1. **Live viewer: embedded self-hosted Lichtblick** (open-source Foxglove
   fork, same WebSocket protocol) on the demo page. Rejected: deep link to
   app.foxglove.dev (login wall + manual layout import — v1's accepted
   friction, no longer acceptable).
2. **Local viz: Foxglove/Lichtblick against localhost, not RViz.** RViz
   options (X11 passthrough, noVNC) rejected — cross-platform friction
   (XQuartz flakiness, extra container weight) for no experience gain.
3. **One container, two front doors.** The `demo` compose profile
   (demo.launch.py + slim gateway) is the canonical artifact both flavors
   run, unchanged between them. Local = `make demo` + browser; live = the
   orchestrator spawning the same image on our server.
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
   status UX, graceful shutdown — re-derives encoded battle scars).

## Architecture

```
robium.ai/demos/nav-trial (rebuilt page, two paths)
├── "Try it live"
│     Start → orchestrator createInstance('nav-trial', session)
│           → poll GET /status?session= (boot log ring, RTF, countdown)
│           → ready: embed /lichtblick/ iframe,
│             ?ds=foxglove-websocket&ds.url=wss://<instance-host>?session=…
│             (nav layout preloaded; goals clicked via /goal_pose)
│     Stop / beforeunload beacon → orchestrator deleteInstance
└── "Run it locally"
      git clone … && cd indoor-navigation && make demo
      → same container on the visitor's Docker
      → connect Foxglove/Lichtblick to ws://localhost:8765

Container (identical in both flavors):
  demo.launch.py — foxglove_bridge (:8766) first, gz sim headless,
  Nav2 on saved map + AMCL, demo_init (auto /initialpose, RTF measure,
  status file, boot-race watchdog), demo_gateway.py on :8765
  (WS tunnel + start/status/shutdown/logs only)
```

The orchestrator stays lifecycle-only and out of the data path (existing
design fact, unchanged).

## Changes — robium-internal-apps

1. **`indoor-navigation-workspace/` (new):** verbatim copy of today's
   `indoor-navigation/`, then registry quick-index row + card ("IDE-workspace
   flavor — file tree, editor, PTY terminal; runnable/deployable, not routed").
   Done bar: its `make demo-smoke` passes post-copy.
2. **`indoor-navigation/` slimmed:**
   - `scripts/demo_gateway.py`: delete `pty_bridge`, `/pty`, `/fs/*`,
     `safe_path`, `WORKSPACE_ROOT`. Keep tunnel/claim semantics, `/start`,
     `/status`, `/shutdown`, `/logs`, CORS, fleet stub. (~130 lines removed.)
   - `Makefile demo-smoke`: drop PTY probe + fs steps; keep WS handshake,
     claim, budget, ready, intruder 409/403, nav goal via send_goals,
     shutdown, teardown.
   - `tests/pty_probe.py`: moves with the workspace app; deleted here.
   - README: "Run it locally" quickstart becomes the headline — prereqs
     Docker + Chrome, `make build && make demo`, connect to
     `ws://localhost:8765`, import layout, click goals. Framed as the same
     container the live demo runs. Written as the future public README.
   - Registry card updated (two-flavor story, workspace sibling noted).
   - Unchanged: Dockerfile, compose, all launch files, params, map,
     `make smoke`, cloudbuild.
3. **Learnings** captured throughout to `learnings/2026-08-03-indoor-navigation.md`
   (robium repo), per the two-hats rule.

## Changes — robium-website

1. **Self-hosted Lichtblick:** web build served as static assets (e.g.
   `/lichtblick/` path or equivalent). **De-risk task #1:** verify the
   current Lichtblick web build accepts a data-source URL (and ideally a
   layout) via URL parameters (upstream Foxglove supported
   `?ds=foxglove-websocket&ds.url=…`; Lichtblick is its fork — NOT yet
   verified against current Lichtblick docs/source). Fallback presentation
   if iframe embedding fights us (CSP/service-worker): "open viewer in new
   tab" with the same auto-connect URL.
2. **`/demos/nav-trial` page rebuilt:** drops the Workspace IDE component;
   two paths as in Architecture. Boot phase shows the gateway's log ring +
   RTF + session countdown; ready phase swaps in the viewer. Stop button +
   beacon cleanup as today.
3. **Orchestrator:** logic untouched. `demo-orchestrator/src/demos/nav-trial.json`
   updated to the post-rename names (image `indoor-navigation:latest`,
   package `indoor_nav_bringup`) — fixes a live stale reference.
4. **Workspace components** (`Workspace.tsx`, FileTree, Editor, Terminal,
   WorkTabs) remain — manip/vla demo pages still use them. Only the
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
- Local flavor README troubleshooting: Safari blocks `ws://localhost` from
  https origins (use Chrome), port 8765 collisions, cold `make build` time.

## Testing

- **Apps:** `make smoke` unchanged (app pass bar). Slimmed `make demo-smoke`
  (demo bar): removed surfaces must be *gone* (assert `/fs/list` and `/pty`
  return 404/close, not 200). Workspace sibling: full original
  `make demo-smoke` passes there.
- **Website:** site smoke extended — Lichtblick assets served, demo page
  contains both paths and the viewer URL shape; orchestrator unit tests +
  `e2e.sh` pass with the updated demo config.
- **Local-flavor honesty check:** execute the README quickstart from a
  clean clone exactly as written, on the Mac host, before calling it done.

## Out of scope (deferred)

- Promotion to public robium-apps (explicit follow-up once this lands).
- Prebuilt public image handout (`docker run` no-clone path) — promotion-time
  decision.
- manip/vla demo pages migrating off the Workspace IDE — separate efforts.
- Cloud Run vs orchestrator hosting changes; egress verification (#6 in
  robium-website's tracker) — unchanged by this work, though shelving the
  workspace route removes the exposed PTY from prod.

## Open risks

1. **Lichtblick URL-parameter surface unverified** (de-risk task #1 above).
2. **Iframe embedding constraints** (Lichtblick service worker, COOP/COEP or
   CSP requirements) — fallback is new-tab presentation.
3. **Layout preload mechanics** — if no URL/layout-injection path exists,
   fallback is a committed default layout baked into the self-hosted build,
   or a one-click "import layout" step (strictly better than today's flow
   either way).
