# Pre-engine learnings loop: history and manual fallback

Before the delta pipeline existed, "hardening" a skill from session friction
was an entirely manual loop: write dated notes by hand, then run a dedicated
session (skill-author Mode 3, or the on-demand skill-updater) that read
those notes, edited SKILL.md files directly, and committed. This reference
keeps that process on record for two reasons: it explains where today's
schema-v2 learnings entries, the evidence bar, and the placement rule came
from, and it is still the right thing to do by hand when the engine's
tooling genuinely isn't available: a remote or CI environment with no
scripts/engine/ checkout, or a repo that hasn't adopted the plugin hooks
yet.

## What the manual loop looked like

1. **Capture immediately**, in the moment friction happened, into a dated
   learnings/YYYY-MM-DD.md file, never reconstructed from memory at session
   end. One file per day; multiple sessions append to the same file.
2. **Consume** every unabsorbed learnings file in a dedicated hardening
   session, run from the robium repo itself.
3. **Group by skill**: cluster entries by which robium skill they
   implicate; a "no skill fired" entry gets grouped once the right skill
   (or the need for a brand-new one) is determined.
4. **Archive, then bump**: snapshot the skill's current directory to
   archive/<name>/<current-version>/ before the first edit, then raise
   `version:` per the standard bump semantics (build = small fix, minor =
   content addition, major = restructure). One bump covered every edit to
   that skill in the session.
5. **Edit** by hand, applying the placement rule below, always looking for
   the smallest edit that carried the knowledge.
6. **Promote ✓-verified examples**: flip a `status: unverified` example
   marker to `status: verified (date, app)` only on ✓ evidence, never by
   re-reading the example and deciding it looks fine.
7. **Prune** as deliberately as the session added: noise/verbosity entries
   got acted on, and every touched skill got re-checked against the quality
   bar.
8. **Changelog**: one new dated line per touched skill, starting with the
   new version.
9. **Mark absorbed**: append an absorbed marker to each acted-on learning
   so a later hardening session wouldn't reprocess it.
10. **Re-verify triggering**: any description edit motivated by a
    no-skill-fired entry got tested against the exact phrasing that missed,
    via skill-creator's description evals.
11. **Validate and commit**: run the validator, then commit skill edits
    separately from marking learnings absorbed in the application repo.

The two human gates that still govern absorb today came from here
unchanged: a candidate-selection gate (which harvested items proceed) and a
change-summary gate (a concrete diff, reviewed, before anything commits).
skill-updater ran both explicitly in conversation; absorb now expresses the
first as the observation `status: ready` bar and the second as the PR merge;
see the promotion-bar reference for the full mapping.

## Placement rule (unchanged, still load-bearing)

Knowledge goes to the **lowest skill that can hold it**. A nav2 costmap
gotcha is a nav2 edit, not an architect edit, even though architect is what
routed the session to nav2 in the first place: architect stays about
routing and stack selection, tool-specific detail stays at the tool skill.
An entry that seems to belong at a higher level than the tool it's about
usually needs to split: the routing/decision aspect goes to the umbrella,
the tool-specific fact goes to the per-tool skill. This is the same rule
scripts/engine/placement.py now applies mechanically per observation.

## When to still run this by hand

- A remote or CI session with no scripts/engine/ tooling available and no
  practical way to install it for one edit.
- A repo that hasn't picked up the plugin's capture hooks yet, so no
  queue or observations tier exists: write dated learnings entries by hand
  exactly as described above; a later session with the engine available can
  consolidate them retroactively.
- Any situation where the deterministic pipeline itself is broken or under
  active development and a single, well-evidenced fix can't wait: the
  archive-then-bump-then-changelog sequence above is exactly what
  apply_deltas.py automates, so doing it by hand produces a result the
  engine's own validator will still accept.

None of this is an escape hatch around the merge gate: the manual path
removes the tooling, not the gate. A by-hand edit still lands on its own
branch, still gets validated, and still requires the same human approval
before it merges to main skills/** as an engine-drafted PR would; "the
engine isn't available" changes how the diff gets produced, never who
signs off on it landing.

The seven signal types, the three-part evidence bar, and the recurrence
rule are unchanged from this process and are documented in full in
learnings/README.md and the promotion-bar reference; this file is the
procedural memory of how they were applied before there was a script to
apply them.

Adapted from skill-author's learnings-loop reference (skill-author 1.1.3) for
learning-loop's own catalog entry (2026-08-02), the manual process this
skill's consolidate/absorb pipeline now automates.
