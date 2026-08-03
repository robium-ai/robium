# Handover — website repositioning session (2026-08-02) → full-page review pass

Written at context reset. Two parts: (A) what exists now and the decisions that
bind it, (B) the spec for the next task. Read both before touching anything.

---

## A1. State: ALL WORK IS UNCOMMITTED

Everything below is working-tree-only in the `website/` area of the monorepo
(branch `main`, which is now BEHIND the remote — see rebase note). Nothing has
been committed all session.

**⚠ First action of the next session: `git status`, then commit this work to a
feature branch (suggested: `website-repositioning`) BEFORE rebasing or pulling.
Rebasing/pulling with a dirty tree of this size is how the work dies.**
Sequence: branch → commit (one or a few logical commits) → fetch → rebase the
branch on latest main → resolve → `make smoke`.

### Changed/new files (website/)

- `src/components/Hero.astro` — new H1/sub (Variant A copy) + animated typed
  terminal (server-rendered transcript replayed by inline script; reduced-motion
  and JS-off users see the static transcript; `:global()` styles because the
  script creates spans without Astro's scope attr)
- `src/components/LogoStrip.astro` — NEW: single-row logo marquee under hero
- `src/components/ValueProps.astro` — NEW: six "Why robium" cards
- `src/components/SkillsBento.astro` — NEW: static bento of all 25 skills
  (sizes: architect XL / umbrellas wide / gazebo·mujoco·lerobot·isaac-sim tall /
  rest small + stat tile + agent tile; unknown new skills auto-append as small)
- `src/components/HowItFits.astro` — NEW: architecture diagram section
- `src/components/WhoItsFor.astro` — NEW: 3 audience tiers with illustrations
  (dark theme: CSS invert + screen-blend over --panel; light: originals)
- `src/components/Nav.astro` — theme toggle removed from nav
- `src/components/Footer.astro` — toggle moved here; "Brand" link added
- `src/components/SkillsTable.astro` — renamed "Full skill catalog"; "25 skills
  and growing"; GitHub link in head; logo images removed from pills
- `src/components/Brand.astro` — new mark ratio (1388/1454)
- `src/pages/index.astro` — new section order (see A2)
- `src/pages/brand.astro` — NEW: brand guide page (/brand)
- `src/layouts/Base.astro` — dark is the first-visit default (stored choice wins)
- `src/lib/wall.ts` — NEW: logo wall list + per-theme variant map + per-mark
  height compensation (VectorLogoZone lockups carry ~35% padding)
- DELETED: `CatalogBelt.astro`, `CatalogBeltHalf.astro`, `src/lib/belt.ts`
  (recoverable from git history)
- `tests/smoke.sh` — many new/changed pins (hero headline+sub, value-props,
  bento count = 25+agent, strip marks = 24, boundary section, who-section,
  full-catalog rename, brand page)
- `Makefile` — new `diagram-png` target; `scripts/export-diagram.sh` — NEW
  (SVG→PNG export, reads viewBox, macOS qlmanage + uv/Pillow)
- `public/boundary-diagram.svg` — NEW: hand-authored editable architecture
  diagram (robium panel / agent hub / runs-on / yours / learning loop)
- `public/logos/*` — ~20 new official brand assets + light/dark variants,
  all provenance-logged in `public/logos/README.md` (that README is the LAW:
  every logo file needs a provenance row)
- `public/brand/*` — regenerated mark variants from new artwork (v2) +
  NEW lockups (robium-lockup.png / -dark.png); README updated
- `public/audience/*.jpg` — NEW: 3 tier illustrations (maintainer-supplied)
- `public/favicon-64.png` — regenerated from new mark.
  NOTE: `public/favicon.svg` still has OLD artwork (unreferenced by build —
  decide: retrace or delete)

### Current page order (index)

Hero (animated terminal) → LogoStrip → ValueProps (6 cards) → SkillsBento →
HowItFits (diagram) → WhoItsFor (3 tiers) → PluginAnatomy → SkillsTable →
Apps ("Built with Robium") → Faq → Footer.

## A2. Positioning decisions (the brief that was never written — this binds copy)

- **H1:** "Self-improving expertise for agentic physical AI development."
  **Sub:** open catalog + captured/mined/evidence-verified + "so your time goes
  into the application and the model, not the plumbing."
- **Audience:** physical-AI wave (ML/VLA people, less robotics-experienced)
  primary; classical roboticists secondary; teams/startups third. Section line:
  "Bring what you know. Your agent covers the rest." (deliberately compliments
  both sides; do NOT revert to "you don't need to be a roboticist").
- **Category language:** "agentic" modifies *development*, never the product.
  Robium is a knowledge/expertise layer, NOT a platform, NOT an agent runtime.
  Banned words for now: "platform" (until something hosted ships), "studio".
  Avoid the exact bigram "agentic robotics" (AgenticROS brand adjacency).
- **Truth-gates (load-bearing):**
  1. "Self-improving" refers to the CATALOG (learning engine Phase 1+2a is
     real). "Learns YOUR codebase / private overlay" is Phase 2b ROADMAP — may
     be described as future/vision, never as shipped. (User has since said:
     it's OK to mention future features as future — e.g., data layer,
     company-brain ingestion — just don't claim them as current.)
  2. Everything on the site is real (website/CLAUDE.md content rule): real
     transcripts, real skill names/counts (generated from repo at build time),
     real demos. Agent "responses" in the hero terminal are mechanical
     (skill-load lines) — never invented build output.
  3. Diagram chip says "codex" — site fine print says "Cursor and Gemini
     coming". Unresolved inconsistency; flag/fix in review pass.
- **Verb chain (proof layer):** captured from real builds · mined from the
  ecosystem · evidence-verified · pruned when it rots.
- **Reserve lines:** "Agents propose. Evidence decides. Humans merge." /
  "Agents evolve code. Robium evolves the expertise they run on." (for blog/
  launch, not yet on site).
- **Theme:** dark is the brand default (first visit forced dark; toggle in
  footer persists override). Dark-bg logo variants are native; light variants
  swap via `html[data-theme='light']`.

## A3. Conventions that bind any edit

- Done bar: `cd website && make smoke` → "SMOKE PASS". Smoke pins literal
  strings — copy changes REQUIRE matching pin updates in the same change.
- No framework JS on the landing page; only small vanilla `<script>` in the
  component that needs it. Counts/lists generated from repo data at build time
  — never hand-typed (skills count, belt/bento contents, table rows).
- Astro scoped styles don't hit dynamically-created DOM — use `:global()`.
- Logos: official sources only, provenance row in public/logos/README.md,
  dark+light variants, wall wiring in src/lib/wall.ts (WALL_VARIANT + HEIGHT).
- Dev loops: `npm run dev` (site :4321). Don't deploy to iterate.
- A background dev-server task from the old session may be dead — restart it.

---

## B. NEXT TASK — complete webpage review & improvement pass

Goal: a detailed full-page audit + improvement, AND make the website/ area
ready for the repo going public/open-source. The user wants this run as a
long-horizon iterative goal (use the goal/loop mechanism: define checkpoints,
iterate section by section, verify each with smoke + browser, keep a running
findings list; don't try one mega-pass).

### Scope & constraints

1. **Git first:** commit current work to a branch, rebase onto latest main
   (main has moved), resolve, smoke. Only then start the review.
2. **Full audit of every section** for missing pieces, staleness vs the
   repository's CURRENT state (re-read repo: skills count/names/descriptions,
   CLI behavior, learning-engine status, REGISTRY, changelog — main moved, so
   facts may have moved).
3. **Truncation kill-pass:** NO sentence anywhere may end in "…"/"..." —
   especially bento tiles and cards. Rework `compact()`/clamp usage so tiles
   carry short but COMPLETE sentences (hand-curate per-tile text if needed —
   but keep the no-hand-maintained-counts rule; text curation is fine, counts
   are not). Keep roughly current text lengths; complete > long.
4. **Simplification + de-duplication:** find repeated claims across
   hero/cards/bento/anatomy/FAQ; each claim should live in ONE best place.
   Apply reasoning about which bento pieces deserve size/prominence — document
   the reasoning briefly in the PR/commit message or a note.
5. **Tone pass:** professional, startup + open-source project sounding; less
   personal voice ("we might/I want" phrasing out; confident product voice in).
   OK to present future capabilities as roadmap (e.g., data layer, company
   brain / knowledge ingestion) — clearly future-framed, not fake-shipped.
6. **"What's in the plugin" (PluginAnatomy):** update to latest reality but
   optimize for catchy-important over 1:1 completeness (user explicitly allows
   editorial judgment here).
7. **Full skill catalog section:** keep ALL skills listed; keep "and growing";
   ADD the idea that robium can also generate project-specific skills from
   your project context (this is the skill-author/learning-engine capability —
   frame honestly, future-tinted if needed).
8. **FAQ:** update to match the new positioning (self-improving, physical AI,
   audience tiers, open-source readiness). Rewrite stale answers.
9. **DO NOT touch:** "Built with Robium" (Apps) section and the demo pages —
   user does those in a separate pass.
10. **Open-source-ready check** (website/ area): README/DEVELOPING accuracy,
    no secrets/keys in files, license notes, logo/brand provenance completeness
    (it's good — verify), contribution-friendly file layout, no TODO/dead
    files (`favicon.svg` decision!), alt text everywhere, meta/OG tags +
    page titles vs new positioning (`<title>` still says "Physical AI
    expertise for AI agents" — align), and that smoke covers the new claims.
11. **Also still pending from last session:** write the positioning brief into
    docs/ (A2 above is the source material); decide favicon.svg; consider
    "codex"→"cursor" in the diagram; GitHub/npm/plugin-manifest descriptions
    alignment with the new H1 (marketing surfaces beyond the site).

### Suggested goal-loop shape

Iterate: (1) rebase+commit hygiene → (2) repo-fact refresh → (3) per-section
audit top-to-bottom (hero, strip, cards, bento, diagram, who, anatomy, catalog,
FAQ, footer, brand page) with findings list → (4) truncation+tone+dedup fixes
→ (5) open-source readiness sweep → (6) final smoke + full-page browser
walkthrough (both themes) → (7) summary of changes + remaining flags.
Each iteration ends with `make smoke` green; never leave the tree red.
