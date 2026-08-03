# The learnings loop

The operational loop that connects application-building sessions (where
friction with robium's skills actually happens) back to the robium repo
(where that friction gets fixed). This is what "hardening" (Mode 3 in
`../SKILL.md`) consumes.

## Where learnings come from

During any app-building session in a `robium-applications` repo (or any
application repo with the robium plugin enabled), friction with the skills
is captured **immediately**, in the moment it happens — not reconstructed
from memory at the end of the session. Notes go into a dated file in the
application repo:

```
learnings/YYYY-MM-DD.md
```

One file per day is enough; multiple sessions on the same day append to the
same file. Each entry should be a short, self-contained bullet — enough
detail that a later hardening session can act on it without re-deriving the
context.

### What to capture

- **Wrong or missing guidance** — a skill said to do X and X didn't work,
  or produced an error; or the situation needed guidance and none of the
  loaded skills had it.
- **Stale samples** — an `examples/` snippet or reference didn't match the
  current version of the tool (renamed flag, changed config key, deprecated
  API), or a "verified" example actually failed.
- **No-skill-fired gaps** — a question was asked, or a decision point was
  reached, and no robium skill's description triggered, even though one
  arguably should have (this is a description/trigger-surface bug, not just
  a content bug — see `references/quality-bar.md` item 2 in this skill).
- **Figured-out-from-scratch moments** — anything the agent had to work out
  by trial and error, reading source, or web search, that a skill should
  have just told it. These are the highest-value entries: they're proof a
  skill is missing knowledge it should hold.
- **Better-method upgrades** — the skill's guidance *worked*, but a
  superior approach surfaced during the build (simpler command, newer API,
  cleaner pattern). Robium's bar is best-known-method, not
  first-method-that-works; capture the upgrade even though nothing broke.
- **Noise and verbosity** — the needed answer existed in the skill but was
  buried: too much prose before the command, a reference that should be a
  three-line table, duplicated content across sections. Clean skills are a
  deletion product; these entries feed the hardening prune pass.
- **Worked-as-documented successes (✓)** — a non-trivial skill snippet or
  example ran exactly as written. Mark the entry with ✓ and name the
  file/section. These are the evidence hardening uses to promote
  `status: unverified` examples to verified — without ✓ entries, nothing
  ever earns verification.

A good entry names: which skill (or "none") was involved, what was
expected, what actually happened, and — if known — what the fix should be.
Vague entries ("nav2 was confusing") are much less useful during hardening
than specific ones ("nav2's `## Quick start` costmap YAML omits the
`inflation_layer` plugin block; without it the costmap never inflates
around obstacles").

### Example `learnings/2026-07-11.md` entries

```markdown
- [nav2] Quick start costmap YAML has no `inflation_layer` plugin entry;
  robot drove flush against obstacles before stopping. Fix: add the
  plugin block with a sane default radius to nav2's Quick start snippet.
- [none] Asked "why is my odom drifting in sim" — no skill fired on this
  phrasing even though `gazebo` covers sensor-noise plugins that explain
  it. Fix: add 'odom drift', 'odometry drift' as literal keywords to
  gazebo's description.
- [foxglove] Had to read Foxglove's GitHub issues to find the right
  websocket bridge launch args for a remote server setup (no local
  display) — not documented anywhere in the skill. Fix: add a
  remote-server section to foxglove's Platform gotchas.
```

Each bullet is one entry; the `[skill-name]` or `[none]` prefix makes
grouping-by-skill (hardening step 2) a mechanical first pass before the
judgment calls.

### End-of-block retro

In-the-moment capture misses what only hindsight shows. At the end of each
work block (a milestone, or the session), run a short retro over every
robium skill that loaded during the block and add one line per skill to the
same day's learnings file, scoring four things: **fired** (did it trigger
when it should have — and did it stay quiet when it shouldn't?),
**accurate** (was its guidance correct and current?), **complete** (did it
cover what the block needed?), **lean** (was the signal easy to find?). A
skill that scores clean on all four still earns a line — "no findings" from
a real workload is itself evidence.

## What a hardening session does

A hardening session runs in the **robium repo**, with `skill-author`
loaded, some time after one or more app sessions have produced learnings
files. (For absorbing a single session's learnings on the spot, the
`skill-updater` skill runs a session-scoped pass of this same process from
the app session itself.) It follows Mode 3 in `../SKILL.md`:

1. **Consume** — read every `learnings/*.md` file in the application repo
   that isn't yet marked absorbed (see below).
2. **Group by skill** — cluster entries by which robium skill they
   implicate. An entry with "no skill fired" is grouped under whichever
   skill *should* have fired, once that's determined (or under the closest
   umbrella if genuinely no skill exists yet — that's a signal for Mode 1
   fresh authoring instead).
3. **Archive, then bump** — before the first edit to any skill, snapshot
   its current directory to `archive/<name>/<current-version>/` at the
   repo root, then raise `version:` in frontmatter per the bump semantics
   in `references/quality-bar.md` item 9 (build = small fix, minor =
   content addition, major = restructure). One bump covers all of this
   session's edits to that skill. Never edit a skill without the archive
   snapshot landing in the same commit.
4. **Edit** — apply the placement rule (below) to fix each skill: correct
   wrong guidance, refresh a stale sample, add a missing section, or widen
   a description's trigger surface. Always the **smallest edit that carries
   the knowledge**: fix an existing line before adding a new one, add a
   bullet before adding a section. Not every learning earns an edit — a
   one-off note can stay a note; the catalog's default growth rate should
   be near zero.
5. **Promote verified examples** — for every ✓ entry naming an
   `examples/` file that a real build exercised end-to-end, flip that
   file's `status: unverified` marker to `status: verified (YYYY-MM-DD,
   <app>)`. Verification is earned only by ✓ evidence, never by re-reading
   the example.
6. **Prune** — hardening removes as deliberately as it adds. Act on every
   noise/verbosity entry, and re-check each touched skill against the
   quality bar: duplicated content, stale caveats, prose that should be a
   table, sections grown past their point. A hardening session that only
   ever adds content is bloating the catalog, not hardening it.
7. **Changelog** — every skill touched during hardening gets one new
   line appended to its `## Changelog` section, starting with the new
   version: `- <new-version> (YYYY-MM-DD): <what changed and why>` (not
   just "fixed nav2" — enough to trace back to the learning that caused
   it).
