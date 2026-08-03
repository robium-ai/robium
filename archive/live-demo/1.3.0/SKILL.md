---
name: live-demo
version: 1.3.0
description: >
  Turn a working robium app into a public, interactive web demo: a
  mission-control demo page (start/stop instance buttons, live boot
  terminal, fleet budget), per-visitor simulator instances on Cloud Run
  (scale-to-zero), and a visualizer handoff (Foxglove deep link or
  self-hosted viewer). Use when: 'live demo', 'demo page', 'let visitors
  drive the robot', 'try it live on the website', 'demo instance
  start/stop', 'host the sim for the demo', choosing the demo visualizer,
  or budgeting/deploying demo backends. Load after an app passes its smoke
  test (testing) — a demo hosts a finished app. Pairs with foxglove
  (bridge/viewer mechanics) and integration (container patterns). Not for:
  developer-facing visualization during a build (foxglove/rviz2) or
  general website building.
---

# live-demo

Everything between "the app's smoke test is green" and "a stranger on the
website is driving the robot." This skill owns the demo architecture that
robium.ai/demos/nav-trial runs in production: a control page whose
Start/Stop buttons manage private, per-visitor simulator instances on
Cloud Run, a session gateway inside the app container, and a viewer
handoff. Every command, flag, and gotcha here was verified live
(2026-07-13, nav-trial demo) — this is a distillation of a real deployment,
not a design sketch.

## When to use this skill

- Publishing any robium app as an interactive web demo, and every design
  choice inside that: flow shape, page anatomy, instance lifecycle,
  visualizer, budget, and the Cloud Run deployment.
- Debugging a deployed demo (instance won't boot, viewer can't connect,
  status endpoint misroutes).
