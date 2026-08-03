---
name: cloud-run
version: 1.0.2
description: >
  Deploy headless robotics / sim / demo containers to Google Cloud Run: the
  build → Artifact Registry → Cloud Run path plus the gotchas that bite sim
  workloads (no UDP multicast for gz-transport/DDS, CPU allocated only while a
  request is open, session affinity for per-visitor instances, request timeout /
  concurrency for long-lived WebSockets, VPC subnet sizing). Use when: 'deploy to
  Cloud Run', 'gcloud run deploy', 'Cloud Build', 'Artifact Registry', 'host the
  sim in the cloud', 'Cloud Run WebSocket / Foxglove bridge times out', 'session
  affinity', '--no-cpu-throttling', 'GZ_RELAY / GZ_IP on Cloud Run', deploy auth
  from CI with a GCP service-account key. Owns the Cloud Run deploy mechanics
  that live-demo and environments point at. Not for: the demo orchestrator,
  session gateway, or mission-control page (live-demo); GPU-cloud/RunPod or
  uv-vs-Docker choice (environments); general non-robotics gcloud/GCP basics
  (upstream Google docs).
---

# cloud-run

The deploy target for robium's headless robotics and demo containers: a sim +
bridge (or a policy server) built into an image, pushed to Artifact Registry,
and run on Google Cloud Run so a browser can reach it, optionally one private
instance per visitor, scale-to-zero when idle. This skill consolidates the
Cloud-Run-specific mechanics and the robotics/headless gotchas that were
hard-won deploying a Gazebo Harmonic + Nav2 stack (robium's nav-trial demo,
2026-07-12/13). It stays thin on general gcloud/GCP usage (that lives in
Google's own docs) and embeds only what a robotics container hits that a plain
web service never does.

## When to use this skill

- Building and deploying any headless robotics/sim/demo container to Cloud Run:
  the `gcloud` / Cloud Build → Artifact Registry → `gcloud run deploy` path, and
  the flag set a sim workload needs (CPU/memory, timeout, concurrency, affinity).
- Debugging a robotics container that runs locally but misbehaves on Cloud Run:
  gz/DDS discovery silent (no multicast), sim boot freezes (CPU throttled between
  requests), WebSocket drops, affinity cookie ignored, deploy fails on VPC IPs.
- Wiring deploy auth from CI/servers with a GCP service-account key.
- The trigger phrases in the description: 'deploy to Cloud Run', 'gcloud run
  deploy', 'Cloud Build', 'Artifact Registry', 'session affinity',
  '--no-cpu-throttling', 'GZ_RELAY on Cloud Run', 'Cloud Run WebSocket timeout'.
- Cross-references: go to the sibling skill instead when the question is:
  - The demo orchestrator, session gateway (claim/status/shutdown + ws tunnel),
    mission-control page, or viewer handoff → `live-demo` (it *uses* this skill's
    deploy mechanics but owns everything demo-shaped above the container).
  - Whether to use uv vs Docker, local↔remote reproducibility, GPU passthrough,
    or GPU-cloud/RunPod provisioning → `environments` (Cloud Run is CPU-only and
    is one deploy target it points at; RunPod is the GPU one).
  - `foxglove_bridge` mechanics, the `foxglove.sdk.v1` subprotocol, MCAP → the
    `foxglove` skill (this skill only covers reaching the bridge through Cloud
    Run's proxy).
  - The whole-stack decision and where deploy sits → `architect` (routes here).

## Key directives

- **Delegation posture: embed + links.** The robotics/headless Cloud Run
  gotchas (no multicast → unicast relay, CPU-on-request throttling, same-site
  affinity, VPC subnet sizing, long-ws timeout/concurrency) are embedded here
  because they exist nowhere upstream in one place; they were derived by
  deployment. For general gcloud/GCP mechanics (auth, project setup, the full
  `gcloud run deploy` flag reference, Cloud Build, Artifact Registry repo
  creation) point upstream to Google's docs; don't restate them from memory.
- **Scale-to-zero, and state per-session cost.** <!-- id: scale-to-zero-state-cost --> `--min-instances=0` unless a
  warm floor is explicitly justified. The billing-mode choice (request-based vs
  `--no-cpu-throttling`) is a cost decision: state it and its per-session
  figure in the app/demo docs, and put a GCP budget alert on the project.
- **A boot that needs CPU must hold a request while it boots.** <!-- id: boot-needs-held-request --> Cloud Run's
  default (request-based) billing allocates CPU *only while a request is open*.
  A robotics container that boots a sim in the background freezes the moment no
  request is in flight. Either drive the boot with a held connection (the
  viewer's WebSocket does this) or pick `--no-cpu-throttling`.
- **No UDP multicast anywhere on Cloud Run.** <!-- id: no-udp-multicast-cloud-run --> gz-transport and DDS discovery
  both assume multicast; neither gets it. Force unicast/loopback (see Quick
  start) and pair a gz stack with a boot watchdog; the unicast relay is a
  sticky per-boot race that fails ~half the time with >2 gz processes.
- **Never write gcloud flag names or Cloud Run limits from memory.** <!-- id: no-gcloud-facts-from-memory --> CLI shape
  and quotas drift; verify against
  [cloud.google.com/sdk/gcloud/reference/run/deploy](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
  before committing a real deploy. The robotics flag *values* below are
  robium-verified (nav-trial), not guesses; the *availability* of a given flag
  in your gcloud version still needs the reference check.

## Quick start

**1. Build the image and push to Artifact Registry.** <!-- id: build-push-artifact-registry --> Two paths (both are real
`gcloud` surfaces; verify current flags against the reference above):

```bash
# One-shot: Cloud Build builds from the Dockerfile and pushes in one call.
gcloud builds submit --tag \
  <region>-docker.pkg.dev/<project>/<repo>/<image>:<tag>

# Or deploy straight from source (Cloud Run builds it for you):
gcloud run deploy demo-<app> --source . --region=<region>
```

(The Artifact Registry repo is created once with `gcloud artifacts
repositories create <repo> --repository-format=docker --location=<region>`.)

**2. Deploy the container** <!-- id: deploy-container-robotics-flags --> with the robotics/sim flag set (values verified for a
Gazebo Harmonic + Nav2 stack, nav-trial 2026-07-13):

```bash
gcloud run deploy demo-<app> \
  --image=<region>-docker.pkg.dev/<project>/<repo>/<image>:<tag> \
  --region=<region> --port=8765 \
  --concurrency=4 --session-affinity \
  --min-instances=0 --max-instances=5 --timeout=1800 \
  --cpu=8 --memory=8Gi --cpu-boost --no-cpu-throttling \
  --execution-environment=gen2 \
  --set-env-vars=GZ_RELAY=127.0.0.1,GZ_IP=127.0.0.1,FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
  --allow-unauthenticated --quiet
```

Why each robotics-specific piece is there is in Usage patterns and Platform
gotchas below. `--timeout=1800` caps a single request (and so a WebSocket
session) at 30 min; Cloud Run's request timeout is the session cap for a
long-lived ws, so size it to the demo, not the default.

**3. Map a same-site subdomain** <!-- id: map-same-site-subdomain --> (e.g. `demo.yourdomain.org` → the service) if
the page that talks to it lives on your site: the session-affinity cookie is
SameSite-Lax and never flows cross-site to a `*.run.app` host (see gotchas).

## Usage patterns

**Choose the billing mode: the central cost decision.** <!-- id: choose-billing-mode -->

| Mode | Flag | CPU allocated | Use when |
| --- | --- | --- | --- |
| Request-based (default) | *(none)* | Only while a request is open; $0 truly idle | A held connection spans the whole boot (the viewer's ws holds CPU) |
| Instance-based | `--no-cpu-throttling` | Whole instance lifetime | Start-before-view flows where the boot has no held connection |

Instance-based cost: Cloud Run retains idle instances up to ~15 min after the
last request, ≈ $0.20–0.40 per session-end at 8 vCPU / 8 GiB; a churning fleet
can reach a few $/hour. `--min-instances=0` still guarantees $0 when untouched.
(Verified nav-trial, cloud-run-tuning notes.)

**Concurrency & session affinity for per-visitor instances.**

- `--concurrency=1` gives per-connection instances with zero code, but *only* <!-- id: concurrency-1-per-connection -->
  that one connection ever reaches the instance: no room for a status endpoint
  or a stop button. Right for deep-link-only flows.
- `--concurrency=4 --session-affinity` lets a page's status polls and stop calls <!-- id: concurrency-4-affinity-cookie -->
  reach the same instance as its ws, **but** the affinity cookie (`GAESA`) is
  SameSite-Lax and is silently never sent cross-site. Map a same-site subdomain,
  send fetches with `credentials:'include'`, and answer exact-origin CORS with
  `Allow-Credentials`. Without this, routing is pot luck and 409s plague the
  status feed. Browser connection pooling pins fetches to one backend, so cookie
  affinity, not luck, must do the routing.

**Long-lived WebSockets (Foxglove bridge, PTY-over-ws).** <!-- id: long-lived-websockets-timeout --> Cloud Run supports
WebSockets, but the request timeout (`--timeout`, up to 60 min) bounds the
session; a ws is one long request. Set it to the intended session cap. When
probing a boot by hand from a shell, *hold the connection* (`curl -N --http1.1
--max-time 400` with the Upgrade headers): a probe that connects-and-drops
leaves a request-based instance CPU-frozen mid-boot. The bridge subprotocol
(`foxglove.sdk.v1` on bridge ≥3.x; h2 breaks the upgrade: use `--http1.1`) is
the `foxglove` skill's territory.

**Deploy auth from CI / servers (`GCP_SA_KEY`).** <!-- id: deploy-auth-ci-gcp-sa-key --> A service-account key (JSON,
one env var) activates gcloud non-interactively. Materialize it to a temp file
and point `GOOGLE_APPLICATION_CREDENTIALS` at it; robium keeps the key in
Doppler (`GCP_SA_KEY`, SA `robium-deployer@robium-prod`, deploy-scoped: Cloud
Run + Cloud Build + Artifact Registry + Storage + Service Account User):

```bash
f="$(mktemp)"; printf '%s' "$GCP_SA_KEY" > "$f"
gcloud auth activate-service-account --key-file="$f" --quiet
export GOOGLE_APPLICATION_CREDENTIALS="$f"
# ... gcloud builds submit / gcloud run deploy ...
rm -f "$f"
```

See robium's secrets doc for the Doppler/`.env` wiring (the environments skill's
secrets guidance points here for the Cloud Run half). In GitHub Actions the same
key feeds `google-github-actions/auth` + `deploy-cloudrun`.

**Fleet visibility (the "N of budget" count).** <!-- id: fleet-visibility-monitoring --> Query Cloud Monitoring
(`run.googleapis.com/container/instance_count`, sum of latest points) with the
metadata-server token; grant the runtime SA `roles/monitoring.viewer` once.
Cache ~30 s (expect ~1 min metric lag). Never fetch it on page load; a bare
status request cold-boots a billable instance per drive-by visitor; fold it into
an endpoint that only runs while a session is live (that endpoint is the
`live-demo` gateway's).

## Platform gotchas

All verified deploying robium's nav-trial demo (Gazebo Harmonic + Nav2), 2026-07-12/13,
unless dated otherwise. Sources: robium's cloud-run-tuning notes / nav-trial.

- **No UDP multicast → gz-transport needs a unicast relay.** <!-- id: gz-transport-unicast-relay-boot-watchdog --> Set
  `GZ_RELAY=127.0.0.1` + `GZ_IP=127.0.0.1`. Even then the relay is a *sticky
  per-boot race* with >2 gz processes (SO_REUSEPORT flow hashing): a boot either
  fully works or never recovers. Symptom of a lost race: every client loops
  `Requesting list of world names.`, zero gz output, no odom/scan. Pair with an
  in-container **boot watchdog** (no sim data within ~120 s → SIGINT PID 1 → a
  fresh instance boots on the client's reconnect); this recovers the ~50% of
  boots that lose the race.
- **DDS multicast is equally absent.** <!-- id: dds-multicast-fastdds-transport --> `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`
  silences the default shared-memory transport's `open_and_lock_file` error
  storm; single-container FastDDS then unicasts on loopback fine.
- **Request-based billing throttles CPU between requests.** A background sim
  boot with no held connection freezes mid-boot. Use `--no-cpu-throttling` for
  start-button flows, or make the boot ride a held ws (see Usage patterns).
- **A health probe that connects-and-drops throttles the container mid-boot.** <!-- id: health-probe-must-hold-connection -->
  Under request-based billing the probe *is* the only open request; when it
  drops, CPU is deallocated with the sim half-booted. Probes and manual boot
  checks must hold the socket open for the boot's duration.
- **Session-affinity cookies are SameSite-Lax**: they never flow from your
  site's pages to a `*.run.app` host (cross-site). Map a same-site subdomain to
  the service and use `credentials:'include'` + exact-origin CORS, or affinity
  silently does nothing and status/stop calls misroute (409s).
- **Cold start includes image pull on a fresh node.** <!-- id: cold-start-image-pull --> A ~2.5 GB ROS image adds
  30–90 s to the first boot on a node; say so on any user-facing page rather
  than letting it read as a hang.
- **Direct VPC egress: size the subnet for the whole instance pool.** <!-- id: vpc-subnet-sizing --> If you
  attach the service to a VPC, the subnet must hold IPs for `--max-instances`
  containers, not one. A `/28` (16 IPs) failed to deploy at
  `--max-instances=5 --cpu=8` with `no sufficient IP addresses in the VPC
  network`; a `/24` fixed it. Widen in place with `gcloud compute networks
  subnets expand-ip-range`; no need to recreate the subnet or service.
- **Public interactive shells need a real threat model, not just
  `--allow-unauthenticated`.** <!-- id: public-shell-threat-model --> The exposures that matter on a browser-reachable
  container shell are its *credentials* and its *network egress*, not container
  escape. robium's candidate hardening shape, a zero-IAM-role runtime service
  account plus deny-all VPC egress (egress-lockdown), is deployed but **not yet
  verified end-to-end**, so treat it as a direction, not a recipe: until it is
  proven, don't put a public shell on a container holding any credential you'd
  mind losing. (Status per live-demo's orchestrator notes; re-check before
  relying on it.)

## Customization

- **Different sim/stack:** the transport env vars (`GZ_RELAY`/`GZ_IP`,
  `FASTDDS_BUILTIN_TRANSPORTS`) and the watchdog apply to any gz/ROS 2 stack; a
  non-ROS backend (a policy server, a Gradio app) drops the gz/DDS env and the
  watchdog and keeps only the billing-mode, timeout, concurrency, and affinity
  choices. Size `--cpu`/`--memory` to the workload (a Gazebo+Nav2 stack wanted 8
  vCPU for RTF ≈ 1; measure, don't copy the number).
- **Different budget/session cap:** `--max-instances` is the fleet budget,
  `--timeout` the per-session cap, `--min-instances` a warm floor (leave at 0
  for scale-to-zero). State the resulting cost envelope in the app docs.
- **No VPC:** the subnet-sizing gotcha only applies if you attach Direct VPC
  egress (for egress control or reaching private resources). A plain public demo
  needs none of it.
- **GPU workloads:** Cloud Run is CPU-only for robium's purposes; a policy that
  needs a GPU goes to a GPU host (RunPod, per the environments skill), not here.

## References

- Upstream: [Cloud Run docs](https://cloud.google.com/run/docs),
  [`gcloud run deploy` reference](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
  (authoritative flag list; re-check before a real deploy),
  [Cloud Build](https://cloud.google.com/build/docs),
  [Artifact Registry](https://cloud.google.com/artifact-registry/docs),
  [Cloud Run WebSockets guide](https://cloud.google.com/run/docs/triggering/websockets),
  [gz-transport relay](https://gazebosim.org/api/transport/14/relay.html).
  gcloud CLI shape (`gcloud run deploy`, `--source`, `gcloud builds submit
  --tag`, deploy-from-source) confirmed 2026-08-01 via context7 fetch of the
  upstream Cloud Run deploy docs (search-synthesis of Google's docs, not a
  direct cloud.google.com fetch); re-verify flag availability against the
  reference link before committing. The robotics flag *values* and every gotcha
  above are robium-verified from the nav-trial demo deployment (2026-07-12/13),
  not from upstream.
- Sibling skills: `live-demo` (the demo orchestrator, session gateway,
  mission-control page, and viewer handoff that consume this deploy target;
  its cloud-run-tuning notes are the origin of the facts here), `environments`
  (uv-vs-Docker, local↔remote parity, and GPU-cloud/RunPod, the GPU deploy
  target alongside this CPU one), `foxglove` (bridge/subprotocol mechanics for
  the ws this skill routes through Cloud Run), `architect` (routes here for the
  deploy phase). robium's secrets doc (docs/secrets.md) has the `GCP_SA_KEY`
  Doppler wiring.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).

- 1.0.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.0.0 (2026-08-01): created (issue #67); consolidates the robotics/headless
  Cloud Run deploy mechanics and gotchas that were scattered inside live-demo's
  cloud-run-tuning notes and environments/architect prose: build → Artifact
  Registry → deploy path, billing-mode cost decision, gz/DDS unicast relay +
  boot watchdog (no multicast), CPU-on-request throttling and the hold-the-probe
  rule, SameSite-Lax same-site-subdomain affinity, ws timeout/concurrency, VPC
  subnet sizing, fleet-count monitoring IAM, deploy auth via `GCP_SA_KEY`, and
  the not-yet-verified egress-lockdown shape for public shells. Cross-referenced
  from live-demo, environments, and architect's routing table.