8. **Mark absorbed** — once a learning has been acted on (edited into a
   skill, or explicitly decided as not-actionable with a reason), append
   `<!-- absorbed: YYYY-MM-DD -->` to the end of its line in the learnings
   file. This keeps the next hardening session from re-processing it.
9. **Re-verify triggering** — if any description was edited (trigger-surface
   fixes from `[none]` entries), run skill-creator's description evals with
   the exact phrasings recorded in those entries as test cases, so the fix
   is proven against the miss that motivated it rather than assumed.
10. **Validate and commit** — run `scripts/validate_skills.py`, then commit
   the skill edits (in the robium repo) separately from marking learnings
   absorbed (in the application repo).

## Placement rule

Knowledge goes to the **lowest skill that can hold it**. A Nav2 costmap
gotcha is a `nav2` edit, not an `architect` edit, even though `architect`
is what routed the agent to `nav2` in the first place — `architect` stays
about routing and stack selection, not tool-specific detail. If a learning
seems to belong at a higher level than the tool it's about, that's usually
a sign the entry needs to be split: the routing/decision aspect goes to the
umbrella, the tool-specific fact goes to the per-tool skill.

## Recurrence rule

The **first time** something appears in learnings, it may be a one-off
(bad luck, an unusual environment, a fluke). The **second time** the same
gap or wrong guidance appears — even worded differently, even from a
different app session — it becomes a skill edit immediately. Do not wait
for a third occurrence to "be sure": two independent sessions hitting the
same friction is already enough signal that the skill, not the app, is at
fault.
