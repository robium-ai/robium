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

## Cloud Run live-demo block

- [testing] user-correction <!-- id: lrn-0816-06 -->
  symptom: The implementation workflow introduced test-driven-development framing and planned new test scaffolding even though the user wanted direct implementation.
  root-cause: Generic feature-work guidance overrode the user's preferred delivery style.
  fix: Removed TDD phases from the plan, implemented directly, and used the repositories' existing checks only as release verification. (check: user explicitly approved continuing after the revised direct plan.)
  dead-ends: retaining red/green/refactor language after the user rejected it.
  anchors: testing#test-strategy

- [cloud-run] figured-out-from-scratch <!-- id: lrn-0816-07 -->
  symptom: `gcloud billing projects link robium-demos-prod` failed with `Cloud billing quota exceeded` after the project shell was created.
  root-cause: the billing account already had five linked projects, its current quota.
  fix: parameterized `GCP_PROJECT`, deployed dedicated demo identities/resources in `robium-prod`, and documented the weaker isolation boundary. (check: controller, runtime, Scheduler cleanup, and public website all passed production acceptance.)
  dead-ends: retrying the new-project billing link cannot change the account quota; deleting or unlinking unrelated projects was not authorized.
  anchors: cloud-run#project-and-iam-boundary

- [cloud-run] figured-out-from-scratch <!-- id: lrn-0816-08 -->
  symptom: Cloud Build failed with `dockerfile parse error line 64: unknown instruction: IMPORT` although the same Dockerfile built locally.
  root-cause: local buildx accepted Dockerfile heredocs while Cloud Build's Docker step used the legacy parser.
  fix: added `# syntax=docker/dockerfile:1` and `DOCKER_BUILDKIT=1`. (check: build `eef218d2-0bc0-4097-946d-88ce1ae246c1` completed successfully.)
  dead-ends: treating the Python `import` line as a Dockerfile content error; it was parser selection.
  anchors: cloud-run#cloud-build

- [cloud-run] figured-out-from-scratch <!-- id: lrn-0816-09 -->
  symptom: `gcloud builds submit` crashed on an unrelated broken `.pixi` symlink under `robot-navigation/experiments/native-macos`.
  root-cause: the application build uploaded the entire `robium-apps` repository context.
  fix: added a root `.gcloudignore` that includes only Robot Navigation and its required shared assets/dashboard while excluding experiments. (check: the upload shrank to 190 files / 22.5 MiB and reached Cloud Build.)
  dead-ends: retrying the same upload; gcloud traversed the same broken symlink before creating an archive.
  anchors: cloud-run#build-context

- [live-demo] figured-out-from-scratch <!-- id: lrn-0816-10 -->
  symptom: The production viewer returned Lichtblick HTML but rendered an empty root, and a raw WebSocket probe failed.
  root-cause: the gateway served `preinstall-extension.mjs` as `application/octet-stream`, so browsers refused the module bootstrap before the viewer opened its WebSocket.
  fix: serve `.mjs` as `application/javascript`. (check: the public iframe rendered Dashboard controls and live ROS logs; Start mapping changed IDLE to MAPPING.)
  dead-ends: debugging Cloud Run WebSocket support from the raw probe before checking the browser module-loading path.
  anchors: live-demo#viewer-handoff

- [cloud-run] verified <!-- id: lrn-0816-11 -->
  symptom: The first private service on each new digest spent 2m18s–3m14s importing 38 image layers before container health checking.
  fix: expose ALLOCATING separately from BOOTING and keep the same digest pinned for subsequent sessions. (check: the website's next session advanced IDLE → ALLOCATING → BOOTING → READY and embedded a connected Lichtblick viewer.)
  anchors: cloud-run#cold-start

- [live-demo] verified <!-- id: lrn-0816-12 -->
  symptom: The production release needed proof that the mission-control shell controlled real Cloud Run resources rather than a mock/local backend.
  fix: deployed the controller and site, used the public Start button to allocate service `demo-robot-navigation-283e64765b41b4c426a0c3`, observed READY/live ROS data, then used Stop and confirmed IDLE. (check: Cloud Run service list returned only `demo-robot-navigation-control` and `robium-site` after cleanup; the old `demo-nav-trial` service was deleted.)
  anchors: live-demo#acceptance

- cloud-run — fired: yes; accurate: yes for per-visitor services, instance-based CPU, digest pinning, Scheduler cleanup, and multicast-aware single-container design; complete: mostly, but billing-project quota fallback and Cloud Build parser/context details were learned under load; lean: yes.
- live-demo — fired: yes; accurate: yes for the IDLE-first mission-control shell, direct viewer handoff, status phases, fleet cap, and cleanup; complete: improved by adding browser-level MIME/WebSocket acceptance; lean: yes.
- foxglove — fired: yes; accurate: yes for the Foxglove-compatible bridge and Lichtblick WebSocket path; complete: browser module MIME must be checked alongside bridge health; lean: yes.
- gazebo — fired: yes; accurate: yes for loopback transport and headless Cloud Run execution; complete: yes after real cloud lidar and mapping validation; lean: yes.
- testing — fired: too strongly for the user's requested workflow; accurate: existing release checks were useful, but TDD framing was explicitly unwanted; complete: yes after switching to direct implementation; lean: no before the correction, yes afterward.

## Demo information-architecture block

- [live-demo] user-correction <!-- id: lrn-0816-13 -->
  symptom: The first redesign combined the demo catalog, Robot Navigation onboarding, and the running visualizer into one page shape.
  root-cause: The proposed mission-control shell did not distinguish discovery, per-demo launch choices, and the active session workspace.
  fix: Split the experience into a normal site-wide `/demos/` catalog, a regular Robot Navigation detail page with live and local option cards, and a dedicated `/demos/robot-navigation/live/` viewport containing only the compact status bar and edge-to-edge Lichtblick. (check: local browser pass showed the three-card catalog, both option cards with local commands, and a READY simulation whose iframe filled the viewport without page scroll.)
  dead-ends: putting a demo-specific choice screen at `/demos/`; hiding the normal site header and footer before a visitor actually starts a live session.
  anchors: live-demo#mission-control-page

- live-demo — fired: yes; accurate: yes for separating onboarding from the active visualizer; complete: improved by treating catalog, demo detail, and live workspace as distinct reusable page levels; lean: yes after the user's correction.
