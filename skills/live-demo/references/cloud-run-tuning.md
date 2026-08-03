# Cloud Run tuning for simulator demo backends

Every value below was reached by deploying a Gazebo Harmonic + Nav2 stack
(nav-trial) and fixing what broke, 2026-07-12/13.

## The flag set (verified)

```
--port=8765                      # the gateway; Cloud Run routes ONE port
--concurrency=4 --session-affinity
--min-instances=0 --max-instances=<budget>
--timeout=1800                   # session cap (ws request lifetime ≤ this)
--cpu=8 --memory=8Gi --cpu-boost # 8 vCPU → RTF ≈ 0.9–1.2 for gz+Nav2
--no-cpu-throttling              # see billing modes below
--execution-environment=gen2
--set-env-vars=GZ_RELAY=127.0.0.1,GZ_IP=127.0.0.1,FASTDDS_BUILTIN_TRANSPORTS=UDPv4
--allow-unauthenticated
```

## Billing modes: the central cost decision

- **Request-based (default):** CPU allocated only while a request is
  open. $0 truly idle. Works ONLY if a held connection spans the boot
  (deep-link flow: the viewer's ws does this). A start-button flow
  freezes mid-boot between status polls.
- **Instance-based (`--no-cpu-throttling`):** CPU for the whole instance
  lifetime. Required for start-before-view flows. Cost: Cloud Run retains
  idle instances up to ~15 min after the last request, ≈ $0.20–0.40 per
  session-end at 8 vCPU/8 GiB; worst case (all budget slots churning)
  a few $/hour. `min-instances=0` still guarantees $0 when untouched.

State the chosen mode + its cost in the demo's docs. A GCP budget alert
on the project is cheap insurance.

## Concurrency & affinity

- `concurrency=1` gives per-connection instances with zero code, but
  ONLY the one connection ever reaches the instance: no status endpoint,
  no stop button. Right for deep-link-only flows.
- `concurrency=4 + --session-affinity` lets the page's polls and stop
  calls reach the viewer's instance, **but** the affinity cookie
  (`GAESA`) is SameSite-Lax: it is silently never sent cross-site.
  **Map a same-site subdomain** (demo.<yourdomain>) to the service; page
  fetches use `credentials:'include'`; gateway answers exact-origin CORS
  + `Allow-Credentials`. Without this, routing is pot luck and 409s
  plague the status feed (observed).
- Browser connection pooling pins all fetches to one backend connection;
  another reason cookie affinity, not luck, must do the routing.

## Gazebo / ROS transports inside Cloud Run

- **No multicast anywhere on Cloud Run.** gz-transport discovery needs
  `GZ_RELAY=127.0.0.1` + `GZ_IP=127.0.0.1`, and the unicast relay is
  still a sticky per-boot race with >2 gz processes (SO_REUSEPORT flow
  hashing): a boot either fully works or never recovers. Pair with the
  boot watchdog (gateway-pattern.md). Symptom of a lost race: every
  client loops `Requesting list of world names.`, zero gz output, no
  odom/scan.
- **FastDDS:** `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`; the default
  shared-memory transport throws `Failed init_port … open_and_lock_file`
  storms in Cloud Run.
- DDS multicast is equally absent, but single-container stacks work
  because FastDDS unicasts on loopback once SHM is off.

## Fleet visibility (the "N of budget" display)

The gateway queries Cloud Monitoring
(`run.googleapis.com/container/instance_count`, sum of latest points)
using the metadata-server token. One-time IAM:

```bash
gcloud projects add-iam-policy-binding <project> \
  --member="serviceAccount:<project-number>-compute@developer.gserviceaccount.com" \
  --role="roles/monitoring.viewer"
```

Cache ~30 s; expect ~1 min metric lag; count includes idle-retained
instances. Fold into `/status`: a dedicated endpoint polled before Start
would cold-boot a billable instance per page view.

## Probing / verification from a shell

- Handshake: `curl --http1.1` with Upgrade headers and subprotocol
  `foxglove.sdk.v1` (bridge ≥3.x; h2 breaks upgrades; the old
  `foxglove.websocket.v1` gets a misleading 400).
- A probe that connects-and-drops leaves a request-based instance
  CPU-frozen mid-boot; hold the connection (`-N --max-time 400`) when
  verifying boots, or use instance-based billing.
- Cold starts include image pull on fresh nodes: a 2.5 GB ROS image adds
  30–90 s to the first boot on a node. Say so on the page.

## Direct VPC egress: size the subnet for the pool, not for one instance

If you attach the service to a VPC (Direct VPC egress), the subnet must
hold IPs for the whole *instance pool*, not one container. A `/28` (16
IPs) failed to deploy at `--max-instances=5 --cpu=8` with:

```
no sufficient IP addresses in the VPC network
```

A `/24` fixed it. Widen in place with
`gcloud compute networks subnets expand-ip-range`; no need to recreate
the subnet or the service.
