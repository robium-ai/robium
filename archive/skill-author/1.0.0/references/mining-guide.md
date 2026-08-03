# Mining guide

How to run Mode 2 (mining) from `../SKILL.md`: extracting reusable skill
content out of an existing repo — an official demo/example repo for a
tool, or an application repo (robium's own trial apps, or third-party apps)
that was built without robium's guidance.

## What counts as a reusable pattern

Not everything in a target repo is skill material. Mine for things that
meet at least one of these bars:

- **Appears in ≥2 places.** The same launch-file structure, the same
  Docker base-image + apt-package set, the same node-remapping trick shows
  up in more than one place in the repo (or across multiple repos you've
  looked at). Repetition is evidence it's a pattern, not a one-off choice
  specific to that project.
- **Is a hard-won config.** A config value, flag combination, or ordering
  requirement that is *not* obvious from the tool's own docs or `--help` —
  the kind of thing that clearly took the original authors debugging time
  to land on (a nonstandard QoS profile that fixes dropped messages, a
  specific `use_sim_time` propagation order, a GPU driver flag needed only
  on a specific platform). These are high value even if they only appear
  once, because they're exactly the "figured out from scratch" moments the
  learnings loop also targets.

Skip: project-specific business logic, one-off naming choices, anything
that's just a straightforward reading of the tool's own documentation (that
belongs in an upstream link, not a mined snippet — see
`references/quality-bar.md` item 7 in this skill, "no invented syntax").

## How to trim an upstream example

A mined example is not a copy-paste of the source file — it is edited down
to skill material:

1. **Minimal.** Strip anything not load-bearing for the pattern being
   demonstrated: unrelated nodes, project-specific naming, commented-out
   experiments. Keep only what's needed for the example to make its point
   and actually run.
2. **Runnable.** The trimmed example must still work standalone (or with a
   clearly stated minimal setup) — don't ship a fragment that only made
   sense wired into the original project's full stack. If it can't be made
   standalone-runnable without losing the point, say so explicitly in the
   surrounding text instead of shipping something that silently doesn't
   run.
3. **Source-linked.** Note where it came from — repo name and, ideally, a
   URL or commit reference — both for attribution and so a future reader
   can go check whether the upstream has since changed.
4. **Status-marked.** Land it as **unverified** initially (see
   `references/quality-bar.md` item 6) — it worked in the source repo's
   context, but hasn't been exercised inside a robium-guided app yet.
   Promote it to **verified** once a trial run or app iteration actually
   exercises that example.

## Where mined knowledge lands

Same placement rule as hardening (`references/learnings-loop.md`):
knowledge goes to the **lowest skill that can hold it**.

1. Identify which tool or decision the pattern is actually about — not the
   repo it happened to be mined from. A Gazebo world-file trick mined from
   a Nav2 demo repo still belongs in `gazebo`, not `nav2`.
2. Check whether a skill for that tool/decision already exists. If yes,
   this is an edit to that skill, following the same body-vs-`references/`
   vs `examples/` choice described in the Decision guidance section of
   `../SKILL.md`.
3. If no skill fits and the pattern is significant enough to justify a new
   trigger surface of its own, that's a signal to run Mode 1 (fresh
   authoring) instead — create the skill first, then land the mined
   content into it.
4. After editing or creating the skill, run
   `uv run skills/skill-author/scripts/validate_skills.py` and commit.

## Worked example

Say you're mining the official `nav2_bringup` demo repo before deepening
robium's `nav2` skill.

1. **Read the repo.** Walk `launch/`, `params/`, and `docker/` — not just
   the README. The README shows the happy path; the actual gotchas live in
   the launch-file argument wiring and the YAML defaults.
2. **List candidates.**
   - The demo's `nav2_params.yaml` sets `inflation_layer.inflation_radius`
     to a value well above Nav2's own shipped default, with a comment
     explaining it's needed for the demo robot's footprint. That's a
     hard-won config — one occurrence, but non-obvious and worth mining.
   - Every launch file in the repo remaps `/tf` and `/tf_static` the same
     way when running multiple robots in one Gazebo instance. That's a
     pattern appearing in ≥2 places — mine it.
   - The demo also hardcodes a world-specific spawn pose. That's
     project-specific, not a pattern — skip it.
3. **Map to skills.** The costmap inflation value and comment: this is a
   Nav2 costmap-tuning fact → lands in `nav2` (its own domain), most likely
   as a short note in `## Key directives` or a `references/costmap.md` file
   if `nav2` already has one. The multi-robot `/tf` remapping trick spans
   Nav2 and Gazebo equally → since it's about how *Gazebo* spawns multiple
   robots into one `/tf` tree, it lands in `gazebo`, with a cross-reference
   added from `nav2`'s `## When to use this skill` pointing at it.
4. **Trim and land.** The remapping launch-file fragment gets cut down to
   just the remap arguments and the two-robot spawn calls that need them,
   with a comment noting it came from `nav2_bringup`'s
   `multi_tb3_simulation_launch.py` and a link to that file at the pinned
   commit. It lands as an `examples/multi-robot-tf-remap.launch.py` file
   under `gazebo/`, referenced from `gazebo/SKILL.md`'s `## References`
   with an `unverified` marker, since it hasn't run inside a robium-guided
   app yet.
5. **Validate and commit** as in step 4 above.
