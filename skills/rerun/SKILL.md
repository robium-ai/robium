---
name: rerun
version: 1.2.2
description: >
  Rerun for data-centric robotics and ML visualization: logging APIs
  (Python), timelines, entity paths, and viewing policy rollouts, episode
  data, and sensor streams. Use when: 'rerun', visualizing ML training/eval
  rollouts, LeRobot episode data, or custom sensor pipelines outside ROS
  tooling. Defers heavily to Rerun's official examples and docs; check them
  before writing logging code. Pairs with lerobot and data. Not for: live
  ROS topic debugging (rviz2, foxglove).
---

# rerun

The data-centric visualization tool for robium's ML/non-ROS side: a
timeline-and-entity-path logging model (Python-first via `rerun-sdk`,
`pip install rerun-sdk` / `uv add rerun-sdk`, currently at **0.34.1** as of
2026-07-10; verified via direct fetch of `github.com/rerun-io/rerun`'s
release page) for policy rollouts, LeRobot episode data, and arbitrary
sensor streams that don't fit ROS message types. This skill deliberately
stays thin: Rerun's own logging API surface (which archetype for which data
shape, exact keyword arguments) changes across releases, and its own
getting-started docs and example gallery are the actual source of truth;
this skill's job is orientation (what the pieces are called, how the
operating modes map to robium's local/remote needs) and the hand-off into
`lerobot` for episode visualization, not a re-implementation of Rerun's own
tutorials.

## When to use this skill

- Logging and viewing ML rollouts, sensor streams, or embeddings/tensors
  outside ROS's message-type world; visualizing a LeRobot dataset episode.
- The trigger phrases in the description: 'rerun', visualizing ML
  training/eval rollouts, LeRobot episode data, custom sensor pipelines
  outside ROS tooling.
- Before writing any `rr.log(...)` call for a new data shape, check
  Rerun's own examples first (see Key directives); this skill's job is
  pointing there, not supplying every archetype from memory.
- Cross-references: go to the sibling skill instead when the question is:
  - LeRobot dataset mechanics themselves (the `LeRobotDataset` format,
    loading/recording, training/eval CLI) → `lerobot`. This skill only
    covers viewing an episode once `lerobot` has one to show, not the
    dataset format itself.
  - Live ROS 2 topic debugging with a local display → `rviz2`.
  - Live ROS 2 topic debugging remote/headless, or MCAP recording →
    `foxglove`.
  - Deciding *which* dataset to source in the first place → `data`.
  - Choosing which viz tool fits the situation at all → `visualization`
    (routes here once Rerun is the right choice).

## Key directives

- **Delegation posture: point-upstream (delegate-leaning).** Rerun ships
  its own extensive example gallery and API reference at `rerun.io/docs`
  and `rerun.io/examples`, and the archetype/API surface has moved release
  to release (see the SDK's own migration guides). Check those before
  writing logging code for a new data shape; treat this skill as an
  index into them, not a replacement.
- **Never re-teach LeRobot dataset mechanics here.** `lerobot`'s
  `lerobot-dataset-viz` command already wraps Rerun for episode
  visualization end to end (see Usage patterns); this skill's job is
  receiving that hand-off (what the Rerun-specific pieces mean once the
  command is running), not duplicating `lerobot`'s dataset/CLI docs.
- **Pick the operating mode by where the viewer needs to be, not by
  habit.** <!-- id: pick-operating-mode-by-location --> Rerun's Python SDK supports several distinct sinks
  (`rr.spawn()`, `rr.connect_grpc()`, `rr.save()`,
  `rr.serve_grpc()`/`rr.serve_web_viewer()`, `rr.stdout()`): local
  interactive work, a separately-running viewer, a file for later, and a
  browser-accessible remote view are different modes, not variations of
  the same one. See Usage patterns and Rerun's own [operating modes
  docs](https://rerun.io/docs/reference/sdk/operating-modes) (the 2026-07-10 session's
  content came via search-synthesis, not a direct fetch; the URL 404'd; see
  References; re-verify before relying on the exact operating-mode list)
  before defaulting to `spawn()` on a headless box (it will fail; there's
  no local display to spawn a viewer window on).
- **Never write archetype names, constructor arguments, or CLI flags from
  memory.** <!-- id: no-archetype-facts-from-memory --> The archetype list (`Points3D`, `Image`, `Scalars`,
  `Transform3D`, and others) and their exact fields change across
  releases; verify against the `rerun.io/docs` quick-start/data-in pages or
  the `rerun-io/rerun` GitHub repo (fetched directly on 2026-07-10 for these
  facts) before repeating a specific call signature in a real project.

