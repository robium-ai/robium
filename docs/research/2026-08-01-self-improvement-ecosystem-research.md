# Self-Improvement Ecosystem Research — 7 Repo Deep Dives

*2026-08-01. Input to the learning-engine redesign (`docs/superpowers/specs/2026-08-01-learning-engine-design.md`). Seven parallel research agents, each assigned one reference project and asked to extract what transfers to robium's skill-learning loop — and what doesn't. Each report cites the exact files/URLs its agent actually read. Also published as a claude.ai artifact (same content, styled).*

---

## Cross-repo synthesis — what all seven sources converge on

1. **The item, not the file, is the edit unit.** ACE's ID-tagged bullets, ExpeL's per-insight ops, AWM's discrete workflows. Stable anchors make edits surgical, diffs clean, attribution possible.
2. **Evidence counters beat vibes.** ACE's helpful/harmful counts, ExpeL's upvote/downvote, hindsight's proof_count. Robium's ✓ and `(seen 2x)` are primitive counters waiting to be formalized.
3. **Capture is deterministic; reflection is deferred.** claude-reflect and hindsight both keep LLMs out of the hook path: regex/fail-open capture to a quarantine queue, LLM consolidation later, on demand.
4. **Delta edits, deterministic merge.** ACE forbids playbook rewrites; OpenAlpha_Evolve mutates via SEARCH/REPLACE with a no-op fallback. LLM proposes; a script applies. Full-file rewrites cause context collapse.
5. **Verification before promotion — universally.** SkillWeaver practices before promoting; DGM gates on benchmarks; AgentDevel gates on regressions; hindsight keeps its top tier human-curated. Nothing reputable promotes unverified knowledge.
6. **Curation is load-bearing, not bureaucracy.** CTIM-Rover's negative result: unfiltered auto-memory made agents *worse*. ACE documents collapse; ExpeL deletes at zero votes. Deletion machinery matters as much as capture.
7. **Small-N contrastive experimentation, not populations.** OpenAlpha_Evolve's own advice: 2–3 feedback-conditioned variants, blind-judged. ReasoningBank: parallel rollouts exist to create pass-vs-fail contrast for distillation.
8. **Evals come from real sessions, not synthesis.** Hermes generates eval sets from its session DB; robium's recorded trigger-miss phrasings are exactly this. Synthetic-only evals are the weak link everywhere they appear.

---

## Report 1 — ACE (Agentic Context Engineering)

**Sources:** github.com/ace-agent/ace — README.md, EXTENDING_ACE.md, playbook_utils.py, ace/ace.py, prompts/reflector.py, prompts/curator.py · Paper: arXiv 2510.04618 (Stanford/SambaNova, Oct 2025).

### What it is

Improves LLM performance by evolving the *context* (a "playbook") instead of the weights. Three roles (can be the same LLM):

- **Generator** — answers tasks using the current playbook, producing reasoning trajectories that expose strategies and pitfalls.
- **Reflector** — diagnoses each trajectory against feedback (ground truth or execution signal). Outputs JSON: `reasoning`, `error_identification`, `root_cause_analysis`, `correct_approach`, `key_insight`, plus **`bullet_tags`** — a per-bullet verdict (helpful/harmful/neutral) on every playbook bullet the Generator saw. Up to 5 iterative refinement rounds.
- **Curator** — emits **delta operations** (released code: ADD only; UPDATE/MERGE/DELETE documented but unimplemented), merged into the playbook by **deterministic non-LLM code**. The LLM never rewrites the playbook wholesale.

**Playbook format:** sectioned markdown, each bullet `[section-slug-NNNNN] helpful=X harmful=Y :: advice` (e.g. `[mis-00004] helpful=6 harmful=0 :: Don't forget timezone conversions`). `update_bullet_counts()` increments counters from reflector tags; `apply_curator_operations()` parses curator JSON ops and appends bullets with fresh sequential IDs.

**Loop:** per sample → generate → reflect (tag bullets) → update counts → every `curator_frequency` steps, curate + apply deltas → optional embedding-similarity dedup → periodic eval + save best playbook. **Grow-and-refine:** growth appends/increments in place; refine runs semantic dedup and pruning, proactively or lazily (on context overflow).

### How it prevents context collapse

The paper documents collapse concretely: a monolithic-rewrite approach compressed an 18,282-token context to 122 tokens in one step, dropping accuracy 66.7% → 57.1% — below the 63.7% no-context baseline. Defenses:

