# Cloud-GPU environment boundary and hyperscaler quota gates

When a project needs a real NVIDIA GPU that the dev machine doesn't have
(Isaac Sim / Isaac Lab, GR00T, heavy CUDA training), the environment is a
cloud GPU that you drive as a thin client. This reference owns the environment
boundary and hyperscaler quota context. Use the `runpod` skill for RunPod
inventory, provisioning, storage, networking, diagnostics, billing, and
cleanup. Battle-tested on go2-locomotion (Isaac Lab, 2026-07-26..28).

## The one genuine exception to virtual-first local==remote

Robium's default is virtual-first with a local==remote parity guarantee.
Some GPU apps have **no local mirror on a Mac at all**:

- Isaac Sim / Isaac Lab (Omniverse Kit) needs NVIDIA RTX + CUDA on Linux or
  Windows; there is no macOS path, and Docker can't pass through a GPU the
  Mac doesn't have.
- Same class: GR00T and other heavy-CUDA training stacks.

For these, the Mac is a **thin SSH/browser client** and the sim/training
runs entirely on a cloud GPU. State this explicitly in the architecture
brief; it's the sanctioned exception to the local==remote rule, not a
parity failure to fix.

## Choose a provider after defining the environment contract

First pin the image/CUDA contract, GPU floor, storage, network exposure,
budget, and acceptance test. Then compare live provider capacity and quota.
Do not state stock, price, or time-to-first-GPU from memory. RunPod-specific
selection and paid-compute gates live in the `runpod` skill.

### GCP GPU quota gotchas (if you must use GCP)

- The binding quota is the **global `GPUS_ALL_REGIONS`** metric, not the
  per-region one (e.g. `NVIDIA_L4_GPUS`). GCP enforces both; the lower one
  binds, so a per-region grant is useless if the global is still 0.
- A well-formed `GPUS-ALL-REGIONS` increase request can be **auto-denied in
  under a second** on a young project with no billing history; Google
  Support confirmed this is account-standing, not a malformed request.
  Budget 2+ days of lead time or choose a provider whose current account and
  capacity checks satisfy the workload.
- Diagnose current quota programmatically via the Cloud Quotas API
  (`quotaPreferences`).

## Provider handoff

- RunPod inventory, exact GPU/datacenter selection, network volumes, Pod
  creation, proxy/SSH behavior, interactive diagnostics, billing, and cleanup:
  use the `runpod` skill and verify its current official sources.
- Google Cloud Run deployment: use the `cloud-run` skill.
- Framework-specific cloud-image and runtime mechanics stay with the framework
  skill, such as `isaac-lab` or `lerobot`.

The environment contract remains provider-independent: a pinned image or lock,
explicit CUDA/architecture floor, no host-only paths, headless operation,
durable evidence, and a documented exception when no local mirror exists.
