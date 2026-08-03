# test-assets Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author the general-purpose `test-assets` umbrella skill (catalog + layout + vendor script), wire it into the catalog (testing/data/architect cross-refs, README/CLAUDE.md counts), and update the backlog — so the robium-applications corpus can then be built *through* the skill as its first hardening run.

**Architecture:** One new deep umbrella skill `skills/test-assets/` (SKILL.md + 2 references + 1 script + 1 example). Three gated minor bumps to existing skills (testing, data, architect) with archive snapshots. Spec: `docs/superpowers/specs/2026-07-18-test-assets-skill-design.md`.

**Tech Stack:** Markdown skills (agentskills.io format), Python 3.10+ with PEP 723 inline deps (pyyaml, huggingface_hub) run via `uv run`, `git` sparse checkout, `gz fuel` CLI.

## Global Constraints

- After ANY change under `skills/`: `uv run skills/skill-author/scripts/validate_skills.py` must exit 0. It prints "Checked 20 skills: PASS" once test-assets exists (19 before).
- Frontmatter: exactly `name`, `version`, `description` (name == dirname; description ≤1024 chars). New skill version: `1.0.0`.
- SKILL.md body <500 lines; required sections in order: `## When to use this skill`, `## Key directives`, `## Quick start`, `## Decision guidance` (umbrella), `## Platform gotchas`, `## Customization`, `## References`, `## Changelog`. First Key-directives bullet states delegation posture.
- No backticks around another skill's file names/paths — backticks only for files inside the same skill's directory. Grep manually; the validator only catches prefixed paths.
- Citation honesty: every version/status claim in reference files states how it was verified (direct fetch / API check / search synthesis + re-verify prompt). Never write asset facts from memory — the verify steps in Task 3 are mandatory, not optional.
- Skill-update policy for Tasks 8–10: archive `skills/<name>/` → `archive/<name>/<old-version>/` BEFORE first edit; bump version; changelog line starts `- <new-version> (2026-07-18): ...`; archive + edit in the SAME commit. Task 7's user checkpoint is mandatory before any of these commits.
- Commit style: repo uses atomic `skill(<name>): <version> — ...` commits; the new skill lands as one commit (Task 6), not per-file commits. Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- references/ files: single-topic, ~5–10 KB. examples/ files carry a `status: unverified` marker + upstream links until a trial run verifies them.

---

### Task 1: Scaffold skill directory and write SKILL.md

**Files:**
- Create: `skills/test-assets/SKILL.md`

**Interfaces:**
- Produces: the skill body that Tasks 2–5 reference files/scripts must match by name (`references/canonical-assets.md`, `references/test-assets-layout.md`, `scripts/vendor_assets.py`, `examples/assets-manifest.yaml`).

- [ ] **Step 1: Create the file with the complete content below**

```markdown
---
name: test-assets
version: 1.0.0
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
- **Canonical-assets-first.** Prefer a well-known public asset (see
  `references/canonical-assets.md`) over authoring or hosting your own —
  recognizability is part of a fixture's value: reviewers and contributors
  already know how a TurtleBot3 world or pusht should behave.
- **Choose a sourcing mode deliberately — pointer or vendored — and record
  it.** Pointer: pin upstream revisions (Fuel version, git commit, HF
  revision), fetch on demand, never commit data. Vendored: commit real copies
  under a stated size budget, every asset with full provenance in the
  manifest and its license verified at vendor time. Either way, anything with
  no public source is produced by a committed seeded generator script, not
  committed by hand; expensive-to-regenerate recordings can be hosted as MCAP
  in a Hub dataset repo as the escape hatch (mechanics → `huggingface`).
- **Goldens are bands, not checksums.** Physics is noisy — reference
  trajectories and metrics carry tolerances and seeds; exact-match comparison
  is only valid for pure-replay tests where no simulation re-runs.
- **Derived fixtures compound.** One verified scenario's output (a SLAM map,
  a recorded bag) becomes the next scenario's input — prefer this over
  importing unrelated data, and record the derivation in the manifest.
- **Never write asset facts from memory.** Revisions, licenses, episode
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

**4. Fetch:**

```bash
uv run scripts/vendor_assets.py --manifest test-assets/MANIFEST.yaml
```

Re-run any time to refresh; `--check` verifies presence and pins without
fetching. Commit the result (vendored mode) or gitignore the data dirs
(pointer mode).

**5. Wire the assets into the `testing` pyramid** and record goldens from a
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

- **Fuel assets need the `gz` CLI and network on first fetch.** They cache
  under ~/.gz/fuel afterwards, so sims run offline from the second load — CI
  and fresh clones must account for the first-fetch network dependency (or
  use vendored mode).
- **Gazebo-Classic-era worlds don't necessarily load in modern gz.** Famous
  older worlds (e.g. the AWS RoboMaker set) predate modern gz — verify a
  world loads headless in the target gz version at adoption time rather than
  assuming; prefer the modern-gz picks in the catalog.
- **Hub-hosted bags/MCAP have no Dataset Viewer preview.** Arbitrary binaries
  are storable but not browsable on the Hub page — download-only. Ship a
  README next to them saying what the recording contains.
- **Dataset slices must stay loadable.** A naive partial download of a
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

- 1.0.0 (2026-07-18): initial authoring — robot-type suitability matrix,
  sourcing-mode funnel, layout reference, canonical-assets catalog, vendor
  script. Hardening pending: the robium-applications test-assets corpus
  build is this skill's first trial run.
```

