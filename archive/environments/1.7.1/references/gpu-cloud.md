# GPU-cloud environments (RunPod first, hyperscalers behind a quota gate)

When a project needs a real NVIDIA GPU that the dev machine doesn't have
(Isaac Sim / Isaac Lab, GR00T, heavy CUDA training), the environment is a
cloud GPU that you drive as a thin client. This reference owns the
cross-cutting GPU-cloud / RunPod networking facts for robium; other skills
cite environments for them. Battle-tested on go2-locomotion (Isaac Lab,
2026-07-26..28).

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

## Provider choice: RunPod first

For a reference app that only needs a few GPU-hours, **RunPod is the default
low-friction provider**: no quota gate, and a pod is live in ~1 minute.
Keep GCP / AWS as ecosystem alternatives, but flag their quota gate; for a
short job they lose to RunPod on time-to-first-GPU.

### GCP GPU quota gotchas (if you must use GCP)

- The binding quota is the **global `GPUS_ALL_REGIONS`** metric, not the
  per-region one (e.g. `NVIDIA_L4_GPUS`). GCP enforces both; the lower one
  binds, so a per-region grant is useless if the global is still 0.
- A well-formed `GPUS-ALL-REGIONS` increase request can be **auto-denied in
  under a second** on a young project with no billing history; Google
  Support confirmed this is account-standing, not a malformed request.
  Budget 2+ days of lead time, or use a no-quota provider (RunPod).
- Diagnose current quota programmatically via the Cloud Quotas API
  (`quotaPreferences`).

## RunPod networking (the important part)

RunPod's convenience hides several sharp edges. Expose things correctly up
front and you avoid a day of dead-end debugging.

### The HTTP proxy can be silently dead

`{podId}-{port}.proxy.runpod.net` will complete a TLS handshake but the
backend never answers: `curl` returns **HTTP 000** while the same service
on the pod's localhost returns 200. Don't trust the proxy as proof the
service is down; test on localhost inside the pod first.

### Real exposure = public IP + a directly-exposed TCP port

- SSH `-L` port-forwarding does **NOT** work: RunPod's SSH is `docker exec`,
  not a real `sshd`, so there's no forwarding channel.
- The working exposure is the **pod's public IP + a directly-exposed TCP
  port**. Non-root processes can only bind ports **>1024**, so port 22 is
  out for a non-root service.
- Reading the failure: **"connection refused"** = the mapping is fine but
  nothing is listening; **timeout** = there's no route to that port at all.
- **Ports are FIXED at pod creation**; you cannot add one to a running pod.
  Expose everything you might need (SSH-alt, app port, an 8888 http port for
  file pulls) *up front*.

### Driving the pod over proxy SSH

- Proxy SSH **ignores a command passed as an argument** (it just looks like
  a hang). Pipe the command to stdin instead:

  ```bash
  printf 'cmd\nexit\n' | ssh -tt <podHostId>@ssh.runpod.io -i key
  ```

  The `podHostId` is the proxy SSH username.
- The container only needs to be **RUNNING**; no sshd install required.
  Keep it alive with `dockerEntrypoint: ["/bin/sleep"]` and
  `dockerStartCmd: ["infinity"]`.

### Data-center selection (REST vs GraphQL mismatch)

- `dataCenterIds` in the REST API are a **subset** of the GraphQL list:
  `US-CA-1` / `US-OR-*` are **invalid in REST**; `US-CA-2` / `US-WA-1` are
  valid.
- L4 + public-IP capacity is scarce in US-west, so a request there often
  returns **500 "could not find any pods with required specifications"**.
  Pass a **west-first array** of data centers so RunPod can fall through.

### File transfer

- Use `runpodctl send` / `runpodctl receive` (~2-3 MB/s). SCP is
  **unsupported** over proxy SSH.
- Alternatively pull artifacts over HTTP: run `python3 -m http.server 8888`
  **in the foreground** on an 8888/http proxy port and fetch from your
  machine. It must be foreground; `nohup` / `disown` / `setsid` all fail
  because session teardown SIGKILLs the whole process tree. Because the
  server has to stay foreground, that's another reason to expose the 8888
  port at pod creation.
