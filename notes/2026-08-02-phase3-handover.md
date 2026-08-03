# Handover — learning-engine Phase 3 execution (written 2026-08-02)

For the fresh session executing `docs/superpowers/plans/2026-08-02-learning-engine-phase3-experiment.md`.
The plan is self-contained; this document carries state and hard-won process conventions from the
Phase 1/2a/2b sessions that are not in the plan.

## Current state

- **main** = `fb9fdee` (website-repositioning merge) and includes Phase 1 (`6e9b9aa`), Phase 2a
  (`0b1d202`), Phase 2b (`5fe234d`). Local main == origin/main. Baseline verified on this tip:
  155 engine tests, `Checked 24 skills: PASS`.
- **Open PRs (base=main, merge-ready per review, user merges):**
  - #78 `loop/absorb-2026-08-02-external` — 5 external observations into ros2/nav2/gazebo.
  - #79 `loop/absorb-2026-08-02-session` — obs-environments-001 into environments.
  - Plan Task 7 HARD-BLOCKS until both are merged (archive-slot conflicts). Tasks 1–6 are independent.
  - After they merge: rebase the execution worktree branch on main before Task 7.
- **Open issues filed from 2b:** #80 (paragraph anchors — Task 1 closes), #81 (polish bundle — Task 2
  closes), #82 (placement noise), #83 (held-obs + bump policy), #84 (stale website/cli catalogs),
  #85 (plugin-not-loaded SessionStart check). #82–#85 are NOT this plan's scope.
- **User ops items still pending:** enable GitHub branch protection on main (the "merge is the gate"
  mechanism — currently only apply_deltas' refuse-on-main guard enforces it); `/reload-plugins` in
  robium sessions to pick up the 2b hooks.

## Main-checkout `.robium/` facts (read-only inputs, ABSOLUTE paths)

- `/Users/robium/repos/robium/.robium/transcripts/` — 21 archived session JSONLs (primary sources).
- `/Users/robium/repos/robium/.robium/queue.jsonl` — 38 back-mined flags (consolidated in 2b run A).
- `/Users/robium/repos/robium/.robium/mining/` — pinned clones for the 14 external citations
  (`verify_citations.py --repos` must use this absolute path from any worktree).
- `.robium/` is gitignored; worktree copies are DESTROYED on worktree removal — anything that must
  survive (survey reports, retro drafts) goes to the MAIN checkout's `.robium/`.
- The main checkout may carry the user's uncommitted website work — never reset/clean tracked files there.

## Execution conventions that worked (Phases 1–2b, subagent-driven)

- **Isolation:** EnterWorktree (`.claude/worktrees/<name>`); copy the plan file in and commit it as the
  first commit; DELETE the duplicate from the main checkout immediately (avoids merge collisions).
- **Model tiers:** haiku for transcription tasks (plan contains complete code) and tiny fixes; sonnet
  for behavior-spec implementation, integration tasks, and scoped re-reviews; **opus for content
  reviews** (skill prose, observations, PR audits — they verify against primary sources and it has
  paid off every single time); fable for the final whole-branch review.
- **Dispatch preamble (MANDATORY after the Task-9 incident):** every implementer prompt states the
  worktree path imperatively, requires `pwd` + `git branch --show-current` verification BEFORE work
  and `git log` verification of the commit location BEFORE reporting. One agent committed to the main
  checkout's main branch; recovery = cherry-pick into the worktree + `git reset --mixed` on main +
  `git checkout --` of only the affected files (never `--hard`, user files at risk).
- **Reviews:** every task gets a spec+quality review (review-package script, BASE recorded before
  dispatch, never HEAD~1); every fix round ends with a scoped re-review; Minor findings go to the
  ledger, Important+ enter the fix loop even when the verdict says "Approved".
- **Reviewers probe:** the best catches came from adversarial probes (mixed refused+applied batches,
  cap-boundary fixtures, transcript grep verification), not from re-running happy-path tests. Prompt
  reviewers with concrete probe suggestions.
- **Agent flakiness:** background/resumed agents occasionally die mid-response or stall (watchdog).
  Before re-dispatching, ALWAYS check git state — the work is often already committed. Resume the
  same agent id for fix rounds 1–3; fresh implementer + more capable model for 4–5 or after stalls.
- **Trigger-eval judge:** the `claude -p` LLM path behaves oddly under the nested sandbox (stub
  interception observed); `--no-llm` is the deterministic path for gates. Oblique real phrasings
  ("lets do demo 1") FAIL the keyword fallback — that is a known judge-quality limit, not a
  regression. Say which judge ran, always (citation honesty).
- **Engine semantics locked by tests (do not re-litigate):** refusals block a skill's whole batch
  (siblings reported "blocked:…"); no-ops never block; body cap checked on final content; changelog
  inserts below the convention comment, names anchors in plain text; same-destination moves merge
  atomically; no-op moves leave zero destination artifacts; same-file annotate routes through the
  working buffer; apply_deltas refuses to run on main/master (fail-open outside git — variant tmp
  builds rely on this).
- **Citation honesty is enforced at one-word precision** — reviews rejected "twice" vs once and a
  wrong "zero hits" grep claim. Write evidence lines only for checks actually performed.
- **STRICT-era mechanics still apply to hand-authored skill edits in plans:** snapshot to
  `archive/<name>/<old-version>/` BEFORE first edit, bump + top-of-changelog line, same commit.
  Sidecar-only additions (evals.yaml entries) never bump.

## Watch-fors specific to Phase 3

- Task 1 must not change bullet-anchor behavior (guard test included in the plan).
- Task 2 bumps learning-loop 0.1.0→0.1.1; Task 6 bumps 0.1.1→0.2.0 — two snapshots, in order.
- Task 3 edits the validator → skill-author 2.0.0→2.0.1 with snapshot (validator edits are skill content).
- Task 7's three variants must all carry obs-nav2-003's guard sentence (the false-inference warning);
  a variant dropping it is disqualified before scoring, not scored low.
- Task 8: read the lerobot snippet before wiring the command (extras may differ); the pusht download
  is network+disk heavy (timeout 900); Docker ros2 fallback distro comes from the ros2 skill, never
  from memory.
- nav2 post-#78 may or may not have evals.yaml trigger cases — if trigger evals SKIP in the A/B,
  the score table says so and ranking falls to flips/tokens/judge.

## Kickoff for the fresh session

1. Read the plan: `docs/superpowers/plans/2026-08-02-learning-engine-phase3-experiment.md` (its
   header carries the standing decisions; this doc carries the process context).
2. Subagent-driven-development, EnterWorktree `learning-engine-phase3`, plan committed first,
   ledger at the SDD workspace with this file referenced in its header.
3. Check PR #78/#79 state early and tell the user if they're still open (Tasks 1–6 proceed anyway).
