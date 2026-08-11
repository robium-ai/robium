# SEO & Reachability Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make robium.ai fully crawlable (robots/sitemap/real-404s/structured data), fix its broken/false public claims, and sharpen the robium repo's discovery metadata — then deploy to production.

**Architecture:** Two repos. Site work happens in `~/repos/robium-website` (Astro 6 static + nginx on Cloud Run; committed to `main`, deployed via `make deploy`). Repo work happens in `~/repos/robium` (README + `gh repo edit` topics). The site's done bar is `tests/smoke.sh` — every content change lands with its smoke assertion in the same commit.

**Tech Stack:** Astro 6, @astrojs/sitemap, nginx, GitHub CLI, Cloud Build/Cloud Run via `make deploy`.

## Global Constraints

- **Content rule (robium-website CLAUDE.md):** everything on the site is real — never invent a metric, transcript line, or count. JSON-LD must mirror on-page content verbatim.
- **No frameworks on the landing page:** plain `<script>`/static markup only; JSON-LD is inert `application/ld+json`, which is fine.
- **Canonical domain is `https://robium.ai`** — never `.org`/`.dev`.
- **Repository links must reflect current visibility.** Application links target the public robium-ai/robium-apps repository.
- **`tests/smoke.sh` pins literal page strings** — any copy change updates smoke in the same commit.
- Site repo path: `~/repos/robium-website`. Plugin repo path: `~/repos/robium`. Both commit straight to `main` (site deploys are gated by `make smoke`).
- Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Crawl files — robots.txt, sitemap, llms.txt

**Files:**
- Create: `public/robots.txt` (robium-website)
- Create: `public/llms.txt` (robium-website)
- Modify: `astro.config.mjs` (robium-website)
- Modify: `package.json` / `package-lock.json` (via `npx astro add sitemap`)
- Test: `tests/smoke.sh` (append assertions)

**Interfaces:**
- Produces: `dist/robots.txt`, `dist/llms.txt`, `dist/sitemap-index.xml` + `dist/sitemap-0.xml` in every build. Task 7's post-deploy checks curl these paths.

- [ ] **Step 1: Add failing smoke assertions**

Append to the `if [[ -z "$URL" ]]; then` block of `tests/smoke.sh` (after the brand-guide checks, before `fi`):

```bash
  # SEO crawl files (2026-08 SEO pass)
  [[ -f dist/robots.txt ]] && echo "ok: robots.txt" || { echo "FAIL: robots.txt missing"; fail=1; }
  grep -q "Sitemap: https://robium.ai/sitemap-index.xml" dist/robots.txt && echo "ok: robots sitemap line" || { echo "FAIL: robots sitemap line"; fail=1; }
  [[ -f dist/sitemap-index.xml ]] && echo "ok: sitemap index" || { echo "FAIL: sitemap-index.xml missing"; fail=1; }
  grep -q "robium.ai/demos/nav-trial" dist/sitemap-0.xml && echo "ok: sitemap covers demo pages" || { echo "FAIL: sitemap demo pages"; fail=1; }
  [[ -f dist/llms.txt ]] && echo "ok: llms.txt" || { echo "FAIL: llms.txt missing"; fail=1; }
```

- [ ] **Step 2: Run smoke to verify the new checks fail**

Run: `cd ~/repos/robium-website && npm ci && npm run build && bash tests/smoke.sh`
Expected: the five new checks print FAIL (build itself passes; pre-existing checks pass).

- [ ] **Step 3: Add the sitemap integration**

Run: `cd ~/repos/robium-website && npx astro add sitemap --yes`

This installs `@astrojs/sitemap` and updates `astro.config.mjs`. Verify the config now reads:

```mjs
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://robium.ai',
  output: 'static',
  integrations: [react(), sitemap()],
});
```

(If `astro add` writes a different but equivalent shape, keep its shape. `@astrojs/sitemap` excludes the 404 page automatically.)

- [ ] **Step 4: Write robots.txt**

Create `public/robots.txt`:

```
# robium.ai — all crawlers welcome, including AI crawlers.
User-agent: *
Allow: /

Sitemap: https://robium.ai/sitemap-index.xml
```

- [ ] **Step 5: Write llms.txt**

Create `public/llms.txt`:

