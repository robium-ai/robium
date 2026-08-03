# test-assets skill — design

Date: 2026-07-18
Status: approved-pending-user-review
Outcome of the eval/test-data brainstorm (started from BACKLOG Now item 0). Supersedes the
earlier in-conversation "robium-evals repo" shape — the user chose to keep everything inside
the skills repo as a skill.

## Problem

Robium has test *code* (per-app pytest suites in robium-applications) but no owned answer to
"where does test data come from": no canonical sim-asset catalog, no fixture-sourcing policy,
no goldens guidance. The seam is real and un-owned today:

- `data` (v1.1.0) owns **training**-data sourcing strategy (offline vs sim-generated vs
  teleop). Its description explicitly scopes it to robot-learning data.
- `testing` (v1.2.0) owns the test pyramid and pass bars, but not the data those tests
  consume.

## Decision history (settled during brainstorm)

1. **Thin slice across the three existing verticals** (nav, manip, VLA) — one scenario +
   fixture + golden each — over going deep on one.
2. **Sourcing: public-canonical pointers, minimize self-hosting.** User explicitly does not
   want to host data where avoidable.
3. ~~New `robium-evals` repo~~ → **superseded**: deliver as a **skill** in this repo.
   Rationale: don't deviate from the skills-repo identity; anything reusable becomes skill
   scripts.
4. **Execution model: manual/local first.** No CI wiring in v1.
5. **Sourcing is a guided decision, not a mandate.** Two legitimate modes the skill
   teaches and supports: **pointer** (pin upstream revisions, fetch on demand, never
   commit data — light repos) and **vendored** (commit real copies under a size budget
   with full provenance — own the exact bytes your tests ran against). Regenerate-by-
   seeded-script for anything with no public source, in either mode. Escape hatch
   (verified live 2026-07-18 via Context7 fetch of huggingface/hub-docs): HF dataset
   repos accept arbitrary binaries (rosbag/MCAP fine; 200 GB/file max, ~300 GB/public
   repo recommended; no Dataset Viewer preview for these formats) — expensive-to-
   regenerate fixtures can be hosted as MCAP on a hub org.
6. **Asset shortlist locked by user** (see catalog below); worlds explicitly chosen:
   TurtleBot3 House + OpenRobotics "Tugbot in Warehouse".
7. **Skill shape: option A with C's split** — user-facing `test-assets` skill now; the
   robium-self-eval harness (with/without-plugin scenario runs, trigger-reliability
   measurement) is NOT part of this skill. It tests robium, not the user's app; it goes to
   the backlog as a later `skill-author` extension.
8. **General-purpose skill, hardened by our corpus (2026-07-18, supersedes the earlier
   ordering).** The skill is written FIRST and is not specific to robium's own needs —
   it serves any project's test-asset downloading/creation. Its first hardening run is
   then building the vendored test-assets corpus in robium-applications *by invoking the
   skill* (spec: robium-applications docs/superpowers/specs/2026-07-18-test-assets-
   corpus-design.md) — the same demo↔skill pairing pattern as the existing trials.

## The skill

`skills/test-assets/` — **umbrella** skill (selection + cross-cutting practice), version
1.0.0. Deep: ships `references/` and `scripts/`.

**Owns:** where test data for robotics apps comes from — canonical sim assets (worlds, robot
models), sample datasets and recordings for fixtures, the fixture-sourcing policy, and
goldens discipline (tolerance bands, seeds).

**Does not own:** the test pyramid and pass bars (`testing`), training-data sourcing
(`data`), simulator setup mechanics (`gazebo`/`isaac-sim`/`simulation`), hub transfer
mechanics (`huggingface`), LeRobot dataset format (`lerobot`).

### Frontmatter description (trigger surface, drafted)

Capability: canonical test assets and fixture sourcing for robotics testing — which worlds,
robot models, sample datasets, and recordings to test against given the robot type; the
standard test-assets folder layout with provenance manifest; pointer vs vendored sourcing;
golden/fixture policy. "Use when" phrases: 'test world', 'test fixture', 'test assets',
'download a test dataset', 'sample rosbag', 'which world should I test in', 'robot model
for simulation tests', 'golden output', 'regression fixture', 'sample dataset for
testing', 'data for unit tests', setting up test data for any new robotics project.
Workflow position: load with `testing` when the pyramid needs data. Negative scope: not
for training-data sourcing (`data`), not for test structure/pass bars (`testing`), not
for simulator selection rationale (`simulation`).

### Body sections (per format rules, in order)

- **When to use this skill** — choosing assets for smoke/regression tests; setting up
  fixtures for a new app; cross-refs to `testing`, `data`, `gazebo`, `simulation`,
  `huggingface`, `lerobot`.
