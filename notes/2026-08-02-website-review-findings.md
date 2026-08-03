# Website review pass — findings & decisions (2026-08-02)

Running list for the Part B audit (see 2026-08-02-website-handover.md). Repo
facts refreshed first: catalog is **24 skills** (Phase 2b retired skill-updater
+ skill-refiner, added learning-loop; mining came in 2a), learning engine
Phases 1/2a/2b **shipped**, private overlay / "learns your codebase" is Phase
3/4 **roadmap** (design spec §9, user-tier table), CLI lives in monorepo
`cli/` (`robium-ai` npm), CLI roadmap = Cursor + Gemini (not codex).

## Findings → fixes

1. **Hero terminal** "✓ 25 skills installed" — hand-typed AND stale. → render
   `{allSkills.length}` (content rule: counts always generated).
2. **Hero CTA** linked `robium-ai/robium-cli` — repo merged into monorepo. →
   link `robium-ai/robium/tree/main/cli`.
3. **Duplication:** "your time goes into the application and the model" in
   hero sub AND "Plumbing handled" card; "which sim, which viewer, which data
   source" in bento agent tile AND anatomy agents row AND FAQ. → each claim
   keeps ONE home (hero keeps the time-goes line; FAQ keeps the judgment
   list); the other spots reworded.
4. **Bento ORDER** still listed retired skill-updater/skill-refiner;
   learning-loop was auto-appended as a small tile. → retired names removed;
   learning-loop placed deliberately.
   **Prominence reasoning:** architect stays XL (entry point). Umbrellas wide
   (they're the routing/judgment layer). gazebo/mujoco/lerobot/isaac-sim tall
   (flagship tool skills = the four sim/learning ecosystems people arrive
   for). learning-loop gets **wide**: "self-improving" is the H1 claim — the
   skill that implements it must be visible, next to skill-author + mining so
   the catalog-upkeep trio reads as one machine.
5. **Truncation kill-pass:** 33 "…" in built homepage (bento tiles + table
   teasers). → new hand-curated `src/data/skill-taglines.json` (short COMPLETE
   sentences, derived from each skill's real description; text curation is
   allowed, counts are not). `compact()`/`teaser()` replaced by tagline lookup
   with a sentence/clause-boundary fallback that never emits "…". The one
   remaining "…" is the PluginAnatomy file-tree elision line — a tree
   continuation glyph, not a truncated sentence; kept. Smoke now pins
   "exactly one … in the page".
   Browser walkthrough exposed a second truncation channel the server-side
   check can't see: CSS line-clamp. Real tile budgets (measured at desktop
   6-col): small ≈ 40 chars (2 lines × ~20), wide ≈ 90, tall ≈ 140 (7 lines
   × ~20), xl ≈ 330; the agent tile fits ONE line after its label+name.
   Taglines were tightened to those budgets and verified clamp-free via
   `scrollHeight > clientHeight` over every tile in the live page.
6. **pillars.json gaps:** mujoco and cloud-run were in no pillar → they fell
   into the derived "Catalog upkeep" group (wrong). → mujoco → Simulation;
   cloud-run → Architecture & proof (pairs with live-demo, which points at
   cloud-run for deploy mechanics). Catalog-upkeep blurb now tells the
   learning-engine story (that group is skill-author/learning-loop/mining).
7. **Boundary diagram:** "25+ skills" count removed (SVG can't be generated at
   build time — a count there will always rot; category names carry the
   scale); "codex" chip → "cursor" (matches CLI roadmap + site fine print).
   Alt text updated to match.
8. **WhoItsFor** truth-gate comment referenced "Phase 2b roadmap" — Phase 2b
   shipped; the private-overlay feature is Phase 3/4. Comment fixed; copy was
   already correct (capture hooks are real).
9. **PluginAnatomy:** tree's "reference apps 3" actually counted live-demo
   pages → relabeled "live demos" (count stays real, from pages glob);
   reference-apps row copy keeps the proof story; learning-engine line added
   (catchy-important over 1:1 completeness, per handover §B6).
10. **SkillsTable:** added the project-specific-skill-generation idea
    (skill-author + learning engine; honestly framed), kept "and growing".
11. **FAQ:** freshness answer rewritten around the real learning engine
    (capture → evidence → PR → human merge); stale "a dedicated skill folds
    learnings" framing replaced; personal voice removed.
12. **Base meta:** `<title>`/description aligned to the new H1; OG/twitter
    tags added (were missing entirely); canonical URL added.
13. **favicon.svg:** deleted — old artwork, unreferenced by the build
    (recoverable from git history).

## Flags (not fixed here)

- Discord link is a non-vanity invite (`discord.gg/cyd8xC6W6`) — confirm it's
  set to never expire, or mint a permanent invite.
- huggingface.co/robium link assumed live (smoke pins it; not re-verified in
  this pass).
- "Built with Robium" (Apps) + demo pages untouched per handover §B9.