```
# Robium

> Open-source, continuously evolving collection of field-tested robotics
> expertise for AI coding agents. Install Robium as a plugin to give your
> agent (Claude Code, Codex, Gemini CLI, Cursor) the robotics skills it
> needs: ROS 2, Nav2, Gazebo, MuJoCo, NVIDIA Isaac Sim, Isaac Lab, LeRobot,
> Foxglove, Rerun, RViz2, Hugging Face, and cloud deployment.

MIT-licensed. The skills are natural-language SKILL.md files (open Agent
Skills format) plus curated references and runnable examples — no invented
syntax or DSL.

## Install

- Quick: `npx robium-ai setup` (auto-detects your agents)
- Source: https://github.com/robium-ai/robium

## Links

- Website: https://robium.ai
- Skill catalog: https://github.com/robium-ai/robium/tree/main/skills
- npm CLI: https://www.npmjs.com/package/robium-ai
- Discord: https://robium.ai/join/discord
- Hugging Face: https://huggingface.co/robium
```

- [ ] **Step 6: Build and verify smoke passes**

Run: `npm run build && bash tests/smoke.sh`
Expected: `SMOKE PASS`, including the five new `ok:` lines. Also verify `dist/sitemap-0.xml` does NOT contain `/404` (`! grep -q "404" dist/sitemap-0.xml`).

- [ ] **Step 7: Commit**

```bash
cd ~/repos/robium-website
git add public/robots.txt public/llms.txt astro.config.mjs package.json package-lock.json tests/smoke.sh
git commit -m "feat: robots.txt, sitemap via @astrojs/sitemap, llms.txt

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Real 404s — 404 page + nginx

**Files:**
- Create: `src/pages/404.astro` (robium-website)
- Modify: `nginx.conf:26` (the `location /` fallback)
- Test: `tests/smoke.sh` (dist-mode file check + URL-mode status check)

**Interfaces:**
- Consumes: `Base.astro` layout as-is (Task 3's `description` prop is optional — this page builds before and after Task 3).
- Produces: `dist/404.html`; nginx serves it with status 404 for any unknown path. Task 7 curls a garbage URL expecting 404.

- [ ] **Step 1: Add failing smoke assertions**

In `tests/smoke.sh`, append to the dist-mode block (`if [[ -z "$URL" ]]`):

```bash
  [[ -f dist/404.html ]] && echo "ok: 404 page" || { echo "FAIL: 404.html missing"; fail=1; }
```

And in the URL-mode `else` branch near the viewer checks (inside `if [[ -n "$URL" ]]`-equivalent, i.e. the `else` of `if [[ -z "$URL" ]]` at the bottom):

```bash
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL/definitely-not-a-page")
  [[ "$code" == "404" ]] && echo "ok: unknown path returns 404" || { echo "FAIL: unknown path returned $code (soft-404)"; fail=1; }
```

- [ ] **Step 2: Run smoke (dist mode) to verify the 404.html check fails**

Run: `bash tests/smoke.sh`
Expected: `FAIL: 404.html missing`.

- [ ] **Step 3: Create the 404 page**

Create `src/pages/404.astro`:

```astro
---
import Base from '../layouts/Base.astro';
import Nav from '../components/Nav.astro';
import Footer from '../components/Footer.astro';
---
<Base bodyClass="landing" title="Page not found — Robium.ai">
  <Nav />
  <main>
    <section>
      <div class="container notfound">
        <h1>404 — page not found</h1>
        <p>
          This URL doesn't exist. The skill catalog, install guide, and live
          demos all live on the <a href="/">home page</a>.
        </p>
      </div>
    </section>
  </main>
  <Footer />
</Base>

<style>
  .notfound { text-align: center; padding: 140px 0 160px; }
  .notfound h1 { margin: 0 0 12px; }
  .notfound a { color: var(--accent-ink); }
</style>
```

(If `Nav`/`Footer` require props when built standalone, check how `src/pages/contact.astro` uses them and mirror that usage exactly.)

- [ ] **Step 4: Fix the nginx fallback**

In `nginx.conf`, change the main server block's last location from:

```
    location / { try_files $uri $uri/ /index.html; }
```

to:

```
    error_page 404 /404.html;
    location / { try_files $uri $uri/ =404; }
