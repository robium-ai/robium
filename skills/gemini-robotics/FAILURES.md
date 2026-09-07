# Gemini Robotics streaming failures

Start with the first missing event in the session rather than rewriting the
prompt.

## The session stops after a tool call

- The Live API does not execute or answer functions automatically. Build a
  `FunctionResponse` for every requested call and send the complete response
  list with `send_tool_response`.
- Preserve each call's ID and name. A robot action completing locally does not
  unblock the model until its response reaches the session.
- Keep the receive loop alive after the response; one tool result may lead to
  another tool call before the turn completes.

## Physical actions overlap or the model plans from an unfinished action

- Confirm every physical function declaration uses `behavior: BLOCKING`.
- Do not report success when an action was only accepted. Wait for its terminal
  result or return an explicit timeout/failure.
- Keep asynchronous/non-blocking tool behavior out of the physical-action path
  even when another Live model supports it.

## The model sees frames but does not react

- Video input alone does not initiate a reasoning turn. Send user text/audio or
  a deliberate heartbeat after the latest frame.
- Respect the current JPEG rate limit. Dropped or delayed frames can otherwise
  look like a reasoning failure.
- Heartbeats can interrupt an in-progress response. Serialize them with turns
  when interruption is not the intended behavior.

## The next decision describes the old scene

- Capture after the robot action reaches a terminal state and send that fresh
  frame before asking for the next decision.
- Attach timestamps or freshness metadata at the camera/adapter boundary. Do
  not infer freshness from a non-empty JPEG.
- Keep camera acquisition outside the cloud receive loop so a stalled camera
  cannot silently stall tool-response delivery.

## Audio input never completes

- Confirm raw signed 16-bit mono PCM, little-endian, at 16 kHz and the matching
  MIME type.
- Preserve sample alignment when chunking; every chunk must contain an even
  number of bytes.
- Send `audio_stream_end=True` for a finite utterance. For continuous listening,
  configure turn detection deliberately instead of sending arbitrary file
  boundaries.

## No speech comes from the robot

- Gemini Robotics ER 2 Streaming produces text output. Feed completed text to
  a TTS adapter or let the model call a bounded `speak` tool.
- Keep TTS failure separate from motion completion so audio-device trouble
  cannot make a successful navigation action appear failed.

## A model-generated action bypasses robot constraints

- Treat this as a missing application guard, not a prompt-tuning problem.
- Reject unknown functions, extra arguments, unconfigured waypoints, out-of-
  range values, and object identifiers not issued by current perception.
- Make stop/cancel callable by the host on deadline or disconnect. The model
  must not be the only component able to stop motion.

Re-check the current [Live API tool guide](https://ai.google.dev/gemini-api/docs/live-api/tools)
when message fields or function-calling behavior differ from the application.
