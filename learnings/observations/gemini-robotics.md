## bind tool-requested images to the matching function response <!-- id: obs-gemini-robotics-001 -->
status: absorbed 2026-09-17
proof: 1
signal: better-method
sources: [lrn-0917-01]
target: gemini-robotics (update) — attach an observation tool's fresh image to its `FunctionResponse` when supported instead of relying on realtime-media ordering
evidence: stale same-session scene reasoning reproduced ✓ · two opposite physical views were described correctly after binding the image to the response ✓ · adjacent realtime input and per-view session resets were ruled out ✓

## half-duplex audio requires an application-owned device handoff <!-- id: obs-gemini-robotics-002 -->
status: absorbed 2026-09-17
proof: 1
signal: better-method
sources: [lrn-0917-02]
target: gemini-robotics (update) — pause microphone ingestion around device speech/actions and resume from deterministic hardware readiness
evidence: shared microphone/speaker mode produced a concrete concurrency boundary ✓ · repeated physical speech and vision turns resumed continuous listening ✓ · prompt-only serialization and unsupported full duplex were ruled out ✓

## tool declarations must follow connected capability preflight <!-- id: obs-gemini-robotics-003 -->
status: absorbed 2026-09-17
proof: 1
signal: better-method
sources: [lrn-0917-03]
target: gemini-robotics (update) — remove disconnected hardware capabilities from the model-visible tool list
evidence: optional LEGO startup created a real availability branch ✓ · connected and no-LEGO tool-list tests plus physical voice motion passed ✓ · runtime rejection and prompt-only discouragement were ruled out ✓
