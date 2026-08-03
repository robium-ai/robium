# Robium Learning Engine — Design

*2026-08-01. Replaces the skill-author / skill-updater / skill-refiner three-tier meta-layer with a role-based, research-grounded learning engine. Research foundation: `docs/research/2026-08-01-self-improvement-ecosystem-research.md` (7 repo deep dives). Status: draft for review.*

---

## 1. Summary

Robium's product is a compounding knowledge catalog. Today the compounding loop — sessions produce learnings, humans absorb them into skills, a refiner prunes — works but is bottlenecked in four places: capture depends on session discipline, absorption depends on scarce human sessions, the skill format resists precise editing and attribution, and there is no way to test a candidate improvement before shipping it.

This design rebuilds the loop as a **learning engine** with seven roles, each grounded in a proven pattern from the ecosystem research:

| Role | What it does | Runs | Grounded in |
|---|---|---|---|
| **Capture** | Hooks + transcript miner record friction as it happens | Always-on, deterministic, no LLM | claude-reflect, hindsight, AWM |
| **Mine** | Surveys + deep-reads approved external example repos into evidence-cited observations — the ecosystem as a second experience source | Discovery autonomous; runs on approval (registry-driven) | skill-author Mode 2, SkillWeaver, AWM offline mode |
| **Recall** | Injects matching, high-confidence observations back into live sessions — learnings pay off same-day, before any skill edit merges | Always-on hook, deterministic match, token-budgeted | hindsight recall; CTIM-Rover guardrails |
| **Consolidate** | Turns raw captures into canonical, evidence-counted observations | Autonomous (never touches `skills/`) | hindsight, ACE reflector |
| **Absorb** | Drafts anchor-targeted delta edits; a script applies them; output is always a PR | Autonomous up to PR; human merges | ACE curator, OpenAlpha_Evolve, AgentDevel |
| **Verify** | Validator + trigger evals + regression flip-gate; occasional deep-verify in sim/apps | Deterministic core, LLM judges at edges | AgentDevel, OAE evaluator, AgenticROS |
| **Refine** | Counter-armed pruning, dedup, staleness — the existing five passes, now evidence-driven | Scheduled / on demand, PR-gated | ACE grow-and-refine, ExpeL, MUSE |

One engine serves two tiers: **contributors** (destination: PRs to the robium repo) and **users/companies** (destination: a private overlay in their own repo, with an opt-in path to contribute generalizable items upstream).

The human gate does not disappear — it **moves to `git merge`**. Everything before the merge may run autonomously; nothing lands on `main` in `skills/**` without a human. This is the single policy change, and it is what unblocks throughput.

## 2. Design principles (from the research, held as constraints)