- [ ] **Step 2: Run the validator**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 20 skills: PASS`, exit 0. (references/scripts/examples files don't exist yet — if the validator errors on the referenced local paths, note it and proceed to Tasks 2–5 which create them, then re-run.)

- [ ] **Step 3: Manual rule checks**

Run: `grep -n '`[a-z0-9_-]*\.\(md\|py\|yaml\)`' skills/test-assets/SKILL.md`
Expected: matches ONLY files inside `skills/test-assets/` (references/, scripts/, examples/ paths above). No other skill's filenames in backticks.
Run: `wc -l skills/test-assets/SKILL.md` → expected well under 500.

### Task 2: references/test-assets-layout.md

**Files:**
- Create: `skills/test-assets/references/test-assets-layout.md`

**Interfaces:**
- Produces: the MANIFEST.yaml schema consumed verbatim by `scripts/vendor_assets.py` (Task 4) and `examples/assets-manifest.yaml` (Task 5): fields `name`, `path`, `kind` (github|fuel|hf-dataset), `upstream`, `subpath` (github only), `revision`, `fetched`, `license`, `notes`, optional `deps` (fuel), optional `allow_patterns` (hf-dataset).

- [ ] **Step 1: Create the file with the complete content below**

```markdown
# The standard test-assets layout

The folder format for a repo's owned test data — worlds, models, datasets,
recordings, goldens — with provenance for every asset. Works in both sourcing
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

`bags/` and `goldens/` start empty and fill from seeded runs — they are
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

- `revision` is always pinned — never a branch name. The vendor script
  records the resolved value after fetching.
- `license` is read from the upstream repo/dataset card at vendor time, never
  from memory. An asset whose license forbids redistribution is NOT vendored —
  it stays pointer-mode and the README flags it.
- Every local modification to a vendored file is listed in `notes`; otherwise
  files are verbatim upstream. This is what makes refresh = re-fetch + diff.

## Slice conventions (datasets)

