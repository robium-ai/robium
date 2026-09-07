# Host-level session control

The gateway dies with its container, so it cannot create or authoritatively
delete that container. A browser also cannot allocate provider resources. Keep
provider lifecycle in a host-level control plane and keep visitor traffic out of
that control plane after it returns a connect host.

## Divide ownership by lifetime

| | Host-level controller | Per-instance gateway |
| --- | --- | --- |
| Lifetime | Outlives every visitor instance | Dies with one instance |
| Owns | provider allocation or routing, expiry, fleet cap, registry lookup | first claim, readiness, viewer transport, app-local shutdown |
| Knows | which instances or routes exist | what is healthy inside one instance |
| Visitor data path | No | Yes |

The controller returns an instance ID, lifecycle phase, expiry, and connect
host. The verified gateway then uses a browser-provided claim ID to prevent two
active visitors from sharing one process. That first-claim mechanism is not
authentication. If the public boundary needs access control, the controller
must also issue a signed or high-entropy value bound to the instance and expiry,
and the gateway must validate it on every lifecycle and viewer route.

## Keep one configuration source

- The application's `robium-app.yaml` owns the runnable
  `demo.orchestrator` facts: image, command, gateway port, readiness contract,
  provider requirements, resources, lifetime, and fleet or budget limits that
  the current schema supports.
- The website/orchestrator registry is a derived deployment projection. Do not
  hand-maintain a competing copy of application runtime facts.
- Current public enablement and editorial presentation remain website-owned.
  Validate the app manifest before deriving or deploying its registry record.

## Let providers realize the contract differently

| Provider | What allocate/release means | Important boundary |
| --- | --- | --- |
| Local Docker | Create and remove a labeled container on an ephemeral host port | Cheapest full lifecycle probe; shared hosts require explicit isolation |
| RunPod | Create and delete a paid Pod, often with an attached network volume | The authoritative Pod list and confirmed deletion define cleanup; route mechanics to `runpod` |
| Cloud Run | Route a claim/request to a predeployed service and let Cloud Run start or retain instances | Do not create a new Cloud Run service per visitor; request lifetime, concurrency, affinity, and max instances define behavior |

A small session interface keeps the browser contract stable without pretending
the providers expose identical resources:

```ts
interface SessionDriver {
  begin(app: AppRuntime): Promise<{ id: string; host: string; expiresAt: string }>
  end(id: string): Promise<void>
  capacity(): Promise<Capacity>
}
```

For Local Docker and RunPod, `begin` creates an explicit resource and `end`
deletes it. For Cloud Run, `begin` issues or records a claim and triggers the
predeployed route; `end` ends the app session while the platform controls
instance retention. It is not a per-visitor Admin API service creator. Keep
current deploy flags and request semantics in `cloud-run`, and current Pod
inventory, volume, proxy, and deletion operations in `runpod`.

## Isolate concurrent ROS graphs

Concurrent ROS instances on one Docker network must not share a fixed
`ROS_DOMAIN_ID`. Robium's July 2026 local nav-trial assigned the lowest free ID
from 1 through 200 and labeled each container so it could recover the ID on
restart. The important invariant is one free domain per concurrent instance;
the range and allocation strategy are evidence from that host, not a universal
default.

Without isolation, graphs merge, multiple Gazebo servers publish `/clock`, and
logs can repeatedly report transforms moving backward in time. Diagnose this as
cross-instance graph contamination, not simulator physics.

## Make budget and teardown authoritative

- Local Docker and RunPod can count their labeled containers or Pods before
  allocating. Refuse starts beyond the configured cap and make the busy state
  visible.
- Cloud Run enforces its configured maximum instances; monitoring-derived fleet
  counts are approximate and lagging. Use them for display, not as an exact
  admission lock.
- Expiry and provider cleanup must work when the browser disappears. A beacon or
  gateway shutdown is only a best effort; RunPod deletion and any paid storage
  policy need explicit verification.

## Keep the local loop honest

- Start should create a disposable local container and Stop should remove it.
  Reusing an unrelated warm container hides lifecycle bugs.
- Let the frontend target either the local controller or deployed route without
  rebuilding app code.
- Start the site and local controller together so the end-to-end lifecycle is
  exercised routinely.
