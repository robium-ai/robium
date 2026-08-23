## verify dataset scene identity with a stable camera, not schema alone <!-- id: obs-data-001 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0817-07, lrn-0817-08]
target: data#verify-embodiment-match-before-committing (update) — require a scene-level check against a static reference camera when feature shapes and task labels cannot distinguish environment variants
evidence: two schema-compatible datasets rendered visibly different scenes ✓ · the selected static overhead-camera comparison accepted the matching dataset at 0.0023 and rejected the alternate under a 0.05 tolerance ✓ · comparing the randomized wrist camera and loosening its tolerance were ruled out ✓

## generate demonstrations in the pinned environment when no published dataset matches <!-- id: obs-data-002 -->
status: ready
proof: 1
signal: figured-out-from-scratch
sources: [lrn-0817-16]
target: data#offline-first-search-before-collect (update) — after a documented search finds no dataset for the exact scene and control contract, generate demonstrations inside the pinned application environment and retain only successful episodes
evidence: the Hub survey found no stock-scene dataset larger than ten episodes and no trained policy ✓ · the in-app scripted expert recorded demonstrations that replayed successfully under the app's own control mode ✓ · adopting larger datasets from neighboring scenes and forking a mismatched environment were ruled out ✓