1. **Never rewrite, only append/patch** — deltas merged deterministically; the LLM physically cannot summarize away accumulated knowledge.
2. **Itemized bullets with IDs** — edits localize to single bullets.
3. **Counters as evidence** — pruning driven by accumulated helpful/harmful counts, not one model's momentary judgment.
4. **Reflector separated from Curator** — evaluation quality isn't diluted by the write operation (ablation: removing iterative reflection costs ~4%).
5. **Anti-brevity-bias stance** — rejects optimizers that reward concise generic instructions; domain heuristics and failure modes are kept even as the playbook grows.

### Evaluation

- Benchmarks: AppWorld (agentic tool use) + finance (FiNER XBRL, Formula). +10.6% agents, +8.6% finance; 82–91% lower adaptation latency; ~83.6% lower token cost vs GEPA / Dynamic Cheatsheet / ICL.
- Per-update signal: the counters — every generation implicitly A/B-tests every bullet in context; the reflector attributes success/failure to individual bullets.
- With labels, a correctness check feeds the reflector; without, execution feedback substitutes. Label-free ACE still improves; feedback quality is the binding constraint.
- Offline (optimize-then-freeze) vs online (sliding-window test-then-train). Ablations: iterative reflection ~4%, multi-epoch ~2.6%, offline warmup all matter.

### Transferable patterns

1. **Helpful/harmful counters on skill content** — formalize `(seen 2x)` + ✓ as per-anchor `helpful=N harmful=N`, incremented from learnings (✓ → helpful; wrong-guidance/user-correction → harmful). Gives the prune pass a deterministic target.
2. **Bullet-level IDs for attribution** — stable anchors inside SKILL.md let a learning cite the exact guidance that helped or misled; absorption diffs become mechanical instead of interpretive.
3. **Reflector/Curator separation = capture vs absorption — but structure the reflection.** The reflector schema (error → root cause → correct approach → key insight → per-item tags) is a better learnings-entry template than free-form bullets.
4. **Delta-only edits, deterministic merge** — absorption emits `{skill, section, op, content}` deltas; a script applies them + bumps version + archives. The human approves the delta list. Removes the collapse risk of an LLM "cleaning up" a skill while editing it.
5. **Grow-and-refine cadence** — maps to absorb-often/refine-occasionally; arm the refiner with similarity dedup and counter-based prune candidates.
6. **Eval-gated promotion** — trigger-miss learnings are eval cases; run the suite before/after each absorption; only promote if no regression.

### Anti-patterns / caveats

