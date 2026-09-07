# Cloud Run deployment decisions

Use this card for deployment mechanics. Verify every current flag and quota in
the official `gcloud` reference before applying it to a real service.

## Build and deploy

- Build from source or push an immutable image through Artifact Registry using
  the current documented Cloud Build and Cloud Run path.
- Record the deployed digest, region, service account, port, CPU, memory,
  concurrency, request timeout, minimum and maximum instances, and billing
  mode.
- Keep `min-instances` at zero unless a warm floor has an explicit owner and
  budget.
- Map resource values to observed workload behavior. Robium's Gazebo and Nav2
  trial used 8 vCPU and 8 GiB to obtain roughly 0.9 to 1.2 real-time factor on
  2026-07-12/13; this is not a general sizing recommendation.

Official starting points:

- [Cloud Run deployment](https://cloud.google.com/run/docs/deploying)
- [`gcloud run deploy`](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
- [Cloud Build](https://cloud.google.com/build/docs)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)

## Choose the billing mode

- Request-based CPU works when a request or WebSocket remains open throughout
  boot and active work. It can reach zero CPU between requests.
- Instance-based CPU is appropriate when a start action launches background
  boot before the viewer connects. It continues billing while the instance is
  retained.
- Robium observed roughly $0.20 to $0.40 of retained-idle cost after a session
  at 8 vCPU and 8 GiB in July 2026. Treat this as a dated observation and use
  current pricing for any decision.

## Concurrency and affinity

- Concurrency of one can isolate one long-lived connection but leaves no room
  for separate status or stop requests on the same instance.
- A higher concurrency with session affinity can support the viewer and
  lifecycle requests, but affinity is routing rather than authorization.
- In Robium's deployment, the affinity cookie was SameSite-Lax. Cross-site
  requests to a `run.app` host did not carry it; a same-site subdomain plus
  credentialed, exact-origin CORS did. Re-check current behavior before relying
  on this shape.
- If the demo requires access control, validate a host-issued signed or
  high-entropy capability in the gateway even when affinity works. A
  browser-chosen first-claim key coordinates visitors but is not authorization.

## WebSockets and probes

- A WebSocket is a long request and is bounded by the configured request
  timeout. Match it to the advertised session length.
- Validate the actual upgrade protocol through the Cloud Run URL using HTTP/1.1
  when the selected bridge requires it.
- Under request-based CPU, hold the probe through boot. A short health request
  can disappear while the background process is still starting and leave the
  instance frozen.
- Declare `Connection: close` when a hand-written server closes an HTTP
  response. Robium observed malformed-response edge 503s without it in the
  July 2026 gateway.

## Deployment authentication

- Prefer short-lived workload identity where the delivery environment supports
  it. If a service-account key is explicitly authorized, materialize it only in
  a protected temporary file, activate it non-interactively, and remove the
  file immediately after the deploy.
- Never print the key, put it in a command URL, or commit the materialized
  credential. Current authentication guidance belongs to Google Cloud's
  official documentation.

## Fleet visibility and VPC capacity

- Read fleet count from Cloud Monitoring only while a live session needs it;
  polling a dedicated service on an idle page can cold-start billable capacity.
- The July 2026 deployment queried
  `run.googleapis.com/container/instance_count`, cached it for roughly 30
  seconds, and observed around one minute of lag. Current metric semantics may
  differ; present the count as approximate and verify the runtime service
  account has only the monitoring access it needs.
- Direct VPC egress needs subnet space for the whole possible instance pool.
  Robium observed a `/28` fail at five 8-vCPU instances and a `/24` work on
  2026-07-12/13. Preserve this as evidence of the sizing relationship, not a
  universal prefix recommendation.

## Final verification

- Confirm the deployed digest and service configuration.
- Exercise readiness and the real HTTP or WebSocket path through Cloud Run.
- Verify idle scale-down, timeout, session isolation, and teardown.
- Record the measured cold start and cost conditions in the application rather
  than copying this card's observations.
