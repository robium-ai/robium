---
name: test-assets
version: 1.0.1
description: >
  Canonical test assets and fixture sourcing for robotics testing: which
  worlds, robot models, sample datasets, and recordings to test against for a
  given robot type; the standard test-assets folder layout with a provenance
  manifest; pointer vs vendored sourcing modes; fixture and golden policy
  (tolerance bands, seeded generation). Use when: 'test assets', 'test world',
  'test fixture', 'download a test dataset', 'sample rosbag', 'which world
  should I test in', 'robot model for simulation tests', 'golden output',
  'regression fixture', 'data for unit tests', setting up test data for any
  new robotics project. Load alongside testing when the test pyramid needs
  data. Not for: training-data sourcing (data), test structure and pass bars
  (testing), simulator selection rationale (simulation).
---

# test-assets

The test-data umbrella for robium. Every smoke, regression, or policy-eval
test consumes data — a world to load, a robot model to spawn, a dataset slice
to train on, a bag to replay, a golden to diff against — and picking those
assets ad hoc produces unrecognizable, irreproducible fixtures. This skill
owns which canonical assets to test against for a given robot type, the
standard test-assets folder layout with its provenance manifest, and the
sourcing decision (pointer vs vendored). It does not own the test pyramid and
pass bars (`testing`), training-data sourcing strategy (`data`), simulator
selection rationale (`simulation`), or asset loading/spawning mechanics
(`gazebo`, `isaac-sim`).

## When to use this skill

- Setting up test data for any new robotics project — load together with
  `testing`: that skill decides which pyramid layers to build; this one
  supplies the data those layers run against.
- The trigger phrases in the description: 'test assets', 'test world', 'test
  fixture', 'download a test dataset', 'sample rosbag', 'which world should I
  test in', 'golden output', 'regression fixture'.
- Choosing a world, robot model, or sample dataset for a smoke or regression
  test — including "we should own copies of these" vendoring decisions.
- Standing up a `test-assets/` folder (or auditing an existing one) for a
  repo's apps.
- Cross-references — go to the sibling skill instead when the question is:
  - Test structure, layers, and pass bars (what to test, when it counts as
    done) → `testing`. This skill only supplies the data.
  - Sourcing *training* data for robot learning (offline vs sim-generated vs
    teleop) → `data`. Same funnel instinct, different artifact: `data` feeds
    policies, this skill feeds tests.
  - Which simulator to use at all → `simulation`; this skill's matrix names a
    best-fit simulator per robot type for *testing* but cites `simulation`
    for the selection rationale.
  - Loading/spawning mechanics for the chosen assets → `gazebo` or
    `isaac-sim`; MuJoCo asset usage inside LeRobot environments → `lerobot`.
  - Hub download/upload mechanics and auth → `huggingface`; the
    LeRobotDataset format itself → `lerobot`.

## Key directives

- **Delegation posture: embed + links.** The catalog, layout, and sourcing
  policy live here (with pinned upstream links); mechanics of loading,
  spawning, or converting assets live in the tool skills; simulator *choice*
  logic stays with `simulation`.
- **Canonical-assets-first.** <!-- id: canonical-assets-first --> Prefer a well-known public asset (see
  `references/canonical-assets.md`) over authoring or hosting your own —
  recognizability is part of a fixture's value: reviewers and contributors
  already know how a TurtleBot3 world or pusht should behave.
- **Choose a sourcing mode deliberately — pointer or vendored — and record
  it.** <!-- id: choose-sourcing-mode-deliberately --> Pointer: pin upstream revisions (Fuel version, git commit, HF
  revision), fetch on demand, never commit data. Vendored: commit real copies
  under a stated size budget, every asset with full provenance in the
  manifest and its license verified at vendor time. Either way, anything with
  no public source is produced by a committed seeded generator script, not
  committed by hand; expensive-to-regenerate recordings can be hosted as MCAP
  in a Hub dataset repo as the escape hatch (mechanics → `huggingface`).
- **Goldens are bands, not checksums.** <!-- id: goldens-are-bands-not-checksums --> Physics is noisy — reference
  trajectories and metrics carry tolerances and seeds; exact-match comparison
  is only valid for pure-replay tests where no simulation re-runs.
- **Derived fixtures compound.** <!-- id: derived-fixtures-compound --> One verified scenario's output (a SLAM map,
  a recorded bag) becomes the next scenario's input — prefer this over
  importing unrelated data, and record the derivation in the manifest.
- **Never write asset facts from memory.** <!-- id: never-write-asset-facts-from-memory --> Revisions, licenses, episode
  counts, and download URLs change; verify against the live source at
  adoption time. `references/canonical-assets.md` records how and when each
  entry was verified — keep that discipline for entries you add.

## Quick start

**1. Identify the robot type under test** and pick model + world + dataset
from the suitability matrix in Decision guidance (details and links in
`references/canonical-assets.md`).

**2. Choose the sourcing mode** with the funnel in Decision guidance and
record it (and the size budget, if vendoring) in the test-assets README.

**3. Write the manifest.** Create the folder per
`references/test-assets-layout.md` and describe each asset in MANIFEST.yaml —
`examples/assets-manifest.yaml` is a working starting point.

**4. Fetch:** <!-- id: vendor-assets-fetch-command -->

