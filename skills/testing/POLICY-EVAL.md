# Learned-policy test patterns

## Pipeline smoke

- For training-pipeline changes, train at tiny scale, then run a few deterministic evaluation
  episodes.
- For an inference-only demo, reuse the pinned pretrained checkpoint and one
  bounded existing inference path. Do not train, add a harness, or run a
  multi-seed evaluation merely to demonstrate bring-up. One rollout is not a
  policy-reliability claim.
- Assert completion, expected artifacts, schemas, and numeric metrics.
- Do not require a success threshold from an intentionally undertrained policy.
  Robium's 2026-07-12 manipulation trial legitimately scored zero while still
  proving the pipeline worked.

## Regression gate

- Use a pinned known-good checkpoint, fixed environment and dataset revisions,
  deterministic seeds, a bounded episode set, and a stated threshold.
- Record per-episode results and aggregate the metric the product claim uses.
- Keep broad multi-task or multi-seed qualification separate from the quick
  default gate.

## Benchmarks are different

- A benchmark measures latency, memory, throughput, or quality across a broader
  matrix. It does not become a regression test merely because pytest launches
  it.
- Mark expensive benchmark work slow or otherwise exclude it from the default
  suite. One Robium suite grew from roughly 3.5 to 8 minutes when a large-model
  benchmark ran on every push.
- When first-use compilation dominates, report it separately from steady-state
  measurements.

## Harness guards

- Fail when zero devices, episodes, or samples were measured. A per-device
  exception loop can otherwise exit zero with no evidence; Robium observed this
  during a transient Hugging Face 401.
- Import configuration constants when they are the subject of the assertion.
  Re-typing their rendered values can leave a stale test green after the source
  changes.
- Verify artifacts independently after the run; do not treat a final log line
  as the sole success signal.

## Before paid or remote evaluation

- Run the same path locally with tiny data and CPU where possible.
- Pin the immutable image, checkpoint, dataset, framework, device, seed, and
  stop condition.
- Bound cost and lifetime, then preserve result artifacts before cleanup.
- Provider allocation and cleanup belong to its owning provider skill.
