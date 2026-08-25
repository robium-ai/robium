---
name: runpod
version: 0.1.0
description: >
  Operate RunPod Pods safely: inspect balance, compare alternative GPU resources
  and US regions, launch immutable images, attach network volumes, expose
  services, diagnose logs/startup, validate workloads, and clean up paid
  compute. Use when: 'RunPod', 'runpodctl', 'check alternative resources in
  RunPod', 'find an available RunPod GPU in the same region as my volume', 'try
  A40/A100/H100/4090', 'networkVolume is null', 'start container begin', 'check
  RunPod logs before terminating', 'RunPod proxy', 'connect interactively', or
  'delete the Pod'. Load after environments defines the workload contract. Not
  for: uv/Docker or CUDA image parity (environments), application Dockerfiles
  (integration), the cloud-run skill, or framework-specific model/simulator
  mechanics.
---

# runpod

RunPod operations for generic container workloads. Turn workload requirements
into one bounded, verified allocation; diagnose it without leaking credentials
or burning through repeated guesses; prove the immutable result; then clean up
compute and evidence. Provider documentation supplies the current interface;
this skill supplies the safety gates and battle-tested operating sequence.

## When to use this skill

- Inspect RunPod balance, spend, Pods, network volumes, datacenters, or live GPU
  inventory before a workload is allocated.
- Compare alternative GPU types or regions against VRAM, CUDA, cloud tier,
  price, stock, ports, and storage locality.
- Create or update a Pod/template from a pinned public or private image.
- Debug a Pod with missing storage, no ports, slow image pull, restart loop,
  provider/application log disagreement, or a proxy that does not answer.
- Connect to one explicitly approved interactive Pod to iterate on a workload,
  then convert the result back into an immutable deployment.
- Validate HTTP proxy isolation, workload cancellation, evidence artifacts,
  billing, deletion, and authoritative zero-Pod cleanup.
- Cross-references:
  - Choose uv versus Docker, pin the base image/CUDA contract, and establish
    local-to-remote parity first with `environments`.
  - Build application Dockerfiles or multi-container wiring with `integration`.
  - Use `cloud-run` for Google Cloud Run and a framework skill such as
    `lerobot`, `isaac-sim`, or `isaac-lab` for workload mechanics.

## Key directives

