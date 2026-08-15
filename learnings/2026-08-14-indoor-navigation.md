# Indoor navigation learnings — 2026-08-14

- [foxglove] figured-out-from-scratch <!-- id: lrn-0814-01 -->
  symptom: rebuilding a same-version preinstalled Lichtblick `.foxe` left the old gradient and geometry visible after reload even though the served archive contained the new CSS
  root-cause: both the extension asset response and the unchanged bootstrap-module URL were satisfied from browser caches
  fix: fetch bundled assets with `cache: "no-store"` and fingerprint the bootstrap import from the `.foxe` SHA-256 — check: a rebuilt mapping image loaded `preinstall-extension.mjs?v=d10b436518e11f29`, computed `background-image: none`, and displayed all nine controls at 1024×576
  dead-ends: rebuilding and force-recreating the mapping container alone did not change the browser-rendered CSS

- [testing] figured-out-from-scratch <!-- id: lrn-0814-02 -->
  symptom: `make smoke` timed out after 180 seconds with `SMOKE RESULT: 137` while Gazebo flooded `Detected jump back in time. Clearing TF buffer.`
  root-cause: the interactive mapping container and smoke container were running separate simulator stacks concurrently on the constrained local Docker runtime
  fix: stop/remove the mapping stack and rerun smoke with one simulator — check: goals `(3.4,0.8)` and `(5.1,1.8)` both returned `TaskResult.SUCCEEDED`, followed by `PASS: all goals reached`
  dead-ends: waiting through the first bounded run did not recover; it exited 137 as designed

- [none] user-correction <!-- id: lrn-0814-03 -->
  symptom: the first compact Robot Control design still used a 28% right rail and retained eyebrow copy, direction captions, helper paragraphs, speed/readiness badges, and fixed drive speeds
  root-cause: the initial density pass optimized vertical fit but did not reserve enough horizontal space for the main visualization or expose operator-tunable drive speed
  fix: changed the saved layout to 76/24, removed secondary copy and badges, and added persisted forward/turn sliders — check: the real 1024×576 Lichtblick view showed both sliders and all nine controls without clipping; extension tests and the two-goal Nav2 smoke passed
  dead-ends: reducing only padding and control sizes did not meet the user's preferred information density

- [nav2] user-correction <!-- id: lrn-0814-04 -->
  symptom: a fresh dashboard immediately showed a map and disabled Start mapping even though the intended workflow requires an explicit Start mapping or Load map action
  root-cause: `mapping.launch.py` defaults to launch-time `mode:=mapping`, starts `slam_toolbox` immediately, and publishes `MAPPING`; the UI's Start mapping service only resets the already-running mapper, while Stop mapping only saves and keeps mapping
  fix: added a persistent session manager that starts only Gazebo, owns restartable mapping/localization child groups, and saves maps per world — check: fresh startup returned `IDLE` with `Unknown topic '/map'`; Start produced one `/map` publisher and `MAPPING`; Stop saved the map, returned `IDLE`, and reduced `/map` publishers to zero; Load started map_server + AMCL and returned `LOCALIZATION`
  dead-ends: changing button enablement or hiding `/map` in Lichtblick would mask the launch-state mismatch without stopping the underlying mapper

- [gazebo] better-method <!-- id: lrn-0814-05 -->
  symptom: Fuel display names and mutable download counts were insufficient to wire deterministic world choices, and `gz fuel download` warned that only the latest world version is supported even when given a versioned URL
  root-cause: the web UI is client-rendered, while the Fuel REST metadata and cache layout expose the canonical owner/name/version records directly
  fix: resolve metadata through `/1.0/<owner>/worlds/<name>`, launch explicit versioned Fuel URLs, and persist `/root/.gz/fuel` as a Docker volume — check: cached paths recorded Tugbot v2, industrial-warehouse v4, and living_room v1; each world started in Gazebo Harmonic and restored TurtleBot `/scan` and camera publishers
  dead-ends: guessed owner/name combinations and generic Fuel search results were ambiguous; direct `.zip` and `/files` URL guesses returned 404

- [test-assets] verified <!-- id: lrn-0814-06 -->
  symptom: three large external simulation worlds needed provenance and repeatable first-use behavior without vendoring or modifying a CC BY-NC-ND asset
  fix: kept pinned upstream pointers, added curated spawn poses, cached downloads in a named volume, and smoke-tested the same TurtleBot sensor contract in all four worlds — check: House, Living Room, Tugbot Warehouse, and Industrial Warehouse each produced `/scan`; all Fuel assets remained unchanged
  dead-ends: embedding a modified environment-only copy of Tugbot in Warehouse would conflict with its no-derivatives license

## End-of-block retro

