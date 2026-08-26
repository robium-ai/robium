## assert meaningful image pixels instead of treating HTTP success as visual proof <!-- id: obs-testing-001 -->
status: ready
proof: 1
signal: better-method
sources: [lrn-0817-13]
target: testing#test-at-right-layer-not-everything-in-sim (update) — for camera-driven demo smoke tests, fetch the returned image payload and assert it is neither black nor a flat fill
evidence: endpoint and status-string checks passed while the primary viewer displayed nothing ✓ · mean-greater-than-20 and standard-deviation-greater-than-5 assertions passed for both live and recorded camera sources in a clean checkout ✓ · HTTP 200 and status-copy checks alone were ruled out as visual evidence ✓

## rebuild the deployment image after gateway lifecycle changes <!-- id: obs-testing-002 -->
status: ready
proof: 2
signal: verified
sources: [lrn-0825-08, lrn-0826-03]
target: testing#gate-paid-remote-run-behind-free-dry-run (update) — after gateway lifecycle changes, rebuild the deployment-platform fake image and exercise allocation, capability isolation, one rollout, deletion, and zero-resource cleanup before a paid remote smoke
evidence: the earlier local and first paid images predated ready-window termination behavior ✓ · the rebuilt Linux/amd64 fake image passed the free lifecycle, then the exact replacement GPU digest exposed `remaining_s`, completed a genuine rollout and active cancellation, and left zero Pods ✓ · reusing a stale pre-change digest or changing the immutable evaluation pointer was ruled out ✓