```

Leave the `/viewer/` location's own fallback untouched (the Foxglove viewer needs it).

- [ ] **Step 5: Build + dist-mode smoke passes**

Run: `npm run build && bash tests/smoke.sh`
Expected: `SMOKE PASS` including `ok: 404 page`.

- [ ] **Step 6: Container smoke proves the 404 status**

Run: `cd ~/repos/robium-website && make docker-smoke`
Expected: passes, including `ok: unknown path returns 404`. (If `make docker-smoke` doesn't pass a URL to smoke.sh, read the Makefile target and run the equivalent: build the image, run it on :8080, `bash tests/smoke.sh http://localhost:8080`.)

- [ ] **Step 7: Commit**

```bash
git add src/pages/404.astro nginx.conf tests/smoke.sh
git commit -m "feat: real 404s — branded 404 page, nginx =404 fallback

Every unknown URL previously returned 200 with the homepage (soft-404).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Per-page meta descriptions

**Files:**
- Modify: `src/layouts/Base.astro:3-12` (make `description` a prop)
- Modify: `src/pages/contact.astro`, `src/pages/brand.astro`, `src/pages/demos/nav-trial.astro`, `src/pages/demos/vla-trial.astro`, `src/pages/demos/manip-trial.astro`, `src/pages/404.astro`
- Test: build output grep (one-off, not smoke — descriptions aren't load-bearing content)

**Interfaces:**
- Produces: `Base.astro` accepts optional `description` prop (default = current site description, unchanged). Task 4 relies on Base also exposing a `<slot name="head" />`.

- [ ] **Step 1: Make description a prop and add a head slot in Base.astro**

Replace the frontmatter const block:

```astro
---
import '../styles/theme.css';
const SITE_DESCRIPTION =
  'An open-source, continuously evolving collection of field-tested robotics ' +
  'expertise spanning the leading Physical AI frameworks, simulators, libraries, ' +
  'and developer tools. Install Robium as a plugin to give your AI coding agent ' +
  'the robotics skills it needs.';
const {
  title = 'Robium.ai — Physical AI skills for your agents',
  bodyClass = '',
  description = SITE_DESCRIPTION,
} = Astro.props;
const SITE = 'https://robium.ai';
---
```

The `<meta name="description">`, `og:description`, and `twitter:description` tags already interpolate `{description}` — no tag changes needed. Then add `<slot name="head" />` on its own line immediately before `</head>`.

- [ ] **Step 2: Give each page its description**

Real, specific, ≤160 chars each — pass as a `description` prop next to the existing `title`:

- `contact.astro`: `Contact the Robium maintainers — Discord community, GitHub issues and discussions, or email.` (adjust to match what the page actually offers — read it first; the content rule applies.)
- `brand.astro`: `Robium brand guide — logo lockups, marks, and usage rules for the Robium open-source robotics skills project.`
- `demos/nav-trial.astro`: `Drive a live ROS 2 + Nav2 + Gazebo robot simulation in your browser — built end-to-end by an AI coding agent with the Robium plugin.`
- `demos/vla-trial.astro`: `Live VLA policy demo — a vision-language-action model evaluated in simulation, built with the Robium plugin.` (verify against the page's actual claims before writing.)
- `demos/manip-trial.astro`: `Live robot manipulation demo — a LeRobot policy trained and evaluated in simulation, built with the Robium plugin.` (verify against the page's actual claims before writing.)
- `404.astro`: `This page doesn't exist. Find the Robium skill catalog, install guide, and live robot demos on the home page.`

- [ ] **Step 3: Build and spot-check**

Run: `npm run build && grep -o '<meta name="description" content="[^"]*"' dist/contact/index.html dist/demos/nav-trial/index.html`
Expected: each page shows its own description, not the site default. Also `bash tests/smoke.sh` still passes.

- [ ] **Step 4: Commit**

