# Scenes, robots, sensors, and synthetic data

USD stage/scene basics, the standalone `SimulationApp` Python workflow,
importing robots, attaching sensors, and the Replicator synthetic-data
pipeline. Source: `docs.isaacsim.omniverse.nvidia.com`'s quickstart, robot
setup, and Replicator tutorial index pages — mostly search-synthesis level
(page-navigation-hub content rather than a single copy-pasteable snippet);
re-verify exact API calls against the live tutorials before depending on
them in a real project. The clock-publisher pattern in
`references/ros2-integration.md` is the one piece of code on this topic
confirmed by direct fetch on 2026-07-10.

## USD stage and scene basics

Isaac Sim scenes are USD (Universal Scene Description) stages. Everything
doable through the GUI can also be done through Python — the standard
workflow is to author or assemble a scene interactively, export it as a
`.usd`/`.usda` file, then drive it from a standalone Python script for
repeatable runs (batch synthetic-data generation, headless regression
testing, and so on).

**Standalone Python workflow.** A standalone script must construct
`SimulationApp` *before* importing anything else from Isaac Sim — the app
object owns the render/physics context that later imports depend on:

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})  # or False for a local display

# Isaac Sim imports must come after SimulationApp is constructed.
import omni.usd
# ... build or load a stage, add robots/sensors, step the sim ...

simulation_app.close()
```

This import-order requirement (`SimulationApp` first, everything else
after) is a common source of confusing import errors if violated — treat
it as a hard rule, not a style preference. Re-verify the exact
`isaacsim.SimulationApp` import path against the current tutorials before
depending on it verbatim; older Isaac Sim releases used
`omni.isaac.kit.SimulationApp` instead, and the module path has moved
across major versions.

**Loading an existing scene.** Open a `.usd` file directly from the GUI's
Asset Browser, which is backed by NVIDIA's Nucleus asset library (hosted
robot and environment assets ready to drop into a stage), or point a
standalone script's stage-open call at a local or Nucleus-hosted USD path.

## Adding a robot

Isaac Sim ships several importers rather than one universal path:

- **URDF Importer** — the most common path for a ROS-ecosystem robot that
  already has a URDF.
- **MJCF Importer** — for robots described in MuJoCo's MJCF format.
- **USD to URDF Exporter** — the reverse direction, useful for round-
  tripping a hand-authored USD robot back into a ROS-facing URDF.
- **Nucleus-hosted assets** — pre-built robot USDs available directly from
  the Asset Browser, skipping import entirely.

Once a robot is in the stage, Robot Setup tooling covers the rest:

- **Robot Inspector** — examine a robot's structure/properties.
- **Robot Assembler** — compose a robot from separate component assets
  (e.g. an arm plus a gripper).
- **Joint Inspector** — examine and tune articulation joints.
- **Robot Poser** — position a robot and save named poses.

Real hardware fit matters here the same way it does for `gazebo`'s sensors:
an imported robot's joint limits, masses, and articulation setup should
match the physical unit's datasheet before results are trusted, not just
whatever the importer's defaults produce.

## Adding sensors

Three sensor families, per the Robot Setup documentation:

- **Camera sensors** — standard RGB/depth rendering through Isaac Sim's RTX
  renderer.
- **RTX sensors** — lidar and radar simulated via the same RTX ray-tracing
  pipeline as camera rendering, rather than a separate physics-only model.
- **Physics-based sensors** — IMU and contact sensors, driven by the physics
  simulation rather than rendering.

As with Gazebo (see that skill's Key directives), pull real rate/FOV/range/
noise numbers from the target sensor's datasheet rather than leaving
importer or tutorial defaults in place — a sensor that "looks right" in a
demo scene but doesn't match the real unit's characteristics produces a
perception stack that quietly breaks the moment it meets real data.

## Generating synthetic data (Replicator)

`omni.replicator.core` (Replicator) is Isaac Sim's synthetic-data-
generation toolkit. This skill owns the *mechanics* of running it inside
Isaac Sim; deciding how much synthetic data a project needs, and how it
combines with real or teleop-collected data, is the `data` umbrella
skill's call.

The pipeline has three parts:

1. **Randomization** — systematically varying scene parameters (object
   poses, lighting, materials/textures, physics properties) across
   generated frames so a downstream perception model doesn't overfit to one
   fixed scene layout.
2. **Annotators** — capture ground-truth semantic information alongside
   each rendered frame (bounding boxes, segmentation, depth, and other
   modalities) as the scene is randomized.
3. **Writers** — export the annotated frames to a standardized on-disk
   format; COCO is one supported output format among others.

Typical use cases called out in the docs: domain randomization for
training robustness, sensor/perception dataset generation, and
robotics-specific scenarios (navigation, manipulation, grasping). Treat any
specific Replicator API call (writer names, randomizer function
signatures) as something to look up against the live Replicator tutorials
per scene rather than assumed stable across releases — this reference
intentionally stops at the conceptual pipeline rather than inventing exact
function signatures that weren't directly confirmed on 2026-07-10.