- **ADD-only in practice → unbounded growth.** The released code never deletes or updates bullets. Robium's editorial prune gate is a feature ACE lacks.
- **Machine-optimized artifacts.** ACE playbooks are flat bullet dumps consumed only by the Generator; robium skills are pedagogical documents — counter metadata belongs in comments/sidecars, not in place of prose.
- **Requires dense automated feedback.** Robium's signal is sparse and qualitative; single-digit counters are evidence weights, not statistics.
- **Autonomous curation — correctly forbidden.** The paper concedes a weak reflector degrades the playbook. Keep the human gates, and keep "log now, absorb later, never edit mid-build" (avoids ACE's same-session update bias).

---

## Report 2 — OpenAlpha_Evolve

**Sources:** github.com/shyamsaktawat/OpenAlpha_Evolve — README, task_manager/agent.py, prompt_designer/agent.py, evaluator_agent/agent.py, database_agent/agent.py, selection_controller/agent.py, core/interfaces.py, config/settings.py, code_generator/agent.py · Background: arXiv 2506.13131, DeepMind AlphaEvolve blog.

### Architecture

Faithful small-scale re-implementation of AlphaEvolve's four pillars as six asyncio agents:

- **Candidate:** a `Program` dataclass — id, code, fitness_scores, generation, parent_id, island_id, errors, status. A `TaskDefinition` carries description, function to evolve, leveled tests, allowed imports, expert knowledge.
- **Loop:** initialize N programs → distribute across islands → per generation: select parents (top half) → offspring via mutation prompts → concurrent evaluation → merge survivors per island.
- **LLM ensemble:** cheap model for breadth (initial population, low-fitness parents); strong model reserved for parents with correctness ≥ 0.8.
- **Storage:** in-memory dict persisted to JSON; elites from all islands deduplicated, then roulette-wheel selection with an epsilon so zero-fitness programs can still breed. Sort key `(correctness, -runtime_ms, -generation)`. Defaults tiny (population 5, 2 generations, 4 islands) — the architecture, not the scale, is the point.

### Evaluator design — the gate that makes evolution possible

- **Staged, cheap-first:** syntax check → Docker-sandboxed execution (`--network none`, timeout with stop → kill escalation) → per-test timing.
- **Fitness = pass fraction + tiebreakers:** correctness, runtime, highest difficulty level passed. Tests grouped into levels, run in order, halting at first failing level. Floats via `math.isclose`; tests may supply a validation function.
- **Partial/failed candidates are data, not discards:** errors accumulate verbatim; partial correctness recorded — this feedback is what the next mutation prompt consumes. Failed programs can still be selected and routed to the bug-fix path.

### Prompt design for variation

Bug-fix prompt (correctness < 0.1 with errors) or mutation prompt = task description + expert knowledge + full parent code + formatted eval feedback (correctness %, runtime, verbatim errors) + directives ordering priorities. **Diff-based mutation, not rewrite:** the LLM answers in SEARCH/REPLACE blocks; a three-tier matcher applies them (exact → whitespace-normalized → line-anchored); if nothing applies, falls back to the unchanged parent — a malformed mutation degrades to a no-op instead of corrupting the lineage.

### Transferable patterns

1. **Eval-gated absorption** ("nothing enters the population unscored") — run candidate skills against recorded trigger phrasings + validator before commit.
2. **Feedback-conditioned mutation prompts** — variant prompt = current SKILL.md + exact tagged learnings (error verbatim, passing check, dead-ends) + smallest-edit directive. Robium's evidence bar *is* the eval-feedback formatter for markdown.
3. **Diff-based variation with no-op fallback** — variants emit minimal diffs, never rewrites; a bad diff leaves the skill intact.
4. **Breadth/depth model split** — N cheap agents draft variants/attempt tasks; the expensive judge runs only on variants that beat baseline.
5. **Tiered fitness with tiebreakers** — score variants as (trigger accuracy, task completion, −token length): leanness as the runtime analogue.
6. **Archive as population history** — add parent-version + eval-score metadata (and losing A/B variants) to `archive/` and it becomes queryable lineage, not write-only backup.

### Anti-patterns

- **Full generational search is overkill** — populations/islands/roulette solve exploration problems robium doesn't have and would flood the human gate. Skill fitness is noisy; LLM-judged evals need repeated runs; budget explodes.
- **Unattended selection contradicts the STRICT policy** — in OA, selection *is* the merge decision. The human stays the survivor-selector; evolution only ranks and recommends.
- **Diff-blind mutation of load-bearing structure** — any variant must pass `validate_skills.py` as the syntax-check equivalent.
- **Minimal high-value subset (recommended):** population 2–3, one generation — baseline vs 1–2 feedback-conditioned diff variants, blind A/B judged on recorded phrasings + one scripted app task, winner presented to the human.

---

## Report 3 — Hermes Agent (Nous Research)

**Sources:** github.com/NousResearch/hermes-agent (repo, docs/, skills/), hermes-agent.nousresearch.com/docs (skills, memory, personality, architecture), github.com/NousResearch/hermes-agent-self-evolution README.

### What it is

A Python agent framework ("the agent that grows with you") with genuine learning machinery, not just an inference harness. Core: `AIAgent`, a synchronous loop over three API modes; sessions in SQLite with FTS5 search and lineage tracking; a gateway serving 25+ surfaces; ~70 tools across ~28 self-registering toolsets; `SOUL.md` persona; prompt built in ordered tiers (stable → context → volatile) to preserve prefix cache.

### Learning / memory mechanisms

- **Bounded curated memory:** `MEMORY.md` (2,200-char cap) + `USER.md` (1,375-char cap), injected as a frozen snapshot at session start, never mid-session. At capacity the memory tool errors and forces consolidation; memory does not auto-compact.
- **Session search:** FTS5 over raw messages — no LLM summarization, ~20 ms, zero LLM cost.
- **Autonomous skill creation:** a `skill_manage` tool (create/patch/edit/delete) — trigger heuristics: successful complex task (5+ tool calls), working path found after dead ends, non-trivial workflow discovered. `patch` preferred over full edit.
- **Human gates:** `skills.write_approval`/`memory.write_approval` stage every write to `~/.hermes/pending/` (survives restarts) with `/skills pending|diff|approve|reject`. A background self-improvement review captures repeated corrections into staged writes.
- **Offline evolution** (separate repo): DSPy + GEPA reflective prompt evolution mutates SKILL.md files against eval datasets that are synthetic or **generated from real session DB data**. Guardrails per variant: test suite, ≤15 KB, caching compatibility, semantic preservation, human PR review. ~$2–10/run. Phases 2–5 (tool descriptions, system prompt, tool code, continuous automation) are planned, not built.

### Harness design choices worth stealing

- **Progressive disclosure:** `skills_list()` (names+descriptions) → `skill_view(name)` → `skill_view(name, path)` for reference files; skills auto-exposed as stackable slash commands.
- **Conditional gating:** `requires_toolsets`/`platforms` frontmatter hides skills entirely when irrelevant.
- **Provenance manifest:** `.bundled_manifest` maps each bundled skill to its origin hash — unchanged skills auto-update; user-modified ones are skipped until explicit reset. Clean answer to upstream-update-vs-local-edit.
- **Federated hub:** taps (any GitHub repo with `skills/`), skills.sh, well-known URLs — all agentskills.io format, with a mandatory security scan on install.
- **Bundles:** YAML groupings of skills + one instruction under a single slash command; external skill dirs with local-wins precedence.

### Transferable patterns

1. **Staged-write pending queue** — capture hooks write structured candidate edits to a pending dir with approve/reject/diff review; approval becomes diff-review, not re-derivation.
2. **Origin-hash manifest** — the enabling mechanism for per-user/company profiles layered over the shared catalog with local-wins precedence.
3. **Session-DB-derived eval sets** — generate eval cases from real transcripts; variants must pass validator + size + semantic-preservation + human PR review.
4. **Skill-creation trigger heuristics as hook conditions** — "5+ tool calls succeeded / recovered from dead end / repeated correction" gates when capture fires.
5. **Conditional frontmatter gating** — e.g. gate isaac-sim on GPU presence to cut trigger-surface noise.
6. **Bundles** — "sim-stack" = gazebo + ros2 + testing + one instruction; cheaper than the architect routing table for common combos.

### Anti-patterns / poor fits

- Hard char-capped monolithic MEMORY.md — wrong for a 24-skill catalog; per-skill references already beat it.
- Fully autonomous `skill_manage` (their no-approval default) — adopt the staging, not the autonomy.
- GEPA on skills without domain evals — robotics skills fail on *facts*, which text-mutation optimizers can silently "improve." Use the sessiondb-eval idea; skip synthetic-only evolution. Self-evolution phases 2–5 are vaporware.
- Everything-in-SQLite state and the 25-platform gateway — irrelevant infrastructure weight.

---

## Report 4 — AgenticROS

**Sources:** github.com/agenticros org (14 repos) — agenticros core README, agenticros-skills README, docs/strategy-ai-agents-plus-ros.md, packages/agenticros-claude-code, agenticros-skill-followme/package.json · Open Robotics Discourse thread 53699 · agenticros.com, skills.agenticros.com.

### What the org is

Real, active, single-maintainer project (Chris Matthieu, "PlaiPin"), launched ~March 2026: connects AI agent platforms to **live ROS 2 robots at runtime**. Core monorepo (128 stars): transport core, per-agent adapters (OpenClaw/Claude/Gemini/Codex/Hermes), MCP server, CLI, ROS 2 workspace. Eight `agenticros-skill-*` npm packages (followme, find, navigate-to, navigate-through-poses, start-slam, detect-humans, dock-to-charger, moveit-pick), marketplace, website. Early-stage but architecturally serious; not battle-hardened (0-star tail, no benchmarks).

### How they structure robotics capabilities

Their unit is the **runtime tool**, not the knowledge document — the opposite pole from robium:

- **MCP server + adapters:** ~20 tools — raw ROS primitives (publish/subscribe/service/action/params, camera snapshot, depth distance), fleet tools, missions, memory.
- **Skills = npm packages** with capability manifests: `{id, verb, description, interruptible, blocks_base}` + typed inputs/outputs and preconditions (TypeBox). Agents plan against **verbs**, not raw topics. Deterministic stacks (Nav2, MoveIt2, RTAB-Map) join via descriptors wrapping existing binaries.
- **Mission chaining:** declarative step graphs with template wiring, or English goals compiled via **deterministic pattern matching — no LLM in the runtime**. Per-step transcripts go to shared memory so a second agent can resume mid-mission.
- **Cross-agent memory** namespaced by robot; **marketplace** atop npm (planned 70/30 paid listings).

### Learning / eval mechanisms

**Essentially none.** Their own gap list: "No evaluation metrics, no performance benchmarks, no user-studies plan." Adjacent bits: deterministic goal compiler (replayable/testable), doctor health checks, sim launchers as informal proving grounds, semver-pinned skills. Robium's learnings loop has no counterpart here.

### Transferable patterns

1. **Capability manifests / typed verb registries** — a structured "what this skill can verify/produce" manifest could power agentic routing; theirs is A2A/agent-card-compatible.
2. **Deterministic core, LLM at the edges** (their strongest idea) — keep verification (validators, smoke tests, sim runs) deterministic; LLMs only propose.
3. **Skill-as-package with install/publish/search + marketplace** — the distribution shape if the contributor funnel grows; robium has the validator but lacks the publish/discovery pipeline.
4. **Sim launchers as standard fixtures** — pin a sim fixture per verifiable example so the loop can promote `status: unverified` → verified by actually running them.
5. **Mission transcripts to shared memory** — structured, replayable execution traces as absorption raw material.
6. **Spectrum seeding** — seed the pilot skills across AI-driven/deterministic/hybrid to stress-test the contract before scaling.

### Competitive positioning

AgenticROS is a *runtime control plane* (makes an agent able to drive a robot that already works); robium is a *development knowledge layer* (makes the agent good at building the stack — env setup, Nav2 tuning, Gazebo, MuJoCo, LeRobot, Isaac, none of which they touch). Someone using AgenticROS still needs robium-shaped knowledge to configure Nav2, debug DDS, or build their assumed Docker env. Their moat bet — a compounding catalog of named AI-callable ROS verbs — is robium's thesis applied to runtime instead of dev knowledge; the catalogs could cross-reference (a robium ros2/nav2 skill teaching agents to use/extend AgenticROS is a cheap integration play).

---

## Report 5 — Hindsight (Vectorize)

**Sources:** github.com/vectorize-io/hindsight README, hindsight.vectorize.io docs (retain, retrieval, observations, memory-banks API, Claude Code integration), two Vectorize blog posts, raw source: engine/consolidation/prompts.py, claude-code/hooks/hooks.json, docs-integrations/skills.md · Paper: arXiv 2512.12818.

### Architecture

Open-source (Python/Postgres) agent memory server around **retain / recall / reflect**:

- **Granularity:** conversations/transcripts/documents → LLM extraction into **narrative facts** (not vector chunks, not full trajectories). Each fact preserves reasoning context, canonical entity references, **dual timestamps** (occurred vs learned), tags.
- **Four memory networks** separating evidence from inference: **World facts**, **Experience facts** (first-person), **Observations** (auto-consolidated beliefs with `proof_count` + source-fact citations), **Opinions** (confidence-scored). **Mental Models** sit above all: human-curated summaries with highest retrieval priority.
- **Retrieval ("TEMPR"):** four strategies in parallel — vector, BM25, entity-graph traversal, temporal — fused via reciprocal rank fusion, cross-encoder reranked, boosted by recency/proximity/proof-count. Results cut by a **token budget** (default 4096), not top-k.
- **Isolation:** memory banks — fully isolated units with per-bank missions, directives, disposition traits, tag-based visibility.

### Consolidation

Runs **automatically in the background after every retain/update/delete** (disableable; manual scoped runs exist). Consolidator prompt: merge aggressively on same event/finding/decision; one canonical observation with many `source_fact_ids` beats many one-source siblings; every create/update cites exact source UUIDs and a `reason`; contradictions are **evolved, not overwritten** ("was React, now Vue") with history preserved. An embedding pass (0.97 cosine) reconciles near-duplicates but keeps ones differing by "a number, a negation, a named entity." Observations are *not* auto-promoted to mental models — the top tier is human-curated only. Reflect retrieves hierarchically: mental models → observations (freshness-checked) → raw facts for verification.

### Integration surface

REST + SDKs + CLI + MCP; ~60 integrations. The **Claude Code plugin is the relevant blueprint**: **SessionStart** (health check), **UserPromptSubmit** → auto-recall injected as `additionalContext` (visible to model, invisible in transcript), **Stop** → async transcript retention every N turns (default 10, 2-turn overlap, including tool calls), **SessionEnd** (cleanup). Bank IDs dynamic — per `["agent","project"]` by default, switchable to per-user/channel. Their skills doc pairs memory with markdown skills: local embedded DB for individuals, shared bank for teams, project conventions shared broadly, personal preferences tagged per person.

### Transferable patterns

1. **Structured learning schema** — fact → observation → mental model ≈ entry → learning → skill. Adopt: source citation, dual timestamps, skill references, formalized proof_count, a `reason` on every absorption.
2. **Consolidation as evolution, not overwrite** — "X (previously believed Y)" with history preserved; merge duplicate learnings into one canonical entry with accumulated evidence rather than appending siblings.
3. **Hook-based capture is proven** — copy the hook shape, not the server.
4. **Two-tier = bank scoping** — shared bank (skill repo, PR-gated) vs per-user/project banks (private local profiles); private learnings graduate via the same human gate.
5. **Token-budgeted hierarchical retrieval vs always-loaded** — skills = mental models (always loadable); private learnings = observations (on demand, freshness-checked); raw notes = facts (verification only).
6. **Consolidation trigger = after every capture + manual scoped runs** — cheaper and fresher than batch hardening; keep the human gate at the observation→skill boundary (hindsight does too).

### Anti-patterns — with git-native equivalents

- **Postgres/vector-DB/embedding dependence** → grep/glob + frontmatter tags + a lightweight index; skill descriptions already are the "reranker."
- **LLM extraction on every retain** → structured markdown templates filled by the session agent itself via a hook — the agent is the extractor.
- **Opaque DB state** → observations as dated markdown with source citations; consolidation as PR-reviewable rewrites.
- **Auto-consolidation into the authoritative tier** → automate only note-tier merging/dedup, never `skills/**`. Confidence scores/dispositions over-engineered; `unverified/✓-verified` + seen-count is the honest analog.

---

## Report 6 — awesome-Self-Improving-Agents (field survey)

**Sources:** full list README (854 lines, ~200 entries) + companion survey arXiv 2607.13104 + 8 selected paper abstracts (cited inline).

### Taxonomy — which component improves

- **1. Foundation-model improvement** (weight updates — out of scope): self-generated demos (Self-Instruct), intrinsic feedback (self-reward RL, Constitutional AI), exploratory experience (WebRL, RoboCat, SEAgent).
- **2. Scaffolding improvement** (persistent artifacts — robium's entire quadrant):
  - **2.1 Prompt optimization** — OPRO, Self-Refine, Reflexion, GEPA, Promptbreeder, TextGrad.
  - **2.2 Memory** — object (workflows/insights/cheatsheets), structure (Mem0, Zep, A-MEM), processing (consolidation/pruning: ACE, Dynamic Cheatsheet).
  - **2.3 Tool** — routing, iterative refinement (MUSE, SkillWeaver, CODESKILL), autonomous creation (Alita, OS-Copilot).
  - **2.4 Full scaffolding** — the agent rewrites its own harness (Darwin Gödel Machine, ADAS, AgentDevel, Live-SWE-agent).

Robium sits at the **intersection of 2.2 memory-processing and 2.3.2 skill refinement** — the literature treats skills as tool-shaped memory. The field's hottest 2025–26 clusters are exactly the v2 topics. Voyager appears under all three 2.3 sub-categories (the ur-skill-library); MUSE under iterative tool refinement; **SkillsBench is not on the list at all** — the curated-vs-generated result is knowledge the list doesn't carry.

### Eight selected entries

- **ACE** (arXiv 2510.04618) — evolving playbooks via generate → reflect → curate; names *brevity bias* and *context collapse*; the edit unit is the bullet, not the file.
- **Agent Workflow Memory** (2409.07429) — induces reusable workflows from trajectories, offline or online (+24.6/+51.1% relative on Mind2Web/WebArena). Capture as a byproduct of doing work — the template for hook-based capture with recurrence as the induction signal.
- **ReasoningBank** (2509.25140) — distills strategy items from *both* successful and failed trajectories; MaTTS spends parallel compute to generate diverse rollouts whose **contrast** yields higher-quality memory. Closest published match to "parallel experimentation agents with eval-gated distillation." Failures are first-class.
- **ExpeL** (2308.10144) — insight-editing op set: ADD, UPVOTE, DOWNVOTE (delete at zero), EDIT, applied by comparing success/failure pairs. A formal grammar for absorption; per-bullet vote counters mechanize ✓-promotion and give the refiner a principled deletion criterion.
- **SkillWeaver** (2504.07079) — propose → **practice repeatedly** → synthesize into tested APIs (+31.8% WebArena); skills distilled by strong agents lift weak agents by up to 54.3%. Empirical proof for the shared-repo thesis; practice-reps before promotion matches ✓-verification.
- **Darwin Gödel Machine** (2505.22954) — archive of all past variants as the exploration substrate; only benchmark-validated variants kept (SWE-bench 20%→50%). Stepping-stone variants seed later wins. Vindicates `archive/` as branch points, not just history.
- **CTIM-Rover** (2505.23422) — **negative result:** cross-task episodic memory added to AutoCodeRover *never* outperformed the memoryless baseline; retrieved memories acted as distracting noise. The cautionary bound: ungated auto-capture makes agents worse. The editorial gate is load-bearing.
- **AgentDevel** (2601.04620) — self-evolution as **release engineering**: one canonical version line, implementation-blind critic, auditable specs, "flip-centered" gating (preventing pass→fail regressions is the primary objective). Closest philosophical match to robium; its addition is a behavioral regression check per skill edit.

### Convergent findings — load-bearing principles

1. **Verification before promotion** — universal.
2. **Curation beats accumulation** — deletion machinery matters as much as capture; the refiner is mainstream, not optional.
3. **Distill, don't store raw** — raw-trajectory memory consistently loses.
4. **Failures are as valuable as successes** — success-only libraries plateau.
5. **Small, itemized, incrementally-edited knowledge units** — the file is the wrong edit granularity.
6. **Skills transfer across agents/operators** — validates the shared-repo tier.

### Gaps exposed in robium's current design

- **No behavioral regression gate on skill edits** (AgentDevel) — validator + human review check form, not effect.
- **No contrastive parallel rollouts** (ReasoningBank/MaTTS) — pass-vs-fail diffs across parallel attempts of the same task are the highest-quality distillation signal; gate on contrast, not volume.
- **Edit granularity is the file, not the item** (ACE/ExpeL) — no stable IDs or per-item counters.
- **Capture is manual and lossy** (AWM) — hook-based capture with post-hoc induction is proven.
- **No retrieval-quality safeguard** (CTIM-Rover) — trigger work needs negative evals ("skill should NOT fire") too.

### Skipped / flagged for follow-up

- **GEPA** (2507.19457) — Pareto-frontier candidate selection suits eval-gated distillation but optimizes prompts, one level below skills.
- **2026 trace-derived verified-skill cluster** — Socratic-SWE (2606.07412), SkillOpt (2605.23904), CoEvoSkills (2604.01687), CODESKILL, OpenSkill — young preprints overlapping MUSE/SkillWeaver; worth a follow-up sweep. CoEvoSkills' co-evolving-verifier idea (evals evolve with skills) directly addresses the regression-gate gap.
- **Group-Evolving Agents** (2602.04837) — experience sharing across a population; nearest to the two-tier design but preprint-thin.
- **Gödel-machine family beyond DGM** — full-scaffold self-rewriting; robium keeps the harness fixed; only the archive/gating pattern transfers.
- **All of section 1** — requires weight updates.

---

## Report 7 — claude-reflect (hook-based capture, working code)

**Sources (read in full):** github.com/BayramAnnakov/claude-reflect — hooks/hooks.json, capture_learning.py, check_learnings.py, session_start_reminder.py, post_commit_reminder.py, extract_tool_errors.py, extract_tool_rejections.py, lib/reflect_utils.py (1,173 lines), lib/semantic_detector.py, commands/reflect.md (1,512 lines), SKILL.md, README, plugin.json.

### Exact mechanism

Two-stage: **automatic capture (hooks, no LLM) → manual processing (/reflect, LLM + human gates)**. Four hooks:

- **UserPromptSubmit** → regex-classifies every prompt; matches append a JSON item (type, message, timestamp, project, patterns, confidence, sentiment, decay_days) to `~/.claude/learnings-queue.json` and print "📝 Learning captured (confidence: X%)" as injected context. Prompts >500 chars skipped unless they contain `remember:`.
- **PreCompact** → backs up the queue before compaction.
- **PostToolUse (Bash)** → detects `git commit` (not --amend), injects "You have N queued learning(s)… Run /reflect."
- **SessionStart** → pending-queue summary (top 5, confidences); warns if transcript retention is too short (it mines session JSONL).

Notably **no Stop/SessionEnd hook**. Loop closure: /reflect writes approved learnings to auto-loaded memory files — global/project/local CLAUDE.md, rules, an auto-memory low-confidence tier, skill files, AGENTS.md sync.

### Signal taxonomy & noise control

- **Classes:** explicit `remember:` (0.90 confidence, 120-day decay); guardrails ("don't add X unless…" — 0.80–0.90); corrections — strong openers (`^no,`, `^don't`, "that's wrong", "I meant", "I told you", "use X not Y") vs weak (`^actually`), with parallel CJK patterns; positive feedback ("perfect!" — 0.70).
- **Confidence composes** from pattern count/strength + structural signals (<80 chars +0.10; >300 chars −0.15).
- **False-positive filters:** questions, task-request openers, error reports, "no problem" idioms, XML/tool-result content.
- **Offline extractors** mine session JSONL: tool **rejections** (user hit Esc on a tool call — the strongest correction signal) and **repeated** project-specific errors (min 2 occurrences, harness noise excluded, suggested guideline per error type).
- **Dedup/promotion in /reflect:** per-item semantic validation, within-queue semantic dedup, cross-tier duplicate detection with line numbers, --dedupe/--organize maintenance, per-item decay flagging. **Skill routing:** corrections that follow a skill invocation are offered for routing into that skill's file instead of CLAUDE.md.

### Cost / latency / failure

**Hooks never call an LLM** — pure regex, milliseconds, every script wrapped in try/except exit-0 ("never block on errors"). LLM cost deferred to /reflect (`claude -p` per item, 30 s timeout, regex-confidence fallback). Misfire cost low by design: false captures sit in the queue until discarded; decay flags stale items. Annoyance surface: capture confirmations inject tokens; session-start banner nags (disableable); history mining wants long transcript retention.

### Transferable hook designs for robium

All patterns keep absorption human-gated — hooks only feed the queue/learnings.

1. **UserPromptSubmit correction capture** — reuse their pattern set + FP filters; append verbatim to a pending queue (not learnings/ directly). Maps to **User-corrected approach**.
2. **PostToolUse(Bash) error capture** — on error-bearing results (colcon/ros2/gz/docker failures), log exact command + verbatim error. Auto-satisfies part 2 of the evidence bar.
3. **Offline JSONL mining, min-count ≥ 2** — automates `(seen 2x)`; tool-rejection extraction is a free **User-corrected approach** detector robium currently loses entirely.
4. **Skill-context tagging** — record which robium skill loaded near the event, auto-supplying the `[skill-name]`/`[none]` tag; "no skill loaded but robotics keywords present" becomes an automated **No-skill-fired** detector.
5. **Post-milestone nudge** — after git commit or a passing smoke test: "N pending learnings; retro due." Mechanizes the mandatory OFFER step without mechanizing absorption.
6. **Two-tier storage** — queue file for hook captures ≈ "tentative until evidence complete"; learnings/ as the human-promoted tier.

### Anti-patterns & mitigations

- **Regex false positives** — large FP list + idiom exclusions + length heuristics; still imperfect. Keep confidence scores; never auto-write to durable memory.
- **LLM in hooks** — deliberately avoided (latency, cost, `claude -p` spawning sessions risks reflection loops). Keep hooks regex-only, fail-open.
- **Memory bloat** — auto-synced memory grows monotonically; they need dedupe/organize/decay countermeasures. Robium's editorial gate is the stronger answer — hooks widen capture, never absorption.
- **Secret capture** — queue/error logs record verbatim prompts and errors; with Doppler in play, a hook logging raw Bash errors into committed learnings/ could leak env values. Scrub key/token patterns; keep the queue gitignored until human promotion.
- **Nag fatigue / injected noise** — make confirmations silent, reminders threshold-based. History mining requires long transcript retention (disk growth).

### Adjacent projects worth knowing

- **pskoett/self-improving-agent** (clawhub.ai) — skill-instruction-driven `.learnings/` directory with stable Pattern-Key dedup and promotion only at recurrence ≥ 3 across 2+ tasks — structurally the closest thing to robium's learnings→absorption model.
- **Developers Digest, "Self-Improving Skills"** (developersdigest.tech) — a Stop-hook `reflect --auto` that proposes git-versioned skill-file diffs for approval; the Stop-hook variant claude-reflect lacks, and the closest analogue to skill-updater.
