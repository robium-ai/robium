# RunPod provisioning: from workload contract to verified Pod

Read this reference before any paid allocation. It separates current upstream
interfaces from Robium's dated provider observations and makes the post-create
resource, not the submitted command, the source of truth.

Official RunPod CLI, Pod REST, GraphQL, storage, and billing pages were directly
fetched on 2026-08-24. Re-check them before paid work because flags, schemas,
stock, prices, and product behavior change.

## Define the complete contract

Write down all required fields before looking for a machine:

| Concern | Required decision |
|---|---|
| Workload | Command/mode and one acceptance test |
| Compute | CPU or exact minimum GPU architecture, VRAM, count, CUDA support |
| Image | Registry path pinned by immutable digest; architecture/platform |
| Registry | Provider-side credential ID; never the credential value |
| Storage | Network-volume ID or Pod volume, size, mount path, persistence |
| Placement | Cloud tier, datacenter/country, volume locality, public IP |
| Network | HTTP/TCP ports and workload authentication |
| Safety | Production-disabled mode, maximum hourly price, total budget |
| Lifetime | Provider termination control and local monitoring deadline |
| Evidence | Durable phase/failure paths and artifacts to download/hash |

Do not let a convenient template silently fill a safety-critical blank.

## Run read-only inventory first

The current official CLI documents these commands:

```bash
runpodctl user
runpodctl pod list --all
runpodctl network-volume list
runpodctl gpu list --include-unavailable
runpodctl datacenter list
```

Use `runpodctl billing pods` with an explicit RFC3339 window when historical
cost attribution is needed. Inspect `runpodctl <group> --help` before relying
on a flag in automation.

Extract only safe fields:

- balance, current spend per hour, and spend limit;
- Pod ID, name, status, image, cost per hour, GPU ID/count, datacenter, ports,
  network-volume ID, mount path, and termination time;
- volume ID, name, size, and datacenter;
- GPU ID, display name, memory, cloud support, stock, and price;
- datacenter ID and GPU availability.

Do not print email, API keys, complete environment maps, registry secrets,
capability tokens, or full authenticated resource objects. A provider object
that looks like metadata can include injected environment values.

## Select compute and storage together

Use this order:

1. Filter GPUs by the workload's hard architecture, VRAM, CUDA, and count
   floor.
2. Filter by allowed cloud tier and maximum price.
3. If a network volume is required, restrict placement to its datacenter.
4. Compare live stock at the resulting datacenter(s).
5. Rank compatible candidates by cost and availability; keep incompatible and
   unavailable candidates in separate lists.

Official network-volume guidance says Pod network volumes are available in
Secure Cloud, GPU choices depend on volume location, and attachment occurs
during deployment. A volume cannot be attached or detached from an existing
Pod without deleting that Pod. The volume exists independently after compute
termination and continues accruing storage cost.

When no compatible GPU exists in the volume's datacenter, the choices are:

- wait for stock;
- use another compatible GPU already colocated;
- create and populate a new volume in another datacenter, if separately
  approved and feasible;
- remove the persistent-volume requirement only if the workload genuinely does
  not need it.

Trying GPU names in sequence without this intersection wastes time and can
select a machine that cannot see the required data.

## Stop at the paid-compute gate

Present one bounded candidate before creation:

```text
GPU ID/count:
cloud tier/datacenter:
network volume/mount:
image digest/registry ID:
ports and disabled-production mode:
hourly price and maximum duration:
acceptance test:
cleanup plan:
```

Stop when credentials, balance, licensing, image access, volume/data, stock, or
required infrastructure is absent. Operator approval applies to this resource
and lifetime. A rejected create or incorrect Pod does not automatically
authorize another paid attempt.

## Choose an interface by contract coverage

| Interface | Good fit | Required caution |
|---|---|---|
| Console | One-off human deployment and visual log access | Record/re-read the resulting exact fields |
| `runpodctl` | Inventory and straightforward Pod lifecycle | Verify current help and post-create volume/image/termination fields |
| REST | Structured automation against documented v1 resources | Live inventory identifiers can outrun generated enums/clients |
| GraphQL | Exact live schema fields or gaps in another interface | Query only safe fields; schema and docs can differ |
| SDK | Repeated automation with typed/reusable code | Pin/version it and still verify the created object |

The current CLI reference documents Pod creation fields including image,
template, GPU ID/count, cloud type, datacenter IDs, ports, environment,
network-volume ID, mount path, registry-auth ID, CUDA floor, and automatic
termination. The current REST create API documents `networkVolumeId`,
`volumeInGb`, `volumeMountPath`, and registry auth. The live GraphQL schema
documents the same core placement/lifetime fields on its on-demand input.