1. **The item is the edit unit, not the file.** Knowledge claims get stable anchors; learnings cite anchors; counters attach to anchors; edits target anchors. (ACE, ExpeL)
2. **Evidence counters, not vibes.** Every claim accumulates `helpful`/`harmful` counts with sources. Pruning and promotion read counters. At robium's volume counters are evidence weights, not statistics — single digits still beat adjectives. Counters must accumulate from *successes* too (attribution, §6), not only from friction — a harmful-only ledger biases pruning against quietly-working content. (ACE, ExpeL, hindsight)
3. **Deterministic core, LLM at the edges.** Hooks are regex-only and fail-open. Delta application, version bumps, archiving, changelog lines, and validation are scripts. LLMs propose, diagnose, and judge — they never hold the pen on merges. (AgenticROS, claude-reflect, ACE)
4. **Delta edits with no-op fallback.** Skill edits are expressed as minimal, anchor-targeted operations applied by a script. An unappliable delta degrades to a no-op, never a corrupted file. Full-file LLM rewrites are forbidden — that is how context collapse happens. (ACE, OAE)
5. **Quarantine before promotion.** Raw captures live in a gitignored queue; promotion into durable tiers is an explicit act with an evidence bar. Ungated auto-memory demonstrably makes agents worse. (CTIM-Rover, claude-reflect)
6. **Evolve, don't overwrite.** Contradictions become "X (previously believed Y)" with history preserved; duplicate findings merge into one canonical entry with accumulated evidence. (hindsight)
7. **Failures are first-class.** Errors verbatim, dead-ends, and rejections carry as much distillation value as successes. (ReasoningBank, ExpeL)
8. **Regression gating over form checking.** An edit that passes the validator but breaks a previously-passing eval case does not ship. (AgentDevel's flip gate)
9. **Evals accumulate from real usage, never synthesis.** Recorded trigger-miss phrasings, real errors, real tasks. The eval suite is a byproduct of the loop, not a prerequisite. (Hermes sessiondb-evals; lightweight by explicit user decision)
10. **Curation stays human.** Merge is the gate. The archive keeps everything recoverable. Catalog growth rate targets ~zero (additions paired with prunes). (SkillsBench, MUSE, standing robium policy)
11. **The ecosystem is a primary teacher.** Working external repos encode more accumulated judgment than our own sessions can generate; mining them is a first-class learning path — sharing the same observation → delta → PR machinery as session learning, so there is one engine with two experience sources, not two pipelines. (skill-author Mode 2, SkillWeaver's strong-source distillation, AWM's offline mode)

## 3. Architecture overview

```
            ┌────────────────────────  SESSION (any repo with robium enabled)  ─┐
            │  hooks: UserPromptSubmit · PostToolUse(Bash) · Stop · SessionStart │
            │         · SessionEnd (transcript archiver)                         │
            └──────────────────────────────┬─────────────────────────────────────┘
                                           ▼  (deterministic, fail-open)
   Tier −1 TRANSCRIPTS    .robium/transcripts/*.jsonl   full session logs, archived from
                          Claude Code's auto-saved JSONL; gitignored; THE raw record
                                           │  flag (hooks, real time) + mine (offline)
                                           ▼
   Tier 0  QUEUE          .robium/queue.jsonl          flags = pointers into transcripts
                                           │  promote (consolidator reads the flagged
                                           ▼            transcript windows in full context)
   Tier 1  FACTS          learnings/YYYY-MM-DD.md      dated, structured entries
                                           │  consolidate (LLM, autonomous — never touches skills/)
                                           ▼
   Tier 2  OBSERVATIONS   learnings/observations/<skill>.md   canonical, proof-counted,
                          + skills/<name>/evidence.yaml        evolution-not-overwrite
                                           │  absorb (LLM drafts deltas → script applies →
                                           │          validator + trigger evals + flip gate)
                                           ▼
   Tier 3  SKILLS         skills/<name>/…              PR branch → HUMAN MERGE ← the gate
                                           │
                                           ▼
                          archive/<name>/<version>/    lineage + losing variants + eval scores
```

Cross-cutting: the **recall hook** (§5) closes the short loop — `ready` observations matching the current task are injected back into live sessions as additional context, so knowledge pays off before it ever reaches Tier 3; the **experimentation engine** (§9) generates contrastive evidence for contested edits; the **refine role** (§10) runs the reverse direction (prune/dedup/staleness) through the same delta→PR machinery.

## 4. Substrate

### 4.0 Transcripts — Tier −1, the raw record

Claude Code already saves every session — including all robium work to date — as JSONL transcripts under `~/.claude/projects/<encoded-path>/*.jsonl` (one event per line: user/assistant turns, tool calls, tool results). This is the engine's ground truth, per the research consensus (claude-reflect mines exactly these files; hindsight retains raw transcripts and derives facts from them; Hermes builds eval sets from its session DB; AWM/ReasoningBank induce from raw trajectories).

Design consequences:

- **Learnings are derived views, never the only copy.** Every fact/observation carries a transcript coordinate (`source: transcript <session-id>#<turn-uuid>`); consolidation and any later re-audit read the flagged window from the log *in full context* rather than trusting a summary written mid-session. A learning entry that looks wrong later can be re-derived from source.
- **Hooks flag, they don't transcribe.** Queue items are pointers (session, turn, type, confidence, short grep-excerpt) into the transcript, not copies — so nothing is lost to in-session summarization, and the copy-time secret-leak surface shrinks to the excerpt.
- **Archive before Claude Code prunes.** Transcripts are deleted after `cleanupPeriodDays` (default ~30). A SessionEnd hook copies the session's JSONL into `.robium/transcripts/` (gitignored, optionally gzipped); the miner and consolidator read from the archive, so learning never depends on retention settings. Setup docs also recommend raising `cleanupPeriodDays`.
- **No invented log format.** Claude Code's JSONL *is* the standard here; the archive stores it verbatim. (No cross-tool standard exists in the ecosystem — hindsight and Hermes each roll their own — and converting would be a lossy copy. If a tool-agnostic export is ever needed, that's a Phase-4+ exporter, not a storage decision.)

### 4.1 Anchors — stable IDs on claim-bearing items

Format-compatible with agentskills.io (HTML comments are plain markdown; humans and renderers ignore them):

```markdown
- Nav2's default costmap YAML omits the inflation_layer block — add it or the
  robot hugs obstacles. <!-- id: costmap-inflation -->
```

- Syntax: `<!-- id: kebab-case -->` at the end of the item's first line. Unique per skill; globally referenced as `nav2#costmap-inflation`.
- Anchored: discrete claims — gotchas, version facts, commands, config rules, decision rules. Not anchored: connective prose, headings (headings are already addressable by slug), template boilerplate.
- Validator additions: anchor-format check, per-skill uniqueness, and **anchor stability** — an absorb/refine edit may not silently delete an anchor that has ledger evidence (delete requires an explicit `retire` op, §7.2).
- Anchors are added: (a) in bulk during Phase-1 migration (mechanical pass over all skills, one reviewed PR), (b) by any absorb PR touching new content. Evidence that predates an anchor references `file + quoted-line prefix`; the first absorb PR touching that content converts it to an anchor.

### 4.2 Evidence ledger — `skills/<name>/evidence.yaml`

One sidecar per skill. Written only by engine tooling (consolidator increments, absorb/refine PRs edit); humans read it and see it in diffs.

