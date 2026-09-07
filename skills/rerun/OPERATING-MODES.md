# Rerun operating modes

Use the current SDK documentation and installed API as the source of truth.
The shapes below explain the decision; they do not freeze signatures.

## Local viewer

- `rr.init(..., spawn=True)` is appropriate when the producer has a local
  desktop and the run is exploratory.
- `spawn()` is the wrong default on a headless server. A display failure says
  nothing about the validity of the recording.

## Separate or remote viewer

- A producer can connect to an already-running viewer, or host a gRPC recording
  that a viewer connects to later.
- A browser-facing viewer is useful when installing a native viewer is not
  practical. Treat its bind address, exposed port, authentication, and retained
  history as service concerns.
- Rerun's served recording may buffer history for late clients. Set an
  intentional memory limit for long-running or high-bandwidth streams.
- LeRobot's distant dataset-viewer mode follows this same producer/server and
  remote-client shape; prefer its wrapper for LeRobot episodes.

## File output

- Save `.rrd` for CI, offline inspection, comparisons, and handoff.
- Record the application/schema version and the input revision beside the file
  when the recording is a test or experiment artifact.
- Prefer file output over opening a viewer in unattended jobs.

## Timelines and paths

- Use a sequence timeline for ordered episode steps and a timestamp/duration
  timeline when real timing matters. Do not infer alignment from logging order
  across concurrent producers.
- Static entities follow latest-at semantics and need not be logged at every
  step.
- Group paths by stable concepts such as `robot/camera`, `robot/state`,
  `policy/action`, and `world`; adapt this to the application's real hierarchy
  rather than copying the names literally.

## Version-sensitive failures

- If an archetype or time API is missing, inspect the installed SDK and its
  migration notes. Robium's 0.34.1 application used plural `rr.Scalars` and
  `rr.set_time(..., sequence=...)`; these are evidence for that pin, not a
  promise about another version.
- The Python SDK bundled the viewer in that application; C++ and Rust paths
  required a separately installed CLI. Verify the current packaging before
  depending on it.