No interface deserves implicit trust. Prefer the simplest one that expresses
the entire contract, then verify the result.

## Use immutable images and explicit modes

- Pin deployable images by digest. A mutable tag may identify the build for
  humans, but it is not evidence of which bytes ran.
- Keep credentials in provider secrets/registry-auth resources. Do not bake
  private model data or tokens into a public image.
- Make the container entrypoint noninteractive and deterministic. Prompting for
  paths or licenses in a headless Pod is a startup defect.
- Include runtime compilers/system headers when the framework performs JIT
  compilation; a builder-only compiler does not satisfy the runtime contract.
- Persist a small sanitized phase marker before expensive stages and a bounded
  failure marker on exception.
- Set production-disabled mode explicitly. Omission is not a safe default when
  the image has multiple startup modes.

## Network-volume contract

Use one mount owner. When a network volume owns the workload mount, avoid also
requesting a default Pod volume at the same path. Issue #69's successful
GraphQL allocation used:

```graphql
mutation CreatePod($input: PodFindAndDeployOnDemandInput!) {
  podFindAndDeployOnDemand(input: $input) {
    id
    imageName
    networkVolumeId
    volumeInGb
    volumeMountPath
    desiredStatus
    costPerHr
  }
}
```

Its input selected the exact live GPU ID and supplied `networkVolumeId`,
`volumeInGb: 0`, and the intended `volumeMountPath`. This shape was checked
against the live GraphQL schema and worked on 2026-08-24. It is not a promise
that every workload needs zero Pod volume or GraphQL; it is evidence that
storage ownership must be explicit and the result must be checked.

Before startup monitoring, query a Pod representation that includes the
network volume and verify:

- expected network-volume ID is non-null;
- returned volume datacenter matches the allocated machine;
- mount path is exact;
- Pod/default volume size does not shadow or conflict with the mount;
- expected durable files are readable through a safe channel.

If any check fails, preserve safe evidence and delete the incorrect Pod. Do not
wait for application logs from a Pod that cannot meet its storage contract.

## Issue #69 interface mismatch evidence

Observed on 2026-08-24 with `runpodctl` v2.8 and the then-current APIs:

1. A template/CLI create accepted the requested network volume but the returned
   Pod reported `networkVolume: null`. Once the image started, it repeatedly
   failed to create diagnostics under the intended mount.
2. A second CLI create with explicit network-volume and mount flags again
   returned a null attachment and was deleted before startup.
3. Direct REST rejected the live inventory's exact “Server Edition” GPU ID
   because the request schema exposed a shorter enum name.
4. Direct official GraphQL creation expressed the exact inventory GPU and
   network-volume contract; the response and follow-up read confirmed the
   attachment, and the workload passed.

Generalize this to one rule: accepted arguments, templates, client-side enums,
and HTTP success do not prove provider-side realization. Re-read the resource.

## Exact post-create checklist

Before counting startup time, compare:

- [ ] one new Pod ID exists; no accidental duplicate exists;
- [ ] image resolves to the approved digest;
- [ ] GPU ID/count, cloud tier, datacenter, CUDA filter, and hourly cost match;
- [ ] registry-auth ID is correct, without printing its secret;
- [ ] network-volume ID, volume datacenter, mount path, and volume size match;
- [ ] ports/public-IP/global-network settings match;
- [ ] mode flags preserve production-disabled state;
- [ ] provider termination control and local deadline are active;
- [ ] durable evidence paths are on persistent storage when required.

Only after this checklist passes should application startup monitoring begin.

## Official sources

- [RunPod CLI overview](https://docs.runpod.io/runpodctl/overview)
- [`runpodctl pod`](https://docs.runpod.io/runpodctl/reference/runpodctl-pod)
- [`runpodctl user`](https://docs.runpod.io/runpodctl/reference/runpodctl-user)
- [`runpodctl gpu`](https://docs.runpod.io/runpodctl/reference/runpodctl-gpu)
- [`runpodctl datacenter`](https://docs.runpod.io/runpodctl/reference/runpodctl-datacenter)
- [Pod REST create API](https://docs.runpod.io/api-reference/pods/POST/pods)
- [GraphQL Pod management](https://docs.runpod.io/sdks/graphql/manage-pods)
- [Live GraphQL schema](https://graphql-spec.dev.runpod.io/)
- [Network volumes](https://docs.runpod.io/storage/network-volumes)
- [Billing](https://docs.runpod.io/accounts-billing/billing)

All were directly fetched on 2026-08-24. Issue-specific behavior comes from
Robium issue #69 and its dated learning/evidence records, not from upstream
guarantees.
