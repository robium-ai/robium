---
name: skill-updater
version: 1.0.0
description: >
  Fold the current session's learnings back into the robium skills, on
  demand. Harvests gotchas from the conversation and any unabsorbed
  learnings/ files, confirms the list, then edits the robium source
  checkout: fixes wrong/stale guidance, widens missed trigger surfaces,
  adds figured-out-from-scratch knowledge, prunes noise, and promotes
  ✓-verified examples. Use when: a work session surfaced gotchas,
  frictions, or better methods worth keeping; 'skill-updater', 'update my
  skills', 'absorb these learnings', 'fold these gotchas into the skills',
  end of an app-building session with the robium plugin. Runs ONLY on
  explicit user request — agents surface candidate learnings and offer,
  never invoke this themselves. Developer workflow — requires a local
  robium checkout. Not for: authoring a new skill from scratch
  (skill-author) or building apps (architect).
---

# skill-updater

The end-of-session absorption command for robium developers. `skill-author`'s
hardening mode assumes a dedicated later session in the robium repo; this
skill is the in-the-moment variant — invoked from whatever repo you're in,
right when the session that produced the learnings is still in context. The
conversation itself is the richest learnings source there is: harvest it
before it's gone.

## When to use this skill

- A build/debug session with robium skills loaded is wrapping up and
  produced gotchas, frictions, trigger misses, better methods, or
  worked-as-documented ✓ evidence.
- The user says any of: "update my skills", "absorb these learnings",
  "fold this into the skills", "skill-updater".
- Unabsorbed `learnings/*.md` entries exist and the user wants them applied
  now rather than in a future hardening session.
- Not this skill: writing a brand-new skill (that's `skill-author` Mode 1,
  run in the robium repo), routine hardening of accumulated files from many
  sessions (that's `skill-author` Mode 3 — prefer it when learnings span
  several sessions you weren't part of), or anything app-building.

## Key directives

- **Invocation is the user's, always.** This skill never fires on its own
  initiative: an agent that spots skill-worthy learnings OFFERS a candidate
  list and asks whether to run skill-updater — it does not run it. Capture
  (writing learnings notes) is automatic and lossless; absorption (editing
  skills) is a curated, human-gated act. The asymmetry is the anti-bloat
  mechanism: unabsorbed notes cost nothing, an unneeded skill edit costs
  every future reader.
- **Two explicit gates — no edit is committed past either without a yes.**
  Gate 1 (candidate gate): the harvested list is presented and the user
  selects items. Gate 2 (change-summary gate): after drafting the edits but
  BEFORE committing anything, present a per-skill summary — skill name,
  version bump (old → new), and the concrete changes (diff-level: which
  lines/sections change and how) — and get an explicit go-ahead. If the
  drafted edits drifted from what Gate 1 approved, say so. Never collapse
  the two gates into one.
- **Per-item opt-in, not opt-out.** The confirmed list is what the user
  affirmatively selected; anything they skip stays in `learnings/` — a
  perfectly good permanent home. Do not bundle borderline items in with
  obvious ones.
- **Smallest edit that carries the knowledge.** Prefer correcting an
  existing line over adding a new one; a new bullet over a new section; a
  keyword added to a description over a description rewrite. Pair additions
  with prunes where the noise entries allow — the catalog's default growth
  rate should be near zero. If an item can't land small, say so and defer
  it to a hardening session rather than forcing it in.
- **Never edit the installed plugin copy.** The plugin cache
  (`~/.claude/plugins/cache/...`) is a deployment artifact. All edits go to
  the robium **source checkout**; locate it first (ask the user if it isn't
  obvious — do not guess a path silently), and remind them at the end to
  push and reinstall/`/reload-plugins` so the running plugin picks up the
  changes.
- **Harvest before you edit.** Sweep the current conversation for all six
  signal types from the capture taxonomy (wrong/stale guidance, trigger
  misses with exact phrasing, figured-out-from-scratch, better methods,
  noise/verbosity, ✓ successes), merge with any unabsorbed `learnings/*.md`
  entries in the working repo, and show the user the consolidated list with
  the skill each item targets **before** touching anything. The user
  confirms or trims the list; user-confirmed items proceed to drafting
  without waiting for a second occurrence (the developer invoking this
  skill IS the recurrence signal) — but still pass Gate 2 before any
  commit.
- **The rules live in skill-author — follow them, don't fork them.** Read
  the checkout's skill-author references before editing: quality-bar (what
  a skill must look like), learnings-loop (placement rule: lowest skill
  that can hold it; ✓-promotion; prune; changelog; absorbed markers). This
  skill orchestrates a session-scoped pass of that same process.
