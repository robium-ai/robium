- [simulation] figured-out-from-scratch <!-- id: lrn-0810-01 -->
  symptom: The indoor-navigation demo needs to show an interactive simulator UI directly in the browser, but the simulator-selection guidance only compares Gazebo, Isaac Sim, and MuJoCo; modern Gazebo has no official browser GUI and the existing Lichtblick panel visualizes ROS state rather than Gazebo's scene.
  root-cause: Browser delivery is not represented as a simulator-selection axis, so Webots' built-in X3D-over-WebSocket streaming mode is absent from the decision tree.
  fix: Evaluate Webots as the browser-first mobile-navigation alternative while keeping Gazebo as the ROS/Nav2-first default — check: Cyberbotics' current Web Streaming and R2025a protocol documentation describes `--stream` and an embeddable interactive 3D browser client; implementation and app smoke remain untested.
  dead-ends: Native Gazebo GUI connected to the Docker server is architecturally supported by Gazebo's server/client split, but Docker Desktop NAT still has to expose mutually reachable Gazebo Transport endpoints after discovery; `GZ_RELAY` alone only repairs discovery, not unreachable data endpoints.
  anchors: simulation#headless-default-for-both-ci, visualization#headless-default-web-based-tool

## End-of-block retro (2026-08-10, indoor-navigation simulator-view evaluation)

- [simulation] fired ✓ · accurate ✓ (Gazebo remains the ROS-centric mobile-navigation fit; MuJoCo is correctly routed away) · complete − (no browser-delivery axis or Webots alternative) · lean ✓
- [gazebo] fired ✓ · accurate ✓ (server/client split, macOS native GUI caveat, and Docker transport caveat all matched upstream docs and this app) · complete ✓ · lean ✓
- [mujoco] fired ✓ · accurate ✓ (correctly identifies MuJoCo as a non-ROS manipulation simulator, not a drop-in Nav2 replacement) · complete ✓ for its scope · lean ✓
- [visualization] fired ✓ · accurate ✓ (Lichtblick/Foxglove is the right headless ROS-state viewer) · complete ✓ for visualization rather than simulator UI delivery · lean ✓
- [environments] fired ✓ · accurate ✓ (doctor confirmed macOS arm64, Docker healthy, no native ROS 2, no NVIDIA GPU) · complete ✓ · lean ✓
- [integration] fired ✓ · accurate ✓ (the current one-container design avoids Docker Desktop DDS discovery failures; Gazebo Transport across native/container boundaries needs explicit networking) · complete ✓ · lean ✓
- [foxglove] fired ✓ · accurate ✓ (the app's bundled Lichtblick path is correctly distinguished from Gazebo's own GUI) · complete ✓ · lean ✓
- [live-demo] fired ✓ · accurate ✓ (the current per-visitor gateway/viewer architecture matches the app) · complete − (simulator-native browser streaming is not a visualizer option) · lean ✓

## End-of-block retro (2026-08-10, Apple Silicon GPU follow-up)