- foxglove — fired: yes; accurate: yes; complete: partial (preinstalled web-extension cache refresh behavior was not covered); lean: yes.
- testing — fired: not loaded automatically for the final smoke failure; accurate: not scored; complete: missing guidance on avoiding concurrent local simulator stacks; lean: not scored.
- nav2 — fired: yes; accurate: yes; complete: yes for identifying mutually exclusive SLAM/localization ownership, while the app-specific idle supervisor remains local architecture; lean: yes.
- gazebo — fired: yes; accurate: yes; complete: partial (Fuel versioned-world CLI behavior required live discovery); lean: yes.
- simulation — fired: yes; accurate: yes; complete: yes for preserving the common robot/sensor contract across environments; lean: yes.
- test-assets — fired: yes; accurate: yes; complete: yes for pointer, provenance, cache, and representative smoke guidance; lean: yes.

- [gazebo] figured-out-from-scratch <!-- id: lrn-0814-07 -->
  symptom: restarting into makerspet/living_room v1 killed Gazebo with `tv_65in_emissive/4 ... REST response code: 404`, then `A model must have at least one link` and `Failed to load a world`; after those were repaired the world ran but `/scan` and `/camera/image_raw` never produced messages
  root-cause: the published world contains a stale model-material version, two empty `living_room` model records, and no modern Gazebo Sensors/IMU systems
  fix: keep the downloaded Fuel asset immutable, generate a cached launch copy that rewrites only the stale TV URI, removes the two empty records, and injects the standard Physics/UserCommands/SceneBroadcaster/Sensors/Imu systems (check: the real dashboard restart loaded Living Room, spawned TurtleBot successfully, and delivered both `/scan` and `/camera/image_raw`; a subsequent UI restart to House also restored `/scan`)
  dead-ends: correcting only the missing TV version removed the 404 but left the two invalid empty models; removing those models made the world run but sensors stayed silent until the missing system plugins were added

## Restart-debug retro

- gazebo — fired: yes; accurate: yes; complete: partial (the skill correctly requires sensor systems and live topic verification, but did not flag that a syntactically downloadable Fuel world can contain stale nested resource versions, invalid empty models, and omitted systems); lean: yes.

- [gazebo] figured-out-from-scratch <!-- id: lrn-0814-08 -->
  symptom: the pinned AWS RoboMaker Small House ROS 2 world failed in Gazebo Harmonic with `Error Code 19: A link named link has invalid inertia`; after it loaded, portrait textures logged `Could not resolve file [../../../../photos/PortraitA_01.jpg]`
  root-cause: the legacy ShoeRack model declared `<ixx>`, `<iyy>`, `<ixx>` instead of `<ixx>`, `<iyy>`, `<izz>`, and its COLLADA portrait paths climbed one directory above the self-contained asset root
  fix: prepare the pinned asset at launch by correcting the second `ixx` tag, rewriting portrait paths one level closer, and injecting Harmonic's Physics/UserCommands/SceneBroadcaster/Sensors/Imu systems (check: the real Furnished House created the TurtleBot entity without load/texture errors and emitted `/clock`, `/scan`, `/camera/image_raw`, and `/odom`; teleop advanced odometry by 0.118 m)
  dead-ends: injecting only modern system plugins could not overcome the invalid SDF inertia; fixing inertia alone loaded the world but left visible portrait textures unresolved

- [test-assets] better-method <!-- id: lrn-0814-09 -->
  symptom: the desired home environment is about 105 MB extracted and comes from an archived upstream repository, so vendoring it would bloat robium-apps while an unpinned network fetch would be irreproducible
  root-cause: AWS publishes Small House as a Git repository rather than a stable modern Fuel world suitable for the existing runtime
  fix: fetch the GitHub archive at commit `ff9631ca6d1db9c1ba656498151464b5ab74aafe` during the Docker build with traversal/link rejection, retain upstream MIT `LICENSE`, and write a `SOURCE` provenance marker (check: local-fixture safety tests passed, a real fetch produced the expected commit marker, and the built image launched the asset)
  dead-ends: Fuel house searches produced mostly exterior shells; the only furnished home candidate previously tried had invalid nested Fuel resources and poorer visuals

- [simulation] figured-out-from-scratch <!-- id: lrn-0814-10 -->
  symptom: Stop Mapping returned `saving map failed: result=255` even though `/map` had already appeared
  root-cause: `slam_toolbox` published map updates every 5 seconds while its SaveMap helper waited about 2 seconds for a fresh map subscription, so the save outcome depended on timing
  fix: reduce `map_update_interval` to 1 second (check: the real Furnished House mapping session saved `.pgm` and `.yaml`, returned `IDLE`, and left `/map` with zero publishers)
  dead-ends: waiting for one earlier `/map` sample did not guarantee another sample would arrive inside the saver helper's shorter subscription window

## Furnished-house retro

