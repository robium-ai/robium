---
name: live-demo
version: 2.0.0
description: >
  Add safe hosted-session runtime to a working robium app: per-visitor
  instances, a capability-protected gateway, start/status/stop lifecycle,
  boot logs, fleet budgets, Cloud Run or RunPod drivers, and a Gradio,
  Lichtblick, or Foxglove viewer handoff. Use when: 'live demo', 'start a
  private demo instance', 'demo gateway', 'all robots busy', 'host the sim',
  'Cloud Run demo', 'RunPod demo', or 'viewer will not connect'. Load after
  the app smoke test passes; pair with app-publishing for the public project
  page and article. This skill starts only after robot behavior already works.
  Not for: planning or building that behavior (architect), website/article
  composition (app-publishing), developer visualization (foxglove/rviz2), or
  generic containers (integration).
---

# live-demo

Everything between a verified app and a safe, temporary hosted session. This
skill owns the orchestrator/gateway boundary, per-visitor isolation, runtime
state machine, budget behavior, and viewer transport. Public project identity,
catalog cards, overview pages, and articles live in `app-publishing`.

The core patterns were verified on robium.ai with Cloud Run Robot Navigation
(2026-07-13 onward), local Gradio/FastAPI demos (2026-07-15 onward), and the
RunPod Pi0.5 demo lifecycle (2026-08).

## When to use this skill

- Adding hosted lifecycle to a finished robotics or physical-AI application.
- Debugging allocation, claims, readiness, reconnects, viewer handoff,
  expiration, or teardown.
- Choosing Cloud Run, RunPod, or local Docker as a per-session provider.
- Cross-references: use `app-publishing` for project pages, articles, cards,
  shared identity, and publication state; `cloud-run` for the general build and
  deploy path; `foxglove` for bridge/layout mechanics during development;
  `integration` for app containers; `testing` for the smoke-test entry bar.

## Key directives

- **Delegation posture: embed + links.** The session gateway, lifecycle split,
  and demo-specific provider tuning were derived from real deployments and
  live here. General provider and viewer mechanics delegate to `cloud-run`,
  `runpod`, `foxglove`, and upstream documentation.
- **The demo smoke extends the product surface.** <!-- id: demo-smoke-extends-product-surface --> Gate the hosted
  scenario with `make demo-smoke`: gateway claim, readiness, foreign-session
  rejection, one real scripted outcome, and teardown. A process-health probe
  alone is not a demo test.
- **One visitor, one instance, enforced by capability.** <!-- id: one-visitor-one-instance-gateway-enforced --> The
  orchestrator returns an opaque instance ID/capability. The gateway claims
  that session and rejects foreign access. Never depend on provider routing or
  an unguessable hostname as the isolation boundary.
- **Lifecycle outlives the instance.** <!-- id: lifecycle-needs-host-level-orchestrator --> A gateway inside a
  container cannot start or delete its own host. A host-level orchestrator
  owns allocation, provider selection, fleet caps, expiration, and teardown;
  after allocation, the browser talks directly to the protected gateway.
- **Scale-to-zero and cost are explicit.** <!-- id: scale-to-zero-non-negotiable-explicit-cost --> Cloud Run uses
  `min-instances=0`; GPU sessions have an absolute lifetime and daily/hourly
  budget. The UI states cold-boot time, capacity, remaining session time, and
  busy/budget states honestly.
- **No allocation before an explicit visitor action.** <!-- id: never-allocate-on-page-load --> Catalog,
  overview, and idle live pages use static facts. Start is the cost boundary.

## Quick start

1. Add one app-side demo entrypoint: simulator/policy + viewer service +
   readiness signal + the session gateway that owns `$PORT`.
2. Declare the existing `demo.orchestrator` contract in `robium-app.yaml`:
   image, command, gateway port, readiness log, provider, environment,
   resources, session duration, and fleet/budget limits. The website
   orchestrator derives its registry file from this source.