- Deterministic slices: the **first N episodes**, never a random sample.
- Size each slice for its job (a pipeline-smoke slice rarely needs more than
  a handful of episodes; keep each slice small enough for the repo's budget).
- Record N and the source revision in the entry's `notes`.
- A slice must remain a loadable dataset — for LeRobot data, metadata must
  stay consistent with the reduced episode count (validation tooling: the
  `lerobot` skill).

## Mode mechanics

- **Vendored:** commit everything; state the total size budget in README; the
  vendor script's size summary is the budget check on every refresh.
- **Pointer:** add `worlds/ models/ datasets/ bags/` to .gitignore; commit
  README + MANIFEST + goldens only; every clone runs the vendor script once.
```

- [ ] **Step 2: Validate + size check**

Run: `uv run skills/skill-author/scripts/validate_skills.py && wc -c skills/test-assets/references/test-assets-layout.md`
Expected: PASS; size in the ~2.5–10 KB band.

### Task 3: references/canonical-assets.md (with live verification)

**Files:**
- Create: `skills/test-assets/references/canonical-assets.md`

**Interfaces:**
- Consumes: nothing. Produces: catalog entries whose `upstream` URLs Task 5's example manifest must match exactly.

- [ ] **Step 1: Re-verify the from-memory entries against live sources**

The 2026-07-18 brainstorm already verified via API: turtlebot3_simulations (515★, pushed 2025-07-14), aws small-house (322★) / small-warehouse (487★), SO-ARM100 (6,821★, `Simulation/SO101` dir present), unitree_ros (1,477★), unitree_mujoco (1,089★), mujoco_menagerie dirs `unitree_go2`/`unitree_g1`/`trs_so_arm100`, HF `lerobot/svla_so101_pickplace` (42 likes), Fuel "Tugbot in Warehouse" (47,114 downloads). Do NOT restate those without carrying the citation line.

Verify the remaining from-memory candidates now:

Run: `curl -s https://huggingface.co/api/datasets/lerobot/pusht | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['id'], d.get('downloads'), d.get('likes'))"`
Expected: dataset exists; note downloads/likes for the citation line.

Run: `curl -s -o /dev/null -w "%{http_code}\n" https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets` (EuRoC MAV) and `curl -s -o /dev/null -w "%{http_code}\n" https://cvg.cit.tum.de/data/datasets/rgbd-dataset` (TUM RGB-D) and `curl -s -o /dev/null -w "%{http_code}\n" https://foxglove.dev/examples` (Foxglove samples).
Expected: 200 each. If any is not 200, search for the current canonical URL (the projects move) and cite "located via search on 2026-07-18 — re-verify at adoption".

- [ ] **Step 2: Create the file**

Content: title + one-para purpose, then a table per family (Worlds / Robot models / Datasets / Recordings), columns: Asset | Upstream (link) | License | Canonical for | Verified. Populate every row from the evidence above — each `Verified` cell is a citation line like "GitHub API 2026-07-18: 515★, pushed 2025-07-14" or "HTTP 200 2026-07-18 — re-verify license at adoption". Include these rows exactly (plus license values found in Step 1):

- Worlds: TurtleBot3 House; Tugbot in Warehouse (Fuel, pinned version); AWS Small House + AWS Small Warehouse each flagged "Gazebo-Classic era — verify modern-gz load before adopting".
- Robot models: TurtleBot3 burger/waffle; Unitree Go2 (Menagerie MJCF; unitree_ros URDF); Unitree G1 (Menagerie; unitree_ros; unitree_mujoco); SO-101 (SO-ARM100 `Simulation/SO101`) with the note "Menagerie carries only SO-100 (trs_so_arm100)".
- Datasets: lerobot/svla_so101_pickplace (canonical SO-101 sample; note runner-up szk1ck/so101-pickplace-sim-mujoco, inspect-before-trust); lerobot/pusht (CI-sized train-smoke standard).
- Recordings: EuRoC MAV, TUM RGB-D (public replay bags); Foxglove sample MCAPs (viz-tool scenarios).

End the file with two short sections: **Known gaps** — "no canonical public Nav2/TB3 rosbag exists; nav regression bags are always self-recorded (→ seeded generator scripts)"; drone assets unpicked. **Adding an entry** — the three requirements: live verification, license read at adoption, citation line.

- [ ] **Step 3: Validate + size check**

Run: `uv run skills/skill-author/scripts/validate_skills.py && wc -c skills/test-assets/references/canonical-assets.md`
Expected: PASS; ~4–10 KB.

### Task 4: scripts/vendor_assets.py

**Files:**
- Create: `skills/test-assets/scripts/vendor_assets.py`

**Interfaces:**
- Consumes: MANIFEST.yaml entries per Task 2's schema.
- Produces: CLI `uv run vendor_assets.py [--manifest PATH] [--only NAME] [--check]`; exit 0 on success, 1 on any failure; per-asset + total size summary on stdout.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "huggingface_hub>=0.24"]
# ///
"""vendor_assets.py — manifest-driven test-asset fetcher/refresher.

Reads a MANIFEST.yaml (schema: the test-assets skill's
references/test-assets-layout.md), fetches each entry into place, and prints
a per-asset and total size summary. Idempotent: re-fetching an unchanged
pinned revision converges to the same bytes.

  uv run vendor_assets.py --manifest test-assets/MANIFEST.yaml
  uv run vendor_assets.py --manifest ... --only tb3_house
  uv run vendor_assets.py --manifest ... --check

Kinds: github (sparse checkout of subpath at a commit), fuel (gz fuel
download of a world/model plus optional deps), hf-dataset (snapshot of a
dataset, optionally sliced via allow_patterns). Requires: git; gz CLI for
fuel entries; network.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def sh(cmd: list[str], cwd: Path | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n} B"


def fetch_github(entry: dict, dest: Path) -> str:
    """Sparse-checkout entry['subpath'] at entry['revision']; returns resolved sha."""
    with tempfile.TemporaryDirectory() as td:
        sh(["git", "clone", "--filter=blob:none", "--no-checkout", "--quiet",
            entry["upstream"], td])
        sh(["git", "sparse-checkout", "set", entry["subpath"]], cwd=Path(td))
        sh(["git", "checkout", "--quiet", entry["revision"]], cwd=Path(td))
        sha = sh(["git", "rev-parse", "HEAD"], cwd=Path(td))
        src = Path(td) / entry["subpath"]
        if not src.exists():
            raise RuntimeError(f"subpath not found after checkout: {entry['subpath']}")
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / src.name)
        return sha


def fetch_fuel(entry: dict, dest: Path) -> str:
    """gz fuel download the asset (and deps) into the local cache, then copy."""
    if shutil.which("gz") is None:
        raise RuntimeError("fuel entry requires the gz CLI (install gz-sim tools)")
    uris = [entry["upstream"], *entry.get("deps", [])]
    for uri in uris:
        sh(["gz", "fuel", "download", "-u", uri])
    cache = Path.home() / ".gz" / "fuel"
    # cache layout mirrors the URI host/owner/collection/name; find by name
    name = entry["upstream"].rstrip("/").split("/")[-1]
    hits = sorted(cache.rglob(name), key=lambda p: len(str(p)))
    hits = [h for h in hits if h.is_dir()]
    if not hits:
        raise RuntimeError(f"downloaded but not found in cache: {name}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(hits[0], dest)
    return str(entry.get("revision", "latest-at-fetch"))


def fetch_hf_dataset(entry: dict, dest: Path) -> str:
    from huggingface_hub import snapshot_download
    dest.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=entry["upstream"].removeprefix("https://huggingface.co/datasets/"),
        repo_type="dataset",
        revision=entry.get("revision") or None,
        allow_patterns=entry.get("allow_patterns") or None,
        local_dir=dest,
    )
    return str(entry.get("revision", "default-at-fetch"))


FETCHERS = {"github": fetch_github, "fuel": fetch_fuel, "hf-dataset": fetch_hf_dataset}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default="test-assets/MANIFEST.yaml")
    ap.add_argument("--only", help="fetch a single entry by name")
    ap.add_argument("--check", action="store_true",
                    help="verify entries exist on disk; no fetching")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 1
    entries = yaml.safe_load(manifest_path.read_text())
    if not isinstance(entries, list) or not entries:
        print("manifest must be a non-empty list of entries", file=sys.stderr)
        return 1
    root = manifest_path.parent

    failures, total = 0, 0
    for entry in entries:
        name = entry.get("name", "<unnamed>")
        if args.only and name != args.only:
            continue
        dest = root / entry["path"]
        if args.check:
            ok = dest.exists() and any(dest.iterdir()) if dest.is_dir() else dest.exists()
            pinned = entry.get("revision") not in (None, "", "main", "master")
            status = "ok" if (ok and pinned) else ("MISSING" if not ok else "UNPINNED")
            print(f"  {name:30s} {status}")
            failures += 0 if status == "ok" else 1
            continue
        kind = entry.get("kind")
        if kind not in FETCHERS:
            print(f"  {name:30s} FAILED: unknown kind {kind!r}", file=sys.stderr)
            failures += 1
            continue
        try:
            resolved = FETCHERS[kind](entry, dest)
            size = dir_size(dest)
            total += size
            print(f"  {name:30s} {human(size):>10s}  @ {resolved}")
        except Exception as e:  # keep going; report at end
            print(f"  {name:30s} FAILED: {e}", file=sys.stderr)
            failures += 1

    if not args.check:
        print(f"  {'TOTAL':30s} {human(total):>10s}")
    if failures:
        print(f"{failures} entr{'y' if failures == 1 else 'ies'} failed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-test the github fetcher against a real, small asset**

Create `/private/tmp/claude-501/-Users-robium-repos-robium-plugin/8b7c4f9f-81e2-4fb8-968d-deb0778a2e06/scratchpad/ta-smoke/MANIFEST.yaml`:

```yaml
- name: so101_model
  path: models/so101
  kind: github
  upstream: https://github.com/TheRobotStudio/SO-ARM100
  subpath: Simulation/SO101
  revision: main
  fetched: 2026-07-18
  license: check-at-vendor
  notes: smoke test only
```

Run: `uv run skills/test-assets/scripts/vendor_assets.py --manifest <scratchpad>/ta-smoke/MANIFEST.yaml`
Expected: `so101_model` line with a size and resolved sha; `TOTAL` line; exit 0. (Uses `main` only because this is a throwaway smoke; note the resolved sha it prints — real manifests pin it.)

- [ ] **Step 3: Idempotence + check mode**

Run the same command again → same size, exit 0.
Run with `--check` → `so101_model  UNPINNED` (revision is `main`), exit 1 — confirming the pin check works. Then edit the smoke manifest's `revision:` to the sha printed in Step 2, re-run `--check` → `ok`, exit 0.

- [ ] **Step 4: Validator**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → PASS.

### Task 5: examples/assets-manifest.yaml

**Files:**
- Create: `skills/test-assets/examples/assets-manifest.yaml`

**Interfaces:**
- Consumes: Task 2's schema; upstreams exactly as in Task 3's catalog.

- [ ] **Step 1: Create the file**

```yaml
# status: unverified — becomes verified when the first hardening run
# (the robium-applications test-assets corpus build) fetches it end-to-end.
# Upstreams: see the skill's references/canonical-assets.md for evidence lines.
# Revisions below say PIN-AT-ADOPTION: resolve each to a concrete
# sha/version/revision when you first vendor (vendor_assets.py prints the
# resolved value; --check fails until pins are concrete).

- name: tb3_house
  path: worlds/tb3_house
  kind: github
  upstream: https://github.com/ROBOTIS-GIT/turtlebot3_simulations
  subpath: turtlebot3_gazebo/worlds
  revision: PIN-AT-ADOPTION
  fetched: null
  license: Apache-2.0   # verify against repo LICENSE at vendor time
  notes: verbatim

- name: tugbot_warehouse
  path: worlds/tugbot_warehouse
  kind: fuel
  upstream: "https://fuel.gazebosim.org/1.0/OpenRobotics/worlds/Tugbot in Warehouse"
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor
  notes: flatten model deps via `deps` so the world loads offline
  deps: []              # fill with the model URIs the world <include>s

- name: turtlebot3_models
  path: models/turtlebot3
  kind: github
  upstream: https://github.com/ROBOTIS-GIT/turtlebot3_simulations
  subpath: turtlebot3_gazebo/models
  revision: PIN-AT-ADOPTION
  fetched: null
  license: Apache-2.0   # verify at vendor time
  notes: verbatim

- name: unitree_go2
  path: models/unitree_go2
  kind: github
  upstream: https://github.com/google-deepmind/mujoco_menagerie
  subpath: unitree_go2
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor   # per-model licenses in Menagerie
  notes: verbatim

- name: unitree_g1
  path: models/unitree_g1
  kind: github
  upstream: https://github.com/google-deepmind/mujoco_menagerie
  subpath: unitree_g1
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor
  notes: verbatim

- name: so101
  path: models/so101
  kind: github
  upstream: https://github.com/TheRobotStudio/SO-ARM100
  subpath: Simulation/SO101
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor
  notes: verbatim

- name: so101_pickplace_sample
  path: datasets/so101_pickplace_sample
  kind: hf-dataset
  upstream: https://huggingface.co/datasets/lerobot/svla_so101_pickplace
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor   # dataset card
  notes: "slice: first N episodes, N sized to <=50 MB; confirm slice loads (lerobot)"
  allow_patterns: []         # fill per dataset file layout at vendor time

- name: pusht_sample
  path: datasets/pusht_sample
  kind: hf-dataset
  upstream: https://huggingface.co/datasets/lerobot/pusht
  revision: PIN-AT-ADOPTION
  fetched: null
  license: check-at-vendor
  notes: "slice: first N episodes; train-smoke fixture"
  allow_patterns: []
```

- [ ] **Step 2: Parse check + validator**

Run: `uv run skills/test-assets/scripts/vendor_assets.py --manifest skills/test-assets/examples/assets-manifest.yaml --check`
Expected: every entry listed as `MISSING` or `UNPINNED`, exit 1 — correct for an example manifest (it parses; nothing is fetched into the plugin repo).
Run: `uv run skills/skill-author/scripts/validate_skills.py` → PASS.

### Task 6: Commit the new skill

- [ ] **Step 1: Final validator + manual sweeps**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → `Checked 20 skills: PASS`.
Run: `tr '\n' ' ' < skills/test-assets/SKILL.md | grep -o "verified via direct fetch"` → expected: no output (citation honesty — no such claim exists unless literally true).

- [ ] **Step 2: Commit**

```bash
git add skills/test-assets/
git commit -m "skill(test-assets): 1.0.0 — canonical test assets, layout + manifest, vendor script

New umbrella skill: robot-type suitability matrix, pointer-vs-vendored
sourcing funnel, verified canonical-assets catalog, standard test-assets
layout with provenance MANIFEST, and manifest-driven vendor_assets.py.
Spec: docs/superpowers/specs/2026-07-18-test-assets-skill-design.md.
Hardening pending: robium-applications corpus build.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 7: CHECKPOINT — user go-ahead for cross-skill edits (Gate 2)

- [ ] **Step 1: Present the per-skill change summaries and STOP**

Per the skill-update policy, present exactly this table to the user and wait for explicit approval before Tasks 8–10 commit anything:

| Skill | Version | Change |
|---|---|---|
| testing | 1.2.0 → 1.3.0 | When-to-use cross-ref: test *data* questions route to `test-assets`; References sibling line |
| data | 1.1.0 → 1.2.0 | Description negative-scope gains "(test fixtures → test-assets)"; When-to-use cross-ref; References sibling line |
| architect | 1.3.1 → 1.4.0 | Routing table row for `test-assets` in the testing category |

No commits for these three skills before the go-ahead. If the user amends scope, adjust Tasks 8–10 accordingly.

### Task 8: testing 1.2.0 → 1.3.0 cross-ref (after Gate 2 approval)

**Files:**
- Create: `archive/testing/1.2.0/` (copy of current `skills/testing/`)
- Modify: `skills/testing/SKILL.md`

- [ ] **Step 1: Archive first**

```bash
mkdir -p archive/testing && cp -R skills/testing archive/testing/1.2.0
```

- [ ] **Step 2: Edit skills/testing/SKILL.md**

(a) Frontmatter: `version: 1.2.0` → `version: 1.3.0`.
(b) In `## When to use this skill`, in the "Cross-references" bullet list, insert before the "General (non-robotics) testing practices" item:

```markdown
  - Where the test *data* comes from — worlds, robot models, sample
    datasets, fixture folders, goldens → `test-assets`. This skill decides
    what to test and when it passes; `test-assets` supplies what it runs
    against.
```

(c) In `## References`, in the "Sibling skills:" list, insert after the `simulation` entry: `` `test-assets` (the data the pyramid's layers consume), ``
(d) Append to `## Changelog` (top of the list):

```markdown
- 1.3.0 (2026-07-18): route test-data sourcing to the new test-assets
  skill (cross-ref + sibling line); no content changes otherwise.
```

- [ ] **Step 3: Validate + commit (archive + edit together)**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → PASS.

```bash
git add archive/testing/1.2.0 skills/testing/SKILL.md
git commit -m "skill(testing): 1.3.0 — route test-data questions to test-assets; archive 1.2.0

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 9: data 1.1.0 → 1.2.0 cross-ref (after Gate 2 approval)

**Files:**
- Create: `archive/data/1.1.0/` (copy of current `skills/data/`)
- Modify: `skills/data/SKILL.md`

- [ ] **Step 1: Archive first**

```bash
mkdir -p archive/data && cp -R skills/data archive/data/1.1.0
```

- [ ] **Step 2: Edit skills/data/SKILL.md**

(a) Frontmatter: `version: 1.1.0` → `version: 1.2.0`.
(b) Description, final sentence: `Not for: model training itself (lerobot, isaac-lab).` → `Not for: model training itself (lerobot, isaac-lab) or sourcing test fixtures/assets (test-assets).` Confirm total description stays ≤1024 chars (`python3 -c "import yaml,sys; d=yaml.safe_load(open('skills/data/SKILL.md').read().split('---')[1]); print(len(d['description']))"`).
(c) In `## When to use this skill` under "Cross-references", append a final item:

```markdown
  - Sourcing *test* data — worlds, models, sample datasets, fixtures, and
    goldens for smoke/regression tests → `test-assets`. This skill owns data
    that trains policies; `test-assets` owns data that tests apps.
```

(d) In `## References`, "Sibling skills:" list — append `` `test-assets` (test-fixture sourcing, the non-training counterpart of this skill), `` before the `architect` entry.
(e) Changelog, new top line:

```markdown
- 1.2.0 (2026-07-18): scope seam with the new test-assets skill made
  explicit — description negative-scope, cross-reference, sibling link.
```

- [ ] **Step 3: Validate + commit**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → PASS.

```bash
git add archive/data/1.1.0 skills/data/SKILL.md
git commit -m "skill(data): 1.2.0 — test-fixture sourcing routed to test-assets; archive 1.1.0

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 10: architect 1.3.1 → 1.4.0 routing row (after Gate 2 approval)

**Files:**
- Create: `archive/architect/1.3.1/` (copy of current `skills/architect/`)
- Modify: `skills/architect/SKILL.md`

- [ ] **Step 1: Archive first**

```bash
mkdir -p archive/architect && cp -R skills/architect archive/architect/1.3.1
```

- [ ] **Step 2: Edit skills/architect/SKILL.md**

(a) Frontmatter: `version: 1.3.1` → `version: 1.4.0`.
(b) Read the routing-table section (the category containing the `testing` row, around line 163) and insert directly after the `testing` row, matching the table's exact column format:

```markdown
| `test-assets` | Sourcing the data tests run against — canonical worlds/models/datasets, fixture layout, goldens. Load with `testing` when planning the test setup. |
```

(c) Changelog, new top line:

```markdown
- 1.4.0 (2026-07-18): routing table gains the new test-assets skill
  (test-data sourcing, paired with testing).
```

- [ ] **Step 3: Validate + commit**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → PASS.

```bash
git add archive/architect/1.3.1 skills/architect/SKILL.md
git commit -m "skill(architect): 1.4.0 — routing table gains test-assets; archive 1.3.1

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 11: Repo sweep — counts and stale claims

**Files:**
- Modify: `README.md`, `CLAUDE.md`

- [ ] **Step 1: Newline-flattened sweep for stale facts**

```bash
for f in README.md CLAUDE.md docs/BACKLOG.md skills/*/SKILL.md skills/*/references/*.md; do
  tr '\n' ' ' < "$f" | grep -oE "19 skills|nineteen skills" >/dev/null && echo "STALE COUNT: $f"
  tr '\n' ' ' < "$f" | grep -oiE "no (skill|coverage) (for|of)[^.]*test.?(data|asset|fixture)" >/dev/null && echo "STALE QUALIFIER: $f"
done
```

Expected hits: README.md and CLAUDE.md (counts). Fix every hit; re-run until silent.

- [ ] **Step 2: README.md**

(a) `## Skills` intro: `19 skills: 9 umbrellas` → `20 skills: 10 umbrellas`.
(b) Add a table row in the umbrella block, after the `testing` row:

```markdown
| test-assets | umbrella | deep | Canonical test assets and fixture sourcing: which worlds, robot models, and sample datasets to test against, the standard test-assets layout, and pointer-vs-vendored policy. |
```

- [ ] **Step 3: CLAUDE.md**

(a) Commands section: `Must print "Checked 19 skills: PASS"` → `"Checked 20 skills: PASS"`.
(b) Architecture bullet listing the umbrellas: add `test-assets` to the umbrella list and update `19 skills` → `20 skills`.

- [ ] **Step 4: Validate + commit**

Run: `uv run skills/skill-author/scripts/validate_skills.py` → `Checked 20 skills: PASS`.

```bash
git add README.md CLAUDE.md
git commit -m "docs: catalog count 19 → 20 — test-assets added to README table and CLAUDE.md

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 12: Backlog updates

**Files:**
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Edit three places**

(a) **Now item 0** (the eval item added 2026-07-18): replace its body with the current plan of record — keep the heading, replace content with:

```markdown
0. **Test data track** (re-scoped 2026-07-18 after brainstorm; specs committed).
   Shipped shape: the `test-assets` skill (this repo) + an owned vendored corpus in
   robium-applications built THROUGH the skill as its first hardening run. Specs:
   docs/superpowers/specs/2026-07-18-test-assets-skill-design.md and
   robium-applications docs/superpowers/specs/2026-07-18-test-assets-corpus-design.md.
   Sequence: (a) author skill ✓ when Task 6 lands; (b) corpus hardening run in
   robium-applications (vendored mode, plain git, ~300 MB budget, worlds: TB3 House +
   Tugbot in Warehouse; models: TB3, Unitree Go2/G1, SO-101; datasets:
   svla_so101_pickplace + pusht slices); (c) learnings absorbed per the loop.
```

(b) **Later** section, add two items:

```markdown
- Robium self-eval harness (with/without-plugin scenario runs, trigger-paraphrase
  reliability measurement) — as a skill-author extension, NOT part of test-assets
  (decided 2026-07-18). Feeds the launch-readiness with/without showcase numbers.
- HF org `robium` as fixture host: verified 2026-07-18 that Hub dataset repos accept
  arbitrary binaries (rosbag/MCAP; 200 GB/file; no viewer preview) — deliberately
  unused for now; the escape hatch for expensive-to-regenerate fixtures.
```

(c) **Quality & battle-testing track** item 1 ("Eval harness v1 — promoted to Now item 0"): update to "superseded by the test-data track in Now item 0; the agent-eval harness itself moved to Later (skill-author extension)."

- [ ] **Step 2: Commit**

```bash
git add docs/BACKLOG.md
git commit -m "docs(backlog): test-data track re-scoped — test-assets skill + corpus-via-skill; eval harness to Later

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 13: Handoff to the hardening run (no code)

- [ ] **Step 1: Tell the user the skill is live and the next session's shape**

The corpus build happens as a **hardening session anchored in robium-applications** (per its CLAUDE.md and the corpus spec) — invoke the `test-assets` skill there and follow its Quick start to build `test-assets/` in vendored mode; capture friction in `learnings/`; flip the example manifest's `status: unverified` on success. Deliberately not scripted here: it must exercise the skill the way a user would. Also note for later: the robium-cli catalog is regenerated from skill frontmatter at publish time — next CLI publish picks up the new skill automatically (memory: robium-cli-npm-package).

---

## Self-review (completed at authoring)

- **Spec coverage:** description/trigger surface (T1), body sections + matrix + funnel + pyramid mapping (T1), layout reference (T2), catalog with citations + gaps (T3), vendor script both modes (T4), example manifest unverified (T5), validator-to-20 (T1/T6), cross-skill edits gated (T7–T10), sweep including CLAUDE.md "19 skills" (T11), backlog updates incl. eval-harness Later item and HF escape hatch (T12), hardening plan (T13). Excluded per spec: record-a-bag helper, eval harness, CI.
- **Placeholders:** the example manifest's `PIN-AT-ADOPTION` values are the spec'd design (pins resolve at first vendor; `--check` enforces), not plan gaps.
- **Type consistency:** manifest field names identical across T2 schema, T4 script, T5 example (`name/path/kind/upstream/subpath/revision/fetched/license/notes/deps/allow_patterns`); script CLI flags consistent (`--manifest/--only/--check`).
```
