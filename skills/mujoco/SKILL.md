---
name: mujoco
version: 1.0.2
description: >
  MuJoCo for lightweight, contact-rich robot manipulation simulation on
  macOS/Linux, especially single-arm grasping without ROS: headless offscreen
  rendering, MJCF models, mujoco_menagerie assets, damped-least-squares inverse
  kinematics, and empirical grasp calibration. Use when: 'MuJoCo', 'MJCF',
  'mjpython', 'MUJOCO_GL', 'menagerie', 'SO-101' / SO-ARM100 arm, 'offscreen
  render', 'inverse kinematics' / 'IK', 'grasp' / 'pick and place' in sim,
  hand-building a manipulation env, or headless mujoco.Renderer determinism.
  Load after architect or simulation route a non-ROS single-arm manipulation
  task here (Gazebo and Isaac Sim are the ROS / GPU-photoreal alternatives).
  Defers to MuJoCo's own docs and mujoco_menagerie for the physics/model API;
  embeds the macOS-arm64 platform and grasp/IK gotchas hard-won from a real
  SO-101 build. Not for: ROS-integrated sim (gazebo), GPU-parallel RL or
  photoreal synthetic data (isaac-sim / isaac-lab), or LeRobot policy
  training/eval mechanics (lerobot).
---

# mujoco

MuJoCo 3.x for robium's lightweight, non-ROS manipulation side: a fast
contact-rich physics engine with an offscreen renderer, well suited to
hand-building a single-arm grasping/pick-and-place environment when the full
ROS + Gazebo stack (or a GPU-gated Isaac stack) is more than the task needs.
This skill stays deliberately thin on the MuJoCo API itself: the model format
(MJCF), the Python bindings, and the robot assets in mujoco_menagerie are all
documented upstream and move release to release. What it embeds instead is the
set of hard-won gotchas from the vla-trial SO-101 build (macOS arm64, MuJoCo
3.x, observed 2026-07-13/14): the macOS headless-render backend, version-pin
traps, offscreen-render determinism, and the IK / grasp-calibration failure
modes that cost the most time and give no error message when they bite.

## When to use this skill

- Simulating a low-DOF arm (grasping, pick-and-place, contact-rich
  manipulation) where ROS is not required and a GPU-photoreal simulator is
  overkill; MuJoCo runs natively and fast on Apple Silicon.
- Rendering camera observations headless for a policy/dataset pipeline, and
  needing that rendering to be deterministic/reproducible.
- Writing an inverse-kinematics reach + grasp routine by hand (damped
  least-squares), and debugging why the arm won't reach or knocks the object
  over.
- Loading a robot from mujoco_menagerie (e.g. the SO-101 / SO-ARM100 arm) and
  adapting its scene into a manipulation task.
- The trigger phrases in the description: 'MuJoCo', 'MJCF', 'mjpython',
  'MUJOCO_GL', 'menagerie', 'SO-101', 'offscreen render', 'IK', 'grasp'.
- Cross-references: go to the sibling skill instead when the question is:
  - A ROS 2-integrated simulation (ros_gz bridge, SDF worlds) → the `gazebo`
    skill.
  - Photoreal rendering, synthetic data at scale, or GPU-parallel RL → the
    `isaac-sim` / `isaac-lab` skills (GPU-gated).
  - Which simulator to pick at all → the `simulation` umbrella (routes here for
    lightweight non-ROS manipulation).
  - LeRobot dataset/policy training/eval mechanics → the `lerobot` skill;
    MuJoCo here is only the sim that produces observations/actions.
  - The whole-stack decision this feeds into → the `architect` skill.

## Key directives

- **Delegation posture: embed + links.** The robium-specific,
  hard-won gotchas (macOS render backend, version pins, offscreen-render
  determinism, IK/grasp failure modes) live here because they are not written
  down anywhere upstream. For the physics/model API itself (MJCF syntax, the
  `mujoco` Python bindings, `mj_step`/`mj_forward`, the `Renderer` class, and
  robot assets) point upstream to MuJoCo's docs and the mujoco_menagerie repo
  (see References); do not restate the API from memory, it changes across 3.x
  releases.
