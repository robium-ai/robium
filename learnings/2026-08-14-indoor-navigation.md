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
