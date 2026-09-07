# Silly TurtleBot evidence

This card records one Robium application run on 2026-09-07. It is evidence for
the narrow Gemini Robotics integration path, not a universal robot design.

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
- Six hardware-free tests covered the comedy mission, action guard, audio
  framing, manual Live API tool mediation, post-action camera forwarding, and
  the HTTP adapter.
- An unrecognized `publish_cmd_vel` call was returned to the model as rejected.
- The Gazebo Harmonic TurtleBot 4 runtime exposed both Nav2 actions and a fresh
  simulated OAK-D JPEG; a real Nav2 quarter-turn completed successfully.

## What the app changed after implementation evidence

- Tool schemas remained semantic and blocking; the independent guard enforced
  exact arguments, named waypoints, ranges, and latest-scan object IDs.
- A successful look action caused the robot adapter to fetch and queue a fresh
  JPEG, which the receive loop streamed before the next model decision.
- A model-turn deadline invoked the same stop path available to the operator.
- Text-to-speech stayed behind a replaceable adapter because the endpoint's
  output modality is text.

## Not yet proven

- The ROS bridge, OAK-D topics, speaker, and cancellation path have not been
  exercised on the physical TurtleBot 4.
- A complete Gemini-driven navigation turn has not yet been rehearsed against
  the Gazebo robot; the live-model and simulated-motion acceptance checks were
  run separately.
- RGB-depth grounding of floor objects and person detection remain application
  work, so this skill does not prescribe either pipeline.
