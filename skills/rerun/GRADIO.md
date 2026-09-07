# Rerun inside Gradio

Use this only when the application needs an embedded Rerun viewer. A standalone
viewer or saved recording is simpler for ordinary debugging.

## Tested application shape

- Robium's 2026-07-15 VLA trial used `gradio_rerun` with a Rerun
  `RecordingStream` and `binary_stream`, yielding chunks from `stream.read()`
  into a streaming viewer component.
- The Gradio application was mounted into FastAPI. This kept simulation or
  policy execution separate from the web route while the component consumed
  recording bytes.
- JPEG-compressing browser-bound image logs materially reduced bandwidth in
  that application.

## Dependency boundary

- `lerobot[viz]==0.6.0` required a Rerun SDK below 0.34, while
  `gradio_rerun==0.34.1` required exactly 0.34.1. The resolver could not satisfy
  both.
- That application dropped LeRobot's `viz` extra and pinned the SDK required by
  the Gradio component. Re-resolve against current package metadata; do not
  preserve these old pins as universal defaults.
- Keep the Rerun SDK and embedded component on compatible versions. Verify a
  minimal streaming render before integrating the robot workload.
