# learnings/observations/

The single durable store of findings on their way into skills. One file per
target skill (`<skill>.md`, stem must be a real skill directory); cross-catalog
proposals go in `new-skills.md`. Historical files keep their original IDs when
a skill is renamed. Lint:
`python3 scripts/engine/observations.py --check learnings/observations/*.md`.

There is no separate dated-learnings tier. Raw capture lands in
`.robium/queue.jsonl` during a build; consolidation writes it here as a
`tentative` entry and it climbs the same ladder from there.

    .robium/transcripts + queue.jsonl  →  observations/<skill>.md  →  skills/

## Entry template

    ## costmap inflation missing from quick start <!-- id: obs-navigation-007 -->
    status: ready
    proof: 2
    signal: wrong-guidance
    sources: [robium-apps/robot-navigation 2026-07-10, 2026-07-26]
    target: navigation/FAILURES.md (update) — distinguish missing sensor data from layer tuning
    evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓
    symptom: `[controller_server]: Costmap layer error` — robot hugged obstacles
    root-cause: quick-start costmap YAML omits the inflation_layer block
    fix: added inflation_layer, cost_scaling_factor 3.0 (check: nav smoke test passed)
    dead-ends: tuning robot_radius — no effect, wrong layer
    source: transcript robium__a1b2c3.jsonl#turn-142..158

External (mined) entries carry `origin`, `source`, and `quote` instead of the
narrative fields:

    ## single-node composition uses NodeOptions everywhere <!-- id: obs-ros2-001 -->
    status: ready
    proof: 1
    signal: better-method
    sources: [ros2/examples@ab12cd3]
    target: ros2#composition-node-options (add) — composition idiom for rclcpp components
    evidence: official repo, consistent with docs (search-synthesis 2026-08-01 — docs.ros.org fetch blocked; re-verify on absorb)
    origin: external
    source: ros2/examples@ab12cd3 rclcpp/composition/src/manual_composition.cpp#L28-L34
    quote: rclcpp::NodeOptions options;

## Rules (lint-enforced where deterministic)

- **id**: `<!-- id: obs-<file-stem>-NNN -->` at the end of the `##` heading;
  three digits; unique within the file; prefix must match the filename stem.
- **status**: `tentative` | `ready` | `absorbed YYYY-MM-DD` | `rejected (<reason>)`.
  `absorbed`/`rejected` entries stay in place — they are the audit trail and the
  dedup memory (dedup against everything *seen*).
- **tentative is the capture stage.** It needs only `status` and `signal`;
  write the one-liner while the context is fresh and let consolidation fill the
  rest. Never block a build to complete an entry.
- **proof**: integer ≥ 1 — count of independent occurrences/sources.
- **signal**: one of `wrong-guidance`, `no-skill-fired`,
  `figured-out-from-scratch`, `better-method`, `noise`, `verified`,
  `user-correction`. Mined entries map: new transferable pattern →
  better-method; confirms existing skill content → verified; contradicts skill
  content → wrong-guidance; domain no skill owns → no-skill-fired (routes to
  new-skills.md).
- **sources**: non-empty `[a, b, …]` list — app/session refs and/or
  `repo@short-sha` refs (convergence witnesses; only `source:` is quote-verified).
- **target**: `<skill>[/support-file] (add|update|retire|move) — <decision to
  change>`, or in `new-skills.md`: `new-skill: <proposed-name> — <what>`.
  Choose the narrowest likely file, but treat this as intent: the author may
  place the final wording elsewhere after reviewing the current skill.
- **narrative fields** (`symptom`, `root-cause`, `fix`, `dead-ends`) are
  optional and belong to findings from your own builds. `dead-ends` earns its
  place: it is the part a lean skill will not carry, and the reason the next
  agent does not repeat the same probe.
- **ready bar**: `status: ready` requires proof ≥ 2, OR signal =
  user-correction, OR the three-part evidence bar (three ✓ marks in evidence),
  OR origin external with the word "official" in evidence (the official-source
  bar — vendor repo consistent with current docs).
- **external contract**: `origin: external` requires `source:`
  (`<org>/<repo>@<short-sha> <path>#L<a>[-L<b>]`) and `quote:` (verbatim text
  from those lines). A quote that fails scripts/engine/verify_citations.py is
  a discarded candidate — fix the citation or drop the entry. `quote:` may
  span multiple lines: continue it on following lines indented at least one
  space/tab (parse_file joins them with `\n`; whitespace differences don't
  affect verification).
- **Merge-on-same-finding**: one canonical entry per finding; new occurrences
  append to sources and bump proof — never sibling entries. Contradictions
  evolve in place: "now X (previously Y)".
- **Absorption**: edit the live skill directly, run the checks appropriate to
  the change, then mark the observation absorbed in the same reviewed diff.
- **Compact on absorb.** Once the skill carries the knowledge, the entry's job
  is dedup, not instruction. Cut `target` and the narrative fields down to the
  one-line claim that identifies the finding, and keep `id`, `status`,
  `signal`, `sources`, and any correction note ("previously claimed X — wrong,
  because Y"). Correction notes stay forever; they are what stops a rejected
  claim coming back.
