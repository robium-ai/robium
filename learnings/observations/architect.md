## architect never fires on natural-language new-app kickoff phrasing <!-- id: obs-architect-001 -->
status: rejected (disconfirmed — plugin not loaded, not a trigger gap)
proof: 2
signal: no-skill-fired
sources: [lrn-0802-01, lrn-0802-02]
target: architect#description (update) — REJECTED, see evidence. Originally
  proposed widening the trigger-surface phrasing; not applicable, since the
  plugin wasn't loaded in either source session, so no phrasing would have
  helped.
evidence: proof=2 independent sessions, but the "no-skill-fired" diagnosis
  itself was wrong — both sessions' own transcripts state the robium plugin
  was not loaded. `ac1f31b9...jsonl` turn 344: "Those robium skills/agents
  (robium-architect, architect, environments, testing) are not loaded in
  this session." `20531984...jsonl` turns 4076-4085: the only attempted
  robium Skill invocation, `skill-updater`, returned `Unknown skill:
  skill-updater` (once). architect could not have fired regardless of
  phrasing. The real finding moved to learnings/observations/new-skills.md
  obs-new-skills-001. Kept here rejected rather than deleted, as dedup
  memory — a future consolidator re-finding "architect doesn't fire on
  kickoff phrasing X" should land on this note before re-proposing an
  architect description edit. Note: a legitimate prior architect
  trigger-surface fix already exists (learnings/2026-07-13.md:20-38 ->
  architect 1.3.0) and was not re-examined here; check that history before
  drafting any new architect trigger-surface delta.
