# STACK-CHAN ER 2 learnings, 2026-09-17

- [gemini-robotics] better-method <!-- id: lrn-0917-01 -->
  symptom: Realtime video sent immediately before a `look` tool response was not deterministically associated with that call, so a later visual question could reuse an older image from the same Live session.
  root-cause: Realtime media and tool responses are independent streams; temporal adjacency is not an ownership contract.
  fix: Attached the fresh JPEG as inline media in the matching `FunctionResponse.parts`. (check: the endpoint accepted the response and two opposite physical views in one session produced descriptions of the new view; a regression test asserts that `look` sends no realtime-video message.)
  dead-ends: Sending the image just before the response; starting a new model session for every view; continuously streaming a camera that is needed only on request.
  target: gemini-robotics — bind tool-requested observations to their function response
  source: robium-apps/stackchan-er2/src/stackchan_er2/agent.py and tests/test_agent.py (2026-09-17)

- [gemini-robotics] better-method <!-- id: lrn-0917-02 -->
  symptom: STACK-CHAN's microphone and speaker share a half-duplex device path, so leaving audio ingestion active across physical actions could race device mode changes or feed playback back into the model.
  root-cause: The model stream and the device audio lifecycle have different concurrency rules.
  fix: Paused microphone chunks around guarded device actions, waited for the action and hardware readiness, then resumed the continuous loop explicitly. (check: physical mic → ER 2 → onboard speech and vision turns resumed listening cleanly; continuous and push-to-talk boundaries are covered by tests.)
  dead-ends: Treating model turn completion as device readiness; relying on the prompt to avoid overlap; full-duplex playback on hardware that cannot support it.
  target: gemini-robotics — keep half-duplex device handoff outside the model
  source: robium-apps/stackchan-er2/src/stackchan_er2/agent.py and device.py (2026-09-17)

- [gemini-robotics] better-method <!-- id: lrn-0917-03 -->
  symptom: Advertising the LEGO motion tool when its BLE controller was absent gave the model a capability the running application could not fulfill.
  root-cause: A static tool list described the product rather than the capabilities that passed startup preflight.
  fix: Derived function declarations from the connected capability set and removed `drive_lego` under `--no-lego`. (check: the no-LEGO tool-list test passes and the combined physical voice turn selected one bounded direction only when the controller was connected.)
  dead-ends: Keeping the unavailable tool and returning runtime failures; telling the model in prose not to call it; allowing raw wheel power or duration.
  target: gemini-robotics — advertise only preflighted physical capabilities
  source: robium-apps/stackchan-er2/src/stackchan_er2/agent.py and tests/test_agent.py (2026-09-17)
