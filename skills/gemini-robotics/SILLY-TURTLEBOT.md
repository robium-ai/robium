# Silly TurtleBot evidence

This card records one Robium application developed from 2026-09-07 through
2026-09-14. It is evidence for the narrow Gemini Robotics integration path, not
a universal robot design.

## Observed stack

- Python 3.10 with `google-genai>=2.22.0,<3`.
- `gemini-robotics-er-2-streaming-preview` through
  `client.aio.live.connect`, with text output and manual function responses.
- A cloud-side agent calling a loopback HTTP adapter; a ROS 2 process owned
  Nav2 actions, camera subscriptions, cancellation, and TTS.
- Semantic tools for named navigation, bounded quarter-turn inspection,
  approaching a perception-issued object ID, facing a person without
  approaching, speaking, and stopping.

## What passed

- A live model turn called a guarded fake-robot tool successfully.
- Thirteen hardware-free tests covered the mission guard, audio framing, manual
  Live API tool mediation, persistent-session reuse, heartbeat filtering, SSE
  replay, cancellation, terminal response ordering, camera flow, and the HTTP
  adapter.
- An unrecognized `publish_cmd_vel` call was returned to the model as rejected.
- The Gazebo Harmonic TurtleBot 4 runtime exposed Nav2 actions and a fresh
  simulated OAK-D JPEG; forward and quarter-turn actions completed.
- The physical TurtleBot 4 smoke verified ROS/Nav2 state, fresh full-resolution
  OAK-D frames, a separate low-bandwidth operator preview, and bounded neural
  speech without commanding an autonomous mission.

## What the app changed after implementation evidence

- Tool schemas remained semantic and blocking; the independent guard enforced
  exact arguments, named waypoints, ranges, and latest-scan object IDs.
- A successful look action caused the robot adapter to fetch and queue a fresh
  JPEG, which the receive loop streamed before the next model decision.
- A model-turn deadline invoked the same stop path available to the operator.
- Text-to-speech stayed behind a replaceable adapter because the endpoint's
  output modality is text.
- The long-lived session kept local tool progress and camera frames flowing
  during blocking motion, but withheld model-facing heartbeats until the tool
  response and turn were resolved.

## Not yet proven

- A complete Gemini-driven navigation mission has not yet been repeated three
  times on the physical TurtleBot 4 under supervision.
- RGB-depth grounding of floor objects and person detection remain application
  work, so this skill does not prescribe either pipeline.
