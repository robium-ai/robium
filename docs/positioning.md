# Robium positioning brief

Written 2026-08-02, from the website repositioning session (decision record:
notes/2026-08-02-website-handover.md §A2, refined by the full-page review
pass). **This document binds marketing copy** — the site, the GitHub/npm/plugin
manifests, launch posts. If copy and this brief disagree, fix one of them
deliberately.

## The one-liner

**H1:** "Self-improving expertise for agentic physical AI development."

**Sub:** An open catalog of robotics skills for AI agents — captured from real
builds, mined from the ecosystem, evidence-verified — so your time goes into
the application and the model, not the plumbing.

## What robium is (category language)

Robium is a **knowledge / expertise layer** for coding agents. It is NOT a
platform, NOT an agent runtime, NOT a framework.

- "Agentic" modifies *development* — never the product. Robium is not "an
  agentic X".
- **Banned words:** "platform" (until something hosted ships), "studio".
- **Avoid the exact bigram** "agentic robotics" (AgenticROS brand adjacency).

## Audience (in priority order)

1. **Physical-AI wave** — ML/VLA people with less robotics experience.
2. **Classical roboticists** crossing into the learning stack.
3. **Teams & startups** standardizing agent-assisted robotics development.

Section line: "Bring what you know. Your agent covers the rest." — it
deliberately compliments both sides. Do NOT revert to "you don't need to be a
roboticist" (condescends to audience 2).

## Truth-gates (load-bearing — check before shipping any claim)

1. **"Self-improving" refers to the CATALOG.** The learning engine's capture,
   mining, consolidate, absorb and recall paths (Phases 1, 2a, 2b) are
   shipped and real. "Learns YOUR codebase" / private overlay / company-brain
   ingestion is **roadmap** (design-spec Phase 3/4, user tier) — it may be
   described as future/vision, never as shipped.
2. **Everything on the site is real** (website/CLAUDE.md content rule): real
   transcripts, real skill names, counts generated from the repo at build
   time, real demos. Agent "responses" in the hero terminal are mechanical
   skill-load lines — never invented build output. Hand-typed counts are
   forbidden everywhere, including SVGs and repo descriptions — where a count
   can't be generated, write count-free copy.
3. **Agent support:** Claude Code today; Cursor and Gemini planned (the CLI's
   own roadmap). Diagram chips, fine print, and FAQ must agree.

## Proof layer (the verb chain)

captured from real builds · mined from the ecosystem · evidence-verified ·
pruned when it rots.

## Reserve lines (for blog/launch — deliberately NOT on the site yet)

- "Agents propose. Evidence decides. Humans merge."
- "Agents evolve code. Robium evolves the expertise they run on."

## Theme

Dark is the brand default: first visit is forced dark; the footer toggle
persists any override. Dark-background logo variants are the natives; light
variants swap in via `html[data-theme='light']`.

## Where the copy lives

- Site: `website/src/components/*` (smoke-pinned: `website/tests/smoke.sh`).
- Plugin manifests: `.claude-plugin/plugin.json` + `marketplace.json`.
- CLI: `cli/package.json` description (npm surface at next publish).
- GitHub repo description: set via `gh repo edit` (aligned 2026-08-02).
