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

## End-of-block retro

- foxglove — fired: yes; accurate: yes; complete: partial (preinstalled web-extension cache refresh behavior was not covered); lean: yes.
- testing — fired: not loaded automatically for the final smoke failure; accurate: not scored; complete: missing guidance on avoiding concurrent local simulator stacks; lean: not scored.
