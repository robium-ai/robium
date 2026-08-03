# test-assets corpus — design

Date: 2026-07-18
Status: approved-pending-user-review
Owned, vendored test assets for this repo's apps — smoke tests, regression tests, and
"see what the data looks like" inspection. Ordering (revised 2026-07-18, same day): the
robium-plugin `test-assets` skill (spec: robium-plugin docs/superpowers/specs/
2026-07-18-test-assets-skill-design.md) is authored **first** as a general-purpose
skill, and this corpus is then built **by invoking that skill** — its first hardening
run, the standard demo↔skill pairing. The vendor script ships in the skill
(scripts/vendor_assets.py), not in this repo.

## Decisions (settled in brainstorm)

1. **Own the assets.** Even open/public assets get vendored copies here — upstream
   deletions or changes must never lose us the exact bytes our tests ran against. This
   deliberately differs from the skill's pointer-first policy: the skill serves users;
   this corpus serves our regression suite.
2. **Plain git, size-budgeted** (user choice over LFS / fetch-on-demand): commit files
   directly; total corpus budget **~300 MB**; trim where easy (textures, meshes,
   dataset slices); no LFS tooling.
3. Asset shortlist as locked in the brainstorm (worlds: TB3 House + Tugbot in
   Warehouse; robots: TB3, Unitree Go2, Unitree G1, SO-101; datasets:
   svla_so101_pickplace slice + pusht slice).

## Layout

```
test-assets/
  README.md                 # inventory: what each asset is, why it's here, license
  MANIFEST.yaml             # provenance per asset (see schema below)
  worlds/
    tb3_house/              # SDF + referenced models, from turtlebot3_simulations
    tugbot_warehouse/       # Fuel world + model deps, flattened to load offline
  models/
    turtlebot3/             # burger/waffle URDF+SDF+meshes
    unitree_go2/            # Menagerie MJCF + meshes
    unitree_g1/             # Menagerie MJCF + meshes
    so101/                  # TheRobotStudio/SO-ARM100 Simulation/SO101
  datasets/
    so101_pickplace_sample/ # slice of lerobot/svla_so101_pickplace, LeRobot format
    pusht_sample/           # slice of pusht for train-smoke tests
  bags/                     # self-recorded from seeded oracle runs (starts empty)
  goldens/                  # tolerance-band reference outputs per app/scenario (starts empty)
```

(No local script — fetching/refreshing uses the `test-assets` skill's
vendor_assets.py; this layout is the skill's standard layout, instantiated here in
vendored mode.)

Top-level in this repo, sibling of `apps/` — shared across apps. App tests reference it
by relative path (e.g. nav-trial launch tests point at `test-assets/worlds/tb3_house`).

## MANIFEST.yaml schema

One entry per vendored asset:

```yaml
- name: tb3_house
  path: worlds/tb3_house
  kind: github            # github | fuel | hf-dataset
  upstream: https://github.com/ROBOTIS-GIT/turtlebot3_simulations
  subpath: turtlebot3_gazebo/worlds/...   # what was taken
  revision: <commit sha / fuel version / hf revision>   # pinned at vendor time
  fetched: 2026-07-18
  license: Apache-2.0     # verified against upstream at vendor time
  notes: trimmed X, flattened Y            # any local modification, or "verbatim"
```

Rules: every local modification to a vendored file is listed in `notes` — otherwise
files are verbatim upstream. License field is read from the upstream repo at vendor
time, never from memory. `README.md` renders the same inventory human-first.

## Fetch/refresh mechanics

Owned by the `test-assets` skill: its scripts/vendor_assets.py does the manifest-driven
fetch (sparse git checkout at `revision`; `gz fuel download` + dependency flattening;
`huggingface_hub` snapshot of the slice), prints diff summaries and sizes, idempotent
re-runs. This corpus build is that script's first real workout — any friction is a
learning for the skill, not a local workaround here.

Dataset slicing follows the skill's layout conventions: **first N episodes**
(deterministic, not random), N sized to keep each dataset ≤ ~50 MB; N + source revision
recorded in MANIFEST; slices stay valid LeRobotDataset directories (loadable by
`lerobot`, metadata consistent with the reduced episode count).

## Size budget

~300 MB total, enforced socially (README table lists per-asset sizes; vendor script
prints totals). Expected big-ticket items: Tugbot warehouse textures, Go2/G1 meshes,
dataset slices. If an asset can't fit its share, trim (lower-res textures, fewer
episodes) and record the trim in MANIFEST `notes`; if it still can't fit, that asset
falls back to the HF-hosted escape hatch (documented in the plugin skill spec) rather
than busting the budget.

## Licenses / attribution

All shortlist upstreams are expected permissive (Apache-2.0 for TB3/Menagerie; check
SO-ARM100, unitree assets, Fuel world, dataset cards at vendor time). README carries an
attribution section. Any asset whose license forbids redistribution is NOT vendored —
it drops to manifest-pointer-only, flagged in README. Verification happens at vendor
time per asset; nothing asserted from memory.

## What consumes it (initial wiring targets, same effort or follow-up)

- nav-trial: launch/smoke tests use `worlds/tb3_house` + `models/turtlebot3`;
  its empty per-app `bags/` idea is superseded by the shared `bags/`.
- vla-trial: `models/so101` + `datasets/so101_pickplace_sample` for dataset-format and
  pipeline-smoke tests.
- manip-trial: `datasets/pusht_sample` for train-smoke.
- Go2 / G1: vendored ready, no consumer yet — future legged vertical (coverage gap
  already flagged in robium-plugin BACKLOG).

## Out of scope

Goldens content and recorded bags (they arrive per-app as tests get wired, into the
dirs created here); CI wiring; authoring the `test-assets` skill itself (own spec,
built first, in robium-plugin); any HF-hosted publishing.

## Acceptance

- `test-assets/` committed with all shortlist assets, MANIFEST complete, README
  inventory with sizes + licenses; total ≤ ~300 MB.
- `vendor_assets.py` re-run reports "up to date" (idempotence).
- Dataset slices load: `LeRobotDataset` opens both samples without error.
- TB3 house world + Tugbot warehouse load in modern `gz sim` headless on the dev
  machine (the Tugbot world's flattened deps resolve offline).
- At least one existing app test rewired to consume the corpus (nav-trial world path
  or vla-trial dataset sample) and passing.

## Backlog updates (robium-plugin docs/BACKLOG.md, at implementation)

- Now item 0 re-pointed: author the `test-assets` skill first, then build this
  vendored corpus through it (skill's first hardening run); eval harness follows later.
