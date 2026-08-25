# robium changelog

Dated record of shipped work across the robium repos. Newest on top.

Forward-looking work is tracked in **GitHub Issues**, not here — see
`robium-ai/robium/issues` (and the sibling repos for demo and site work).
This file is the history the old `docs/BACKLOG.md` "Done" section held, migrated
verbatim on 2026-07-22.

## 2026-08-24: Generic RunPod operations skill

Added `runpod` as the provider-specific owner for safe inventory, GPU/region
and network-volume selection, immutable Pod provisioning, multi-signal startup
diagnostics, bounded interactive iteration, proxy/cancellation validation,
billing, and cleanup. The skill embeds the battle-tested evidence from issue
#69 while treating current RunPod CLI, REST, and GraphQL shapes as upstream
facts to re-verify. `environments` now owns only environment/image parity and
routes provider operations to `runpod`; architect, cloud-run, and Isaac Lab
cross-references were updated with archived prior versions.

## 2026-08-16: Standard application lifecycle CLI

Published `robium-ai` CLI 0.6.0 with standard `app help`, `doctor`, `build`,
`run`, `status`, `logs`, and `stop` commands. Application manifests can attach
summaries to lifecycle verbs, and named run variants now use `--mode` instead
of `--scenario`. Runtime-validated prototypes no longer need to declare an
automated smoke command just to pass manifest validation.

## 2026-08-07 — Codex-native maintainer and installation support

Added canonical `AGENTS.md` guidance across every Robium repository, kept
`CLAUDE.md` as a compatibility bridge, moved the local Codex marketplace to
`.agents/plugins/`, and made the plugin explicitly package its skill catalog.
The shared capture hooks now use the Codex/Claude plugin-root compatibility
contract and emit valid structured Stop output. The `robium-ai` CLI 0.5.0
installs and diagnoses the native Codex plugin; Codex-only workstations no
longer fail doctor checks. The authoring template moved outside `skills/` so
the plugin passes native validation (skill-author 2.0.3).

## 2026-08-02 — Learning engine Phase 3: experiment engine + deep-verify

Engine hardening: `find_anchor_block` resolves bold-paragraph, ordered-list,
and fence-aware anchors as full blocks (commits carry "closes #80"); an
apply_deltas + recall polish bundle — anchor-named add-op changelogs, stable
changelog spacing, null-reason sort safety, recall ellipsis truncation, and
the `learnings/deltas/` convention adopted in practice (commits carry
"closes #81"). GitHub resolves both close-keyword trailers once this branch
reaches main, not before. New engine tooling: `run_task_checks.py`
(evals.yaml `tasks:` fixtures checked against a validator schema;
skill-author bumped to 2.0.1), `run_variants.py` (blind A/B harness —
tmp-catalog builds, fitness-ranked scoring, honest-fallback judging, loser
variants archived), `deep_verify.py` (fixture-run promotion lane for
`status: unverified` examples). `learning-loop` reaches 0.2.0 with
experiment and deep-verify modes plus `experiment-recipes.md`, covering
variant A/B (run this phase) and contrastive rollouts (recipe-only by
standing decision — reserved, not executed). Engine test suite grew 155 →
207 tests; catalog holds at 24. Two pilots landed as open PRs: #86 runs
deep-verify against the lerobot `pusht-dataset-loads` fixture and promotes
`examples/load-dataset-snippet.py` to verified — merging completes exit
criterion 2; #87 runs a blind A/B over three feedback-conditioned variants
to resolve the held observation obs-nav2-003, with variant C (carrying the
nav2 1.5.0 re-verify caveat) as the scored winner — merging completes exit
criterion 1.
Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §8 layer 4, §9, Phase 3 row of §15.

## 2026-08-02 — Learning engine Phase 2b: consolidate + absorb + recall

