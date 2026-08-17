# Indoor navigation learnings, 2026-08-16

- [none] figured-out-from-scratch (seen 2x) <!-- id: lrn-0816-01 -->
  symptom: `TS2322: Type 'SimulationWorld[]' is not assignable to type 'never[]'` stopped `npm run package` inside the Dashboard Docker stage, while the reported Compose tail only showed Webpack shutdown frames.
  root-cause: spreading `DEFAULT_CONFIG` and overriding `simulationWorlds` with an untyped `[]` inferred that property as `never[]` on the mutable local object.
  fix: annotated the local object as `PanelConfig` — check: the focused Dashboard target packaged `robium.dashboard-0.9.0.foxe`, then two complete `make build` runs produced `indoor-navigation:latest`.
  dead-ends: Docker and Compose were not the failing boundary; `docker build --progress=plain --target dashboard` exposed the earlier TypeScript diagnostics hidden above the pasted wrapper stack.
  source: indoor-navigation main checkout and promote/indoor-navigation-control-panel worktree builds, 2026-08-16

- [visualization] user-correction (seen 4x) <!-- id: lrn-0816-02 -->
  symptom: a close Lichtblick 3D view made the TurtleBot3 Waffle Pi appear exploded, with the wheels visually detached from the chassis; the detached right wheel remained after the user enabled Perspective.
  root-cause: the model looked mechanically broken because several viewer cues overlapped. Empty `transforms` made Lichtblick render every frame axis at full scale; `displayMode: auto` renders collision primitives for links without visuals as floating white boxes; the 3D camera showed the chassis almost edge-on; and the top-mounted circular LDS lidar was easy to mistake for a detached wheel while the far drive wheel was occluded. Gazebo's SDF and the visualization URDF do use different wheel-link frame conventions, but they are geometrically equivalent: live ROS TF placed both drive wheels symmetrically at y = ±0.144 m and z = 0.023 m with identical rotations, and composing the TF with the URDF visual rotation produced a wheel axle along robot Y (`0.0007, 0.9999996, 0.0005`).
  fix: slash-free TF plus hidden axes and an isometric camera are verified presentation improvements. No wheel-axis or wheel-position rewrite is warranted. Keep the upstream model and improve only the viewer framing and visual-vs-collision presentation after user approval.
  dead-ends: Perspective and isometric camera changes alone did not make the robot recognizable; switching `map` to `odom` did not change the shape; slash-free TF did not change wheel geometry; a proposed visualization-only URDF rewrite was rejected before implementation; the SDF/URDF frame mismatch hypothesis was ruled out by live transforms and quaternion composition.
  anchors: visualization#visualize-concrete-not-just-no-errors, visualization#tf-tree-check
  source: indoor-navigation live Lichtblick session, 2026-08-16

- [nav2] figured-out-from-scratch <!-- id: lrn-0816-03 -->
  symptom: stopping an active mapping session twice failed with `map_saver: Failed to spin map subscription` after almost exactly two seconds, followed by `session_manager: saving map failed: result=255`, even though `/map` had one reliable transient-local publisher and was publishing at 1 Hz.
  root-cause: the app calls slam_toolbox's `/slam_toolbox/save_map` wrapper. The Jazzy wrapper launches `map_saver_cli` with transient-local QoS but does not pass `save_map_timeout`, so Nav2's two-second CLI default applies; the app's `nav2_params.yaml` value of five seconds is not loaded by that subprocess. Startup plus DDS discovery exhausted the two-second window before the fresh saver consumed `/map`.
  fix: pending app change; use a map-saver path whose timeout is explicitly configured above the discovery/startup latency, then verify `.pgm` and `.yaml` creation. The map name `map` is valid and is slam_toolbox/session_manager's default, so renaming it is not a fix.
  dead-ends: map-name validation accepts `map`; the requested path `/ws/maps/furnished_house/map` passed validation; `/map` was present, reliable, transient-local, and observable; retrying the same UI action failed twice.
  anchors: nav2#mapping-and-map-saving
  source: indoor-navigation live container logs and ROS graph, 2026-08-16; slam_toolbox Jazzy `src/map_saver.cpp`; Nav2 map-saver default launch configuration

- [none] figured-out-from-scratch <!-- id: lrn-0816-04 -->
  symptom: the Robium Dashboard simulation-world selector immediately reverted from Warehouse to House, so the user could not select Warehouse before pressing Restart simulation.
  root-cause: `DashboardPanel.tsx` synchronizes local `selectedWorld` from `/simulation/state`, but the effect depends on `selectedWorld` itself. Every dropdown change reruns the effect while the backend still correctly reports the currently running `furnished_house`, immediately overwriting the pending `tugbot_warehouse` selection.
  fix: changed the effect to use a functional state update and depend only on backend world/config feedback, preserving an intentional pending selection until the backend actually changes. Check: the focused Dashboard Docker package stage completed, the full local image built, and the recreated container serves Lichtblick with that exact image digest. No unit or smoke suite was run per user instruction.
  dead-ends: the world list is configured correctly; `/session_manager.world` and `/simulation/state` both consistently reported `furnished_house`; no Warehouse restart request reached the backend.
  source: indoor-navigation live ROS graph plus `shared/lichtblick-dashboard/src/DashboardPanel.tsx`, 2026-08-16

## End-of-block retro

- nav2: fired correctly for the SLAM-to-localization sequence and map-save failure; accurate on ROS graph checks, but incomplete on slam_toolbox's wrapper bypassing the app's configured map-saver timeout.
- environments: fired correctly for the Docker build failure; accurate and lean, with no missing environment guidance found.
- integration: fired correctly for the Dockerfile/Compose boundary; accurate and lean, with the focused build-stage isolation sufficient for this failure.
- visualization: fired correctly for the malformed-looking 3D model, but the initial camera diagnosis was incomplete; raw frame-name comparison was required to find the split TF tree.
- foxglove: fired for the Foxglove-compatible Lichtblick panel; accurate and lean, but its troubleshooting guidance did not call out leading-slash frame mismatches.
- ros2: fired correctly for TF verification; accurate, complete, and lean.
