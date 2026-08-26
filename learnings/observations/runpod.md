## atomic reservations keep a public GPU demo inside its daily cap <!-- id: obs-runpod-001 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0825-07]
target: runpod (new-section) — reserve conservative per-session cost in an external generation-conditional ledger before Pod creation, reconcile only owned Pod IDs to final billing, and fail closed on write conflicts
evidence: the broad storage SDK introduced a moderate production audit finding ✓ · direct authenticated GCS JSON API generation reads and `ifGenerationMatch` writes passed success and HTTP-412 conflict tests with a 0-vulnerability production audit ✓ · unconditional overwrite and the unnecessary broad SDK were ruled out ✓