```yaml
# skills/nav2/evidence.yaml — maintained by the learning engine; do not hand-edit
costmap-inflation:
  helpful: 3          # ✓ worked-as-documented, task success attributed to this item
  harmful: 0          # wrong-guidance, user-correction, misfire attributed to this item
  last_verified: 2026-07-26
  sources:
    - learnings/2026-07-10.md#lrn-0710-03
    - learnings/2026-07-26.md#lrn-0726-01
dds-domain-id:
  helpful: 0
  harmful: 2
  sources: [learnings/2026-07-24.md#lrn-0724-02]
```

Semantics: `helpful++` on ✓ entries and attributed task successes; `harmful++` on wrong/stale-guidance, user-corrections, and misfires naming the anchor. `harmful > 0 && helpful == 0` items are the refiner's first prune candidates; `helpful` history is the defense against over-pruning. Counters carry sources — every increment is auditable back to a dated learning entry.

### 4.3 Eval seeds — `skills/<name>/evals.yaml`

Accumulated from real usage, per the lightweight-evals decision. Empty files are legal; the suite grows as the loop runs.

```yaml
# skills/nav2/evals.yaml
triggers:
  positive:            # phrasings that MUST select this skill (from trigger-miss learnings)
    - phrase: "robot keeps clipping corners near walls"
      source: learnings/2026-07-10.md#lrn-0710-03
  negative:            # phrasings that must NOT select this skill (CTIM-Rover safeguard)
    - phrase: "simulate a 2D lidar in gazebo"
      expect: gazebo
tasks: []              # optional deep checks: {app, command, pass_criteria} — Phase 3
```

### 4.4 Learnings schema v2 — Tier 1 facts

`learnings/YYYY-MM-DD.md` stays a dated, human-readable markdown file (git-native, PR-reviewable — a hard constraint from the hindsight anti-patterns). Entries gain structure borrowed from ACE's reflector schema and hindsight's fact fields:

```markdown
- [nav2] wrong-guidance (seen 2x) <!-- id: lrn-0710-03 -->
  symptom: `[controller_server]: Costmap layer error` — robot hugged obstacles
  root-cause: Quick-start costmap YAML omits inflation_layer block
  fix: added inflation_layer with cost_scaling_factor 3.0 — check: nav smoke test passed
  dead-ends: tuning robot_radius (no effect — wrong layer)
  anchors: nav2#costmap-inflation
  source: transcript a1b2c3#turn-142..158 (apps/nav-trial, 2026-07-10)
```

- The seven signal types are unchanged; they become the entry's type token.
- `symptom` / `fix (check: …)` / `dead-ends` are the existing three-part evidence bar, now named fields. Entries missing parts are legal and stay `tentative`.
- Entry IDs (`lrn-MMDD-NN`) make entries citable by ledgers and observations.
- Humans can still hand-write entries mid-session exactly as today; the consolidator formats/completes them later. Capture must never be blocked on schema.

### 4.5 Observations — Tier 2, `learnings/observations/<skill>.md`

