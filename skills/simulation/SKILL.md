---
name: simulation
version: 1.1.2
description: >
  Choose and set up robotics simulators, and simulate sensors correctly: Gazebo
  vs Isaac Sim selection, sensor fidelity (rates, noise models, frames matching
  the real robot), determinism, and sim-to-real considerations. Use when:
  'simulate', 'which simulator', 'test without hardware', 'sensor simulation',
  'sim-to-real', or any simulation-strategy question. Umbrella skill: after
  selection, load gazebo or isaac-sim for mechanics. Selection rule of thumb:
  ROS-centric mobile robotics or no NVIDIA GPU → gazebo; photorealism,
  synthetic data at scale, or NVIDIA RL stack → isaac-sim. Not for:
  simulator-specific how-to (gazebo, isaac-sim).
---

# simulation

The simulator-selection umbrella for robium. Testing without hardware is one of
robium's default postures, but "simulate it" is not itself a decision; Gazebo
and Isaac Sim solve different problems and have different (GPU) requirements,
and either one produces a sensor stack that is only as trustworthy as the
fidelity choices made when setting it up. This skill decides which simulator
fits a given project and states the cross-cutting sensor-correctness practice
that applies to whichever one gets chosen. It does not teach either
simulator's own mechanics (SDF worlds, `ros_gz`, USD scenes, the ROS 2
bridge); that is `gazebo` and `isaac-sim`'s territory.

## When to use this skill

- The simulator hasn't been chosen yet for a project; this is a required
  early decision for any sim-first build, the same way `environments` is
  required before writing application code.
- The trigger phrases in the description: 'simulate', 'which simulator', 'test
  without hardware', 'sensor simulation', 'sim-to-real'.
- Setting up a new sensor in *either* simulator and the question is about
  correctness (rate, noise, frame, timestamp) rather than the SDF/USD syntax
  to express it.
- Cross-references: go straight to the tool skill, skipping this one, once
  the simulator is already chosen and the question is mechanics:
  - SDF worlds/models, `ros_gz` bridge config, spawning a robot into Gazebo →
    `gazebo`.
  - USD scenes, the Isaac Sim ROS 2 bridge, Replicator synthetic-data
    generation → `isaac-sim`.
  - Whether an NVIDIA RTX GPU is actually available/confirmed on the target
    machine → still this skill's gate (see Key directives), but the detailed
    GPU/driver floor table lives in `isaac-sim`.
  - Autonomous navigation behavior once sensor data is flowing → `nav2`.
  - Deciding *what data* to generate in sim (as opposed to how) → `data`.
  - The whole-stack decision this feeds into → `architect` (routes here).

## Key directives

- **Delegation posture: route + embed the decision logic.** The simulator
  *selection* and the sensor-correctness checklist live here; SDF/USD syntax,
  bridge configuration, and scene-building mechanics live downstream in
  `gazebo` and `isaac-sim`. Never re-teach either tool's mechanics here.
- **State the GPU requirement before recommending Isaac Sim, every time.** <!-- id: state-gpu-requirement-before-isaac-sim -->
  Isaac Sim needs an NVIDIA RTX-class GPU; the current floor, per
  `isaac-sim`'s own verified requirements, is an RTX 4080 with 16 GB VRAM
  minimum (GPUs without RT cores, e.g. datacenter A100/H100 parts, are
  unsupported regardless of VRAM). If a qualifying GPU hasn't been confirmed,
  do not design the project around Isaac Sim; route to `gazebo` and log the
  GPU question as an open risk, matching `architect`'s posture.
- **Sensor fidelity is not optional.** <!-- id: sensor-fidelity-not-optional --> A sensor simulated at a default
  rate/noise/frame that doesn't match the real target hardware produces a
  stack that "works in sim" and then behaves differently the moment it meets
  real sensor data. Walk the sensor-correctness checklist in Decision guidance
  for every simulated sensor before treating it as ready; this applies
  identically in Gazebo and Isaac Sim.
- **Determinism matters for regression testing, not just fidelity.** <!-- id: determinism-matters-for-regression-testing --> A
  simulation used as a CI/regression check (see the `testing` skill's sim
  scenario layer) needs a seeded, repeatable configuration (physics step
  size, RNG seeds for any randomization, and `use_sim_time` set consistently),
  or a flaky test will get blamed on the code instead of the sim setup.
- **Sim-to-real is a gap to close, not assume away.** <!-- id: sim-to-real-gap-close-not-assume --> Neither simulator
  produces real-world-identical sensor data or dynamics by default; state the
  known gap (visual domain gap, contact/friction modeling, latency) as an open
  risk for anything that will eventually run on real hardware, and prefer
  matching real sensor specs over relying on domain randomization alone unless
  the project is specifically generating training-scale synthetic data (see
  `data`).

## Quick start

**1. Answer the selection question** using the rule of thumb below, confirming
the GPU floor first if Isaac Sim is even a candidate.

**2. Load the matching tool skill** (`gazebo` or `isaac-sim`) for installation
and world/scene setup.

**3. For every sensor added, walk the sensor-correctness checklist** in
Decision guidance before trusting its output.

**4. If the simulation will back a regression test,** confirm determinism
(seeded config, `use_sim_time`) before wiring it into `testing`'s sim-scenario
layer.

## Decision guidance

**Selection tree:**

