# Silly TurtleBot learnings, 2026-09-07

- [gemini-robotics] no-skill-fired <!-- id: lrn-0907-01 -->
  symptom: The first Robium application using Gemini Robotics ER 2 Streaming had no owning skill, so Live session, multimodal input, tool-response, and model-boundary decisions had to be derived from official documentation and implementation probes.
  root-cause: Issue #25 intentionally deferred Google robotics guidance until a real application named a specific tool.
  fix: Added a focused `gemini-robotics` skill for ER endpoint selection, Live API orchestration, guarded execution, and the fake-to-simulation-to-hardware validation ladder. (check: skill validator passed and four no-LLM routing diagnostics matched the intended skill boundaries.)
  dead-ends: A broad Google-vendor skill would have duplicated ROS 2, navigation, Gazebo, and integration guidance; treating the standard ER 2 endpoint as Live-capable contradicts the current model capability table.
  target: new-skill: gemini-robotics — own Gemini Robotics ER endpoint and streaming-agent decisions
  source: robium-apps/silly-turtlebot/src/silly_turtlebot/live_agent.py and docs/architecture-brief.md (2026-09-07)

- [gemini-robotics] better-method <!-- id: lrn-0907-02 -->
  symptom: A function schema and system prompt alone could still let a generative planner request undeclared motion, unchecked coordinates, or stale object IDs.
  root-cause: Model-facing tool declarations describe affordances but do not enforce the physical robot's state-dependent safety constraints.
  fix: Exposed only blocking semantic tools and validated their allowlist, exact arguments, ranges, named locations, and latest-scan object IDs in an independent mission guard. (check: six app tests pass, including rejection of `publish_cmd_vel`; simulated Nav2 quarter-turn succeeded through the same semantic bridge.)
  dead-ends: Exposing `/cmd_vel` or arbitrary poses; relying on prompt wording as the enforcement layer; treating action acceptance as completion.
  target: gemini-robotics/SKILL.md — make the deterministic adapter and guard the actuator boundary
  source: robium-apps/silly-turtlebot/src/silly_turtlebot/guard.py and tests/test_live_agent.py (2026-09-07)

- [gemini-robotics] better-method <!-- id: lrn-0907-03 -->
  symptom: The image sent with a user turn described the scene before motion, so later reasoning could use stale visual state after a look action.
  root-cause: Tool completion and visual feedback were initially separate data paths with no post-action freshness contract.
  fix: After a successful inspection action, fetched a fresh JPEG through the robot adapter and streamed it into the still-open session before the next decision. (check: camera-forwarding unit test and fresh simulated OAK-D health smoke pass.)
  dead-ends: Reusing the initial frame; assuming any non-empty JPEG is fresh; importing ROS into the cloud agent instead of keeping a narrow adapter boundary.
  target: gemini-robotics/FAILURES.md — diagnose stale post-action scene reasoning
  source: robium-apps/silly-turtlebot/src/silly_turtlebot/rest_robot.py and tests/test_live_agent.py (2026-09-07)

- [gazebo] figured-out-from-scratch <!-- id: lrn-0907-04 -->
  symptom: Headless TurtleBot 4 simulation first failed because the vendor model-scoped Sensors system selected Ogre 1; adding an Ogre2 Sensors system at world scope then caused duplicate rendering-scene and HLMS datablock failures.
  root-cause: The installed Jazzy Create 3 xacro already owned the Sensors system and hard-coded its render engine, so a second system was not an override.
  fix: Patched that exact installed xacro to Ogre2 in the reproducible container image and kept only one Sensors system. (check: fresh-container Gazebo/Nav2/OAK-D smoke passed and the raw camera published about 3.5 Hz.)
  dead-ends: Xvfb plus Ogre 1 hit texture limits in the furnished home; adding a second world Sensors plugin duplicated scene ownership.
  target: gazebo/FAILURES.md — inspect vendor model-scoped sensor ownership before adding a world plugin
  source: robium-apps/silly-turtlebot/simulation/Dockerfile and silly_turtlebot_sim/launch/home.launch.py (2026-09-07)