- **Delegation posture: embed + links.** Embed RunPod-specific safety,
  selection, verification, and recovery patterns here; verify changing CLI,
  REST, GraphQL, pricing, and product behavior against
  [official RunPod documentation](https://docs.runpod.io/) before acting.
- **Inventory first; allocate only after an explicit paid-compute gate.** <!-- id: inventory-before-paid-allocation -->
  Read balance/current spend, running Pods, persistent storage, exact GPU IDs,
  stock, price, and datacenter locality before proposing one bounded resource.
  Stop if credentials, funding, licensing, or required infrastructure are
  unavailable. Approval names the allocation and lifetime; it is not blanket
  permission for retries.
- **Treat accepted create inputs as unverified until a safe-field re-read.** <!-- id: verify-created-pod-contract -->
  Compare the resulting Pod's exact image digest, GPU ID/count, cloud tier,
  datacenter, network-volume ID, mount path, ports, registry auth identity,
  operational mode, and termination time. Delete a mismatched Pod instead of
  debugging it as though the request succeeded.
- **Never print a full authenticated Pod or environment object.** <!-- id: safe-field-provider-diagnostics -->
  Provider responses can contain injected credentials. Query an explicit
  allowlist, redact values, and keep API keys out of URLs, shell history,
  evidence, and committed files.
- **Use multiple startup signals before classifying or terminating.** <!-- id: multi-signal-startup-diagnosis -->
  Combine safe control-plane state, system logs, container logs, storage
  identity, durable phase/failure markers, object timestamps, and a health
  endpoint. `runtime: null`, missing ports, or repeated start events alone do
  not distinguish a cold pull from a crash loop.
- **Interactive overlays diagnose; only an exact immutable rerun proves.** <!-- id: overlay-not-deployment-proof -->
  Bound interactive work by one approved Pod and deadline. Apply reviewed
  source overlays only to isolate defects, then rebuild and rerun the clean
  digest without diagnostic bypasses before claiming deployment readiness.
- **Cleanup and production enablement are separate gates.** <!-- id: cleanup-and-production-separate-gates -->
  Download and validate evidence, record the observed cost window, delete
  temporary objects and Pods, and verify zero Pods. Never enable production as
  a side effect of a passing feasibility or proxy test; require separate
  explicit approval.

## Quick start

**1. Write the allocation contract before touching paid compute.** Record:

- workload and acceptance test;
- minimum VRAM/GPU architecture/CUDA support and GPU count;
- immutable image digest and registry credential identity;
- required network volume, mount path, region, ports, and cloud tier;
- maximum hourly price, total budget, deadline, and termination control;
- operational mode flags, especially the production-disabled value.

**2. Run read-only inventory.** Current official CLI surfaces, directly
verified 2026-08-24:

```bash
runpodctl user
runpodctl pod list --all
runpodctl network-volume list
runpodctl gpu list --include-unavailable
runpodctl datacenter list
```

Do not paste full output into chat or logs. Extract only the safe fields needed
for the decision. See `references/provisioning.md` for the contract worksheet,
interface selection, and volume-aware placement flow.

**3. Stop for paid approval.** Present one candidate with exact GPU ID, region,
cloud tier, volume, image digest, price, and lifetime. If approved, create one
Pod and immediately perform the exact post-create comparison.

**4. Monitor and validate.** Use `references/diagnostics-and-lifecycle.md` for
the multi-signal startup tree, bounded interactive loop, service/proxy tests,
artifact checks, billing, and cleanup.

## Usage patterns

### Choose a GPU and region

Start from the workload floor, not a favorite SKU. Filter live inventory by
VRAM, architecture/CUDA compatibility, GPU count, cloud tier, and price. Then
intersect with datacenters that satisfy the volume and networking contract.
Report unavailable candidates separately from incompatible ones; “no stock”
and “wrong region for the volume” require different fixes.

Network volumes are a placement constraint, not an afterthought. Official
RunPod storage guidance says Pod network volumes are Secure Cloud resources,
available GPU choices depend on the volume location, and the volume must be
attached at deployment. See `references/provisioning.md`.

### Provision an exact contract

Prefer the simplest current official interface that exposes every required
field. The CLI is convenient; REST and GraphQL offer explicit object fields;
SDKs can make repeated automation safer. Do not assume those interfaces are
behaviorally identical. Verify current help/schema, submit once, and re-read
the created object with network-volume details included.

Issue #69 evidence (2026-08-24): `runpodctl` v2.8 accepted network-volume
flags but two Pods reported `networkVolume: null`; direct REST rejected the
live inventory's exact Server Edition GPU ID; the official GraphQL create
mutation expressed the full contract and attached the volume when passed the
exact GPU ID, `networkVolumeId`, `volumeInGb: 0`, and `volumeMountPath`. Treat
this as dated provider behavior and a permanent reason to verify, not a rule
that GraphQL is always required.

### Diagnose a slow or restarting Pod

Large private images may take many minutes to pull. Repeated “start container”
events may instead indicate restarts. Check both provider log types: system
logs describe lifecycle events; container logs contain application stdout and
stderr. Confirm storage attachment and durable markers before changing GPU or
image. Preserve the exact bounded error, ruled-out causes, and timestamps.

### Iterate interactively without losing immutability

When repeated rebuild/pull cycles dominate diagnosis, request approval for one
time-bounded interactive Pod. Confirm its contract first; use SSH, Web Terminal,
or a durable command/evidence channel supported by the workload. Overlay only
reviewed source, run focused checks, and stop once the defect is isolated.
Commit the fix, rebuild the image, and repeat the acceptance test from the exact
digest. Never promote the overlay result itself.

### Validate a service and close the allocation

Test localhost inside the Pod before the provider proxy. Then test the public
URL, authentication/capability isolation, expected success path, foreign-scope
denial, cancellation, and return-to-ready behavior as applicable. Hash
downloaded evidence independently. Query billing for the observed time window,
delete the Pod, and re-list all Pods. Persistent volumes keep accruing storage
cost until intentionally deleted; do not delete them unless that destructive
scope was explicitly approved.

## Platform gotchas

- **Exact GPU IDs are provider data.** <!-- id: exact-gpu-id-from-live-inventory --> Use live `gpuId` values from
  inventory. Display names, REST enums, GraphQL IDs, and marketing names can
  differ or drift.
- **Volume attachment changes placement and lifecycle.** <!-- id: volume-locality-and-lifecycle --> Network volumes
  constrain the Pod to their datacenter and must be attached at creation.
  Official docs say Pods with network volumes cannot use the ordinary stop
  lifecycle; terminate compute while preserving the independent volume.
- **A template is not the resulting Pod.** Re-read the allocated resource even
  when the template was re-read just before creation. Provider defaults or
  interface omissions can still change image, volume, ports, or mode.
- **RunPod exposes system and container logs separately.** A healthy image pull
  can have no application output; a restart loop can repeat system start events.
  Inspect both before attributing the delay to capacity or CUDA.
- **Proxy access requires a declared HTTP port.** Current official CLI docs use
  `https://<pod-id>-<port>.proxy.runpod.net`; declare ports at creation and
  verify localhost before proxy behavior. Workload authentication remains your
  responsibility.
- **Editing/resetting can erase nonpersistent data.** Export evidence first and
  know whether data lives on container disk, Pod volume, or network volume.
- **Balance and storage outlive the Pod.** Compute deletion does not remove a
  network volume or its hourly storage charge. Low balance can stop or terminate
  compute and eventually endanger persistent data; keep external backups.

## Customization

- **CPU workload:** use the same approval, exact-object verification,
  diagnostics, and cleanup sequence; omit GPU/CUDA fields and validate the CPU
  flavor instead.
- **Spot workload:** add interruption handling, resumable checkpoints, and an
  external source of truth. Do not use interruptible compute for a one-shot
  acceptance gate unless the protocol explicitly allows restart.
- **No persistent data:** omit volumes, keep artifacts external, and confirm the
  container/Pod disk loss semantics before deletion or reset.
- **Private registry:** identify the registry credential by provider-side ID;
  never materialize its secret in a command, Pod readback, or evidence bundle.
- **Different service protocol:** HTTP proxy guidance applies only to declared
  HTTP services. For TCP/SSH/WebSocket details, verify the current official
  connection documentation and test the actual protocol end to end.

## References

- `references/provisioning.md`: safe inventory, workload contract, interface
  choice, network-volume placement, immutable image creation, and post-create
  verification. Read before any allocation.
- `references/diagnostics-and-lifecycle.md`: multi-signal startup diagnosis,
  interactive iteration, proxy/cancellation validation, evidence, cost, and
  cleanup. Read after a Pod is created or when one is unhealthy.
- Upstream: [RunPod CLI reference](https://docs.runpod.io/runpodctl/overview),
  [Pod management](https://docs.runpod.io/pods/manage-pods),
  [Pod REST create API](https://docs.runpod.io/api-reference/pods/POST/pods),
  [GraphQL Pod management](https://docs.runpod.io/sdks/graphql/manage-pods),
  [live GraphQL schema](https://graphql-spec.dev.runpod.io/),
  [network volumes](https://docs.runpod.io/storage/network-volumes), and
  [billing](https://docs.runpod.io/accounts-billing/billing). Interface claims
  in this version were directly fetched from these official pages on
  2026-08-24; re-verify before paid operations.
- Evidence: Robium issue #69 and
  learnings/2026-08-24-vla-pick-and-place.md entries `lrn-0824-05` through
  `lrn-0824-29`. Sibling skills: `environments`, `integration`, `cloud-run`,
  `testing`, and the workload-specific framework skills.

## Changelog

- 0.1.0 (2026-08-24): created as the generic RunPod operations owner; absorbs
  issue #69's volume-verification, safe-diagnostics, interactive-iteration,
  immutable-revalidation, proxy/cancellation, cost, cleanup, and production-gate
  evidence while delegating changing provider syntax to official documentation.