```
Does the project need photorealism, synthetic data at scale, or the NVIDIA RL
stack (Isaac Lab)?
│
├─ Yes, AND an NVIDIA RTX GPU (RTX 4080/16GB VRAM floor) is confirmed
│   → isaac-sim
│
├─ Yes, but no qualifying GPU confirmed
│   → gazebo (log the GPU gap as an open risk; revisit if hardware changes)
│
├─ No, AND the task is lightweight contact-rich single-arm manipulation
│   with no ROS requirement (e.g. a grasp / pick-and-place policy env)
│   → mujoco (see the mujoco skill: fast, native on Apple Silicon, no GPU
│     or ROS needed; the non-ROS manipulation alternative to gazebo)
│
└─ No: ROS-centric mobile robotics, standard sensor sim, no need for
   photoreal rendering or GPU-parallel RL
   → gazebo (the paired sim for the robium nav vertical, Gazebo Harmonic ↔
     ROS 2 Jazzy)
```

For a contact-rich single-arm manipulation task that does not need ROS
integration, GPU-photoreal rendering, or a mobile-robot sensor stack (a
hand-built grasp / pick-and-place environment, for instance), MuJoCo is the
lightweight option: it runs fast and natively (including on Apple Silicon,
where the ROS + Gazebo stack needs Docker) with headless offscreen rendering.
Route those tasks to the `mujoco` skill, which owns MuJoCo's mechanics and the
manipulation-sim gotchas (MJCF assets, hand-rolled IK, grasp calibration).

**Sensor-correctness checklist** (walk this for every simulated sensor,
regardless of simulator):

- [ ] **Rate** <!-- id: sensor-rate-matches-datasheet -->: matches the real sensor's datasheet rate, not the tutorial's
  default (a lidar or camera simulated too fast/slow skews anything tuned
  against real hardware, e.g. a costmap update rate).
- [ ] **Noise model** <!-- id: noise-model-present -->: present and roughly matched to the real sensor's noise
  floor; a zero-noise sensor is a common cause of a perception/localization
  stack that "works perfectly in sim" and then struggles on real data.
- [ ] **Frame names** <!-- id: frame-names-match-real-tf -->: `frame_id`/`child_frame_id` match the real robot's TF
  tree exactly, not a simulator-default name, so downstream consumers (Nav2,
  a perception node) don't need sim-only remapping.
- [ ] **Timestamps** <!-- id: timestamps-from-sim-clock -->: derived from the simulation clock, not wall-clock time.
- [ ] **`use_sim_time`** <!-- id: use-sim-time-consistent-everywhere -->: set to `true` consistently across every node in the
  system; a single node left unset runs off wall-clock time while everything
  else uses sim time, producing subtle, hard-to-diagnose TF/timing mismatches.

## Platform gotchas

- **Isaac Sim has no macOS support at all** <!-- id: isaac-sim-no-macos-support -->: not the GUI, container, or pip
  package (see `isaac-sim`'s Platform gotchas). A macOS dev machine needs a
  remote Linux or Windows GPU host for that path; there is no local
  workaround.
- **Gazebo's ROS 2 integration still needs Docker on macOS.** <!-- id: gazebo-ros2-integration-needs-docker-macos --> `gz sim` itself
  has a native macOS build, but the `ros_gz` bridge links against ROS 2, which
  has no native macOS install, so the full ROS 2 + Gazebo + bridge stack this
  skill assumes runs in Docker on a Mac dev machine (see `gazebo`'s and
  `ros2`'s macOS gotchas).
- **Headless is the default for both, for CI and remote work** <!-- id: headless-default-for-both-ci -->: Gazebo's
  server-only mode and Isaac Sim's `runheadless.sh` both avoid needing a local
  display; route the general headless/remote strategy question to
  `environments` if it isn't decided yet.

## Customization

- **Mixed pipeline (Gazebo for the robot, Isaac Sim for synthetic data):** the
  selection tree picks a primary simulator per concern, not per project; it's
  reasonable to prototype navigation in `gazebo` while generating training-scale
  synthetic manipulation data separately in `isaac-sim`, provided the GPU floor
  is met for the latter. Keep the two uses and their sensor-correctness
  checklists independent.
- **GPU becomes available mid-project:** re-run the selection tree rather than
  assuming the original `gazebo` choice is permanent; a project that starts
  GPU-less and later gets access to a qualifying RTX machine can migrate
  synthetic-data-heavy or photoreal-dependent work to `isaac-sim`.

## References

- Upstream: [Gazebo documentation](https://gazebosim.org/docs/),
  [Gazebo releases](https://gazebosim.org/docs/all/releases/),
  [Isaac Sim documentation](https://docs.isaacsim.omniverse.nvidia.com/),
  [Isaac Sim installation requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html).
- Sibling skills: `gazebo` (no-GPU / ROS-centric simulator mechanics),
  `mujoco` (lightweight non-ROS contact-rich single-arm manipulation sim),
  `isaac-sim` (GPU-gated photoreal simulator mechanics), `isaac-lab` (RL
  training on top of Isaac Sim, same GPU gate), `data` (what data to generate
  in sim, as opposed to how), `nav2` (consumes sensor data this skill's
  checklist governs), `environments` (headless/remote and GPU-container
  setup), `architect` (routes here, GPU-gated).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.1.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 1.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.1.0 (2026-07-31): note MuJoCo (see the mujoco skill) as the lightweight non-ROS manipulation-sim option.