3. Implement the host-level driver behind the existing Driver seam. Local
   Docker is the cheapest lifecycle probe; use the cloud provider only for
   behavior that cannot be reproduced locally.
4. Connect the browser state machine described in
   `references/session-ui.md`: allocate, claim, poll, reconnect, render the
   viewer only when ready, and stop/delete.
5. Run the app's `make demo-smoke`, the orchestrator tests, and the local
   start-to-delete lifecycle before enabling production capacity.

For the verified ROS/WebSocket gateway shape, adapt
`examples/demo_gateway.py` (status: verified 2026-07-13). A Gradio app uses the
same lifecycle endpoints and mounts Gradio behind its capability-aware gateway.

## Usage patterns

**Choose the provider.**

| Provider | Use when | Main constraint |
| --- | --- | --- |
| Local Docker driver | Frontend/lifecycle development and CPU smoke | Not public; one host's resources |
| Cloud Run | CPU-heavy or ROS/sim containers that can boot from an immutable image | No UDP multicast; CPU/billing mode matters |
| RunPod | Large pinned GPU model and attached model volume | Paid allocation, regional GPU/volume availability, deletion certainty |

Provider-specific launch syntax belongs in the matching provider skill. Keep
the browser/orchestrator contract provider-neutral.

**Choose the viewer adapter.**

| Viewer | Runtime handoff | When |
| --- | --- | --- |
| Gradio | Capability-scoped `/ui` URL in an iframe or supported web component | Model/policy inputs and outputs |
| Self-hosted Lichtblick | Capability-scoped websocket URL + bundled layout | Public ROS visualization without login |
| Foxglove deep link | `foxglove-websocket` URL opened in a new tab | Zero viewer hosting; login acceptable |
| Custom | App-specific capability URL | The interaction cannot fit the common adapters |

The live shell is shared; only URL formation and viewer rendering belong in
the adapter. Project tabs, overview, guide, and visual identity are owned by
`app-publishing`.

**Instance lifecycle contract.** <!-- id: instance-lifecycle-gateway-contract --> The proven gateway shape is:
`POST /start?session=U` claims; `GET /status?session=U` returns
`claimed/ready/remaining_s/log[]` plus app metrics; foreign sessions return
409/403; a protected viewer/websocket route serves only the current
capability; orchestrator deletion is the authoritative stop. The gateway may
expose `/shutdown` for direct/local mode, but cloud lifecycle stays outside the
container. See `references/gateway-pattern.md`.

**Orchestrator response.** Return an opaque instance ID, lifecycle phase,
message, expiry, and protected host/capability only when allocated. The UI
polls the orchestrator through allocation/boot/deletion, then claims and polls
the gateway when a host exists. See `references/orchestrator-pattern.md`.

## Platform gotchas

- **Gazebo discovery needs help on Cloud Run.** <!-- id: gazebo-discovery-cloud-run-boot-watchdog --> There is no
  multicast; use loopback relay settings and a boot watchdog that terminates a
  sticky failed boot so reconnect can land on a fresh instance.
- **Hand-written HTTP responses declare `Connection: close`.** <!-- id: connection-close-header-required --> Cloud
  Run's proxy pools connections; closing without the header can surface as an
  edge 503 malformed response.
- **ROS 2 launch as PID 1 stops on SIGINT, not an assumed SIGTERM.** <!-- id: sigint-not-sigterm-for-ros2-launch-pid1 -->
  Verify the actual entrypoint signal behavior before using shutdown as a test.
- **Cloud Run affinity is same-site.** <!-- id: session-affinity-cookies-samesite-lax --> Map the demo service under
  the site's registrable domain and use credentialed exact-origin requests;
  cross-site `run.app` cookies will not preserve the intended affinity.
- **Request-based CPU throttling can freeze boot.** <!-- id: request-based-billing-cpu-throttle-needs-no-throttling -->
  A start-button flow with no held request needs instance-based CPU allocation;
  a websocket-held flow may use request-based billing. State the cost.
