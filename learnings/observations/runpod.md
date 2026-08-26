## atomic reservations keep a public GPU demo inside its daily cap <!-- id: obs-runpod-001 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0825-07]
target: runpod (new-section) — reserve conservative per-session cost in an external generation-conditional ledger before Pod creation, reconcile only owned Pod IDs to final billing, and fail closed on write conflicts
evidence: the broad storage SDK introduced a moderate production audit finding ✓ · direct authenticated GCS JSON API generation reads and `ifGenerationMatch` writes passed success and HTTP-412 conflict tests with a 0-vulnerability production audit ✓ · unconditional overwrite and the unnecessary broad SDK were ruled out ✓

## exact RunPod inventory and volume contracts may require GraphQL creation <!-- id: obs-runpod-002 -->
status: ready
proof: 2
signal: figured-out-from-scratch
sources: [lrn-0824-25, lrn-0826-01]
target: runpod#verify-created-pod-contract (update) — when REST rejects an exact live inventory ID or cannot preserve the network-volume contract, use the authenticated GraphQL create mutation, keep its credential-bearing URL out of logs, and safe-field re-read the complete Pod contract before monitoring
evidence: REST rejected the exact Server Edition ID and earlier CLI Pods omitted the volume ✓ · GraphQL Pods twice attached the exact GPU/image/region/volume contract and passed genuine episodes ✓ · REST retry, Bearer-only GraphQL authentication, and trusting accepted create inputs without re-read were ruled out ✓
