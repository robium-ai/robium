---
name: data
version: 1.2.3
description: >
  Data sourcing strategy for robotics and physical-AI: choose between offline
  datasets (HuggingFace hub, Open X-Embodiment and similar), simulation-generated
  data, and teleop/real-robot collection; plan storage formats, episode
  structure, and dataset versioning. Use when: 'where do we get data', 'training
  data for the robot', 'dataset for manipulation', 'generate data in sim',
  'collect demonstrations', planning any data pipeline for robot learning.
  Umbrella skill; mechanics live downstream: hub operations in huggingface,
  LeRobot formats in lerobot, synthetic generation in isaac-sim/gazebo. Not for:
  model training itself (lerobot, isaac-lab) or sourcing test
  fixtures/assets (test-assets).
---

# data

The data-sourcing umbrella for robium. Before any policy gets trained, something
has to decide where the training data comes from (an existing hub dataset, data
generated in simulation, or demonstrations collected via teleop on a real robot)
and how it will be stored and versioned once it exists. This skill owns that
selection and the cross-cutting sourcing rules; it does not own hub mechanics
(`huggingface`), the LeRobotDataset format (`lerobot`), or the mechanics of
generating synthetic data inside a simulator (`isaac-sim`, `gazebo`). It also
does not own training itself; that is `lerobot` and `isaac-lab`'s territory.

## When to use this skill

- Starting any robot-learning task and the data source isn't decided yet; this
  is a required early step for the manipulation vertical, the same way
  `environments` is a required early step for reproducibility.
- The trigger phrases in the description: 'where do we get data', 'training
  data for the robot', 'dataset for manipulation', 'generate data in sim',
  'collect demonstrations'.
- Planning storage format, episode structure, or dataset versioning before a
  collection or generation effort starts, not after.
- Cross-references: go to the sibling skill instead when the question is:
  - Actually pulling, pushing, or browsing a dataset on the Hub → `huggingface`.
    This skill decides *which* dataset or source strategy to use; it does not
    own hub auth or transfer mechanics.
  - The LeRobotDataset directory/Parquet+MP4 shape, recording CLI, or dataset
    editing tools → `lerobot`. This skill decides *whether* to record real
    demonstrations at all; `lerobot` owns how a recording actually happens.
  - The mechanics of generating synthetic data inside a simulator (Replicator,
    domain randomization, writers) → `isaac-sim` or `gazebo`. This skill
    decides *whether* sim-generated data is the right call for a task.
  - Training a policy on the data once sourced → `lerobot` (or `isaac-lab` for
    the NVIDIA RL stack).
  - The whole-stack decision this feeds into → `architect` (routes here).
  - Sourcing *test* data (worlds, models, sample datasets, fixtures, and
    goldens for smoke/regression tests) → `test-assets`. This skill owns data
    that trains policies; `test-assets` owns data that tests apps.

## Key directives

- **Delegation posture: route + embed the decision logic.** The sourcing
  *decision* (offline vs sim-generated vs teleop, and how much of each) lives
  here; the *how-to* for each source lives in the skill it routes to. Never
  re-teach hub operations, LeRobot dataset internals, or simulator synthetic-
  data pipelines here; link to the owning skill instead.
- **Offline-first: search before you collect.** <!-- id: offline-first-search-before-collect --> Before generating or recording
  a single new episode, search the Hub (and Open X-Embodiment specifically for
  manipulation) for an existing dataset that already covers the task and
  embodiment. Collection and generation both cost real time and compute;
  skipping the search step is the most common way a project re-collects data
  that already exists.
- **Verify embodiment match before committing to a dataset.** <!-- id: verify-embodiment-match-before-committing --> A dataset with
  the right task but the wrong action space, camera viewpoint(s), gripper type,
  or degrees of freedom does not transparently transfer; check the dataset's
  state/action features and camera configuration against the target robot
  before planning a project around it, not after a training run underperforms.
  A near-match is a candidate for co-training or fine-tuning, not a drop-in
  replacement.