- gazebo — fired: yes; accurate: yes; complete: partial (modern system composition was accurate, while malformed legacy SDF and COLLADA path repair still required file-by-file diagnosis); lean: yes.
- simulation — fired: yes; accurate: yes; complete: partial (the common sensor and lifecycle contract guided the smoke pass, but the map-publish/save-timeout interaction was not covered); lean: yes.
- test-assets — fired: yes; accurate: yes; complete: yes for pinned provenance, license retention, safe acquisition, and real-runtime verification; lean: yes.

- [gazebo] figured-out-from-scratch <!-- id: lrn-0814-11 -->
  symptom: the Tugbot visible in the warehouse looks like a natural selectable robot, but it cannot replace TurtleBot3 through the existing `TURTLEBOT3_MODEL` switch
  root-cause: the warehouse embeds MovAi Tugbot v1 as a legacy Ignition SDF with a 46.2 kg base, two planar lidars, a Velodyne, two RGB-depth cameras, old plugin identifiers, derived Gazebo topic names, and no matching ROS robot-description/Nav2 profile in this app; the Fuel asset is also CC BY-NC-ND 4.0
  fix: treat Tugbot as a separate robot adapter with an immutable upstream model, explicit bridge/TF/sensor selection, and robot-specific Nav2 parameters; use the already-installed TurtleBot3 Waffle Pi when the requirement is only a larger stable drop-in (check: the Jazzy image contains Waffle Pi SDF and matching bridge YAML with the same `/cmd_vel`, `/odom`, `/tf`, `/imu`, `/scan`, and camera interfaces as Burger Cam)
  dead-ends: assuming the Tugbot already present in the world inherits the app's TurtleBot ROS bridge would silently control the wrong entity and omit its sensor/TF contract

## Robot-options research retro

- gazebo — fired: yes; accurate: yes; complete: yes for separating model spawning, bridge configuration, frames, and sensors; lean: yes.
- simulation — fired: yes; accurate: yes; complete: yes for preserving the sensor contract when comparing robot platforms; lean: yes.

- [gazebo] worked-as-documented <!-- id: lrn-0814-12 -->
  symptom: the application needed a larger single robot without changing its established movement, lidar, camera, odometry, or TF interfaces
  fix: select the installed upstream TurtleBot3 Waffle Pi model and matching bridge/URDF through `TURTLEBOT3_MODEL=waffle_pi`, reduce only its camera update rate to 10 Hz, and use the upstream 0.15 m Nav2 radius (check: the freshly built image emitted `/clock`, `/scan`, `/camera/image_raw`, and `/odom` in both Furnished House and Tugbot Warehouse; teleop changed odometry in both worlds; 57 Python tests and 28 extension/deployment tests passed)
  dead-ends: no custom robot adapter or topic remapping was needed; the preinstalled Waffle Pi profile preserved the existing ROS contract

## Waffle-Pi migration retro

- gazebo — fired: yes; accurate: yes; complete: yes for selecting the upstream Waffle Pi SDF, bridge, and robot description while preserving the ROS interfaces; lean: yes.
- simulation — fired: yes; accurate: yes; complete: yes for verifying the same sensor and control contract across House and Warehouse; lean: yes.

- [testing] user-correction (seen 2x) <!-- id: lrn-0814-13 -->
  symptom: `make mapping` still exported the removed `house` identifier even though Compose defaulted to `furnished_house`; the initial response added a permanent regression test for the resolved Make variable
  root-cause: `WORLD ?= house` lived in the later RTF section but Make variables are global, so it overrode Compose for every target
  fix: change the single Makefile default to `furnished_house`, update the RTF example, and verify through the real `make mapping` path without retaining a narrow implementation test (check: launch logged `world:=furnished_house`, Waffle Pi spawned, state was `IDLE`, and `/map` was absent)
  dead-ends: checking Compose configuration alone missed the value exported by Make; the user explicitly corrected the approach: “please don't add the test. You don't need to add test for everything”
  source: the preference recurred during named-waypoint implementation as “Don't run any tests. remove all the tests.. don't do any unit testing,” then was clarified as “no even remove the old tests ... this is not a production code”; the entire indoor-navigation and Robot Control automated test/smoke surface was removed, while runtime workflows remain