- **New facts get verified, not remembered.** If a learning adds a
  version/status/API claim, verify it against live docs at edit time and
  cite the verification method — the citation-honesty bar applies to
  hardening edits exactly as it did to original authoring.
- **Leave the repo green.** Run the validator after edits; commit skill
  edits in the robium checkout separately from marking
  `<!-- absorbed: YYYY-MM-DD -->` in the working repo's learnings files.

## Quick start

1. Locate the robium source checkout (confirm with the user).
2. Harvest: conversation sweep + unabsorbed `learnings/*.md` → consolidated
   list, one line per item: `[target-skill] finding → intended edit`.
3. **Gate 1:** present the list; the user selects which items proceed.
4. For each skill about to be touched: snapshot its current directory to
   `archive/<name>/<current-version>/`, then bump `version:` per the
   quality bar's semantics (build = small fix, minor = content addition,
   major = restructure; one bump per skill per session).
5. Draft the edits per skill-author's learnings-loop: lowest skill that can
   hold each item, promote ✓ examples to `status: verified (date, app)`,
   act on noise entries by deleting, changelog line starting with the new
   version: `- <new-version> (YYYY-MM-DD): ...`.
6. **Gate 2:** present the per-skill change summary (name, old → new
   version, concrete diff-level changes); commit NOTHING until the user
   explicitly approves.
7. `uv run skills/skill-author/scripts/validate_skills.py` → must PASS.
8. Commit + push the robium checkout (skill edits + archive snapshots in
   the same commit); mark absorbed markers in the working repo's learnings
   files and commit those there.
9. Remind the user: `/reload-plugins` (local marketplace) or plugin update
   to run on the new version.

## Decision guidance

- **Apply now vs defer to hardening** ("now" = in this session's gated
  pass — both gates still apply): factual corrections (wrong command,
  stale version, broken snippet) and ✓ promotions always qualify for now.
  Structural changes (new section, description rewrite, splitting a skill)
  apply now only if the user confirms; otherwise leave the learning file
  unabsorbed with a note — a dedicated hardening session has more room for
  that judgment.
- **Trigger-miss fixes:** add the exact recorded phrasing as literal
  keywords to the missed skill's description; keep the description within
  1024 chars — if it won't fit, tighten prose before dropping keywords.
- **Where an item lands:** placement rule from learnings-loop — tool fact →
  tool skill; routing/decision aspect → umbrella; split entries that span
  both.
- **Conflicting learnings** (session says X, skill says Y, both plausible):
  don't silently overwrite — verify against live docs; if still ambiguous,
  record both in the learning entry and defer.

## Platform gotchas

- Claude Code plugin installs are copies: edits to the source checkout do
  nothing for the running session until pushed + reinstalled/reloaded.
  Budget for that last step or the next session tests stale skills.
- If this skill fires in a repo with no robium checkout available (e.g. a
  remote/CI environment), fall back to capture-only: write/complete the
  `learnings/*.md` entries so a later hardening session can absorb them,
  and say that's what happened.
- Session context is the harvest source — if the conversation was already
  compacted, the early gotchas may be gone; harvest what survives and note
  the gap rather than reconstructing from memory.

## Customization

- Default source-checkout convention is a sibling `robium/` repo next to
  the app repos; teams with a different layout should state the path in the
  app repo's CLAUDE.md so this skill finds it without asking.
- The confirm-before-edit gate (Quick start step 3) is deliberate and
  upstream robium never runs without it: automated absorption is how
  catalogs bloat. A fork that removes the gate takes on monotonic skill
  growth as a maintenance burden — if you must, at least keep the
  smallest-edit rule and the prune pairing.

## References

- The robium checkout's skill-author references are the canonical rules:
  quality-bar (structure + description bar) and learnings-loop (capture
  taxonomy, placement, recurrence, ✓ promotion, prune, absorbed markers).
  This skill deliberately carries no copy of those rules — read them from
  the checkout at run time so they can't drift.
- Capture taxonomy also lives in the app-repo CLAUDE.md convention (see
  robium-applications) — the six signal types this skill harvests.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 2026-07-10: created (thin) — on-demand session-end absorption entry point
  wrapping skill-author's hardening rules.
