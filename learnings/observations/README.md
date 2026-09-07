# learnings/observations/

Tier 2 of the learning engine — canonical, proof-counted, absorption-ready
findings (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md
§4.5 + §6a.3). One file per target skill (`<skill>.md`, stem must be a real
skill directory); cross-catalog proposals go in `new-skills.md`. Historical
files keep their original IDs when a skill is renamed. Lint:
`python3 scripts/engine/observations.py --check learnings/observations/*.md`.

## Entry template

    ## costmap inflation missing from quick start <!-- id: obs-navigation-007 -->
    status: ready
    proof: 2
    signal: wrong-guidance
    sources: [lrn-0710-03, lrn-0726-01]
    target: navigation/FAILURES.md (update) — distinguish missing sensor data from layer tuning
    evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓

External (mined) entries add three fields:

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
  dedup memory (dedup against everything *seen*, spec §6 rule 3).
- **proof**: integer ≥ 1 — count of independent occurrences/sources.
- **signal**: one of the seven types from learnings/README.md. Mined entries
  map: new transferable pattern → better-method; confirms existing skill
  content → verified; contradicts skill content → wrong-guidance; domain no
  skill owns → no-skill-fired (routes to new-skills.md).
- **sources**: non-empty `[a, b, …]` list — `lrn-…` entry ids and/or
  `repo@short-sha` refs (convergence witnesses; only `source:` is quote-verified).
- **target**: `<skill>[/support-file] (add|update|retire|move) — <decision to
  change>`, or in `new-skills.md`: `new-skill: <proposed-name> — <what>`.
  Choose the narrowest likely file, but treat this as intent: the author may
  place the final wording elsewhere after reviewing the current skill.
- Existing anchor-shaped targets remain as immutable audit history. Do not add
  new anchor IDs just to make an observation addressable.
- **ready bar** (spec §4.5 + §6a.4): `status: ready` requires proof ≥ 2, OR
  signal = user-correction, OR the three-part evidence bar (three ✓ marks in
  evidence), OR origin external with the word "official" in evidence (the
  official-source bar — vendor repo consistent with current docs).
- **external contract** (spec §6a.3): `origin: external` requires `source:`
  (`<org>/<repo>@<short-sha> <path>#L<a>[-L<b>]`) and `quote:` (verbatim text
  from those lines). A quote that fails scripts/engine/verify_citations.py is
  a discarded candidate — fix the citation or drop the entry. `quote:` may
  span multiple lines: continue it on following lines indented at least one
  space/tab (parse_file joins them with `\n`; whitespace differences don't
  affect verification).
- **Merge-on-same-finding**: one canonical entry per finding; new occurrences
  append to sources and bump proof — never sibling entries. Contradictions
  evolve in place: "now X (previously Y per lrn-…)".
- **Absorption**: edit the live skill directly, run the checks appropriate to
  the change, then mark the observation absorbed in the same reviewed diff.
  The legacy version-and-anchor delta applier is not the live-skill writer.