The consolidated, absorption-ready tier (hindsight's observations). One file per target skill; one canonical entry per finding:

```markdown
## costmap inflation missing from quick start <!-- id: obs-nav2-007 -->
status: ready          # tentative | ready | absorbed (+ date) | rejected (+ reason)
proof: 2               # independent occurrences
signal: wrong-guidance
sources: [lrn-0710-03, lrn-0726-01]
target: nav2#costmap-inflation (update) — add inflation_layer block to Quick start YAML
evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓
```

Rules: merge-on-same-finding (one canonical entry, accumulated sources — never siblings); contradictions evolve with history ("now X, previously Y per lrn-…"); `status: ready` requires the three-part evidence bar **or** `proof ≥ 2` **or** signal = user-correction (the strongest single-observation signal). Absorption consumes only `ready` observations. `absorbed` entries stay as the audit trail (replaces the `<!-- absorbed -->` markers).

## 5. Capture & recall layer

Ships **in the plugin** (`hooks/hooks.json` + `hooks/scripts/`, stdlib-only Python) so every install — contributor or user — gets capture for free. All hooks: regex-only, no LLM, fail-open (`try/except → exit 0`), millisecond-budget, silent by default.

| Hook | Trigger logic | Effect |
|---|---|---|
| **UserPromptSubmit** | claude-reflect's correction taxonomy: strong openers (`^no,` `^don't` `^stop`, "that's wrong", "I meant", "use X not Y"), guardrails, explicit `remember:`; FP filters (questions, task-openers, error reports, >500 chars) | queue flag `{type: user-correction, session, turn, excerpt, confidence, ts}` — a pointer into the transcript, not a copy (§4.0) |
| **PostToolUse (Bash)** | Error-bearing results matching robotics/tooling patterns (`colcon`, `ros2`, `gz`/`ign`, `docker`, `uv`, `pytest`, exit≠0 with stderr); dedup by command hash within session | queue flag `{type: error, session, turn, command, excerpt, ts}` — excerpt **secret-scrubbed** (§12) |
| **PostToolUse (Bash)** | `git commit` (not `--amend`) and N_queue > threshold | injects context: "N pending learnings — end-of-block retro due" |
| **Stop** | Queue count > 0 at turn end (throttled: at most once per M turns) | injects one-line nudge to promote/consolidate |
| **SessionStart** | Always | injects queue summary (count + top 3 by confidence); creates `.robium/` if absent |
| **SessionEnd** | Always | **archives the session's JSONL** to `.robium/transcripts/` before Claude Code's retention can prune it (§4.0); prunes archive by age/size policy |

**Transcript miner** (`mine_transcripts.py`, run by the consolidator, not a hook): walks archived transcripts (Tier −1) — including sessions where the real-time hooks flagged nothing — for (a) tool **rejections** — user pressed Esc then gave guidance (the strongest correction signal, currently lost entirely), (b) **repeated errors** — same error class ≥ 2 occurrences → auto `(seen 2x)`, (c) **skill-context tags** — which robium skills were invoked near each event, auto-supplying `[skill-name]`; robotics keywords with no skill loaded → automated **no-skill-fired** entry with the exact phrasing (a free trigger-eval case), (d) **success heuristics** (Hermes): 5+ tool calls succeeding after dead-ends → candidate figured-out-from-scratch entry.

Locations: `.robium/queue.jsonl` (flags) and `.robium/transcripts/` (archived logs) in the working repo — project-local, discoverable, survive across sessions; `.robium/` is gitignored by convention (the bootstrap and docs add it). The flags are an optimization, not the record: consolidation that finds a stale or ambiguous flag re-reads the archived transcript window, and a full offline mining pass needs no flags at all — which also means the engine can back-mine sessions that ran before the hooks shipped, to the extent their transcripts still exist.

### Recall hook — the short loop

Between capture and merge, a `ready` observation is knowledge the engine has but the session doesn't. The recall hook (hindsight's UserPromptSubmit pattern) closes that gap: the same UserPromptSubmit script that classifies corrections also **matches the prompt against the observations tier** and injects hits as additional context — visible to the model, invisible in the transcript. Learnings pay off the same day they're captured, without waiting for a skill-edit PR.

Guardrails (CTIM-Rover showed ungated recall makes agents *worse*, so these are load-bearing):

- **Deterministic matching only** — keyword/tag/skill-name/error-signature match against observation headers and symptoms; no LLM, no embeddings in the hook path. Milliseconds, fail-open.
- **Token budget** (default ~500 tokens) and top-k cutoff; the budget is the cap, not a target — zero matches injects nothing, low-confidence matches inject nothing.
- **Eligibility:** `status: ready`, or `tentative` with `proof ≥ 2`; `absorbed` observations are excluded (the skill now carries them); user tier recalls only its own repo's observations.
- **Injected content is marked** so capture hooks and the miner ignore it (no reflection loops), and each injection cites its observation ID so a wrong recall can be traced and `harmful`-counted — recall misfires are themselves capture signal.

## 6. Consolidate role

An LLM pass (main-agent skill mode or subagent) that is **autonomous-safe because its write surface excludes `skills/**`**. Runs on demand ("consolidate", end-of-block), on the Stop-hook nudge, or scheduled.

Input: queue flags + miner output + unconsolidated Tier-1 entries, each resolved back to its archived-transcript window and read **in full context** — the entry the consolidator writes is distilled from the log, not from a mid-session summary. Output — commits to the working repo:

1. **Promote** queue items that clear the noise bar into Tier-1 entries (structured per §4.4, verbatim text preserved); discard sub-threshold noise (queue is quarantine — discarding costs nothing).
2. **Complete** hand-written Tier-1 entries: attach mined evidence (verbatim errors, checks), skill tags, recurrence counts.
3. **Merge into observations** (§4.5 rules): dedup against all existing observations (including `rejected` — ReasoningBank's lesson: dedup against everything *seen*, or judged-rejected findings reappear forever), evolve contradictions, update `proof`, set `status`.
4. **Increment evidence ledgers** (`skills/*/evidence.yaml`) with sources.
5. **Harvest eval cases**: no-skill-fired phrasings → `evals.yaml` `triggers.positive` of the right skill; misfires → `triggers.negative`.

Steps 4–5 are the only writes consolidation makes inside `skills/` — data sidecars only, never SKILL.md or references. That boundary is what keeps the role autonomous-safe.
6. **Draft the end-of-block retro** (which skills fired, scores) for human sign-off — retros stay the usage signal for the refiner's retirement pass.
7. **Attribute successes** (ACE's implicit per-bullet A/B): for session blocks that ended green (task success, passing smoke test), credit `helpful` to the anchors whose guidance visibly shaped the session's actions — best-effort, transcript-based, neutral by default. Without this, ledgers accumulate only friction and the refiner's pruning biases against content that was quietly doing its job.

The consolidator (and the absorber, §7) runs **one self-check refinement round** on its output before writing — re-reading its draft against the source transcript window for misattribution, missed dead-ends, and wrong anchors (ACE's ablation prices iterative reflection at ~4%; one round captures most of it).

## 6a. Mine role — learning from external examples (Phase 2)

*(Lettered section: inserted after the numbering stabilized; renumbering would break committed cross-references in the plan.)*

Session capture learns from what happened to *us*; mining learns from what already works for *everyone else*. It is a first-class learning path (principle 11) implemented as a **new catalog skill, `mining`** — a fan-out exploration engine, not a mode of another skill — sharing the observation → delta → PR machinery so external and session knowledge flow through one pipeline. It serves both tiers: hardening robium's catalog from ecosystem repos, and (Phase 4) letting a company point it at their own fleet-control repo, custom robot stack, or internal knowledge base to grow their private overlay — one of the engine's primary use cases.

### 6a.1 Source registry

`learnings/SOURCES.md` (committed, human-curated, engine-annotated) is the living registry: candidate repos with one-line whys, statuses (`todo → exploring → distilled | dropped | recheck`), and engine-maintained **crawl records** (`crawled: date @ short-sha → fed: skills/observations`). Users get the same file privately (`.robium/sources.md`, gitignored or committed at their choice). **Discovery is autonomous, spending is gated:** the engine periodically sweeps the registry's discovery sources (awesome-lists, GitHub topics) and files new candidates into the triage inbox with a one-line rationale — but mining runs only on repos the human approved (or named directly: "mine repo X").

### 6a.2 Run types and tiers

- **Single-repo run — survey then deep.** Survey pass (1–2 cheap agents): map the repo, inventory candidate pattern areas, check the license, estimate value → a short report proposing which areas earn the deep pass. Deep pass (approved areas only, or pre-authorized `survey+deep` in the registry): reader agents fan out per subsystem and return candidates. **Code only** — no issue-tracker crawling; commit-history mining (reverts, fix-chains as dead-end evidence) is a considered-and-deferred extension, recorded here so it isn't re-litigated.
- **Comparative run — first-class.** The registry can define comparison *sets* (e.g. turtlebot3_simulations + turtlebot4_simulator + linorobot2). Readers fan out across all members; the distiller's explicit job is the **common/divergent split**: patterns common to all arrive pre-verified (they *are* the convergence bar), divergences become decision-surface candidates for umbrella skills. A comparative run also always compares against **our own catalog and learnings** — where the ecosystem contradicts a skill, that diff routes to the wrong-guidance/better-method signal types.

### 6a.3 Extraction contract

Candidates use the same schema as session learning and land as **observations with `origin: external`** and `source: <repo>@<short-sha> <path>#<lines>`. Anti-hallucination rule (deterministic, from the eval-seeding review pattern): every cited quote/config is verified to exist at the cited location before the observation is written — a citation that doesn't grep is a discarded candidate. The generic-vs-specific triage applies unchanged: transferable patterns (idioms, orderings, workarounds, config shapes, how-large-apps-are-structured) distill; project-local choices (names, ports, one-off tunings) don't.

### 6a.4 Evidence bar and conflicts

- **Official/vendor repo** + consistent with the tool's current docs → absorbable outright, citing `repo@commit` + the docs-check date. Mandatory dated provenance: official examples lag their releases, so every authority-sourced fact enters the 90-day staleness sweep like any other dated claim.
- **Community repo** → convergence: the same pattern in ≥2 independent reputable repos (a comparative run's common-split satisfies this by construction). Single-source community patterns stay `tentative`.
- **Extracted examples** enter `status: unverified` regardless of source, promoted only by a robium trial or the Phase 3 deep-verify lane.
- **Conflict policy — record both, field-tested leads.** When mined guidance contradicts session-verified knowledge, the skill carries both with provenance: our field-tested guidance leads, the official idiom is noted alongside with why it bit us. The divergence itself is flagged for re-verification — upstream may have fixed the original reason.

### 6a.5 Vendoring and citation

Pointer-first: skills cite `repo + path + commit` in References/examples prose, and anchors may carry these citations; the registry row is the indirection point for re-crawls. Vendor actual code only when it is a short adapted snippet or a file we materially modified, only from permissive licenses (Apache/BSD/MIT — attribution header + upstream link + commit), never GPL into the plugin. Vendored files carry `status: unverified` until trial-verified.

### 6a.6 New-skill path

When mining surfaces a domain no skill owns (ros2_control, MoveIt — both already probed by the registry): the engine files a **new-skill proposal** — overlap analysis against the catalog, trigger-surface sketch, evidence inventory from the run — as an issue/observation. The human approves the *concept*; only then does the engine author the skill (template-compliant, routing/cross-ref updates included) up to a PR. Two light gates, because new skills change catalog shape (listing budget, architect routing) — a bigger blast radius than editing one skill. In the user tier the same flow runs with the user as approver, generating new *overlay* skills for their custom robots and stacks.

### 6a.7 Re-crawl and drift

Refine runs propose re-crawls for `distilled` repos past the staleness window or with major upstream releases. A re-crawl diffs the repo against the recorded SHA and re-mines only what changed; distillations whose source lines changed upstream get flagged `recheck` — the external analog of the staleness sweep, and the reason crawl records exist.

## 7. Absorb role — the delta pipeline

### 7.1 Flow

Invoked ("absorb", "run the loop"), scheduled, or offered by the post-commit nudge. Operates on `status: ready` observations.

1. Branch: `loop/absorb-YYYY-MM-DD` (or `-<topic>`).
2. **Draft deltas** — feedback-conditioned (OAE): prompt = current SKILL.md + the observation (symptom verbatim, fix + check, dead-ends) + smallest-edit directive + placement rule (lowest skill that can hold it). Output: delta ops, not prose.
3. **Apply** via `apply_deltas.py` (deterministic): archive snapshot → apply ops (no-op fallback on anchor/content mismatch) → bump `version:` (build/minor/major inferred from op types, overridable) → append changelog line → update ledger/evals sidecars → mark observations `absorbed`.
4. **Verify** (§8): validator → trigger evals for touched skills → flip gate.
5. **Scoped refine** over touched skills (dup check — fresh absorption is where duplication enters).
6. **Open PR** with the evidence table: per edit — skill, anchor, op, observation link, sources, eval results before/after. Losing alternatives (if experimentation ran) attached with scores.
7. Human reviews → merge. Merge is Gate. Post-merge: `/reload-plugins` reminder unchanged.

### 7.2 Delta operation format

```yaml
- skill: nav2
  op: update            # add | update | retire | move | annotate
  anchor: costmap-inflation      # or section: "Quick start" + position for add
  content: |
    - Nav2's default costmap YAML omits the inflation_layer block — add it
      (cost_scaling_factor: 3.0 worked) or the robot hugs obstacles. <!-- id: costmap-inflation -->
  reason: obs-nav2-007
```

- `add` (new anchored item), `update` (replace one item's text), `retire` (remove item + move its ledger entry to the archive snapshot — the only legal delete), `move` (relocate to another skill/section — placement-rule enforcement), `annotate` (status/verification marker change, e.g. unverified → ✓ verified).
- `apply_deltas.py` refuses: ops on nonexistent anchors (→ no-op + report), ops that would breach the 500-line cap (→ split suggestion: content to `references/`), retires of anchors with `helpful > 0` unless the PR flags it explicitly.
- **Co-evolving evals** (CoEvoSkills): a major bump requires touching the skill's `evals.yaml` in the same PR — at minimum re-confirming that existing cases still map onto the restructured content — so eval suites evolve with skills instead of rotting against them.

### 7.3 Policy change (CLAUDE.md rewrite, Phase 2)

The STRICT policy's intent — no unsupervised skill mutation — is preserved; its mechanism changes:

- Old: *never edit skills without explicit per-session user approval; two conversational gates.*
- New: **`skills/**` on `main` is merge-protected. The engine may capture, consolidate, and draft absorb/refine PRs autonomously. No agent merges to `main`. Mid-build sessions still never edit skills directly (ACE's same-session-bias rule) — they capture; the pipeline absorbs.**
- Gate 1 (candidate selection) becomes the observation `status` field — visible, editable, reviewable in git rather than transacted conversationally. Gate 2 becomes PR review. Users who want the old conversational gates just don't schedule the pipeline and invoke it interactively.

## 8. Verify role

Layered, cheap-first (OAE's staged evaluator):

1. **Form** — `validate_skills.py` (extended: anchor rules, sidecar schema checks, delta-format lint). Deterministic, free, blocking.
2. **Triggers** — `run_trigger_evals.py`: for each touched skill, present each positive/negative phrasing to a cheap LLM judge with the catalog's descriptions and check selection. Blocking when eval cases exist for the touched skill; skipped (and said so in the PR) when none exist yet. Wraps skill-creator's eval tooling where it fits rather than reinventing.
3. **Flip gate** (AgentDevel) — rerun the touched skill's full eval set on the pre-edit version and post-edit version; any case that passed before and fails after blocks the PR. Cheap because suites are small; value is in the invariant.
4. **Deep verify** (occasional lane, Phase 3) — run `status: unverified` examples in their pinned app/sim fixture (`apps/` + AgenticROS's fixture idea); pass → `annotate` delta promoting to ✓ verified with date+app. Scheduled, not per-PR.

CI: a `skills` workflow runs layer 1 on every PR; layers 2–3 run when an API key is present (contributor-side always, CI optionally) and report into the PR body.

## 9. Experimentation engine (Phase 3)

For contested or structural edits — description rewrites, restructures, competing fixes — where the right answer isn't obvious enough for a single draft:

- **Variant A/B (default):** 2–3 feedback-conditioned *delta* variants (never rewrites) + baseline; blind-judged against the skill's eval suite + task checks; scores attach to the PR; the human picks (the engine ranks and recommends — never selects unattended, per OAE's own warning). Losing variants → `archive/<skill>/variants/<date>/` with scores (DGM: the archive is branch-points, not garbage).
- **Contrastive rollouts (ReasoningBank/MaTTS):** N parallel agents attempt the same scripted app task with/without a candidate variant; the pass-vs-fail diff is distilled into observations. Expensive — reserved for high-stakes questions (a new skill's structure, a disputed best-known-method).
- Fitness ordering, when scored: (trigger accuracy, task completion, −token length) — leanness is the tiebreaker, so distillation prefers the shortest passing variant (OAE's runtime analogue; counters ACE's unbounded-growth failure mode).
- **Breadth/depth model split** (OAE's ensemble): cheap/fast models draft variants and run rollouts; the strong model is reserved for judging and distillation — spend where discrimination matters, not where volume does.

## 10. Refine role

The existing five passes survive with their report-first posture, re-armed:

- **Prune** reads ledgers: `harmful>0 ∧ helpful=0` first; every prune is a `retire` delta with its evidence trail; archive remains the undo.
- **Dedup** seeds from `--dupes` plus anchor-similarity across skills; merge-to-lowest-owner emitted as `move` + cross-ref deltas.
- **Staleness** unchanged (90-day windows, re-verify against live sources) — the pass the wider ecosystem lacks; it stays.
- **Usage/retirement** reads retro lines (now consolidator-drafted, so the signal actually exists) + negative-eval misfire data.
- **Growth review** reads the now-richer archive (scores, variants, parent metadata).

Output: a refine PR through the same delta pipeline. Scoped refine after every absorb; full refine scheduled (~monthly / 2–3 builds).

## 11. Two-tier operation

Same engine, different destination. The plugin ships capture hooks + the learning-loop skill to everyone.

| | Contributor | User / company |
|---|---|---|
| Queue/facts/observations | robium repo (`.robium/queue`, `learnings/`) | their repo (`.robium/queue`, `.robium/learnings/`, `.robium/observations/`) |
| Absorb destination | PR to `robium-ai/robium` `skills/` | their repo's **overlay**: `.claude/skills/<name>/` — native Claude Code project skills, same SKILL.md format, loaded alongside the plugin automatically |
| Gate | robium maintainer merges | their own PR/commit review |
| Sharing | the catalog itself | git — their overlay + learnings travel with their repo to their whole team |

- **Overlay mechanics:** project skills in `.claude/skills/` is a native Claude Code feature — no invented loader. An overlay skill either *extends* (new name, e.g. `acme-fleet-dds`, cross-referencing catalog skills) or *forks* (same name, carrying a `forked-from: robium/nav2@2.1.0` note).
- **Manifest** (`.robium/manifest.yaml`, Hermes's origin-hash pattern): records catalog-skill versions/hashes at install plus fork points. On plugin update, `robium doctor` (CLI) diffs: untouched catalog skills update freely; forked ones get a three-way-merge report instead of silent divergence.
- **Contribute upstream** (`contribute` mode): filters observations for generalizability (not project-local — the existing triage rule), rewrites to strip private context, and drafts a PR to the robium repo via fork. The maintainer-side pipeline treats it as one more evidence-bearing PR. This is the flywheel: every serious user is a potential evidence source, gated twice (their opt-in, robium's merge).
- **Security scan** (Hermes's install-scan pattern): skills are injected into other people's agent contexts, which makes the contribute path a prompt-injection supply chain. A deterministic scanner (`scan_skill.py`) checks contributed and overlay-installed skill content for injection patterns, exfiltration instructions, destructive commands, and credential-shaped strings — mandatory in the contribute pipeline and the maintainer-side PR CI; exposed to users via `robium doctor`.
- **Privacy:** nothing leaves the user's repo except explicit `contribute` output; hooks write only project-locally; scrubbing (§12) applies everywhere.

## 12. Safety & failure handling

- **Hooks:** fail-open everywhere; a broken hook degrades to today's manual capture, never blocks a session. Silent by default (no per-capture confirmations — nag fatigue is a documented failure mode).
- **Secret scrubbing:** before any queue write: regex-scrub `KEY=value`, bearer/token/password patterns, Doppler-injected env values (match against `doppler secrets --only-names` cache when available), URLs with credentials. Queue stays gitignored until consolidation re-checks on promotion. (claude-reflect's warning, sharpened for robium's Doppler usage.)
- **Delta application:** unappliable op → no-op + PR note (OAE fallback); validator red → PR blocked; flip-gate red → PR blocked with the failing case named.
- **Reflection loops:** the consolidator never invokes capture-bearing sessions; hooks ignore engine-generated turns (marker env var); `claude -p` judge calls are timeboxed with regex fallback.
- **Runaway growth:** absorb PRs breaching the 500-line cap are auto-split to `references/`; catalog-level growth is reported per refine cycle against the ~zero target; ADD-heavy PRs without paired prunes get flagged in the PR body.
- **Compaction loss:** PreCompact hook snapshots the queue (claude-reflect); the queue file itself is already outside the context window — and the transcript archive makes compaction irrelevant to learning: the un-compacted log is the source.
- **Transcript archive privacy:** archived logs contain everything a session saw, including possible secrets — they are gitignored, never committed, never leave the repo's machine, and are excluded from `contribute` output by construction (only distilled, re-scrubbed observations can go upstream). Archive pruning policy (age/size) keeps disk bounded; distilled tiers preserve the knowledge past pruning.

## 13. Meta-layer restructure

- **`skill-author`** — stays (bump major): fresh authoring + quality bar + validator custody. Loses the hardening mode (superseded by the engine) and Mode 2 mining (superseded by the `mining` skill, §6a).
- **`learning-loop`** — new umbrella skill: owns the session-side pipeline surface (modes: `status`, `consolidate`, `absorb`, `refine`, `experiment`, `contribute`), the promotion bar, the delta format, and the engine scripts (`apply_deltas.py`, `mine_transcripts.py`, `run_trigger_evals.py`, ledger/metrics tools — `skill_metrics.py` moves here and grows ledger stats).
- **`mining`** — new skill (§6a): the external-exploration engine — registry management, survey/deep/comparative fan-out orchestration, extraction contract, new-skill proposals. Consumes learning-loop's shared machinery (observations, deltas, evidence rules); works in both tiers.
- **`skill-updater`, `skill-refiner`** — retired to `archive/` (recoverable, per the retirement rule). Their durable content (promotion bar, five passes, double-gate rationale) is redistributed into learning-loop's references. Catalog: 24 − 2 + 2 = 24 skills; validator count unchanged; the repo-wide stale-qualifier sweep applies (CLAUDE.md rule 4).
- **Repo additions:** `hooks/` (plugin hooks + scripts), `learnings/observations/`, per-skill `evidence.yaml`/`evals.yaml`, `docs/research/`, CLAUDE.md policy rewrite, `.robium/` convention. CLI (`robium-ai`) gains `doctor` overlay-manifest support (Phase 4).

## 14. Testing the engine itself

- **Scripts:** pytest suites for apply_deltas (op semantics, no-op fallback, cap handling, retire rules), miner (fixture JSONL transcripts → expected entries), scrubber (secret corpora), hooks (fixture events; must exit 0 on malformed input).
- **Pipeline acceptance test:** run the full loop on the real backlog — the 12 existing `learnings/*.md` files — as the Phase-2 exit criterion: consolidation produces observations from them; absorb produces reviewable PRs; nothing merges without review. The backlog is simultaneously the migration path and the proof.
- **Hook dry-run mode** and `absorb --dry-run` (prints deltas, applies nothing) for development and for skeptical users.
- **Validator remains the invariant:** every phase ends with the catalog green.

## 15. Phasing

| Phase | Ships | Exit criterion |
|---|---|---|
| **1 — Substrate + capture** | Anchor migration PR (all skills); ledger + evals sidecar formats and tooling; learnings schema v2; hooks in plugin (incl. SessionEnd transcript archiver); miner; scrubber; validator extensions; `.robium/` convention; back-mining pass over surviving pre-hook transcripts | Hooks flagged ≥1 real session's friction and archived its transcript with zero session breakage; validator green with anchors |
| **2 — Consolidate + absorb + mine** | **Shared core first**: observations tier + extraction schema + overlap/placement analyzer (both sources need them). Then the **`mining` skill** (registry-driven, survey→deep + comparative runs, §6a) piloted on 2–3 SOURCES.md repos as the pipeline's first consumer — external learning literally goes first. Then: consolidator (incl. success attribution + self-check round); **recall hook**; delta format + apply_deltas (incl. co-evolving-evals rule); trigger-eval runner + flip gate; absorb→PR flow; CLAUDE.md policy rewrite; meta-skill restructure (learning-loop + mining land; updater/refiner retire) | ≥1 merged evidence-bearing skill PR sourced from an **external repo** (mining pilot); the 12-file + 38-flag backlog processed end-to-end into ≥1 merged PR; ≥1 recall injection observed helping a live session |
| **3 — Verify deep + experiment** | Variant A/B; contrastive rollouts (Workflow-orchestrated); deep-verify sim/app lane; eval task checks | One contested edit resolved by blind A/B with scores in the PR; ≥1 example promoted to ✓ by automated deep-verify |
| **4 — User tier** | Overlay + manifest + `robium doctor` merge report; `contribute` mode + security scanner; **user-tier mining** (private `.robium/sources.md`, mining custom repos/robots/knowledge bases into overlay skills incl. new-skill generation with the user as approver; mined-from-private content gets an extra provenance review before any upstream contribution); user-facing docs | A non-robium repo runs capture→recall→absorb into its own overlay; ≥1 overlay skill created or updated by mining a private repo; one upstream contribution PR produced by `contribute`, passing the scan |

Loop-health metrics (reported by `learning-loop status`): capture rate (entries/session with friction), queue→merged latency, unabsorbed backlog size, eval-suite size + pass rate, catalog net growth per cycle, % examples verified.

## 16. Out of scope

- Model training / fine-tuning (the entire taxonomy branch 1).
- Full evolutionary search (populations, islands, generations) — variant A/B is the deliberate ceiling.
- Vector DBs, embedding services, memory servers — git-native equivalents only.
- Autonomous merge to `main` `skills/**` — permanently out, not deferred.
- Runtime robot control (AgenticROS's lane); a future ros2/nav2 cross-reference to AgenticROS is a content edit, not engine work.
- Marketplace/distribution beyond the existing plugin + npm CLI (revisit if the contributor funnel grows).

Considered from the research and deliberately deferred (recorded so the reasoning isn't lost):

- **Conditional frontmatter gating** (Hermes `requires/platforms`) — real trigger-noise value, but conflicts with the frontmatter-minimalism rule and agentskills portability; negative trigger evals cover most of the same ground. Revisit if misfire data says otherwise.
- **Capability manifests** (AgenticROS) and **bundles** (Hermes) — routing conveniences; `architect` owns routing today. Revisit when the catalog outgrows one routing table.
- **FTS/search index over the transcript archive** — grep is the git-native answer at current scale; revisit if archives grow past it.