- **On macOS, `MUJOCO_GL=cgl` is the only headless render backend.** <!-- id: macos-gl-cgl-only --> osmesa and
  egl are Linux-only (mujoco#2164). Set it before importing `mujoco`.
- **Watch the version-pin trap.** <!-- id: mujoco-version-pin-trap --> Menagerie's SO-101 needs MuJoCo ≥3.1.3, but
  common gym wrappers pin it *down* (gym-hil pins `mujoco<3.9`, gym-xarm pins
  `<3.0`); depending on one of those can silently downgrade MuJoCo below the
  model's requirement. Pin MuJoCo explicitly and verify the installed version.
- **Hand-written IK fails silently.** <!-- id: ik-fails-silently --> A damped-least-squares solver does not
  raise on an unreachable target or on a bad grasp orientation; it returns a
  locally-optimal pose short of the goal. Probe reachability and calibrate
  grasps empirically (see Usage patterns); never assume a returned qpos means
  success.
- **Verify the asset matches the robot's intended work envelope** <!-- id: verify-asset-work-envelope --> before
  blaming IK. Menagerie scenes are generic and can put the floor, object spawn,
  or camera in the wrong place for the arm (see Platform gotchas).

## Quick start

**1. Install (pin MuJoCo explicitly, above the menagerie floor):** <!-- id: pin-mujoco-install -->

```bash
uv add "mujoco>=3.1.3"   # current 3.10 as of 2026-07; SO-101 needs >=3.1.3
```

Do not let a gym wrapper (gym-hil, gym-xarm) choose the version transitively;
it can pin MuJoCo below what the model needs.

**2. Get the robot asset from mujoco_menagerie, not upstream MJCF.** <!-- id: use-menagerie-not-upstream-mjcf --> Clone
[mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie) and use
its SO-101 model (the robotstudio_so101 directory, which ships a pick-and-place
scene, manipulation-tuned collision geometry, and a camera mount). Do NOT use
the upstream TheRobotStudio/SO-ARM100 MJCF: its own README admits the gripper
linear-joint mapping is not reflected in the model.

**3. Headless offscreen render (macOS):**

```python
import os
os.environ["MUJOCO_GL"] = "cgl"   # macOS headless backend; must precede import
import mujoco

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)
renderer = mujoco.Renderer(model, height=256, width=256)
# warm-up: one throwaway full reset+render (see determinism gotcha below)
mujoco.mj_resetData(model, data)
mujoco.mj_forward(model, data)
renderer.update_scene(data, camera="fixed_cam")
_ = renderer.render()
```

**4. Interactive viewer needs `mjpython`.** `mujoco.viewer.launch_passive`
requires launching with `mjpython`, not `python` (and is buggy under `uv`,
mujoco#1923). Offscreen rendering (step 3) has no such requirement.

For MJCF syntax, the bindings, and API signatures, go to MuJoCo's own docs
(References) before hand-writing model or physics code.

## Usage patterns

**Headless render is not the bottleneck on Apple Silicon.** <!-- id: render-not-bottleneck --> Measured on the
vla-trial build: ~84 fps at 256x256 via `MUJOCO_GL=cgl`, against a 60 fps
floor; `mj_step` ~0.012 ms vs ~11.8 ms per render. This kills the common
upstream worry that "offscreen render is extremely slow": for a low-DOF arm
scene it is comfortably real-time. Render, don't skip frames to save time.

**Deterministic offscreen rendering** (needed for reproducible datasets/evals):

- **Use a static xyaxes look-at camera, not `mode="targetbody"`.** <!-- id: static-camera-not-targetbody --> A
  target-tracking camera re-runs its smoothing filter on every
  `update_scene()`, making the rendered pose call-history-dependent (observed
  up to 85 LSB drift) even when the physics is bit-identical.
- **Warm up the renderer with one throwaway full reset + render in `__init__`.** <!-- id: renderer-warmup-reset -->
  A fresh `mujoco.Renderer`'s first reset→`mj_forward`→render cycle is not
  repeatable against later renders (~6 LSB). A raw pre-`mj_forward` warm-up does
  NOT consume the cold cycle; it must be a full reset+render.
- Ruled out as a cause: MSAA offsamples (a red herring here).

**Reachability probing (IK).** <!-- id: reachability-probing-ik --> Because the DLS solver returns silently on an
unreachable target, probe the full task footprint × every lift height
*independently* before trusting the env. Menagerie's default box spawn
(0.5, 0, 0.03) is unreachable by the SO-101 mount, for example.

**Empirical grasp calibration.** <!-- id: empirical-grasp-calibration --> The end-effector site is not the grasp point.
Calibrate the gripper-local grasp offset by experiment: teleport the object to
a grid, close, lift, and keep the offsets that actually lift. Key facts:

- Calibration is a function of **pose**, not a gripper property; recalibrate <!-- id: grasp-calibration-is-pose-function -->
  after any wrist-orientation change.
- It is millimeter-sensitive and non-monotonic: a 3 mm offset change cost 6/10 <!-- id: grasp-offset-millimeter-sensitive -->
  success in one sweep. Sweep the grasp offset *and* the pedestal height
  end-to-end rather than tuning one in isolation.

**Wrist-roll orientation is the silent half of position-only IK.** <!-- id: wrist-roll-position-only-ik --> On a 5-DOF
arm, position-only IK leaves wrist roll free. At roll≈0 the pinch axis was 91%
vertical, so a 4.2 cm aperture could not span a 6 cm cube (closed on air,
0/10). Diagnostic: print the world-frame pinch axis and check it is
perpendicular to the grasped dimension. Fix: solve wrist roll as a 1-D root
find (`pinch_z(roll)` is a smooth sinusoid), then re-solve position with roll
pinned via jnt_range; adding roll to the DLS objective *diverges*. This took
the oracle grasp from 0/10 to 8/10. (Position-only IK also gives no signal
about the orientation it chose; a level-finger constraint may be genuinely
infeasible on a 5-DOF arm.)

**Debugging "arm won't reach / knocked the object over":**

- **Bisect IK vs obstruction** <!-- id: bisect-ik-vs-obstruction --> by deleting/banishing the object and re-running
  the same pose. Cube present: arm_err=0.18, saturated_joints=[1 2]; cube
  banished: arm_err=0.0006, saturated=[]. Instantly tells you whether IK or a
  collision is the problem.
- **Check `qfrc_actuator` vs `forcerange`** <!-- id: check-qfrc-actuator-forcerange -->: saturated joints mean BLOCKED,
  not slow. Raising settle steps (e.g. 12→60) is a dead end when joints are
  saturated.
- **The first waypoint can sweep the arm through the object** <!-- id: first-waypoint-sweep-collision -->: a position
  servo takes an arbitrary joint path to the target. Raising the initial
  approach waypoint (0.16→0.20 m) fixed a 2/10 → 10/10 grasp.

**Resolve gripper geoms by body, not name.** <!-- id: gripper-geoms-by-body --> Menagerie leaves mesh geoms
UNNAMED, so a name-based gripper-geom list silently misses the fixed-jaw
collision mesh, a false-success risk in contact checks. Collect gripper geoms
by `model.geom_bodyid` membership instead.

**Determine gripper polarity empirically.** <!-- id: gripper-polarity-empirical --> Drive the gripper joint to each end
of its `actuator_ctrlrange` and measure the fingertip gap. SO-101 is
LOW=closed / HIGH=open; the upstream SO-ARM100 docs claim the opposite and even
admit their own MJCF disagrees, so measure, don't trust the docs.

## Platform gotchas

- **macOS headless render backend is `MUJOCO_GL=cgl` only** (osmesa/egl are
  Linux-only, mujoco#2164). Set it before `import mujoco`.
- **The macOS CGL renderer is thread-affine: a cross-thread first render is a
  silent deadlock.** <!-- id: cgl-thread-affine-deadlock --> A `mujoco.Renderer` created on one thread hangs forever
  (no error, no timeout, no exception) the first time a *different* thread
  renders on it; the stack sits in cgl `make_current`. This bites frameworks
  that run handlers on worker threads (e.g. Gradio): a first `env.reset()`
  called from a worker freezes the stream. Fix: construct the env/renderer in
  the same thread that runs the episode (a per-run env in the handler), not once
  at import on the main thread. (observed 2026-07-15, vla-trial)
- **Interactive viewer needs `mjpython`**, <!-- id: mjpython-viewer-required --> not `python`, and is buggy under
  `uv` (mujoco#1923). Offscreen rendering does not need `mjpython`.
- **No off-the-shelf SO-101 Gymnasium env exists.** <!-- id: no-so101-gym-env --> gym-hil is Franka-only;
  LIBERO is Linux-only. A language-conditioned SO-101 sim env must be
  hand-built; budget for it rather than expecting to import one.
- **Menagerie assets can be geometrically wrong for the robot.** <!-- id: menagerie-assets-geometrically-wrong --> The SO-101
  scene put the floor at the arm's base level; a real rig has base + objects on
  a raised surface. A 6 cm pedestal restored the intended work envelope (fixing
  a forced ~32° down-pitch). Check the asset world matches the robot's intended
  envelope before blaming the IK solver.

## Customization

- **Different arm from menagerie:** the failure modes above (silent IK,
  unnamed geoms, empirical gripper polarity, static-camera determinism) are
  general MuJoCo/menagerie traps, not SO-101-specific. Re-run the empirical
  calibration (grasp offset grid, gripper-polarity sweep, reachability probe)
  for the new model rather than porting the SO-101 numbers.
- **Different task envelope:** re-check the scene geometry (floor height,
  object spawn, camera pose) against the robot's reach before writing task
  logic; a pedestal or a re-placed spawn is often the fix, not the IK.
- **Feeding a LeRobot pipeline:** MuJoCo here produces the observations and
  executes actions; the dataset format, recording, and policy training/eval
  belong to the `lerobot` skill; keep the sim env and the dataset layer
  separate.

## References

- Upstream (primary sources; check before writing model or physics code):
  [MuJoCo documentation](https://mujoco.readthedocs.io/) (MJCF, Python
  bindings, the `Renderer` API), [google-deepmind/mujoco GitHub
  repo](https://github.com/google-deepmind/mujoco) (releases and the issues
  cited above: #2164 render backends, #1923 viewer-under-uv),
  [mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie)
  (robot assets, incl. the SO-101 model; prefer this over upstream
  TheRobotStudio/SO-ARM100 MJCF). All facts above observed on MuJoCo 3.x,
  macOS arm64, 2026-07-13/14 (vla-trial SO-101 build); re-verify version-tied
  claims against current releases.
- Sibling skills: the `simulation` umbrella (routes here for lightweight
  non-ROS manipulation; owns the Gazebo-vs-Isaac selection), `gazebo` (ROS 2
  simulation), `isaac-sim` / `isaac-lab` (GPU-gated photoreal / RL sim),
  `lerobot` (policy training/eval that consumes this sim's observations),
  `architect` (routes the whole stack decision here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).

- 1.0.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.

- 1.0.0 (2026-07-31): created: captured from the vla-trial SO-101 manipulation build (2026-07-13/14).
