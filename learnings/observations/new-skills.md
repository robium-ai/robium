## app-build sessions run without the robium plugin loaded — the whole catalog goes dark <!-- id: obs-new-skills-001 -->
status: ready
proof: 3
signal: no-skill-fired
sources: [lrn-0802-01, lrn-0802-02]
target: new-skill: none — process/setup finding: detecting "robium plugin
  not loaded" belongs in session-bootstrap tooling (a `doctor`-style check,
  a hook, or CLAUDE.md guidance to verify `robium:*` resolves before
  building), not in any single skill's content. Decision for the human —
  this observation is scoped to naming the recurring symptom, not
  prescribing the fix.
evidence: proof=3 independent, explicit occurrences: (1)
  `lrn-0802-01` — tb4-teleop kickoff session, the only attempted robium
  Skill call (`skill-updater`) errors `Unknown skill: skill-updater`; (2)
  `lrn-0802-02` — go2-locomotion pre-kickoff session, turn 344 states
  outright "Those robium skills/agents (robium-architect, architect,
  environments, testing) are not loaded in this session"; (3)
  `learnings/2026-07-26-isaac-go2.md:8` (pre-dates this run, already
  `<!-- absorbed -->`-marked but its finding was never turned into a Tier-2
  observation) — "[none] robium plugin not loaded this session... Proceeded
  manually... Surfaced to the user rather than silently substituting",
  footer at line 228: "kickoff-without-plugin session-setup gap
  (environment, not skill content)". All three independently name the same
  root cause in the assistant's own words, in three different sessions —
  proof>=2 clears the ready bar on its own.
