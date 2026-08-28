# The promotion bar: queue to Tier 1 to observation to delta

Knowledge moves through three promotions before it ever touches a skill:
queue flag → Tier-1 learnings entry (consolidate), Tier-1 entry → Tier-2
observation (consolidate), observation → delta (absorb). Each promotion has
its own bar. This reference distills skill-updater's promotion criteria
(the manual, on-demand version of this same ladder) for the automated
pipeline that now walks it.

## Queue → Tier 1 (the noise bar)

Hook-written queue flags (user-correction phrasing, command errors) are
pointers into the transcript, not knowledge yet. The queue is quarantine:
discarding a flag that never amounts to anything costs nothing, so the bar
here is low but real: a flag promotes to a dated learnings entry only when
it resolves to one of the seven signal types (wrong-guidance, no-skill-fired,
figured-out-from-scratch, better-method, noise, verified, user-correction)
with enough substance to name a skill (or "none") and say what was expected
versus what happened. Vague or context-free flags are discarded at this
stage rather than carried forward as vague entries; noise later is more
expensive than silence now.

**Recurrence shortcut carried over unchanged:** the first time something
appears, it may be a one-off. The second independent hit (a different
session, a different app, even worded differently) skips deliberation
entirely and proceeds toward promotion; two independent occurrences is
already the strongest signal there is that a skill, not the situation, is
at fault. Consolidate applies this by watching for repeated queue flags and
repeated Tier-1 entries naming the same anchor or symptom.

## Tier 1 → Observation (the evidence bar)

The field-by-field entry format and the exact `status: ready` requirement
live in the observations tier's own README (learnings/observations/README.md);
read it there rather than duplicating the table here; it is the
lint-enforced source of truth and the two must never drift apart.

What carries over unchanged from skill-updater's promotion bar is the
*shape* of the requirement, not the field names: a learning earns
`status: ready` only when its evidence is verifiable, not merely plausible.
Concretely, that means one of: proof from two or more independent
occurrences, a user-correction signal (the strongest single-observation
proof there is), the three-part evidence bar completed (a named failure
pattern verbatim, a passing check that actually verified the fix, and at
least one ruled-out dead-end), or, for mined content, an official-source
citation consistent with current docs. Wrong-guidance and ✓-verified
entries usually satisfy the three-✓ evidence bar by construction (a
correction and a verified run both tend to carry a named symptom, a
passing check, and a ruled-out dead-end as a matter of how they're
captured), but the lint checks the ✓ marks themselves, not the signal
type: a wrong-guidance entry with only proof:1 and fewer than three ✓
marks still fails the ready bar like any other observation. Everything
short of the bar stays `status: tentative` until the missing part shows
up; missing all three evidence parts is not a failure to fix urgently; it
is exactly what `tentative` status is for.

## Observation → Delta (the placement rule)

Only `status: ready` observations are eligible for absorb; drafting a delta
from anything else is absorbing around the bar, which the engine's own
directives forbid. For each ready observation, the placement question is
the same one skill-updater always asked: **which is the lowest skill that
can hold this knowledge?** A costmap gotcha is a nav2 edit, not an architect
edit, even though architect is what routed the session to nav2 in the first
place: architect stays about routing, nav2 owns the tool-specific fact. An
observation that seems to span both levels usually needs to split into two
deltas: the routing/decision aspect to the umbrella, the tool-specific fact
to the per-tool skill. scripts/engine/placement.py runs this check
mechanically per finding before a delta is drafted.

**Smallest edit that carries the knowledge** is the other half of placement,
carried verbatim from skill-updater: prefer an `update` to an existing
anchor over an `add` of a new one; a new bullet over a new section; a
keyword folded into a description over a description rewrite. Pair
additions with prunes wherever the observation set allows it; the
catalog's default growth rate should stay near zero, which is exactly why
refine's prune pass runs after every absorb rather than on its own separate
schedule. If a finding genuinely can't land as a small delta (it implies a
restructure or a new section), the delta drafter should say so and route it
to a full refine cycle rather than forcing an oversized delta through
absorb.

## Where the two gates live now

skill-updater ran two explicit human gates because it edited skills
directly: Gate 1 picked which harvested items proceeded, Gate 2 approved
the drafted diff before any commit. The engine keeps both gates' *purpose*
but relocates them:

- **Gate 1's job, deciding what's worth carrying forward, is now the
  `status: ready` bar itself.** It is evidence-based rather than a manual
  per-item nod, but it is still a real filter: an observation that hasn't
  earned proof, a user-correction, three-part evidence, or an official
  citation simply isn't eligible for a delta, no matter how plausible it
  looks. A human can still downgrade or reject an observation at
  consolidate time (marking it `rejected (<reason>)`), which is Gate 1's
  manual override valve.
- **Gate 2's job is a concrete, verified diff under current human authority.**
  External contributors, unattended automation, and unrequested absorption
  end in a PR carrying the evidence table (skill, anchor, op, observation link,
  sources, eval results) and the dry-run report, followed by human merge. A
  maintainer may instead explicitly authorize local direct-main work in the
  current conversation. That exception removes branch/PR ceremony only: the
  same evidence table, archive/version/changelog mechanics, evals, validation,
  and concrete diff remain mandatory. It never becomes standing authority for
  a later session.

The asymmetry skill-updater built the whole policy around (capture is
free, absorption is curated) still holds: an observation that never
reaches `ready` costs nothing sitting in learnings/observations/; a
skill edit that lands costs every future reader of that skill.

Adapted from skill-updater 1.1.1 / skill-refiner 1.0.1 at retirement (2026-08-02).
