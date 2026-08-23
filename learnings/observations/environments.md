## don't infer a hung RunPod pod from proxy-timing artifacts — verify with ground truth before terminating <!-- id: obs-environments-001 -->
status: absorbed 2026-08-02
proof: 1
signal: user-correction
sources: [lrn-0802-03]
target: environments (new-section) — `references/gpu-cloud.md` has no
  anchors yet (grepped: zero `<!-- id: -->` comments in that file), so this
  is a new-section addition, not an anchor update. Add to the "RunPod
  networking" prose: a cold pull of a large (10-20GB) image plus per-attempt
  proxy-exec round-trips (15-20s each) look identical to a hung container
  from the outside (no "success" log line for many minutes; RunPod
  console's "Jupyter Lab... taking longer than expected" just means nothing
  listens on 8888 yet, not that the container is stuck). Verify with a
  ground-truth channel — RunPod's Web Terminal (independent of the pod's
  own entrypoint/sshd config) — before terminating or recreating a pod on a
  hang guess; a wrong guess costs a real pod + re-pull.
evidence: symptom verbatim ✓ (user: "this is your second time terminating
  the pod") · assistant's own admission is the passing "check" that the
  correction was accepted ✓ ("I don't actually have proof it was hung ...
  that's the mistake you caught") · dead-end named ✓ (inferring hang from
  log-timing + console Jupyter-init message). signal=user-correction alone
  clears the ready bar; the 3-part evidence also holds.

## verify first-run setup with explicitly cold caches <!-- id: obs-environments-002 -->
status: ready
proof: 1
signal: better-method
sources: [lrn-0817-15]
target: environments#clean-room-cache-caveat (update) — copy the project into a clean directory, empty the relevant package/model caches, and run the complete setup path before claiming first-run reproducibility
evidence: the warm development machine could pass while hiding broken fetch and setup behavior ✓ · an rsync clean copy with empty HF_HOME passed doctor, build, contract, dataset, tests, demo smoke, simulation, and playback including the first pinned-revision pull ✓ · rerunning only in the cached working tree was ruled out ✓