## Quick start

**1. Install:** <!-- id: install-rerun-sdk -->

```bash
uv add rerun-sdk
```

**2. Log something and view it locally** <!-- id: log-and-view-locally -->: `spawn=True` starts a Viewer
process and streams to it over gRPC:

```python
import rerun as rr

rr.init("my_app", spawn=True)
rr.log("world/points", rr.Points3D(points, colors=colors, radii=0.05))
```

**3. For anything beyond a first smoke test** (a new data shape, a
timeline, a blueprint/layout), go to [Rerun's Python quick-start
docs](https://rerun.io/docs/getting-started/quick-start/python) and
[example gallery](https://rerun.io/examples) before hand-writing more
`rr.log()` calls; see Key directives.

## Usage patterns

**Log a simple stream.** <!-- id: log-simple-stream-entity-paths --> `rr.init(app_id, spawn=True)` opens a local
viewer; each `rr.log(entity_path, archetype)` call writes one entity at the
current time. Entity paths (e.g. `"robot/camera/image"`) form a hierarchy
that drives the viewer's tree and default layout; group related data
under a common path prefix rather than flat, unrelated names. For anything
with a time axis beyond wall-clock logging order, set an explicit timeline
first: `rr.set_time("episode_step", sequence=i)` (or `duration=`/`timestamp=`
for the other timeline kinds) before the `rr.log()` calls for that step;
Rerun uses "latest-at" semantics, so static data logged once at the start
persists across the whole timeline without re-logging it every step. See
the quick-start link above for the current archetype list.

**Visualize a LeRobot episode.** <!-- id: visualize-lerobot-episode --> Don't hand-roll this: `lerobot` already
wraps Rerun for exactly this case:

```bash
lerobot-dataset-viz --repo-id=<id> --episode-index=0
```

This is the `lerobot` skill's command, cross-referenced here because it's
the primary way most robium projects will ever invoke Rerun directly. The
entity paths and layout it produces are LeRobot's own convention (camera
streams, state/action vectors, per-episode structure); inspect what it
logs before adding custom `rr.log()` calls alongside it, rather than
guessing the path scheme.

**Remote viewer.** <!-- id: remote-viewer-grpc --> Two shapes, matching `lerobot-dataset-viz`'s own
`--mode distant` flag: either start a gRPC server in the logging process
(`rr.serve_grpc()`, optionally paired with `rr.serve_web_viewer()` for a
browser-based viewer with no local install) and connect to it, or start a
standalone viewer first (`rerun` in a terminal) and have the logging
process call `rr.connect_grpc()` to stream into it. From a separate
machine, the native viewer connects to a running gRPC server with:

```bash
rerun rerun+http://<host>:<grpc_port>/proxy
```

which is the same pattern `lerobot-dataset-viz --mode distant --grpc-port=<port>`
uses under the hood: a headless training/eval box logs, a local machine
watches, with no data ever needing to leave the remote box as a file.

**Embedding in a Gradio demo.** <!-- id: gradio-rerun-embed --> The official `gradio_rerun` component (PyPI
`gradio_rerun`, source `rerun-io/gradio-rerun-viewer`; pin to `0.34.1`
alongside `rerun-sdk` here, needs `gradio>=6.0.0`) puts a Rerun viewer inside
a Gradio app as a component, rather than competing with a separate embed;
see `huggingface` for the demo-hosting side of that pairing. The streaming
pattern ran exactly as written (verified 2026-07-15, vla-trial): create a
`RecordingStream`, open a `binary_stream`, and `yield stream.read()` into a
`Rerun(streaming=True)` viewer component, with the app mounted onto FastAPI
via `gr.mount_gradio_app`. For browser-streamed images, compressing them
(`rr.Image(...).compress(jpeg_quality=...)`) meaningfully cuts bandwidth
(observed with rerun-sdk 0.34.1).

## Platform gotchas

- **The viewer runs natively everywhere** <!-- id: viewer-runs-natively-everywhere --> (Linux, macOS including Apple
  Silicon, and Windows), unlike `rviz2`, which needs ROS 2 and therefore
  Docker on macOS. This is why `rerun` is the default answer for a non-ROS
  pipeline regardless of local vs. remote, per the `visualization`
  umbrella's selection table.
- **`spawn()` needs a local display; it will fail on a bare headless
  box.** <!-- id: spawn-needs-local-display --> If a training/eval script that calls `rr.spawn()` is moved to a
  headless server, switch to `rr.serve_grpc()`/`serve_web_viewer()` or
  `rr.save()` instead; don't try to get a local window working over SSH.
- **The Python SDK bundles the Viewer; C++ and Rust don't.** <!-- id: python-sdk-bundles-viewer --> A pure-Python
  robium project gets the viewer for free via `pip install rerun-sdk`; a
  C++/Rust logging path needs the separate `rerun-cli` (`cargo install
  rerun-cli --locked --features nasm`, per the SDK's own install docs) to
  get the same standalone viewer/CLI.
- **`serve_grpc()` buffers in memory** <!-- id: serve-grpc-memory-buffer --> so late-connecting viewers still get
  full history; on a long-running process logging a lot of data, set its
  `server_memory_limit` argument rather than letting it grow unbounded.
- **0.34.1 API notes: don't reach for older Rerun API names.** <!-- id: api-notes-0341-scalars-set-time --> The scalar
  archetype is `rr.Scalars` (plural; `rr.Scalar` singular does not exist);
  log a single value as `rr.Scalars([x])`. `rr.set_time_sequence("step",
  step)` was removed; use `rr.set_time("step", sequence=step)` instead (see
  Usage patterns above). Confirmed against the pinned `rerun-sdk==0.34.1`;
  re-check Rerun's migration notes before assuming either holds on a
  different pinned version.

## Customization

- **Entity path scheme for a new project:** don't invent one from scratch;
  Rerun's own docs on entity paths and hierarchies (linked from the
  quick-start page above) cover the conventions (grouping by
  sensor/subsystem, using `Transform3D` logs to place entities in a common
  coordinate frame); mirror `lerobot-dataset-viz`'s own scheme when logging
  alongside a LeRobot episode so the two show up coherently in one tree.
- **Mixing ROS and non-ROS data in one debugging session:** per the
  `visualization` umbrella, this is normal: use `rviz2`/`foxglove` for the
  ROS-side state and `rerun` for a policy's own inputs/outputs, viewed
  side by side rather than forcing one tool to cover both.

## References

- Upstream: [Rerun documentation](https://rerun.io/docs) and [Python
  quick-start](https://rerun.io/docs/getting-started/quick-start/python)
  (primary source for logging code; check before writing new `rr.log()`
  calls), [operating modes
  reference](https://rerun.io/docs/reference/sdk/operating-modes) (source
  of the spawn/connect/save/serve/stdout distinction above; the exact URL
  404'd on direct fetch on 2026-07-10, so this content came via
  search-synthesis; re-verify before relying on the exact operating-mode
  list), [rerun-io/rerun GitHub
  repo](https://github.com/rerun-io/rerun) (fetched directly on 2026-07-10;
  source of the current version and `rerun-cli` install command),
  [example gallery](https://rerun.io/examples). Sibling skills: `lerobot`
  (owns LeRobot dataset mechanics; wraps this skill for episode
  visualization via `lerobot-dataset-viz`), `data` (dataset sourcing
  strategy), `rviz2` and `foxglove` (ROS-native live debugging, not this
  skill's territory), `visualization` (umbrella, routes here), `huggingface`
  (demo-hosting side of embedding a Rerun viewer in a Gradio app via
  `gradio_rerun`).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.2.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 1.2.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.2.0 (2026-07-31): vla-trial absorption: the Gradio-embed Usage pattern
  gains the verified gradio_rerun 0.34.1 streaming pattern (RecordingStream +
  binary_stream, yield stream.read() into a Rerun(streaming=True) viewer
  mounted via gr.mount_gradio_app on FastAPI; ran as written) and a
  browser-streaming bandwidth tip (rr.Image(...).compress(jpeg_quality=) cuts
  bandwidth, rerun-sdk 0.34.1).
- 1.1.0 (2026-07-15): add 0.34.1 API-notes gotcha (rr.Scalars plural, rr.set_time replacing removed set_time_sequence; existing snippets were already correct, this pins the facts) and a pointer to the official gradio_rerun component for embedding the viewer inside a Gradio demo (cross-refs huggingface). Verified against pinned rerun-sdk==0.34.1.
- 1.0.1 (2026-07-12): skill-refiner run 1: provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