- **Episode density beats episode count for imitation/VLA datasets.** <!-- id: episode-density-beats-count --> More
  episodes over a wide workspace does not substitute for tighter coverage of a
  small one: 50 episodes over a 30cm workspace was a documented outright failure
  (the policy learned the motion but couldn't pin down grasp locations), while
  75 episodes over ~10cm reached 80% success. When planning episode structure,
  constrain the workspace tightly before adding more episodes over a wide one
  (vla-trial).
- **Discard or retry failed demonstrations; never let oracle misses into the
  training set.** <!-- id: discard-failed-demonstrations-never-train --> When generating a dataset from a scripted oracle (or any
  imperfect source), keep only success episodes; discard or retry failures
  rather than recording them as-is, so oracle misses don't poison training. Add
  a runaway guard that fails loudly if the success rate collapses (a real
  regression) instead of looping forever trying to hit a target episode count
  (vla-trial).
- **Weigh sim-generation against teleop by cost and fidelity, not habit.** <!-- id: weigh-sim-vs-teleop-by-cost-fidelity -->
  Neither is a universal default; see Decision guidance for the trade-off.
- **Never write dataset facts (episode counts, formats, licensing) from
  memory.** <!-- id: never-write-dataset-facts-from-memory --> Hub dataset cards and the Open X-Embodiment dataset list change as
  new contributions land; confirm the current shape of a specific dataset
  against its Hub page or the source repo before planning a project around it.

## Quick start

**1. Define the task and embodiment precisely**: robot morphology, action
space, camera views, task description. This is the search key for step 2 and
the compatibility check for step 3.

**2. Search for an existing dataset first.** Check the Hub's robotics/LeRobot
tags and Open X-Embodiment for a dataset matching the task and embodiment
(mechanics: `huggingface`). If one exists and the embodiment matches, use it
directly; skip to step 5.

**3. If no match, decide sim-generation vs teleop** using the trade-off table
in Decision guidance. Route to `isaac-sim` or `gazebo` for sim-generation
mechanics, or `lerobot` for teleop-based recording mechanics.

**4. Plan storage and versioning before collecting anything.** <!-- id: plan-storage-before-collecting --> Decide the
target dataset format (LeRobotDataset, mechanics in `lerobot`) and where it
will be versioned (a Hub repo with explicit revisions, mechanics in
`huggingface`) so episodes land in their final shape from the first one
recorded, not migrated after the fact.

**5. Record the chosen source strategy** in the project's architecture brief
(the section `architect` maintains) so later phases don't re-litigate it.

## Decision guidance

**Offline-first funnel:**

```
Search Hub + Open X-Embodiment for the task/embodiment
│
├─ Match found, embodiment matches   → use it directly (huggingface + lerobot)
├─ Partial match (task ✓, embodiment ✗) → candidate for co-training/fine-tune,
│                                          not a drop-in; still need new data
└─ No match                          → choose sim-generation or teleop below
```

**Sim-generation vs teleop/real-robot collection trade-offs:**

| Factor | Sim-generated | Teleop / real-robot |
|---|---|---|
| Cost per episode | Low: scales to thousands of episodes with compute, not human time | High: a human operator per episode, hardware wear |
| Scale | Easy to get large volumes via domain randomization | Bounded by operator time; large datasets are expensive |
| Realism / sim-to-real gap | Real risk: visual and physics gaps unless deliberately closed (domain randomization, matched sensor noise) | Ground truth by construction: no sim-to-real gap |
| When to prefer | Early iteration, pretraining, cases where large scale matters more than perfect fidelity<!-- id: sim-preferred-early-iteration-pretraining --> | Final validation, tasks with contact-rich or hard-to-simulate dynamics, or when the sim-to-real gap can't be closed cheaply<!-- id: teleop-preferred-final-validation-contact-rich --> |
| GPU requirement | `isaac-sim` route needs the NVIDIA RTX GPU floor; `gazebo` route does not | None beyond the target robot and a recording workstation |

A common effective pattern is both: bulk sim-generated episodes for scale and
coverage, plus a smaller teleop set for real-world validation and to measure
(and later close) the sim-to-real gap. Decide the mix explicitly and record it
rather than defaulting to only one source.

## Platform gotchas

- **The sim-generation route inherits its simulator's gates.** <!-- id: sim-generation-inherits-simulator-gpu-gate --> Choosing
  `isaac-sim` for data generation means meeting its NVIDIA RTX GPU floor first
  (see that skill's Key directives); choosing `gazebo` does not require a GPU.
  Don't plan a sim-generation-heavy data strategy around Isaac Sim before the
  GPU question is confirmed; fall back to `gazebo` or a teleop-heavy plan
  otherwise.
- **Real-robot teleop collection has no headless shortcut.** <!-- id: teleop-collection-no-headless-shortcut --> It requires a
  physical robot, an operator, and (per `lerobot`'s own gotchas) a working
  keyboard/input teleop path that doesn't fully work over a headless/Wayland
  session; plan collection sessions on a machine with a real display and
  input device attached.

## Customization

- **Different task domain (navigation vs manipulation):** the offline-first
  funnel applies either way, but Open X-Embodiment is manipulation-specific;
  for navigation data, search the Hub's general robotics/SLAM datasets instead
  and lean more heavily on `gazebo`-generated data, since teleop collection for
  navigation is comparatively cheap (no arm/gripper precision required).
- **Multi-embodiment projects:** treat each embodiment's data need separately
  through the same funnel rather than assuming one sourced dataset covers every
  robot in the fleet; verify the embodiment-match step per robot.

## References

- Upstream: [Hugging Face Hub dataset docs](https://huggingface.co/docs/hub/en/datasets-overview),
  [Hugging Face Datasets library docs](https://huggingface.co/docs/datasets/en/index),
  [Open X-Embodiment project page](https://robotics-transformer-x.github.io/),
  [Open X-Embodiment GitHub repo](https://github.com/google-deepmind/open_x_embodiment),
  [LeRobot documentation](https://huggingface.co/docs/lerobot/index) (dataset
  format detail, owned downstream by `lerobot`).
- Sibling skills: `huggingface` (hub operations), `lerobot` (LeRobotDataset
  format and recording mechanics), `isaac-sim` and `gazebo` (synthetic-data
  generation mechanics), `isaac-lab` (RL training that consumes this data),
  `test-assets` (test-fixture sourcing, the non-training counterpart of this
  skill), `architect` (routes here, records the sourcing decision in the
  brief).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.2.3 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 1.2.2 (2026-08-01): decision-table rows anchored (learning-engine Phase 1 follow-up); no content changes.
- 1.2.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.2.0 (2026-07-18): scope seam with the new test-assets skill made
  explicit: description negative-scope, cross-reference, sibling link.
- 1.1.0 (2026-07-15): vla-trial absorption: Key directives gains two
  data-quality bullets: episode density over count for imitation/VLA
  datasets (workspace-width failure vs success case), and discard/retry-
  failed-demonstrations from scripted-oracle sources with a runaway
  success-rate guard.