- **Key directives** —
  1. Delegation posture (first bullet): embed + links — the catalog, layout, and sourcing
     policy live here; mechanics of loading/spawning/converting assets live in the tool
     skills; simulator *choice* logic stays with `simulation` (this skill maps robot type →
     test assets and cites `simulation` for the sim-selection rationale).
  2. Canonical-assets-first: prefer a well-known public asset over authoring or hosting your
     own; recognizability is part of a fixture's value.
  3. Choose a sourcing mode deliberately — pointer or vendored — and record it. Pointer:
     pin upstream revisions (Fuel version, git commit, HF revision), fetch on demand,
     never commit data. Vendored: commit real copies under a stated size budget, every
     asset with full provenance (MANIFEST) and license verified at vendor time. Either
     way: anything with no public source is produced by a committed seeded generator
     script; HF-hosted MCAP as the escape hatch for expensive-to-regenerate fixtures.
  4. Goldens are bands, not checksums: physics is noisy — reference trajectories/metrics
     carry tolerances and seeds; exact-match only for pure-replay tests.
  5. Derived fixtures compound: one verified scenario's output (a SLAM map, a recorded bag)
     becomes the next scenario's input — prefer this over importing unrelated data.
  6. Never write asset facts (revisions, licenses, episode counts) from memory — verify
     against the live source at adoption time; the reference file records how each entry was
     verified.
- **Quick start** — pick assets from the catalog for the robot type under test → choose
  pointer vs vendored mode → write the manifest → fetch/vendor via the script into the
  standard layout → wire into the `testing` pyramid layer → record goldens from a
  known-good seeded run.
- **Decision guidance** (umbrella) —
  - **Robot type → test-asset suitability matrix** (the "what should I test against"
    table): mobile base → TB3 model + TB3 House / Tugbot Warehouse worlds, modern gz
    (Nav2-ready); arm (classical or VLA) → SO-101 model + tabletop scene, MuJoCo (LeRobot-
    native) or gz; quadruped → Unitree Go2 (Menagerie), MuJoCo (no legged skill coverage
    yet — flagged); humanoid → Unitree G1 (Menagerie), MuJoCo/Isaac; drone → gap, noted
    (px4 is a backlog skill). Each row: model pick, world pick, best-fit simulator for
    *testing* (choice rationale cited to `simulation`), matching open dataset if any.
  - **Sourcing-mode funnel**: shared CI/regression corpus you must be able to inspect and
    that must survive upstream changes → vendored (size-budgeted); personal/dev or large
    assets → pointer; no public source → seeded generator script; expensive to regenerate
    → hub-hosted MCAP escape hatch.
  - **"Which layer needs which data"** mapping onto `testing`'s pyramid (unit: none/tiny
    samples; launch smoke: models+worlds; sim regression: worlds+maps+goldens; policy
    eval: datasets+checkpoints).
- **Platform gotchas** — Fuel assets cache under `~/.gz/fuel` (first load needs network;
  offline after); Gazebo-Classic-era worlds (e.g. the famous AWS RoboMaker set) may not load
  in modern gz without porting — check at adoption; HF-hosted bags/MCAP have no Dataset
  Viewer preview (download-only).
- **Customization** — swapping the catalog picks for project-specific robots; adding a
  vertical (the same funnel applies).
- **References / Changelog** — per format.

### references/canonical-assets.md (single-topic, ~5–10 KB)

The verified catalog. Every entry: link, license note, what it's canonical *for*, pin
mechanism, and a citation line (how + when verified). Seed entries, all verified live
2026-07-18 via GitHub API / HF API / Fuel API unless noted:

| Slot | Asset | Source | Evidence |
|---|---|---|---|
| House world | TurtleBot3 House | github.com/ROBOTIS-GIT/turtlebot3_simulations | 515★, pushed 2025-07-14 |
| Factory world | "Tugbot in Warehouse" (OpenRobotics) | app.gazebosim.org (Fuel) | 47,114 downloads — most-used modern-gz warehouse world |
| Mobile robot | TurtleBot3 burger/waffle | same repo as house world | canonical Nav2 tutorial robot |
| Quadruped | Unitree Go2 | google-deepmind/mujoco_menagerie (`unitree_go2`); URDF: unitreerobotics/unitree_ros (1,477★) | dir listing verified |
| Humanoid | Unitree G1 | mujoco_menagerie (`unitree_g1`); unitree_ros; unitree_mujoco (1,089★) | dir listing verified |
| Arm | SO-101 | TheRobotStudio/SO-ARM100 (6,821★), `Simulation/SO101/` | dir listing verified; note: Menagerie carries only SO-100 (`trs_so_arm100`) |
| Arm sample dataset | `lerobot/svla_so101_pickplace` | HF hub | 42 likes — most-liked SO-101 dataset, official org, SmolVLA tutorial dataset. Runner-up (inspect first): `szk1ck/so101-pickplace-sim-mujoco` |
| ML CI dataset | pusht | HF `lerobot` org | the canonical CI-sized LeRobot dataset (from memory — re-verify at authoring) |
| Replay bags | EuRoC MAV, TUM RGB-D sequences | upstream project pages | canonical public rosbag sources (from memory — re-verify at authoring) |
| Viz/tooling samples | Foxglove sample MCAPs | foxglove docs/site | for viz-skill scenarios (from memory — re-verify at authoring) |