```bash
git add src/layouts/Base.astro src/pages
git commit -m "feat: per-page meta descriptions + head slot in Base layout

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: JSON-LD structured data

**Files:**
- Modify: `src/pages/index.astro` (Organization + SoftwareApplication via head slot)
- Modify: `src/components/Faq.astro` (FAQPage, generated from a single data array)
- Test: `tests/smoke.sh` (JSON-LD presence + FAQPage)

**Interfaces:**
- Consumes: `<slot name="head" />` in Base.astro (Task 3).
- Produces: three JSON-LD types on the homepage. Faq.astro exports nothing; its `faqs` array is the single source for both rendered Q&A and FAQPage JSON-LD.

- [ ] **Step 1: Add failing smoke assertions**

Append to the main check list in `tests/smoke.sh` (near the `og:image` check):

```bash
check "application/ld+json" "JSON-LD present"
check "FAQPage" "FAQPage structured data"
check "SoftwareApplication" "SoftwareApplication structured data"
```

Run: `bash tests/smoke.sh` → expected: three FAILs.

- [ ] **Step 2: Organization + SoftwareApplication in index.astro**

In `src/pages/index.astro` frontmatter, add:

```astro
const structuredData = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      '@id': 'https://robium.ai/#org',
      name: 'Robium',
      url: 'https://robium.ai',
      logo: 'https://robium.ai/brand/robium-mark.png',
      sameAs: [
        'https://github.com/robium-ai/robium',
        'https://www.npmjs.com/package/robium-ai',
        'https://huggingface.co/robium',
      ],
    },
    {
      '@type': 'SoftwareApplication',
      name: 'Robium',
      url: 'https://robium.ai',
      applicationCategory: 'DeveloperApplication',
      operatingSystem: 'macOS, Linux',
      description:
        'An open-source, continuously evolving collection of field-tested ' +
        'robotics expertise. Install Robium as a plugin to give your AI ' +
        'coding agent the robotics skills it needs.',
      license: 'https://github.com/robium-ai/robium/blob/main/LICENSE',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
      author: { '@id': 'https://robium.ai/#org' },
    },
  ],
};
```

And inside `<Base bodyClass="landing">`, first child:

```astro
  <Fragment slot="head">
    <script type="application/ld+json" set:html={JSON.stringify(structuredData)} />
  </Fragment>
```

Verify `public/brand/robium-mark.png` exists (it does — seen in `public/brand/`).

- [ ] **Step 3: FAQPage in Faq.astro**

At the top of `src/components/Faq.astro`, add frontmatter holding the Q&A pairs as data, then render both the existing markup shape AND the JSON-LD from that one array. The answer strings must be the current on-page text with markup flattened to plain text (content rule: verbatim, just tag-free). Keep the two existing copy fixes out of this task — Task 5 owns copy changes; here the array carries today's text exactly:

```astro
---
// FAQPage JSON-LD source. The rendered Q&A below stays hand-authored
// (it carries links/<code>); aText is the tag-free mirror of each answer.
const faqs = [
  { q: 'Which coding agents does Robium work with?',
    aText: 'Claude Code, Codex, Gemini CLI, and Cursor. One command — npx robium-ai setup — detects the agents on your machine and sets up each one (or target one: --agent codex). The skills follow the open Agent Skills format, so any agent that speaks it can read them.' },
  { q: 'Do I need a robot or a GPU?',
    aText: 'Not necessarily. Everything starts in simulation — manip-trial trains and evaluates a policy on a GPU-less MacBook, and nav-trial runs Gazebo fully headless in Docker. When a build does need muscle, the skills cover running the same stack on remote GPU servers and in the cloud.' },
  { q: 'What exactly is a skill?',
    aText: 'A versioned folder of expertise your agent loads when a task calls for it: field-tested guidance — which simulator, which viewer, the failure modes docs don\'t mention — plus curated reference notes and runnable examples: real Dockerfiles, launch files, SDF worlds, and Python snippets. No invented syntax to learn; just knowledge your agent acts on.' },
  { q: 'Why not just ask my agent directly?',
    aText: 'Frontier agents know robotics in general. They don\'t reliably know which Gazebo pairs with which ROS 2 release, or why a cloud-hosted sim needs a unicast relay. Skills pin that judgment and those facts — versioned and verified against real builds — so your agent doesn\'t re-derive or hallucinate them.' },
  { q: 'How do skills stay correct as the ecosystem moves?',
    aText: 'The catalog runs a learning engine: build sessions capture what broke and what fixed it, mining pulls proven patterns from ecosystem repos, and evidence-gated pull requests fold both back into the versioned skills — a human merges every change. LeRobot\'s API churn has already forced a major version bump.' },
  { q: 'Can it capture my team\'s own knowledge?',
    aText: 'Yes. Capture hooks log what breaks and what works during your builds, and the skill-author workflow turns that into skills for your own stack — your conventions, your hardware, your infra — hardened by the same loop that maintains the public catalog.' },
  { q: 'Is it free?',
    aText: 'Yes — MIT-licensed, everything public at github.com/robium-ai: the plugin, the reference apps, the CLI, and this site.' },
  { q: 'Can I contribute a skill?',
    aText: 'Yes, and the contribution unit is deliberately small: one skill. Copy the template, pass the validator, open a PR.' },
];
const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqs.map(({ q, aText }) => ({
    '@type': 'Question',
    name: q,
    acceptedAnswer: { '@type': 'Answer', text: aText },
  })),
};
---
```

Keep the existing rendered HTML **unchanged** (don't data-drive the markup — the answers carry links/`<code>` that the array flattens). Add directly after the closing `</section>`:

```astro
<script type="application/ld+json" set:html={JSON.stringify(faqJsonLd)} />
```

Add an HTML comment above the rendered `.faq-grid`: `<!-- Keep the rendered Q&A and the faqs array above in exact sync — JSON-LD must mirror visible content. -->`

- [ ] **Step 4: Build, validate, smoke**

Run: `npm run build && bash tests/smoke.sh`
Expected: `SMOKE PASS` with the three new `ok:` lines.
Then validate the JSON parses: `node -e "const h=require('fs').readFileSync('dist/index.html','utf8'); [...h.matchAll(/<script type=\"application\/ld\+json\">(.*?)<\/script>/gs)].forEach((m,i)=>{JSON.parse(m[1]); console.log('ld+json block', i, 'parses')})"`

- [ ] **Step 5: Commit**

```bash
git add src/pages/index.astro src/components/Faq.astro tests/smoke.sh
git commit -m "feat: JSON-LD — Organization, SoftwareApplication, FAQPage

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Remove broken app links + fix false "everything public" claim

