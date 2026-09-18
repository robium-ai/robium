# STACK-CHAN ER 2 evidence

This card records the STACK-CHAN ER 2 Companion application validated on real
hardware from 2026-09-14 through 2026-09-17. It supports the reusable Gemini
session and tool-boundary guidance; its device limits are not general defaults.

## Observed stack

- `gemini-robotics-er-2-streaming-preview` in one persistent Live API session,
  with automatic voice activity detection over continuous 250 ms microphone
  chunks and text output.
- A Python host process owning the model session, guarded actions, macOS TTS,
  one USB serial request at a time, and an optional dedicated BLE worker.
- M5Stack STACK-CHAN K151 firmware owning the display, servos, microphones,
  speaker, and on-demand 320 by 240 camera capture.
- Six semantic tools: bounded head movement, short display text, bounded speech,
  one fresh `look`, one of five named animations, and enum-only LEGO motion.

## What passed

- Thirty-five hardware-free tests covered the tool allowlist and guards, PCM
  framing, continuous and push-to-talk audio boundaries, inline camera tool
  responses, silent action-only turns, serial framing, BLE selection, and
  confirmed motion-to-stop transmission.
- Real hardware passed display, bounded head motion, microphone capture,
  acknowledged speaker playback, camera capture, and automatic microphone
  resume after half-duplex actions.
- A physical voice turn caused ER 2 to request one image, describe the current
  view, speak through the robot, and resume listening. Ordinary conversation
  did not capture an image.
- A separate end-to-end voice turn selected one bounded LEGO direction; the
  host confirmed the transmitted zero-power revision before returning success,
  while the hub retained an independent 400 ms watchdog.

## What changed after physical evidence

- A `look` image moved from realtime video input into the matching
  `FunctionResponse.parts`. Two opposite views in one session then produced
  answers about the new view rather than stale context.
- Continuous audio and speaker playback became an explicit half-duplex handoff:
  pause input, run the guarded action, wait for device readiness, then resume.
- The LEGO tool is removed from the model declarations when no controller is
  connected; prompt text does not stand in for capability availability.
- Named firmware animations and fixed LEGO directions replaced raw servo modes,
  wheel powers, and durations at the model boundary.

## Limits

- The application continuously sends room audio while running and uses visible
  listening LEDs plus explicit process start/stop rather than a local wake-word
  engine.
- Camera capture is model-selected and single-frame, not a continuous video
  stream. The device temporarily hands shared I2C pins to the camera and then
  restores the audio/display peripherals.
- STACK-CHAN and its LEGO accessory are supervised desktop hardware. These
  results do not establish safe autonomous navigation or manipulation.
