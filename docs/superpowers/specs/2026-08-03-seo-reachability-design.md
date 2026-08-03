# SEO & public-reachability pass — robium.ai + robium repo

**Date:** 2026-08-03
**Status:** approved (design reviewed in session)
**Scope decision:** technical SEO + fixes only — no new content pages, no
visibility changes to robium-internal-apps or robium-website (both stay private),
deploy to production at the end.

## Context

The robium project and the robium.ai site just went public. An audit found:

- robium.ai has good basic meta (title, description, canonical, OG/Twitter
  cards) but **no robots.txt, no sitemap, no structured data, no llms.txt**,
  and nginx's `try_files … /index.html` fallback makes **every URL return
  200 with the homepage** (soft-404s everywhere — poisons crawl signals).
- The homepage has **18 broken links** to
  `github.com/robium-ai/robium/tree/main/apps/*` — those paths moved to the
  private robium-internal-apps repo during the 2026-08-03 repo split. Decision:
  **remove the app deep-links** (not repoint) until the apps are promoted to
  the public robium-ai/robium-apps showcase.
- The GitHub repo (robium-ai/robium) is in decent shape (description,
  homepage, 11 topics) but can improve keyword coverage and social preview.

## Design

### 1. Crawlability foundation (robium-website repo)

- `public/robots.txt` — allow all crawlers (including AI crawlers,
  deliberately), point at `https://robium.ai/sitemap-index.xml`.
- `@astrojs/sitemap` integration in `astro.config.mjs` — auto-generates the
  sitemap from pages at build time; uses the existing
  `site: 'https://robium.ai'` value.
- Real 404s: add `src/pages/404.astro` (branded, links home), change nginx
  `location /` to `try_files $uri $uri/ =404;` plus
  `error_page 404 /404.html;`. The `/viewer/` location keeps its own
  fallback (the Foxglove viewer needs it).
- `public/llms.txt` — machine-readable project summary: what robium is,
  install command, repo link, skill catalog pointer.

### 2. Page-level metadata (robium-website repo)

- `Base.astro` gains per-page `description` + canonical support; contact,
  brand, and the three demo pages each get a real description and their own
  canonical URL.
- JSON-LD on the homepage: `Organization`, `SoftwareApplication`
  (open-source, MIT, free), and `FAQPage` built from the existing FAQ
  section content (verbatim — the content rule applies).
- Remove the broken `apps/*` deep-links from `SkillsTable.astro` and
  `src/components/demo/About.tsx`; adjust surrounding copy so nothing
  dangles. Update `tests/smoke.sh` in the same commit (it pins literal page
  strings).

### 3. Repository polish (robium repo)

- README first-paragraph keyword pass — natural prose covering the terms
  people search ("ROS 2", "Gazebo", "Isaac Sim", "MuJoCo", "LeRobot",
  "AI coding agent", "Claude Code plugin"). No stuffing, no restructure.
- Add high-value topics (candidates: `robot-simulation`, `embodied-ai`,
  `developer-tools`; verify relevance before adding).
- Social preview: check whether one is set; if not, hand the user
  `og-card.png` + the settings path (manual UI step).

### 4. Verify + deploy

- `make smoke` passes (the done bar for the site), then `make deploy`
  (Doppler → Cloud Build → Cloud Run, ~8 min).
- Post-deploy curl checks: robots.txt is text/plain, sitemap is XML,
  a garbage URL returns 404, homepage unchanged otherwise.
- Handoff note for the user: submit the sitemap in Google Search Console
  (requires their Google account).

## Out of scope

New content pages (per-skill pages, comparison landing pages), repo
visibility changes, Search Console registration itself, app deep-link
restoration.
