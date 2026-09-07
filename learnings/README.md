# learnings/

Dated notes from building with the robium plugin — Tier 1 of the learning engine
(spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §4.4). Raw
session transcripts (Tier −1) live gitignored in `.robium/transcripts/`; entries
here are **derived views with pointers back** — never the only copy of anything
a transcript holds.

One file per day per app: `YYYY-MM-DD-<app>.md` — the `-<app>` suffix is
mandatory for app-scoped work (app sessions run in parallel; a shared dated
file would collide). Plain `YYYY-MM-DD.md` only for non-app work.

## Entry template (schema v2)

    - [navigation] wrong-guidance (seen 2x) <!-- id: lrn-0710-03 -->
      symptom: `[controller_server]: Costmap layer error` — robot hugged obstacles
      root-cause: Quick-start costmap YAML omits inflation_layer block
      fix: added inflation_layer, cost_scaling_factor 3.0 — check: nav smoke test passed
      dead-ends: tuning robot_radius (no effect — wrong layer)
      target: navigation/FAILURES.md — clarify costmap evidence
      source: transcript a1b2c3#turn-142..158 (robium-apps/robot-navigation, 2026-08-27)

Rules:
- First line: `[skill-name]` or `[none]`, one of the seven signal types
  (wrong-guidance | no-skill-fired | figured-out-from-scratch | better-method |
  noise | verified | user-correction), optional `(seen Nx)`, and a stable entry
  id `<!-- id: lrn-MMDD-NN -->` so ledgers/observations can cite the entry.
- `symptom` / `fix (check: …)` / `dead-ends` are the three-part evidence bar as
  named fields. Missing parts are fine — the entry is `tentative` until complete.
- `target:` names the skill or focused support file and the intended decision
  change. It is an intent, not a brittle heading or anchor address. `source:`
  points into the transcript archive when known.
- Only the first line is mandatory. Capture is never blocked on schema — write
  the one-liner mid-session; the consolidation pass (Phase 2) completes fields
  from the archived transcript.
- Absorption marking: the observations tier is canonical. After the reviewed
  skill change lands, update its finding to `status: absorbed YYYY-MM-DD` in
  `learnings/observations/` as part of the same change. Legacy anchors and
  `<!-- absorbed -->` markers remain history; do not add new ones.
