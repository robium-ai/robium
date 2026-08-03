# Prebuilt Isaac Lab image + RunPod provisioning

The battle-tested way to get Isaac Lab onto a cloud GPU without the
version-pairing trap or a source install: pull NVIDIA's prebuilt Isaac Lab
container, which bundles a matched Isaac Sim + Isaac Lab in one image.
Observed on a RunPod L4 pod running the go2-locomotion app, 2026-07-26..28.

## Prefer the prebuilt image over source install

- **Image:** `nvcr.io/nvidia/isaac-lab`, latest tag observed
  **3.0.0-beta2-post1** (observed on the NGC catalog 2026-07-26..28). It
  ships a matched Isaac Sim + Isaac Lab together, so it sidesteps the
  Isaac-Sim/Isaac-Lab version-pairing trap (see the skill's Platform
  gotchas) and the multi-step source install entirely — no
  `pip install isaacsim` + `./isaaclab.sh --install` on top.
- **Observed pod environment** (state as observed, not as a floor —
  re-verify per pod): NVIDIA driver **580.159.04**, Python **3.12.13**.
  Note the driver is what the pod host happened to ship; it is not the
  Isaac Sim standalone minimum the sibling `isaac-sim` skill records.
- The image is Isaac Lab pip-installed into the container, which has a
  downstream consequence for custom tasks — see the external-project note
  in the go2-rl-workflow reference.

## Provisioning specifics (RunPod)

- **NGC pull auth.** The image lives on NGC, so the pod needs registry
  credentials — supply them through RunPod's `containerRegistryAuth`
  (an NGC API key), not a bare public pull.
- **EULA / privacy env vars.** Set `ACCEPT_EULA=Y` and
  `PRIVACY_CONSENT=Y` in the pod's environment or the container refuses to
  start, the same gate the `isaac-sim` container uses.
- **Volume-shadow gotcha (the one that hides Isaac Lab).** RunPod's default
  persistent volume mounts at `/workspace`. The prebuilt image places
  Isaac Lab under `/workspace` too, so the volume mount *shadows* the
  bundled install — Isaac Lab appears to vanish. Fix: set the pod's
  `volumeMountPath` to a non-`/workspace` path (e.g. `/data`) so the
  persistent volume and the bundled Isaac Lab don't collide.
- **Custom-image entrypoint (dockerStartCmd becomes ARGS).** The image
  defines its own `ENTRYPOINT`, which means RunPod's `dockerStartCmd` is
  passed to that entrypoint as *arguments*, not run as a shell command —
  so a shell one-liner in `dockerStartCmd` silently does the wrong thing.
  Override `dockerEntrypoint` to `["/bin/bash","-lc"]` so the start command
  runs as a shell. After changing entrypoint/args, **stop then start** the
  pod — RunPod's `/restart` returns HTTP 500 for this change; a clean
  stop→start applies it.

## Pod networking and SSH are the environments skill's territory

Pod port exposure, the dead RunPod proxy, SSH-exec limits, datacenter
enumeration, and `runpodctl` are general RunPod/GPU-cloud mechanics owned by
the `environments` skill's GPU-and-remote reference — do not re-derive them
here. This reference covers only what is Isaac-Lab-image-specific on top of
that groundwork (the auth, EULA, volume-shadow, and entrypoint items above).
