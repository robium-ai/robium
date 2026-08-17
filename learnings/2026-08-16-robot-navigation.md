# Robot Navigation learnings, 2026-08-16

## End-of-block retro

- [testing] worked-as-documented <!-- id: lrn-0816-05 -->
  symptom: The renamed application and new `./app` command surface needed verification beyond shell-level launcher tests.
  fix: Ran the full Docker scenario: Gazebo published lidar, slam_toolbox built and saved `release_smoke_20260816`, the app loaded it into AMCL/Nav2, saved a named waypoint, completed a Nav2 return goal after teleoperation moved and rotated the robot, and restarted into `tugbot_warehouse`. (check: `/mapping/stop` returned the saved YAML path; Nav2 logged `Goal succeeded`; `/simulation/state` returned `tugbot_warehouse`; `/scan` averaged approximately 10 Hz afterward.)
  anchors: testing#smoke-test

- testing — fired: yes; accurate: yes for requiring a real simulator-level pass in addition to `tests/test_app_cli.sh`; complete: yes for the current release path; lean: yes.
- ros2 — fired: yes; accurate: yes for topic-rate, service-response, parameter, and TF checks used to verify each runtime boundary; complete: yes; lean: yes.
- nav2 — fired: yes; accurate: yes for the mapping → map save → localization → waypoint goal sequence; complete: yes, including recovery from one progress-check retry before the goal succeeded; lean: yes.
- gazebo — fired: yes; accurate: yes for validating the world restart through state plus resumed sensor publication; complete: yes for this headless simulation check; lean: yes.
