# The standard test-assets layout

The folder format for a repo's owned test data (worlds, models, datasets,
recordings, goldens), with provenance for every asset. Works in both sourcing
modes: **vendored** (data committed under a size budget) and **pointer**
(data gitignored, only README + MANIFEST committed).

## Layout

    test-assets/
      README.md      # human inventory: what each asset is, why it's here,
                     # license, size; states the sourcing mode + size budget
      MANIFEST.yaml  # machine provenance, one entry per asset (schema below)
      worlds/        # SDF/USD scenes, flattened to load offline
      models/        # robot descriptions: URDF/SDF/MJCF + meshes
      datasets/      # dataset slices (LeRobot format stays loadable)
      bags/          # recorded telemetry (rosbag2/MCAP), self-recorded
      goldens/       # tolerance-band reference outputs per app/scenario

`bags/` and `goldens/` start empty and fill from seeded runs; they are
outputs of the project's own verified scenarios, not downloads.

## MANIFEST.yaml schema

    - name: tb3_house                # unique id, snake_case
      path: worlds/tb3_house        # destination inside test-assets/
      kind: github                  # github | fuel | hf-dataset
      upstream: https://github.com/ROBOTIS-GIT/turtlebot3_simulations
      subpath: turtlebot3_gazebo/worlds/turtlebot3_house.world   # github only
      revision: <commit sha | Fuel version number | HF revision>
      fetched: 2026-07-18           # date of last fetch/refresh
      license: Apache-2.0           # read from upstream AT VENDOR TIME
      notes: verbatim               # or list every local modification/trim
      deps: []                      # fuel only: extra model URIs the world needs
      allow_patterns: []            # hf-dataset only: file globs for a slice

Rules:

- `revision` is always pinned, never a branch name. The vendor script
  records the resolved value after fetching.
- `license` is read from the upstream repo/dataset card at vendor time, never
  from memory. An asset whose license forbids redistribution is NOT vendored;
  it stays pointer-mode and the README flags it.
- Every local modification to a vendored file is listed in `notes`; otherwise
  files are verbatim upstream. This is what makes refresh = re-fetch + diff.

## Slice conventions (datasets)

- Deterministic slices: the **first N episodes**, never a random sample.
- Size each slice for its job (a pipeline-smoke slice rarely needs more than
  a handful of episodes; keep each slice small enough for the repo's budget).
- Record N and the source revision in the entry's `notes`.
- A slice must remain a loadable dataset; for LeRobot data, metadata must
  stay consistent with the reduced episode count (validation tooling: the
  `lerobot` skill).

## Mode mechanics

- **Vendored:** commit everything; state the total size budget in README; the
  vendor script's size summary is the budget check on every refresh.
- **Pointer:** add `worlds/ models/ datasets/ bags/` to .gitignore; commit
  README + MANIFEST + goldens only; every clone runs the vendor script once.