Delta pipeline (apply_deltas: anchor-targeted ops, snapshot/bump/changelog,
ledger-aware refusals, co-evolving evals), evidence-ledger tool, trigger-eval
runner + flip gate, recall injection in the UserPromptSubmit hook + PreCompact
queue snapshot. learning-loop skill lands; skill-updater and skill-refiner
retired to archive/ (catalog at 24); skill-author 2.0.0 (authoring + quality
bar only); CLAUDE.md policy rewritten — merge is the gate. Backlog (12
learnings files + 38 flags) consolidated to observations with ledger and
eval harvest; two absorb PRs opened (external-sourced #78 and session-sourced
#79, stacked pending this branch's merge) with evidence tables. Absorb run B
also surfaced and fixed an apply_deltas same-file-annotate write-order bug.
Recall demonstrated end-to-end.
Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §5–§8, §13.

## 2026-08-02 — Learning engine Phase 2a: shared core + mining

Observations tier (schema, parser/lint) at learnings/observations/; external
citation verifier (quotes must grep at repo@sha); overlap/placement analyzer;
new mining skill (catalog at 25; architect 1.7.0 routes it, skill-author 1.1.2
narrowed). Pilots: ros2/examples and navigation2_tutorials (survey→deep),
TB3/TB4 sims (comparative common/divergent split + catalog diff) — all
observations origin: external with verified citations; SOURCES.md rows carry
crawl records. Back-mining queue regenerated after worktree loss. Pilot fix
rounds corrected several mined-content defects caught by review (pluginlib
discovery mechanics, wire-vs-plugin-API conflation, convergence framings) —
the observation files carry the corrected text.
Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §4.5, §6a.

## 2026-08-01 — Learning engine Phase 1: substrate + capture

Anchor IDs across 22 skills; evidence/evals sidecar formats with validator
enforcement; learnings schema v2; capture hooks shipped in the plugin
(corrections, bash errors, commit nudge, session summary, transcript archiver);
secret scrubber; offline transcript miner; back-mining of 21 rescued session
transcripts. Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md.

## 2026-07-18 — robium CLI shipped: npm package `robium-ai` 0.1.0

New sibling repo robium-ai/robium-cli ("A robium CLI" had been a Later item).
`npx robium-ai install` (Claude-first, drives the non-interactive claude plugin
CLI; cursor/gemini print coming-soon), `doctor [--json]` (environment preflight),
`skills [query]` (catalog generated from this repo's frontmatter at publish
time). Website AgentTabs now shows the one-command install.

Note: npm blocks the bare name `robium` (too similar to `radium`) — permanent,
not squatted. Cursor/Gemini manifest generation stays under "Public release
machinery" (now robium-plugin issue #22). Skill-update candidate shipped:
mention doctor preflight in a skill — shipped as environments 1.3.0
(2026-07-18).

## 2026-07-15 — Demo: `vla-trial` — language-conditioned VLA arm

Chat instruction → SmolVLA → SO-101 arm in MuJoCo; Rerun-in-Gradio viz in the
nav-trial workspace shell; fine-tune loop on HF Jobs; oracle → base → fine-tuned
"watch it learn" checkpoints. Design:
`robium-applications/docs/superpowers/specs/2026-07-13-vla-trial-design.md`.

Hardened lerobot, huggingface, data, rerun, environments, integration, testing,
live-demo; mujoco skill authoring still pending (robium-plugin issue #1).

## 2026-07-15 — vla-trial live demo page (v1, local-only)

At robium.ai/demos/vla-trial: FastAPI session gateway + Gradio 6 with embedded
gradio_rerun viewer; controllers oracle (succeeds) + trained (pipe-test ckpt,
honest fail); orchestrator entry + homepage card; `make demo` (native MPS) and
`make demo-image`/orchestrator (Docker CPU) both verified; `make demo-smoke`
5/5. Spec:
`robium-applications/docs/superpowers/specs/2026-07-15-vla-trial-demo-page-design.md`.

Cloud hosting deferred → robium-website issue #1. Fresh learnings captured
(macOS CGL thread-affinity deadlock; Gradio orphaned-run claims; per-run Rerun
recording ids) — candidates for live-demo/rerun/simulation, not yet absorbed.

## 2026-07-15 — UI improvements batch (robium-website)

Brainstormed 2026-07-12: hero copy rewrite; hero terminal install-to-proof
transcript; how-it-works 5 steps; skill-catalog cards (full descriptions, brand
logos, GitHub deep-links, live star count); reference-demos copy expansion;
"No robot? No problem." and "No data? We've got you." sections.

## 2026-07-18 — test-assets skill shipped 1.0.0

Step (a) of the test-data track, re-scoped 2026-07-18 after brainstorm. Spec:
`docs/superpowers/specs/2026-07-18-test-assets-skill-design.md`. The paired
corpus hardening run is robium-applications issue #1.
