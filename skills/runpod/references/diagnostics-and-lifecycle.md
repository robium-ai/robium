# RunPod diagnostics and lifecycle

Read this reference after a Pod is created, when startup appears stuck, during
an approved interactive diagnosis, and before cleanup. It uses independent
signals so an agent does not confuse capacity, image pull, container restart,
application failure, proxy behavior, or storage mismatch.

Official Pod management, connection, proxy, billing, and storage pages were
directly fetched on 2026-08-24. Re-check current provider behavior before paid
work.

## Start with the verified resource contract

Do not diagnose application startup until the provisioning checklist passes.
A Pod with the wrong GPU, image, network volume, mount, ports, or mode is an
incorrect allocation, not a slow application.

Set two lifetimes:

- a provider-side automatic termination time that survives loss of the local
  process;
- a local orchestration deadline that leaves time to collect logs/evidence and
  delete the Pod cleanly.

The current CLI documents `--terminate-after`; the live GraphQL input exposes
`terminateAfter`. Verify the current interface before use and re-read the
resulting control.

## Use a multi-signal startup matrix

| Signal | What it can prove | What it cannot prove alone |
|---|---|---|
| Pod desired/runtime state | Scheduler/control-plane view | Container health or model progress |
| System logs | Pull/start/stop/restart lifecycle events | Application root cause |
| Container logs | Application stdout/stderr | Correct volume/GPU realization |
| Port mapping/proxy | Declared route and external response | Local application health when proxy fails |
| Local health endpoint | Process readiness inside container | External route/auth correctness |
| Volume identity | Intended persistent storage attached | Application consumed correct files |
| Durable phase/failure marker | Last completed app stage and bounded error | Provider lifecycle before app starts |
| Object timestamps/sizes/hashes | Real persistent side effects | Overall workload success |
| GPU telemetry/CUDA preflight | Runtime can execute on the device | Model/framework acceptance |

Classify only after at least one provider signal and one workload/storage signal
agree.

## Distinguish common startup states

### Cold pull or scheduler delay

Likely when system logs show pull/start progression, no restart cadence exists,
the resource contract is correct, and container logs have not begun. Large
private images can take many minutes. Keep the lifetime bound, communicate the
elapsed time, and continue monitoring without inventing an application cause.

### Restart loop

Likely when system start events repeat and container logs repeat the same early
exception. Capture the exact latest error and verify mount permissions,
entrypoint/arguments, closed-stdin behavior, required runtime packages, and
mode configuration. Do not switch GPUs unless CUDA/architecture evidence points
there.

Issue #69 example: repeated `start container ...: begin` looked like a long
pull, but later container logs repeatedly showed a permission failure at the
intended persistent mount. Safe-field inspection then proved the network volume
was null. Waiting alone would not have fixed it; checking logs and storage did.

### Control-plane lag

Possible when `runtime` or ports remain null while durable markers or objects
continue changing. Treat the provider view as one signal and use the durable
timestamps to show real progress. Do not claim success until the application
acceptance artifact exists.

### Application or framework failure

Use the narrowest durable stage/error. Preserve:

1. exact bounded symptom/exception;
2. root cause when proven;
3. focused passing check after the correction;
4. dead ends ruled out and why.

Do not collapse model loading, simulator reset, compilation, inference,
artifact writing, and gateway readiness into one generic “container failed.”

## Keep diagnostics secret-safe

Use a safe-field allowlist. Never print:

- full environment arrays/maps;
- Pod-scoped API keys or provider API keys;
- registry passwords/tokens;
- model-hub or object-storage credentials;
- private capability URLs/tokens;
- complete authenticated GraphQL/REST objects that may embed any of the above.

Persist small JSON phase/failure records with atomic replacement, bounded
messages, UTC timestamps, and credential-shape redaction. Keep tracebacks in a
private transient channel; commit only sanitized evidence.

If a credential appears in logs, stop further exposure, clean transient copies,
recommend rotation, and follow the operator's explicit security decision. Do
not weaken unrelated budget, lifetime, cleanup, or production gates.

## Use one bounded interactive iteration when justified

Interactive work is useful after the immutable image reaches the workload but
repeated builds/pulls would dominate each application-layer fix.

Before connecting:

- obtain approval for one Pod and a fixed deadline;
- verify exact image/GPU/volume/mode and automatic termination;
- keep the committed worktree authoritative;
- decide how commands and evidence survive an unreliable SSH session.

During diagnosis:

- reproduce one precise failing stage;
- make the smallest source overlay from reviewed local changes;
- run a focused check, then the real acceptance boundary if safe;
- record every runtime dependency or packaging seam that the image must gain;
- avoid changing provider resources unless separately approved.

After diagnosis:

- implement and test the fix locally;
- build a new immutable image once;
- run a fresh Pod from the exact digest with overlays and diagnostic bypasses
  removed;