- **FastDDS shared memory is unsuitable in Cloud Run.** <!-- id: fastdds-shm-misbehaves-cloud-run --> Restrict the
  demo container to UDPv4 and solve discovery separately.
- **Concurrent instances need distinct ROS domains.** <!-- id: concurrent-instances-domain-id-collision --> The
  orchestrator assigns an available domain; a manifest's fixed development
  value must not merge public sessions.
- **A single local instance cannot reroute a rejected claim.** <!-- id: single-instance-503-needs-abortable-takeable-claims --> Make
  claims takeable, runs abortable, and lock acquisition bounded so refresh does
  not orphan a Gradio job and deadlock the next session.
- **Poll through the current host/capability.** A host chosen after allocation
  must live in a ref or equivalent current-state cell; an interval that closes
  over the initial empty host will poll the wrong backend forever.

## Customization

- Readiness is app-specific: ROS navigation may require the initial pose and a
  measured real-time factor; a policy demo may require the checkpoint, env,
  and first frame. Keep the lifecycle fields stable and add app metrics rather
  than changing the common state machine.
- A disabled production demo can keep its overview, guide, recorded proof, and
  local path. Disable allocation in site-owned publication/config state; do not
  rewrite the app's hosted capability as false.
- CPU-only policy images should install CPU PyTorch wheels; default wheels can
  pull an unused multi-GB CUDA stack. GPU images pin model/runtime compatibility
  and use immutable image/model revisions.

## References

- `references/gateway-pattern.md`: claim, status, protected transport,
  readiness, shutdown, and watchdog contract.
- `references/orchestrator-pattern.md`: provider-neutral allocation/deletion,
  Driver seam, per-instance ROS domain, and local development loop.
- `references/cloud-run-tuning.md`: verified demo-specific Cloud Run resource,
  networking, affinity, and billing behavior.
- `references/session-ui.md`: shared browser lifecycle and honest state/copy
  contract consumed by the publishing layer.
- `examples/demo_gateway.py`: verified ROS/WebSocket gateway reference
  (production Robot Navigation lineage, 2026-07-13).
- Upstream: [Cloud Run docs](https://cloud.google.com/run/docs),
  [Foxglove deep links](https://docs.foxglove.dev/docs/visualization/shareable-links),
  [gz-transport relay](https://gazebosim.org/api/transport/14/relay.html),
  [Lichtblick](https://github.com/lichtblick-suite/lichtblick), and
  [Gradio embedding](https://www.gradio.app/guides/sharing-your-app). Sibling
  skills: `app-publishing`, `cloud-run`, `runpod`, `foxglove`, `integration`,
  `testing`, and `environments`.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 2.0.0 (2026-08-28): re-scoped around hosted runtime lifecycle, gateway,
  provider, capacity, and viewer handoff. Public project identity, overview,
  article, catalog, and reusable publishing composition moved to the new
  app-publishing skill; added the shared session-UI contract derived from the
  ACT/PushT workspace refactor.

- 1.3.3 (2026-08-03): style pass; removed em dashes throughout (no content changes).

- 1.3.2 (2026-08-01): decision-table rows anchored (learning-engine Phase 1 follow-up); no content changes.

- 1.3.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.3.0 (2026-08-01): Cloud Run deployment mechanics delegated to the new
  cloud-run skill while this skill retained demo-specific tuning.

- 1.2.0 (2026-07-31): absorbed local single-instance Gradio claim/deadlock
  behavior and the Gradio/FastAPI gateway shape from manipulation trials.

- 1.1.1 (2026-07-15): refreshed production domains for robium.ai.

- 1.1.0 (2026-07-13): added the host-level orchestrator pattern and local/cloud
  Driver seam from the production navigation demo.

- 1.0.0 (2026-07-13): created from the production navigation live demo.