Honest-gap note kept in the file: there is no canonical public Nav2/TB3 rosbag — nav
regression bags are always self-recorded → generator-script territory.

Legged-robot flag: Go2/G1 are in the catalog as assets, but no skill covers legged robots —
recorded as a coverage gap in BACKLOG, not silently implied.

### references/test-assets-layout.md (single-topic, ~5 KB)

The standard test-assets folder format (user-approved shape, generalized from the
robium-applications corpus design):

```
test-assets/
  README.md      # human inventory: what each asset is, why it's here, license, size
  MANIFEST.yaml  # provenance per asset: kind (github|fuel|hf-dataset), upstream,
                 # subpath, pinned revision, fetch date, license (verified at vendor
                 # time), notes (any local modification, else "verbatim")
  worlds/  models/  datasets/  bags/  goldens/
```

Conventions documented alongside: dataset slices are deterministic (first N episodes),
stay valid LeRobotDataset directories, and record N + source revision in MANIFEST;
`bags/` and `goldens/` start empty and fill from seeded runs; in pointer mode the data
dirs are gitignored and only README + MANIFEST are committed; in vendored mode
everything is committed under the stated size budget.

### scripts/vendor_assets.py (genuinely reusable — the quality-bar test for shipping it)

Manifest-driven fetcher/refresher serving both sourcing modes: reads MANIFEST.yaml,
fetches each entry `kind`-appropriately (sparse git checkout at a commit; `gz fuel
download` + dependency flattening so worlds load offline; `huggingface_hub` snapshot of
a dataset slice) into the standard layout, verifies pins, prints a diff summary and
per-asset/total sizes, idempotent re-runs. No robium-specific behavior — any robotics
project can use it. In vendored mode the user commits the result; in pointer mode they
gitignore it.

### examples/assets-manifest.yaml

The locked shortlist expressed as a working manifest for the script — carries
`status: unverified` + upstream links until a trial run verifies it, per format rules.

**Not shipped in v1:** a record-a-bag helper (too app-specific until the nav generator
proves a reusable shape) and any eval-harness scripting (excluded by decision 7).

## Hardening plan (first trial run)

Immediately after authoring, the skill is exercised end-to-end by building the
robium-applications vendored corpus (its spec's implementation) *through* the skill:
follow its Quick start, use its layout reference and vendor_assets.py verbatim. Friction
found there lands in learnings/ and feeds the normal absorption loop before the skill is
considered hardened. The example manifest's `status: unverified` flips on this run.

## Cross-skill edits (each needs its own explicit go-ahead before commit, per policy)

- `testing` — route fixture/asset questions here (When-to-use cross-ref + References
  sibling line). Candidate: minor bump.
- `data` — negative-scope line: test-fixture sourcing → `test-assets`; keeps its
  training-data scope. Candidate: build or minor bump.
- `architect` — routing table gains the new skill (it owns the whole-catalog view).
  Candidate: minor bump.
- Repo sweep for stale claims (newline-flattened grep) — catalog counts, "19 skills" in
  README table and CLAUDE.md validator line become 20.

## Backlog updates (same change)

- Now item 0 rewritten: the "eval harness/robium-evals repo" framing → "test-assets skill"
  as the shipped shape; with/without-plugin eval harness + trigger-paraphrase measurement
  moved to a named Later item under `skill-author`.
- Later: HF `robium` org escape-hatch note (hosting verified possible, deliberately unused).

## Out of scope (v1)

CI wiring; the robium-self-eval harness; Isaac/legged verticals; real-hardware data;
scoreboard/results tooling; per-app scenario YAML corpus (lives with the apps in
robium-applications when built, not in the plugin).

## Acceptance

- `uv run skills/skill-author/scripts/validate_skills.py` prints PASS for 20 skills.
- vendor_assets.py fetches the example manifest end-to-end on a clean machine (network
  required), idempotent second run.
- All catalog entries carry citation lines; from-memory entries explicitly marked for
  re-verification at authoring time.
- Hardening: the robium-applications corpus build (its own spec's acceptance) completes
  using only this skill's guidance + script — friction captured in learnings/.