```bash
uv run scripts/vendor_assets.py --manifest test-assets/MANIFEST.yaml
```

Re-run any time to refresh; `--check` verifies presence and pins without
fetching. Commit the result (vendored mode) or gitignore the data dirs
(pointer mode).

**5. Wire the assets into the `testing` pyramid** <!-- id: record-goldens-from-seeded-run --> and record goldens from a
known-good seeded run into goldens/ with explicit tolerances.

## Decision guidance

**Robot type → test-asset suitability** (selection details, licenses, and
links live in `references/canonical-assets.md`; simulator-choice rationale →
`simulation`):

| Robot type | Model pick | World/scene pick | Best-fit sim for testing | Matching open dataset |
|---|---|---|---|---|
| Mobile base / nav | TurtleBot3 burger or waffle | TurtleBot3 House (indoor), Tugbot in Warehouse (industrial) | Modern Gazebo (gz) — Nav2-ready | none canonical (self-record bags) |
| Arm — classical or VLA | SO-101 | tabletop scene | MuJoCo (LeRobot-native) or gz | SO-101 pick-place sample; pusht for train-smoke |
| Quadruped | Unitree Go2 | flat ground / rough-terrain heightfield | MuJoCo | none yet — no robium legged skill either |
| Humanoid | Unitree G1 | flat ground | MuJoCo or Isaac (GPU floor → `isaac-sim`) | none yet |
| Drone | — gap — | — | — | — (px4 vertical is future work) |

**Sourcing-mode funnel:**

```
Shared CI/regression corpus you must inspect and that must survive
upstream changes?            → vendored (size-budgeted, full provenance)
Personal/dev use, or asset too large to vendor?   → pointer (pinned)
No public canonical source (nav bags, goldens)?   → seeded generator script
Expensive to regenerate (long sim, GPU-gated)?    → Hub-hosted MCAP escape hatch
```

**Which pyramid layer needs which data** (the pyramid itself → `testing`):

| Layer | Data it consumes |
|---|---|
| Unit | none, or tiny inline samples (a single scan/frame as a file) |
| Node/launch smoke | robot model + world |
| Sim scenario / regression | world + map + goldens (+ recorded bags for replay tests) |
| Policy eval | dataset slice + checkpoint |

## Platform gotchas

- **Fuel assets need the `gz` CLI and network on first fetch.** <!-- id: fuel-assets-need-network-first-fetch --> They cache
  under ~/.gz/fuel afterwards, so sims run offline from the second load — CI
  and fresh clones must account for the first-fetch network dependency (or
  use vendored mode).
- **Gazebo-Classic-era worlds don't necessarily load in modern gz.** <!-- id: classic-era-worlds-may-not-load-in-gz --> Famous
  older worlds (e.g. the AWS RoboMaker set) predate modern gz — verify a
  world loads headless in the target gz version at adoption time rather than
  assuming; prefer the modern-gz picks in the catalog.
- **Hub-hosted bags/MCAP have no Dataset Viewer preview.** <!-- id: hub-bags-no-dataset-viewer-preview --> Arbitrary binaries
  are storable but not browsable on the Hub page — download-only. Ship a
  README next to them saying what the recording contains.
- **Dataset slices must stay loadable.** <!-- id: dataset-slices-must-stay-loadable --> A naive partial download of a
  LeRobot dataset can leave metadata inconsistent with the reduced episode
  count — after slicing, confirm the slice actually opens (format details and
  tooling → `lerobot`) before committing it as a fixture.

## Customization

- **Different robot than the catalog picks:** keep the matrix's *shape*
  (model + world + sim + dataset per robot type) and substitute your robot's
  description package; the layout, manifest, and sourcing funnel apply
  unchanged.
- **Adding a vertical (drone, legged, ...):** extend the suitability matrix
  with the same columns rather than inventing a new selection scheme; note
  gaps honestly (as the drone row does) instead of forcing a pick.
- **Tighter or looser size budgets:** the vendored-mode budget is a project
  decision — state it in the corpus README and let the vendor script's size
  summary enforce it socially; trim textures/meshes/episodes before busting
  it, and record trims in the manifest.

## References

- `references/canonical-assets.md` — the verified catalog: worlds, robot
  models, datasets, and recordings with links, licenses, and citation lines.
- `references/test-assets-layout.md` — the standard test-assets folder
  format, MANIFEST.yaml schema, and slice conventions.
- `scripts/vendor_assets.py` — manifest-driven fetcher/refresher for both
  sourcing modes.
- `examples/assets-manifest.yaml` — the catalog shortlist as a working
  manifest (status: unverified until the first hardening run).
- Sibling skills: `testing` (pyramid + pass bars this data serves), `data`
  (training-data sourcing), `simulation` (simulator choice), `gazebo` /
  `isaac-sim` (asset loading mechanics), `lerobot` (LeRobotDataset format,
  slice validation), `huggingface` (hub transfer mechanics), `architect`
  (routes here when a build plans its testing).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.0.0 (2026-07-18): initial authoring — robot-type suitability matrix,
  sourcing-mode funnel, layout reference, canonical-assets catalog, vendor
  script. Hardening pending: the robium-applications test-assets corpus
  build is this skill's first trial run.