- [environments] fired ✓ · accurate ✓ (Docker Desktop's Linux VM cannot expose Apple's Metal GPU as a general Linux graphics device; the skill's no-MPS/no-GPU-container boundary remains load-bearing) · complete ✓ · lean ✓
- [gazebo] fired ✓ · accurate ✓ (the existing GPU-less `gpu_lidar` path already proves llvmpipe can sustain the headless scene near real time; adding GUI rendering and VNC encoding remains a benchmark question) · complete ✓ · lean ✓

## End-of-block retro (2026-08-10, local Gazebo run instructions)

- [gazebo] fired ✓ · accurate ✓ (native macOS installation and split server/GUI invocation directly answer the standalone check; the app remains intentionally server-only) · complete ✓ · lean ✓
- [environments] fired ✓ · accurate ✓ (local preflight found Homebrew and a healthy Docker daemon, with native Gazebo not yet installed) · complete ✓ · lean ✓

- [environments] figured-out-from-scratch <!-- id: lrn-0810-02 -->
  symptom: Native Gazebo on Apple Silicon preserves host graphics acceleration, but the documented Homebrew install modifies a shared machine-wide prefix and the Docker alternative loses general Apple-GPU access.
  root-cause: The environment decision tree does not cover project-local native C++/Qt robotics packages delivered through Pixi/Conda.
  fix: Evaluate a locked Pixi `osx-arm64` environment containing `libgz-sim8` for a native, project-local Gazebo Harmonic GUI — check: conda-forge currently publishes `libgz-sim8` 8.10.0 for osx-arm64 and Pixi installs project environments under `.pixi/envs/<name>`; runtime GUI check remains pending.
  dead-ends: Docker/Lima isolate dependencies but move Gazebo into a Linux VM with no general Apple Metal/OpenGL device; Homebrew works natively but uses the shared `/opt/homebrew` prefix. Full native ROS Jazzy via RoboStack also has osx-arm64 packages, but a published Gazebo Harmonic crash report means it is not yet a proven replacement for the app's Dockerized ROS stack.
  anchors: environments#macos-no-native-ros2-docker-required, environments#docker-macos-no-mps-cpu-fallback, gazebo#macos-gz-native-but-bridge-needs-docker

## End-of-block retro (2026-08-10, isolated native Gazebo evaluation)

- [environments] fired ✓ · accurate ✓ for Docker/Homebrew tradeoffs · complete − (project-local Pixi/Conda native system packages are absent) · lean ✓
- [gazebo] fired ✓ · accurate ✓ (Harmonic remains the compatibility target and native macOS is explicitly best-effort) · complete − (no isolated-native installation pattern) · lean ✓

## End-of-block retro (2026-08-10, Conda versus Homebrew clarification)

- [environments] fired ✓ · accurate ✓ (kept package-manager boundaries explicit: Conda/Pixi environments contain Conda packages, while Homebrew remains a separate shared-prefix manager) · complete ✓ · lean ✓

## End-of-block retro (2026-08-10, Pixi versus Conda versus RoboStack)

- [environments] fired ✓ · accurate ✓ (distinguished environment clients from package channels and identified the project-local native path) · complete − (the skill does not yet explain Pixi versus Conda or RoboStack's role as a channel) · lean ✓

- [ros2] wrong-stale-guidance <!-- id: lrn-0810-03 -->
  symptom: The skill states that every ROS 2 workflow on macOS requires Docker, but RoboStack publishes community ROS 2 Jazzy binaries for osx-arm64 that Pixi can install without Docker; the indoor-navigation package set (Nav2, slam_toolbox, TurtleBot 3, foxglove_bridge, and ros_gz) is present in the current robostack-jazzy osx-arm64 repodata.
  root-cause: “No official supported native ROS 2 distribution from Open Robotics” was collapsed into “no native ROS 2 installation exists,” omitting RoboStack's community Conda distribution and its different support/reliability status.
  fix: Describe Docker as the official/reliable macOS default and Pixi + RoboStack as a community-native experimental path that needs package and runtime smoke tests — check: RoboStack's current Getting Started page recommends Pixi for new installs and demonstrates osx-arm64 workspaces; current channel repodata contains all named app packages. Gazebo sensor rendering remains unverified and upstream gz-sim issue #2877 is still open.
  dead-ends: Package availability alone does not prove the app works: a published Jazzy/Harmonic Pixi reproduction succeeds without rendering sensors but crashes when Metal-backed camera/lidar sensors initialize.
  anchors: ros2#macos-no-native-ros2, environments#macos-no-native-ros2-docker-required, gazebo#macos-gz-native-but-bridge-needs-docker

## End-of-block retro (2026-08-10, fully native macOS feasibility)

- [environments] fired ✓ · accurate − (correct official/reliable default, but “Docker required” omits the RoboStack community-native option) · complete − · lean ✓
- [ros2] fired ✓ · accurate − (same overbroad macOS prohibition; core ROS mechanics remain applicable) · complete − · lean ✓
- [gazebo] fired ✓ · accurate − (correctly warns the official bridge path needs Docker, but does not account for RoboStack's native ros_gz binaries) · complete − (current Metal sensor-rendering failure is absent) · lean ✓

## End-of-block retro (2026-08-10, Pixi isolation boundary)

- [environments] fired ✓ · accurate ✓ for distinguishing project dependency isolation from container isolation · complete − (Pixi's project prefix, user cache, shell-path change, and macOS SDK prerequisite are not documented) · lean ✓

## End-of-block retro (2026-08-10, app-local native dependency install)

- [environments] fired ✓ · accurate − (Docker remains the proven default, but its decision tree omitted a working fully app-local Pixi dependency installation) · complete − (no Pixi isolation mechanics) · lean ✓
- [ros2] fired ✓ · accurate − (core mechanics apply, but the macOS “Docker only” claim is contradicted at package-install level by RoboStack; runtime remains untested) · complete − · lean ✓
- [gazebo] fired ✓ · accurate − (Jazzy/Harmonic pairing remains correct, while the macOS bridge-needs-Docker claim is contradicted at package-install level by native ros_gz binaries; runtime remains untested) · complete − · lean ✓
- [testing] fired ✓ · accurate ✓ · complete ✓ · lean ✓ (loaded for the initially requested staged smoke harness, then correctly left unused when the user narrowed scope to dependency installation only)

- [ros2] figured-out-from-scratch <!-- id: lrn-0810-04 -->
  symptom: A Pixi/RoboStack environment containing Nav2, TurtleBot 3, ros_gz, `ros-jazzy-launch`, and `ros-jazzy-launch-ros` exposed only `daemon`, `pkg`, and `topic`; `ros2 launch ...` failed with `invalid choice: 'launch'`.
  root-cause: The explicit app-package manifest omitted the `ros-jazzy-ros-base`/`ros-jazzy-ros-core` meta layer. The launch Python libraries do not register the ros2 CLI verb; `ros-jazzy-ros2launch` does, and RoboStack's `ros-jazzy-ros-core` depends on it through `ros-jazzy-ros2cli-common-extensions`.
  fix: Include `ros-jazzy-ros-base` in the Pixi manifest, matching the app's Docker base — check: after `pixi install`, `ros2 --help` listed `launch`, `run`, `node`, `service`, `action`, `param`, and the environment inventory contained `ros-jazzy-ros2launch` and `ros-jazzy-ros2run`.
  dead-ends: Installing `ros-jazzy-launch` and `ros-jazzy-launch-ros` transitively was insufficient because those are runtime libraries, not ros2cli command-extension packages.
  anchors: ros2#colcon-build-source, environments#macos-no-native-ros2-docker-required

## End-of-block retro (2026-08-10, missing ros2 launch verb)

- [ros2] fired ✓ · accurate ✓ for treating ROS CLI functionality as package-provided extensions · complete − (does not distinguish launch libraries from the `ros2launch` CLI package or recommend the ROS base meta-package in a non-apt environment) · lean ✓

- [gazebo] figured-out-from-scratch (seen 2x) <!-- id: lrn-0810-05 -->
  symptom: Native `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py` opened Gazebo without a separate `gz sim -g`, spawned the robot, and created the ros_gz bridges, but both server and GUI printed `Unable to load Ogre Plugin[.../.pixi/envs/default/lib/OGRE-Next]. Rendering will not be possible.`
  root-cause: The upstream TurtleBot 3 top-level launch intentionally starts both gz server and GUI. Separately, OGRE2 first calls `dlopen` on incomplete plugin-directory paths and emits the fatal-sounding message, then loads the complete `RenderSystem_GL3Plus.dylib` and `RenderSystem_Metal.dylib` paths successfully; treating the first probe error as final state was incorrect.
  fix: Treat the second GUI command as necessary only for the app's custom server-only `sim.launch.py`, and verify renderer state from the complete OGRE log plus sensor data/process health instead of grepping the probe warning — check: app-native launch stayed alive, `ogre2.log` selected `Apple M5 (system default)` and compiled Metal shaders, `/scan` published non-empty ranges, and Nav2 reached goal `(0.3, 0.5)`.
  dead-ends: A visible Qt window alone was insufficient evidence; conversely, rejecting the run on `Rendering will not be possible` was a false negative because later log lines proved Metal initialization. Forcing legacy `--render-engine ogre` loaded OpenGL but was incompatible with Qt's Metal texture interface and crashed.
  anchors: gazebo#vendor-launch-not-headless, gazebo#gpu-vs-software-rendering, gazebo#verify-data-flowing

## End-of-block retro (2026-08-10, upstream Gazebo launcher behavior)

- [gazebo] fired ✓ · accurate ✓ (already documents that TurtleBot 3's top-level launcher hardcodes a GUI client) · complete − (does not cover the native Pixi OGRE plugin-load failure or app-local ROS/Gazebo log/cache paths) · lean ✓

## End-of-block retro (2026-08-10, GUI command clarification)

- [gazebo] fired ✓ · accurate ✓ (cleanly distinguishes the upstream combined server+GUI launcher from the app's custom server-only launcher) · complete ✓ · lean ✓

- [ros2] figured-out-from-scratch <!-- id: lrn-0810-06 -->
  symptom: In the RoboStack environment, `colcon build --symlink-install` failed with `error: option --editable not recognized`; a subsequent incremental non-symlink build failed with `error: option --uninstall not recognized`.
  root-cause: The unconstrained manifest resolved setuptools 84.0.0, while the installed colcon Python-package extension still invokes legacy `setup.py develop --editable/--uninstall` flags removed in setuptools 80.
  fix: Pin `setuptools = "<80"` in `pixi.toml`, update the lock to 79.0.1, and retain `--symlink-install` — check: clean and repeated native colcon builds completed.
  dead-ends: Removing `--symlink-install` made the first build pass but did not make incremental rebuilds compatible; cleaning every startup would mask the dependency mismatch and discard useful incremental behavior.
  anchors: ros2#colcon-build-source, environments#pinned-base-image-not-latest

- [environments] figured-out-from-scratch <!-- id: lrn-0810-07 -->
  symptom: Setting `GZ_HOMEDIR` to the app runtime did not stop Gazebo from reading and writing `~/.gz`; a diagnostic run created host `server.config` and rendering logs.
  root-cause: In gz-common, `GZ_HOMEDIR` is a compile-time macro whose value is the environment-variable name `HOME`, not a runtime override variable.
  fix: Set `HOME` only in the environment passed to native child processes, while launching the host browser outside that environment — check: the full native demo wrote `.gz` under `experiments/native-macos/runtime/home`, and no host `~/.gz` file changed during the isolated run.
  dead-ends: Exporting an environment variable literally named `GZ_HOMEDIR` had no effect.
  anchors: environments#record-strategy-in-brief, environments#macos-no-native-ros2-docker-required

- [environments] better-method <!-- id: lrn-0810-08 -->
  symptom: colcon's debug event log serialized the complete inherited environment, including an unrelated ambient credential variable.
  root-cause: The native launcher copied the full host environment into build and launch children, and colcon records its command environment in `logger_all.log`.
  fix: Remove common secret-bearing suffixes (`_TOKEN`, `_SECRET`, `_PASSWORD`, `_API_KEY`) from the child environment and redact the already-generated ignored log — check: unit coverage confirms those names are absent from `native_environment` while required host/GUI variables remain.
  dead-ends: Relying on the runtime directory being gitignored prevents commits but does not prevent local secret persistence.

## End-of-block retro (2026-08-10, native Gazebo + Lichtblick implementation)

- [environments] fired ✓ · accurate − (environment-first/isolation framing was useful, but Pixi/RoboStack mechanics and Gazebo's effective HOME behavior were missing) · complete − · lean ✓
- [ros2] fired ✓ · accurate ✓ for workspace/launch composition · complete − (no setuptools 80 / colcon develop-flags compatibility warning) · lean ✓
- [gazebo] fired ✓ · accurate ✓ for explicit server/client composition and `/scan` verification · complete − (fatal-sounding OGRE probe warning before successful Metal fallback was undocumented) · lean ✓
- [integration] fired ✓ · accurate ✓ (one ROS graph, explicit mode/config boundaries, and process-group ownership worked) · complete ✓ · lean ✓
- [foxglove] fired ✓ · accurate ✓ (bridge plus committed layout remained the right complementary ROS-state view) · complete ✓ · lean ✓
- [testing] fired ✓ · accurate ✓ (pure logic checks caught entry-point, shutdown, and environment regressions; end-to-end saved-map goal remained the done bar) · complete ✓ · lean ✓

- [gazebo] user-corrected-approach <!-- id: lrn-0810-09 -->
  symptom: After asking to retain the indoor/home Gazebo environment, the native demo still displayed the sparse `turtlebot3_world` scene instead of `turtlebot3_house`.
  root-cause: The implementation plan interpreted “existing indoor environment map” as the app's existing saved occupancy map and explicitly preserved `turtlebot3_world.world`; `sim.launch.py` therefore remained hardcoded to that world even though the installed package contains `turtlebot3_house.world`.
  fix: Treat the requested visual environment and the Nav2 occupancy map as separate assets; select `turtlebot3_house.world`, then create or verify a matching saved occupancy map, spawn pose, and goal set before claiming the house scenario works. (check: native Gazebo visibly loaded the furnished house; a live SLAM run produced a 237x147 map; native and Docker saved-map runs both reached map goals `(3.4, 0.8)` and `(5.1, 1.8)`.)
  dead-ends: Merely swapping the world filename while retaining the current `map.pgm`, world-to-map transform, and smoke goals would display the house but make localization/navigation geometrically inconsistent.
  anchors: gazebo#vendor-launch-not-headless, gazebo#verify-data-flowing

- [environments] figured-out-from-scratch <!-- id: lrn-0810-10 -->
  symptom: Immediately restarting the native demo after a clean shutdown failed with `native demo failed: port 8766 is already in use`, although `lsof` showed no listening process.
  root-cause: macOS retained the recently closed TCP connection in `TIME_WAIT`; the preflight bind omitted `SO_REUSEADDR` and therefore treated kernel connection state as an active listener.
  fix: Set `SO_REUSEADDR` on the temporary preflight socket before binding. (check: a regression test closes a real loopback listener and immediately verifies `require_free_ports` accepts the released port; all native-path tests pass.)
  dead-ends: Process searches and listener-only `lsof` checks correctly found no owner because the conflict was not a live process.
  anchors: environments#preflight-host-resources, testing#regression-test-the-failure

- [nav2] worked-as-documented <!-- id: lrn-0810-11 -->
  symptom: A world-file swap alone left the saved pillar-world occupancy grid and goals geometrically incompatible with the furnished house.
  root-cause: Gazebo's SDF world, slam_toolbox's saved occupancy map, AMCL's initial pose, and Nav2's goal coordinates are one scenario contract even though they live in separate files.
  fix: Explore the house using incrementally reachable map-frame waypoints, save the resulting occupancy grid, and validate initial/default goals against known-free PGM cells. (check: native and Docker runs loaded the 237x147 map and reached both default goals; `make smoke` and `make demo-smoke` passed.)
  dead-ends: Reusing TurtleBot 3's packaged navigation map was rejected because visual inspection showed it is the hexagonal nine-pillar world, not the house.
  anchors: nav2#map-frame, nav2#amcl-initial-pose, gazebo#verify-data-flowing

## End-of-block retro (2026-08-10, shared TurtleBot 3 house scenario)

- [gazebo] fired ✓ · accurate ✓ (shared world selection and server/client split worked in native and headless modes) · complete − (upstream house asset emits unresolved floor/furniture texture warnings on both platforms) · lean ✓
- [nav2] fired ✓ · accurate ✓ (staged SLAM exploration, saved-map localization, and goal verification produced a working house scenario) · complete ✓ · lean ✓
- [ros2] fired ✓ · accurate ✓ (launch overlay rebuild and map-frame action checks worked) · complete ✓ · lean ✓
- [environments] fired ✓ · accurate ✓ (Pixi isolation and Docker parity held) · complete − (`TIME_WAIT` behavior was not covered) · lean ✓

- [foxglove] user-corrected-approach <!-- id: lrn-0810-12 -->
  symptom: The user reported that Lichtblick's “Publish pose” still did not navigate after following the two-click position-and-heading gesture. The bridge logged `Client ID ... is advertising "/goal_pose"` followed immediately by `is no longer advertising /goal_pose`, and `ros2 topic info -v /goal_pose` reported zero publishers while the viewer was connected.
  root-cause: The earlier diagnosis that the user had stopped after the first click was contradicted by the live publisher lifecycle. Lichtblick's 3D panel advertises `/goal_pose`, `/clicked_point`, and `/initialpose` in a React effect whose cleanup unadvertises all three when the data-source context changes identity; the replacement context's optional-chained advertise calls can no-op, leaving zero publishers. The failure boundary is Lichtblick, not Nav2: `/goal_pose` had a live `bt_navigator` subscriber and direct ROS publication moved the robot.
  fix: In both the Docker build and native viewer installation, guard-match the single minified three-topic cleanup callback and replace it with a no-op so the advertisements persist for the viewer session. (check: after patching, `ros2 topic info -v /goal_pose` reported one publisher from `foxglove_bridge`; a two-click Lichtblick goal emitted map-frame pose `(1.14, 0.10)`, Nav2 logged `Begin navigating`, the controller logged `Reached the goal!`, and Nav2 logged `Goal succeeded`.)
  dead-ends: The committed layout already targets `/goal_pose`; the documented two-click gesture was performed and did not fix the issue; changing Nav2 or the goal topic does not explain the immediate advertise/unadvertise sequence.
  anchors: foxglove#nav2-goal-topic-fix, nav2#basic-navigator-api

## End-of-block retro (2026-08-10, Lichtblick click-to-goal diagnosis)

- [foxglove] fired ✓ · accurate − (the initial gesture-only diagnosis was disproved by the live advertise/unadvertise sequence) · complete − (publisher lifecycle failure is not covered; the app required a guarded prebuilt-bundle rewrite) · lean ✓
- [nav2] fired ✓ · accurate ✓ (topic subscriber, TF-ready stack, and direct goal isolated Nav2 from the UI issue) · complete ✓ · lean ✓

- [gazebo] user-corrected-approach <!-- id: lrn-0810-13 -->
  symptom: The native Gazebo window and Lichtblick navigation state worked, but Lichtblick had no image from the robot; the user clarified that only the Gazebo overhead camera should be removed and that the robot must use `burger_cam`.
  root-cause: Removing the overhead-camera path had been conflated with removing all cameras. The demo still selected the camera-less `burger` model and its two-panel Lichtblick layout had no `/camera/image_raw` Image panel.
  fix: Select TurtleBot 3 `burger_cam` in native and Docker modes, guard-convert its 30 Hz wide-angle sensor to a 10 Hz pinhole camera inside each isolated environment, rely on the upstream spawn launch's `ros_gz_image` bridge, and add only `Image!robotcam` to the committed layouts. (check: `/camera/image_raw` reported one `ros_gz_image` publisher and a received frame with `frame_id: camera_rgb_frame`; Foxglove subscribed; Lichtblick visibly rendered the house hallway; `/overhead/*` topics and overhead layout references were absent.)
  dead-ends: Adding an Image panel alone cannot create sensor data from the camera-less `burger`; restoring the prior Gazebo overhead sensor would show the scene rather than the robot's view and directly contradicts the requested experience. Lichtblick also restores layouts per browser origin, so the native launcher moved from `localhost` to the equivalent `127.0.0.1` origin to load the new bundled default without deleting the user's old saved layout.
  anchors: gazebo#verify-data-flowing, gazebo#gpu-vs-software-rendering, foxglove#ship-layout-json

## End-of-block retro (2026-08-10, robot-mounted camera)

- [gazebo] fired ✓ · accurate ✓ (sensor-to-Gazebo-to-ROS verification correctly required a real received frame rather than topic existence) · complete − (the skill does not cover TurtleBot 3's model-selective upstream image-bridge behavior or lightweight native camera conversion) · lean ✓
- [foxglove] fired ✓ · accurate ✓ (a committed Image panel on `/camera/image_raw` is the right ROS-state experience) · complete − (saved layouts are restored per origin, so changing a bundled default does not update an existing profile) · lean ✓
- [ros2] fired ✓ · accurate ✓ (endpoint and one-message checks proved the image bridge and Foxglove subscription) · complete ✓ · lean ✓
- [environments] fired ✓ · accurate ✓ (native model mutation stayed inside the Pixi prefix and Docker received the equivalent build-time change) · complete ✓ · lean ✓

## End-of-block retro (2026-08-10, mapping-dashboard provenance check)

- [foxglove] fired ✓ · accurate ✓ (the layout JSON and ROS-side helper boundary correctly explained why the service panels require more than copying a dashboard file) · complete ✓ · lean ✓

- [gazebo] figured-out-from-scratch <!-- id: lrn-0810-14 -->
  symptom: The consolidated public app passed unit checks but two launches from a genuinely fresh app-local `HOME` failed with `native demo failed: /scan did not publish within 45 seconds`; `ros_gz_sim create` repeated `Requesting list of world names` and never spawned the robot.
  root-cause: TurtleBot 3's packaged furnished-house world references Fuel-hosted Ground Plane and Sun models. With no user-level Gazebo cache, the server blocked resolving those remote assets before advertising the world; the earlier development checkout had hidden this dependency through accumulated runtime state.
  fix: Package an app-owned house world that keeps `model://turtlebot3_house` but defines the directional light and ground plane inline, and select it for the default house mode in both native and Docker launches. (check: from the new public Pixi runtime, the launcher reached `native demo ready`, `/camera/image_raw` produced a 320-pixel-wide frame, Nav2 reached `(3.4, 0.8)`, and shutdown completed.)
  dead-ends: Increasing the `/scan` timeout would only wait longer on an external asset dependency; copying another checkout's ignored Fuel cache would break clean-clone reproducibility and the app-local isolation guarantee.
  anchors: gazebo#vendor-launch-not-headless, gazebo#verify-data-flowing, environments#record-strategy-in-brief

## End-of-block retro (2026-08-10, public-app consolidation and clean-runtime verification)

- [environments] fired ✓ · accurate ✓ (app-local Pixi isolation remained intact in the new public checkout) · complete − (clean-state verification should explicitly include simulator asset caches) · lean ✓
- [ros2] fired ✓ · accurate ✓ (workspace rebuild, topic type discovery, and action-level goal verification transferred cleanly) · complete ✓ · lean ✓
- [gazebo] fired ✓ · accurate ✓ (server/client split and sensor data-flow checks isolated the failure correctly) · complete − (remote Fuel includes as a hidden clean-start dependency were not covered) · lean ✓
- [nav2] fired ✓ · accurate ✓ (map, initial pose, and known-free goal stayed a coherent scenario contract after migration) · complete ✓ · lean ✓
- [foxglove] fired ✓ · accurate ✓ (robot-camera-only layouts and persistent goal advertisements survived the move) · complete ✓ · lean ✓
- [integration] fired ✓ · accurate ✓ (native and Cloud Run paths share launch/config assets while keeping platform-specific execution boundaries) · complete ✓ · lean ✓
- [testing] fired ✓ · accurate ✓ (failure-first launch/layout checks plus live camera and goal probes caught migration drift) · complete ✓ · lean ✓
- [learning-loop] fired ✓ · accurate ✓ (the end-of-block workflow kept the reusable Fuel-cache finding in learnings without editing skills mid-build) · complete ✓ · lean ✓