**Files:**
- Modify: `src/components/SkillsTable.astro:172-179` (drop the "Used by" block)
- Modify: `src/components/demo/About.tsx:10` (drop the apps deep-link)
- Modify: `src/components/Faq.astro` ("Is it free?" answer — both rendered HTML and `aText`)
- Test: `tests/smoke.sh` (negative check: no `tree/main/apps` links anywhere in dist)

**Interfaces:**
- Consumes: the `faqs` array shape from Task 4 (update `aText` for "Is it free?" in the same edit as the rendered answer).

- [ ] **Step 1: Add failing smoke assertion**

Append to the dist-mode block of `tests/smoke.sh`:

```bash
  # Application paths moved to the public robium-apps repo.
  grep -rq "tree/main/apps" dist/ && { echo "FAIL: stale robium/tree/main/apps link in dist"; fail=1; } || echo "ok: no stale apps links"
```

Run: `npm run build && bash tests/smoke.sh` → expected: `FAIL: stale robium/tree/main/apps link in dist`.

- [ ] **Step 2: SkillsTable — remove the "Used by" block**

Delete this block from `src/components/SkillsTable.astro` (currently lines 172–179):

```astro
              {r.apps.length > 0 && (
                <div class="meta-block">
                  <span class="meta-label">Used by</span>
                  {r.apps.map((a) => (
                    <a class="app" href={`${REPO}/tree/main/apps/${a}`}>{a}</a>
                  ))}
                </div>
              )}
```