- [foxglove] figured-out-from-scratch <!-- id: lrn-0814-14 -->
  symptom: Lichtblick's 3D Publish control hides Publish pose estimate, Publish pose, and Publish point behind a 300 ms press, unlike RViz's separate 2D Pose Estimate and 2D Nav Goal toolbar buttons; operators could not discover how to initialize AMCL or send a goal
  root-cause: Lichtblick still carries the combined Foxglove Studio control introduced in 2023; `RendererOverlay.tsx` uses `react-use`'s `useLongPress` and the 3D panel's only implemented keyboard shortcut is `3`, while `PanelExtensionContext` exposes no API for selecting or starting another panel's publish tool
  fix: upstream a small Lichtblick 3D-toolbar change that exposes pose estimate and goal as visible actions and adds RViz-familiar `p` / `g` shortcuts; until that lands, carry the same source patch in a pinned viewer build rather than driving the toolbar through DOM selectors (check: current Lichtblick commit `64357108ce49764732f53183d89f363d57d50502`, its file history, Foxglove 3D docs, and RViz docs/source were inspected on 2026-08-14)
  dead-ends: saved layout state can select only one default publish type; Robot Control cannot arm the built-in 3D cursor through the supported extension SDK; no existing Lichtblick issue, customization setting, or `p` / `g` shortcut was found
  anchors: foxglove#nav2-goal-topic-fix

## Named-waypoints retro

- ros2 — fired: yes; accurate: yes; complete: yes for the parameter, service, TF, and goal-publisher boundaries; lean: yes.
- testing — fired: yes; accurate: no for this work block because its test-first/completion flow conflicted with the user's explicit no-testing direction; complete: not scored; lean: no.
- foxglove — fired: yes during the immediately preceding control-toolbar investigation; accurate: yes; complete: partial because Lichtblick's inherited long-press UI and extension-API boundary required source inspection; lean: yes.

## Navigation-plan display retro

- nav2 — fired: yes; accurate: yes for identifying `/plan` and `/local_plan` as the global and controller path surfaces; complete: not runtime-scored by explicit user direction; lean: yes.
- foxglove — fired: yes; accurate: yes for configuring both path topics in the committed 3D layout; complete: not runtime-scored by explicit user direction; lean: yes.

- [foxglove] figured-out-from-scratch <!-- id: lrn-0814-15 -->
  symptom: the served Lichtblick default layout contained cyan `/plan` and orange `/local_plan`, but the open browser subscribed only to `/plan` and showed neither line
  root-cause: Lichtblick retained the origin's previously persisted 3D layout, so a reload did not adopt the newly added `/local_plan`; additionally Nav2's volatile `/plan` had not emitted because no navigation goal was active
  fix: open the dashboard on a fresh browser origin/private window to load the new default layout, then send a waypoint goal while localized (check: live ROS graph showed `/plan` and `/local_plan` publishers, the served HTML contained both styles, current `/plan` rate reported no publication before a goal, and the live `map -> base_footprint` TF resolved)
  dead-ends: the screenshot's `Frame map not found` entries were startup transients; the current TF chain was healthy and was not the continuing cause

## Navigation-plan visibility retro

- nav2 — fired: yes; accurate: yes for distinguishing topic existence from an emitted active plan and verifying the TF chain first; complete: yes; lean: yes.
- foxglove — fired: yes; accurate: yes for tracing the discrepancy to origin-persisted layout state; complete: partial because default-layout refresh behavior still required live source/runtime diagnosis; lean: yes.

- [ros2] figured-out-from-scratch <!-- id: lrn-0814-16 -->
  symptom: ordinary `ros2 topic list -t` and `ros2 service list -t` did not show Nav2's navigation status or cancel endpoint even though `bt_navigator` was active
  root-cause: ROS 2 action transport topics and services are hidden names beneath `/navigate_to_pose/_action/`
  fix: inspect with `ros2 topic list --include-hidden-topics -t` and `ros2 service list --include-hidden-services -t`; adapt `GoalStatusArray` plus the zero-ID/zero-stamp `CancelGoal` cancel-all policy into public `/navigation/state` and `/navigation/stop` interfaces (check: the live Jazzy graph exposed the status, feedback, and cancel_goal endpoints with their exact types)
  dead-ends: grepping the default topic/service listing incorrectly suggested the endpoints did not exist

## Navigation-status controls retro

- ros2 — fired: yes; accurate: yes for action transport, QoS, and service-adapter mechanics; complete: partial because hidden action endpoint discovery required the explicit include-hidden flags; lean: yes.
- nav2 — fired: yes; accurate: yes for treating NavigateToPose action status as authoritative instead of inferring activity from velocity; complete: yes; lean: yes.

- [foxglove] figured-out-from-scratch <!-- id: lrn-0814-17 -->
  symptom: the new Stop navigation button stayed disabled while the backend published `NAVIGATING` and the bridge subscribed successfully
  root-cause: Lichtblick restored the browser's version-2 panel state containing `navigationStopService: ""`; the version-3 normalizer copied that legacy empty string over the new `/navigation/stop` default
  fix: migrate only a pre-version-3 empty stop-service value to the version-3 default, while preserving an explicit empty value saved by version 3 (check: live ROS state and service boundaries were healthy, and source tracing isolated the remaining disable predicate to the persisted empty config)
  dead-ends: action-status parsing, transient-local QoS, bridge subscription, and service availability were all verified healthy before changing the panel