- delete the interactive Pod and temporary transfer objects.

Issue #69 used one interactive Pod to isolate a direct-environment batching
seam, a missing runtime compiler, and a Pillow-to-ImageIO artifact boundary.
The overlay episode established the fixes, but only the later digest run with
default compilation established deployment readiness.

## Validate the immutable workload in layers

Use workload-appropriate gates, commonly:

1. **Runtime preflight:** exact device, driver/runtime/framework versions,
   architecture support, memory, and a minimal device operation.
2. **Data/model/config identity:** immutable revisions, required files, sizes,
   hashes, offline behavior, and correct mount/staging paths.
3. **Real acceptance run:** deterministic input/seed where possible, bounded
   step/time limit, authoritative success signal, latency and peak-memory data.
4. **Artifact contract:** expected records/frames/files, schema validation,
   independent hash after download.
5. **Service readiness:** local health before public route.
6. **Isolation:** root/foreign scope denied and authorized scope accepted.
7. **Cancellation:** separate noncanonical run reaches active state, cancels
   cooperatively, returns an explicit cancelled result, and becomes ready again.

Do not hide first-use compilation in aggregate latency. Report mean/p95/max and
identify warmup or first-compile outliers when they materially dominate.

## Test HTTP proxy and connection paths

The current official CLI documents HTTP URLs as:

```text
https://<pod-id>-<port>.proxy.runpod.net
```

Declare required ports at creation. Validate in this order:

1. process is listening on the expected container address/port;
2. localhost health succeeds inside the Pod;
3. provider port mapping matches the request;
4. proxy URL responds;
5. application authentication and scope isolation behave correctly.

A proxy timeout/HTTP error does not prove the local process is down. A local
success does not prove the public proxy or authentication is correct. Test both.

SSH and web-terminal behavior varies by connection mode and image. Verify the
current official connection guide. Do not assume SCP, SSH port forwarding, or a
remote command argument works through every RunPod SSH path; use the provider's
documented transfer/connection method and test it before relying on it for the
only copy of evidence.

## Collect evidence before termination

Download only the artifacts needed to support the claim:

- safe resource identity and timestamps;
- runtime/device preflight;
- sanitized phase/failure records;
- acceptance result and metrics;
- media or output artifact;
- proxy/cancellation response summary;
- cleanup and cost record.

Verify schemas and hashes locally. Store durable public evidence where the
project contract requires it; remove temporary private prefixes after download
and verification. Preserve persistent model/data volumes unless deletion was
explicitly authorized.

## Account for cost honestly

Capture balance/current spend immediately before and after the bounded block,
then query billing with an explicit time window when records are available.
State whether a number is:

- provider-attributed Pod billing;
- an upper bound from hourly price and lifetime; or
- an observed balance-window delta.

An observed-window delta can include failed allocations, image pulls,
persistent storage, and billing lag. Do not attribute it solely to the final
successful Pod unless provider billing proves that attribution.

Official billing guidance says compute and storage consume prepaid balance;
storage charges continue after compute stops/terminates; and insufficient funds
can stop or terminate workloads and eventually endanger data. Keep critical
data backed up outside RunPod.

## Cleanup checklist

- [ ] final evidence downloaded, validated, and independently hashed;
- [ ] temporary transfer/object prefixes removed and re-listed empty;
- [ ] interactive/debug templates or secrets removed if created for the block;
- [ ] Pod deleted/terminated through a current official interface;
- [ ] `runpodctl pod list --all` or an authoritative API list shows no
  unintended Pods;
- [ ] expected persistent volumes remain and their continuing cost is stated;
- [ ] post-block balance/current spend and billing window recorded;
- [ ] production-disabled mode remains unchanged;
- [ ] production enablement is reported as a separate step awaiting approval.

Termination is destructive for data outside a network volume. Resolve and
export the exact targets first. Never delete a network volume just because its
Pod is finished.

## Official sources

- [Manage Pods and Pod logs](https://docs.runpod.io/pods/manage-pods)
- [Connect to a Pod](https://docs.runpod.io/pods/connect-to-a-pod)
- [`runpodctl pod` and proxy URL](https://docs.runpod.io/runpodctl/reference/runpodctl-pod)
- [Pod REST list/read fields](https://docs.runpod.io/api-reference/pods/GET/pods)
- [Network volumes](https://docs.runpod.io/storage/network-volumes)
- [Pod billing history](https://docs.runpod.io/api-reference/billing/GET/billing/pods)
- [Billing overview](https://docs.runpod.io/accounts-billing/billing)

All were directly fetched on 2026-08-24. Dated incident findings come from
Robium issue #69 and learnings/2026-08-24-vla-pick-and-place.md rather than
being represented as permanent RunPod guarantees.