- Cross-references — go to the sibling skill instead when the question is:
  - The Cloud Run deploy mechanics themselves — the build → Artifact Registry
    → `gcloud run deploy` path, the sim flag set, billing modes, the gz/DDS
    transport env vars, session affinity, VPC subnet sizing, deploy auth →
    `cloud-run` (this skill owns the *orchestrator, gateway, and page*; the
    deploy target under them is `cloud-run`'s).
  - foxglove_bridge setup, layouts, or MCAP for *development* use →
    `foxglove` (this skill consumes its bridge; the demo-specific parts —
    session gateway, deep-link handoff — live here).
  - Container/compose patterns for the app itself → `integration`.
  - Whether the app is *done* enough to demo → `testing` (smoke test
    green is this skill's entry bar).
  - Env reproducibility of the app → `environments`.

## Key directives

- **Delegation posture: embed.** The demo architecture (gateway contract,
  Cloud Run tuning for sims, viewer decision table) exists nowhere
  upstream in one place — it was derived by deployment. Bridge mechanics
  are `foxglove`'s; everything demo-shaped is embedded here.
- **A demo is a product surface: the smoke test extends to it.** The app's
  demo scenario gets its own gated smoke (`make demo-smoke`): WebSocket
  handshake through the gateway, `/start` claim, `/status` reaches
  `ready`, intruder session rejected (409/403), one scripted goal
  succeeds, `/shutdown` kills the container. Ship no demo without it.
- **Scale-to-zero is non-negotiable; per-session cost is explicit.**
  `min-instances=0` always. State the per-session cost implication of the
  billing mode you pick (see `references/cloud-run-tuning.md`) — never let
  an "idle" demo bill silently.
- **One visitor, one instance, enforced in the gateway.** The session
  UUID claims an instance; a live tunnel is never shareable; an idle claim
  is takeable (reload semantics). Never rely on Cloud Run routing alone
  for isolation.
- **Lifecycle belongs to something that outlives the instance.** The
  in-container gateway cannot start or restart itself (it dies with the
  container), and a browser cannot start a container — so a real Start
  button needs a host-level **orchestrator**. On Cloud Run the control
  plane *is* that orchestrator, which is why this only becomes visible the
  day you run the demo locally. Build it behind a `Driver` interface
  (LocalDocker now, CloudRun later) rather than special-casing localhost,
  keep it out of the data path (it hands the browser a per-instance host
  and gets out of the way), and give it the fleet cap. See
  `references/orchestrator-pattern.md`.
- **Be honest on the page.** Cold-boot time (30–90 s, with self-restart
  on unlucky boots), session caps, and busy states are stated in the
  demo page's terminal — a demo that pretends to be instant reads as
  broken the moment it isn't.

## Quick start

The proven path (mission-control flow, Foxglove deep-link viewer):

1. **App side** — add a `demo` scenario to the app: one launch = sim +
   nav/policy stack + `foxglove_bridge` on an internal port + an
   auto-init node (set initial pose / whatever makes the app immediately
   drivable) + the session gateway owning `$PORT`. Copy
   `examples/demo_gateway.py` (verified) and adapt the two constants.
2. **Deploy** — Cloud Build the image, then (values verified for a
   Gazebo+Nav2 stack):
   ```bash
   gcloud run deploy demo-<app> --image=<image> \
     --region=us-central1 --port=8765 \
     --concurrency=4 --session-affinity \
     --min-instances=0 --max-instances=5 --timeout=1800 \
     --cpu=8 --memory=8Gi --cpu-boost --no-cpu-throttling \
     --execution-environment=gen2 \
     --set-env-vars=GZ_RELAY=127.0.0.1,GZ_IP=127.0.0.1,FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
     --command=/entrypoint.sh --args="ros2,launch,<pkg>,demo.launch.py" \
     --allow-unauthenticated --quiet
   ```
   Map a **same-site subdomain** (e.g. demo.yourdomain.org) — required
   for the affinity cookie to work from your site's pages (see gotchas).
3. **Site side** — a `/demos/<app>` page with the mission-control
   anatomy (see `references/demo-page.md`): Start/Stop buttons, terminal
   majority, fleet budget line, viewer button gated on `ready`.
4. **Gate it** — demo smoke locally, then the same probes against the
   live URL; only then link it from the homepage proof/apps card
   ("Try the live demo →").

## Usage patterns

**Choose the demo flow.** Three shapes, in order of proven-ness:

| Flow | What the visitor gets | When |
| --- | --- | --- |
| **Mission-control page** (proven) | Start/Stop instance buttons, live boot terminal, fleet count, viewer opens on ready | Default. Honest about boot time; visitors see the machinery (which *is* the pitch for infra products). |
| Deep-link only | One "open in Foxglove" link; connection cold-boots the instance | Minimal page work; boot happens behind the viewer's "connecting" spinner; needs the connection itself to hold CPU (request-based billing). |
| Embedded viewer (self-hosted) | Viewer iframe in the page, no login | Best UX on paper; costs a self-hosted viewer build and iframe/browser-storage complexity. Deferred by robium.ai after trying it — revisit deliberately. |

**Choose the visualizer** (verified facts, 2026-07-13):

| Option | Login | Layout preload | Embeddable | Verdict |
| --- | --- | --- | --- | --- |
| app.foxglove.dev deep link (`/~/view?ds=foxglove-websocket&ds.url=<wss>`) | Required | ✗ (visitor imports the layout file once — link it on the page) | ✗ (`x-frame-options: DENY`) | Default: zero hosting, robotics users have accounts |
| Self-hosted Lichtblick (open-source Foxglove fork, MPL) | None | ✓ (`globalThis.LICHTBLICK_SUITE_DEFAULT_LAYOUT` build hook) | ✓ (you control headers) | Frictionless but you own the build + browser-storage kiosk-wipe; new-tab use is solid, iframe needs care |
| Foxglove embed SDK (embed.foxglove.dev) | Org members only | ✓ | ✓ | Paid tier + viewers must belong to your Foxglove org — internal portals, not public demos |

**Instance lifecycle contract** (the gateway, `examples/demo_gateway.py`):
`POST /start?session=U` claims · `GET /status?session=U` → JSON
(`claimed/ready/rtf/nodes/uptime_s/remaining_s/fleet{running,budget}/log[]`),
409 for foreign sessions · ws upgrade tunnels to the bridge, one live
tunnel max (second → 503) · `POST /shutdown?session=U` → SIGINT PID 1 →
container exits · idle claims takeable · page sends a `pagehide`
sendBeacon shutdown. Full rationale in `references/gateway-pattern.md`.

**Show the demo where the proof lives.** The homepage apps/proof card for
the app gets a primary "Try the live demo →" button to `/demos/<app>`;
the demo page carries the reproduction story (the brief that produced the
app) so the demo sells the plugin, not just the robot.

**Fleet/budget display.** Budget = `--max-instances`, stated statically
on the page. Live count comes from Cloud Monitoring's
`run.googleapis.com/container/instance_count` queried *by the gateway*
(metadata-server token + `roles/monitoring.viewer` on the runtime service
account), folded into `/status` and cached ~30 s. Never fetch fleet
status on page load — that request cold-boots a billable instance per
drive-by visitor; show it only while a session runs.

## Platform gotchas

All verified in production, 2026-07-13 (details + fixes in
`references/cloud-run-tuning.md`), except a bullet dated otherwise:

- **Gazebo discovery needs help on Cloud Run** (no multicast):
  `GZ_RELAY=127.0.0.1` + `GZ_IP=127.0.0.1`, and even then the unicast
  relay loses a *sticky per-boot race* ~half the time — ship a **boot
  watchdog** (no sim data within ~120 s → SIGINT PID 1 → fresh instance
  on the client's reconnect).
- **`Connection: close` on every hand-rolled HTTP response** — Cloud
  Run's proxy pools keep-alive connections; closing without declaring it
  = edge 503 "malformed response" (invisible in local testing).
- **SIGINT, not SIGTERM, stops `ros2 launch` as PID 1** — the kernel
  drops unhandled signals to PID 1 and launch installs no SIGTERM
  handler.
- **Session affinity cookies are SameSite-Lax** — they never flow to a
  `*.run.app` host from your site (cross-site). Map a subdomain of the
  site's domain to the service and use `credentials:'include'` +
  exact-origin CORS, or affinity silently does nothing.
- **Request-based billing throttles CPU between requests** — a sim boot
  with no held connection freezes. Start-button flows need
  `--no-cpu-throttling` (cost: idle-retention after sessions,
  ≈$0.20–0.40/session at 8 vCPU); connection-driven flows can stay
  request-based since the ws holds CPU.
- **FastDDS shared memory misbehaves in Cloud Run** —
  `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` silences `open_and_lock_file` errors.
- **Concurrent instances must not share a `ROS_DOMAIN_ID`** — the project's
  pinned constant merges every instance's ROS graph the moment two run at
  once (two Gazebo `/clock` publishers → `Moved backwards in time,
  re-publishing joint transforms!` forever). The orchestrator assigns the
  lowest free ID (1–200) per instance.
- **WebSocket probes need `curl --http1.1`** against https Cloud Run
  (h2 negotiation breaks the upgrade), and `foxglove_bridge ≥3.x` expects
  subprotocol `foxglove.sdk.v1` (the classic `foxglove.websocket.v1`
  gets a misleading 400).
- **A single local instance has nowhere to reroute a 503 — needs takeable
  claims + abortable runs** (2026-07-15, user-corrected). On Cloud Run a
  503 reroutes to a fresh instance, so "second viewer gets 503" only holds
  with a fleet; a lone local instance can't reroute. Gradio keeps running a
  generator job after its SSE client disconnects, so a page refresh orphans
  the in-flight run holding the app's run lock, and the refreshed page (new
  session UUID) then gets `/start` 503 + `/status` 409 forever. Fix for
  single-instance local demos: make runs abortable (a `threading.Event` per
  step), have `/start` always take the claim, have the page retry `/start`
  on 409, and acquire the run lock with a 30 s timeout.

## Customization

- **Different app:** the gateway and page are app-agnostic; the app-side
  work is the `demo` launch (stack + bridge + auto-init making it
  instantly drivable) and picking what "ready" means (nav: initial pose
  set + RTF measured; a policy demo might be "model loaded + env reset").
- **Different budget/size:** `--max-instances` (budget), `--cpu/--memory`
  (a Gazebo+Nav2 stack wanted 8 vCPU for RTF ≈ 1; measure with the
  `DEMO READY rtf=` log line), `--timeout` (session cap).
- **Non-ROS demos:** the gateway pattern (claim/status/shutdown +
  ws tunnel) works for any ws-speaking backend; swap the bridge for your
  stream and the status file for your readiness signal. A second proven
  backend shape is a Gradio/FastAPI-mount gateway (`gr.mount_gradio_app`
  onto a FastAPI app) — a validated non-ROS gateway shape alongside the
  ws-tunnel one (2026-07-15), worth reaching for so it isn't re-derived.
  For a CPU-only demo image, install torch from the CPU wheel index
  (`--index-url https://download.pytorch.org/whl/cpu`): the default wheel
  drags in the full multi-GB CUDA stack (nvidia-cudnn/cusolver) a CPU
  container never uses — a size issue, not correctness (seen 2x, manip-trial
  + vla-trial).

## References

- `references/gateway-pattern.md` — the session gateway: endpoint
  contract, claim semantics, tunnel guard, shutdown, watchdog.
- `references/orchestrator-pattern.md` — who starts the instance: the
  orchestrator/gateway split, the local-vs-cloud `Driver` seam,
  per-instance `ROS_DOMAIN_ID`, the in-browser PTY shell, the local dev
  loop.
- `references/cloud-run-tuning.md` — flags, billing modes and their
  costs, gz/FastDDS env fixes, same-site affinity, fleet monitoring IAM.
  The general, non-demo-specific form of these mechanics is owned by the
  `cloud-run` skill; this file keeps the demo-tuning specifics.
- `references/demo-page.md` — mission-control page anatomy, session JS
  flow, honesty copy, where demo links go on the site.
- `examples/demo_gateway.py` — the production gateway (status: verified
  2026-07-13, nav-trial live demo on robium.org).
- Upstream: [Cloud Run docs](https://cloud.google.com/run/docs),
  [Foxglove deep links](https://docs.foxglove.dev/docs/visualization/shareable-links),
  [gz-transport relay](https://gazebosim.org/api/transport/14/relay.html),
  [Lichtblick](https://github.com/lichtblick-suite/lichtblick). Sibling
  skills: `cloud-run` (the Cloud Run deploy mechanics/gotchas this demo
  target sits on), `foxglove` (bridge/viewer), `integration` (containers),
  `testing` (the entry bar), `environments` (app env).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.3.0 (2026-08-01): the Cloud Run deploy mechanics/gotchas now have their
  own `cloud-run` skill (issue #67) — added a cross-reference (When to use,
  References) delegating the build → deploy path, flag set, billing modes,
  gz/DDS transport env, affinity, and VPC sizing to it, while this skill keeps
  ownership of the orchestrator, session gateway, and mission-control page. The
  demo-specific cloud-run-tuning notes stay here as the tuned specifics.

- 1.2.0 (2026-07-31): manip-trial + vla-trial absorption — new Platform
  gotcha for single-instance local demos (a lone instance can't reroute a
  503 the way a Cloud Run fleet does; Gradio orphans a generator job after
  its SSE client disconnects, so a refresh deadlocks with /start 503 +
  /status 409 — fix with abortable runs, a takeable /start claim, 409 retry,
  and a 30 s run-lock timeout); Customization Non-ROS demos gains a second
  proven gateway shape (Gradio/FastAPI mount via gr.mount_gradio_app) and a
  CPU-wheel note (install torch from the CPU index so CPU demo images skip
  the multi-GB CUDA stack, seen 2x).

- 1.1.1 (2026-07-15): rebrand — the production demo now serves at robium.ai
  (gateway same-site at demo.robium.ai, CORS origin https://robium.ai).
  Refreshed the current-state domain references in SKILL.md,
  references/demo-page.md, and examples/demo_gateway.py. Dated 1.0.0/1.1.0
  changelog history left unchanged.

- 1.1.0 (2026-07-13): demo v4 absorption (nav-trial) — the orchestrator:
  new `references/orchestrator-pattern.md` (the gateway can't manage its
  own lifecycle and a browser can't start containers, so lifecycle needs a
  host-level orchestrator; the local-vs-cloud `Driver` seam; per-instance
  `ROS_DOMAIN_ID`; PTY-over-WebSocket in-browser shell; local dev loop),
  plus a Key directive and a gotcha pointing at it. Also: Direct VPC egress
  needs a `/24`-sized subnet for the instance pool (a `/28` fails deploy),
  and the stale-host `setInterval` trap that dynamic per-instance backends
  introduce. Public-shell security shape deliberately NOT prescribed yet —
  its egress-block verification is still pending.

- 1.0.0 (2026-07-13): created from the nav-trial live-demo deployment on
  robium.org — mission-control flow, session gateway, Cloud Run tuning,
  and visualizer decision table, all production-verified same day.