Leave `r.apps` in the row data and the `.app` CSS rules alone if removing them cascades (check for a `.app` style block; delete it only if it's now unused and clearly scoped).

- [ ] **Step 3: About.tsx — drop the apps deep-link**

Replace the first `<p>` of `src/components/demo/About.tsx` so the brief attribution keeps its meaning without the dead link:

```tsx
      <p>
        Everything in this workspace — the stack, the map, the running sim —
        was built by Claude Code with the{' '}
        <a href="https://github.com/robium-ai/robium">robium</a> plugin, from
        this brief (verbatim from the robium proving ground):
      </p>
```

- [ ] **Step 4: Fix the "Is it free?" answer (rendered + aText together)**

In `src/components/Faq.astro`, replace the rendered answer:

```astro
        <p>
          Yes — MIT-licensed. The plugin, the full skill catalog, and the CLI
          are open source at
          <a href="https://github.com/robium-ai">github.com/robium-ai</a>.
        </p>
```

And the matching `aText` entry:

```
    aText: 'Yes — MIT-licensed. The plugin, the full skill catalog, and the CLI are open source at github.com/robium-ai.' },
```

- [ ] **Step 5: Build + full smoke passes**

Run: `npm run build && bash tests/smoke.sh`
Expected: `SMOKE PASS` including `ok: no stale apps links`. (If any pre-existing check pinned removed copy, update that check to the new truthful copy in this commit.)

- [ ] **Step 6: Commit**

```bash
git add src/components/SkillsTable.astro src/components/demo/About.tsx src/components/Faq.astro tests/smoke.sh
git commit -m "fix: drop links to private apps repo; correct open-source claim

apps/ moved to the robium-apps repo in the 2026-08-03 split —
18 homepage links 404'd for public visitors, and the FAQ claimed the
apps and site repos were public.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Repo discovery — README keywords, topics, social preview

**Files:**
- Modify: `README.md` (robium repo — intro lines only)
- Repo settings via `gh repo edit` (topics)
- Test: manual grep + `gh repo view`

**Interfaces:**
- None (independent of site tasks).

- [ ] **Step 1: README intro keyword pass**

In `~/repos/robium/README.md`, extend the centered intro (lines 10–12) with one additional line naming the stacks and agents in natural prose. Replace:

```markdown
An open-source, continuously evolving collection of field-tested robotics<br>
expertise — install robium as a plugin to empower your favorite AI coding<br>
agent with the robotics skills it needs.
```

with:

```markdown
An open-source, continuously evolving collection of field-tested robotics<br>
expertise — install robium as a plugin to empower your favorite AI coding<br>
agent with the robotics skills it needs.<br>
Covers ROS 2, Nav2, Gazebo, MuJoCo, NVIDIA Isaac Sim, Isaac Lab, and LeRobot,<br>
for Claude Code, Codex, Gemini CLI, and Cursor.
```

- [ ] **Step 2: Add repo topics**

```bash
gh repo edit robium-ai/robium --add-topic robot-simulation --add-topic embodied-ai --add-topic developer-tools --add-topic simulation --add-topic codex --add-topic gemini-cli --add-topic cursor
```

Then verify: `gh repo view robium-ai/robium --json repositoryTopics`
Expected: 18 topics including the 7 new ones.

- [ ] **Step 3: Check the social preview image**

```bash
curl -s https://github.com/robium-ai/robium | grep -o 'property="og:image" content="[^"]*"'
```

If the URL is `opengraph.githubassets.com/...` → no custom image is set. Note for the final report: user should upload `robium-website/public/og-card.png` at https://github.com/robium-ai/robium/settings → Social preview. If it's `repository-images.githubusercontent.com/...` → already set, nothing to do.

- [ ] **Step 4: Commit (README only)**

```bash
cd ~/repos/robium
git add README.md
git commit -m "docs: name covered stacks and agents in README intro

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Deploy + live verification

**Files:**
- None new. Runs `make smoke`, `make deploy` in robium-website; curls production.

**Interfaces:**
- Consumes: all site commits on `main` (Tasks 1–5).

- [ ] **Step 1: Final full smoke locally**

Run: `cd ~/repos/robium-website && npm run build && bash tests/smoke.sh && make docker-smoke`
Expected: both `SMOKE PASS`.

- [ ] **Step 2: Push and deploy**

```bash
git push origin main
make deploy   # Cloud Build → Cloud Run robium-site (~8 min). If gcloud auth is
              # missing, per docs/secrets.md: doppler run -- make deploy
```

Expected: deploy completes with the new revision serving.

- [ ] **Step 3: Verify production**

```bash
curl -s https://robium.ai/robots.txt | head -5                      # text, Sitemap: line
curl -s -o /dev/null -w "%{content_type}\n" https://robium.ai/robots.txt   # text/plain
curl -s -o /dev/null -w "%{http_code}\n" https://robium.ai/sitemap-index.xml  # 200, XML
curl -s -o /dev/null -w "%{http_code}\n" https://robium.ai/definitely-not-a-page  # 404
curl -s https://robium.ai | grep -c 'application/ld+json'           # >= 2
curl -s https://robium.ai | grep -c 'tree/main/apps'                # 0
bash tests/smoke.sh https://robium.ai                               # URL-mode smoke
```

- [ ] **Step 4: Handoff note**

Include in the final report to the user:
1. Google Search Console: add property `robium.ai` (DNS TXT verification), then Sitemaps → submit `https://robium.ai/sitemap-index.xml`. Same in Bing Webmaster Tools (imports from GSC).
2. Social preview upload (if Step 3 of Task 6 found none): repo Settings → Social preview → upload `og-card.png`.
