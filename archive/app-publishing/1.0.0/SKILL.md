---
name: app-publishing
version: 1.0.0
description: >
  Post-build editorial publication for an already implemented and smoke-tested
  robium reference application: compose its catalog entry, overview, working
  surface, article/guide, source links, media, and metadata from
  repository-owned facts. Use when: 'publish this finished application', 'add
  this tested project to robium.ai', 'unify this existing project's public
  pages', or 'turn this verified project into an article and showcase'. Load
  only after the application smoke passes. Not for: planning, choosing a stack,
  coding, or starting robot behavior (architect), nor gateway, orchestrator, or
  cloud runtime mechanics (live-demo).
---

# app-publishing

Turn a verified reference application into a consistent public project without
hand-maintaining a second copy of its facts. The app manifest owns runtime and
capability truth, the portable case study owns narrative and media metadata,
and the website composes both into overview, live, and guide surfaces.

## When to use this skill

- Adding a finished application to the Robium application/demo catalogs.
- Creating or revising an app-backed article or technical guide.
- Replacing one-off demo pages with shared project identity, navigation, and
  reusable live-workspace components.
- Cross-references: use `live-demo` for session allocation, gateway claims,
  readiness, capacity, shutdown, or viewer transport; use `testing` to decide
  whether the app is ready to publish; use `skill-author` only when changing
  this skill rather than publishing an application.

## Key directives

- **Delegation posture: embed + links.** Embed Robium's repository-to-website
  publishing contract here; link to Hugging Face Spaces and Gradio for the
  upstream repo-backed project and embedded-app patterns.
- **One app, one identity, multiple surfaces.** <!-- id: one-app-one-public-identity --> Overview, live workspace,
  guide, cards, metadata, and source links share the app ID and a common
  project header. They may have different routes and layouts; they must not
  look like unrelated products.
- **Facts stay with their owner.** <!-- id: publishing-facts-stay-with-owner --> Runtime, requirements, tags,
  hosted capability, startup estimate, and session limits come from
  `robium-app.yaml`. Article title, summary, author, hero, social image, and
  prose come from the app's portable case study. Site-owned publication state
  says what robium.ai currently exposes. Do not create a parallel page
  manifest that repeats those values.
- **Working surfaces lead with the work.** <!-- id: live-surface-leads-with-work --> A live route opens on the
  controls, boot state, logs, or viewer. Marketing explanation belongs in the
  overview or guide, not ahead of the primary interaction.
- **Publishing never weakens the evidence bar.** <!-- id: publishing-keeps-evidence-bar --> Media and performance
  claims come from real runs; simulations, fixtures, recorded evidence, and
  live hardware are labeled honestly. A polished card is not evidence.

## Quick start

1. Confirm the app's normal smoke test and hosted `make demo-smoke` (when it has
   a hosted demo) are green.
2. Complete the app's `robium-app.yaml` and `docs/case-study.md`. Keep article
   media below the app's `assets/` directory and reference it with portable
   relative Markdown paths. `robium-ai app new ... --from ...` creates an
   ID-safe case-study starter so copied application prose cannot leak into the
   new project; replace its TODOs only with verified results.
3. Validate the application metadata with the existing CLI:
   ```bash
   npx robium-ai app validate
   ```
4. Build the website against the sibling apps checkout, then run its smoke:
   ```bash
   ROBIUM_APPS_DIR=../robium-apps npm run build
   make smoke
   ```
5. Inspect the generated overview, live, and guide routes locally. Deployment,
   paid capacity, image publication, and production resource changes remain
   separate explicit actions.

## Decision guidance

**Choose the surface without duplicating the project.**

| Visitor intent | Surface | Default first viewport |
| --- | --- | --- |
| Understand the application | Overview | Real preview, outcome, availability, local and live paths |
| Try it | Live | Session state or working viewer, with guide/source links nearby |
| Learn or reproduce it | Guide | Article title and prose inside the same project identity |
| Evaluate the catalog | Card | Name, outcome, maturity, requirements, availability |

**Choose shared code vs an app adapter.** Shared project identity, navigation,
try-live/run-local cards, lifecycle state, boot log, stop/restart behavior, and
iframe framing belong in reusable components. App-specific evidence or a
special viewer belongs in a small adapter or optional section. Promote a
pattern only after a second consumer exists; do not force genuinely different
robot interactions through a lowest-common-denominator UI.

**Choose metadata ownership.** See `references/publication-contract.md`. If a
field changes when the application changes, it belongs with the application.
If it changes when editorial framing changes, it belongs in case-study
frontmatter. If it changes because production capacity is paused or a page is
not yet approved, it belongs to the site's publication registry.

**Choose a live integration.** Reuse the hosted workspace shell and provide a
viewer adapter for Gradio, Lichtblick/Foxglove, or a custom capability URL.
The publishing layer renders the shell; the `live-demo` skill owns the
allocation and gateway state machine beneath it.

## Platform gotchas

- **Committed fallbacks can hide stale source.** The website retains generated
  article/app data so it can build without a sibling checkout. A publication
  check must also build with `ROBIUM_APPS_DIR` pointed at the current apps repo,
  or stale fallbacks can pass locally.
- **Hosted capability is not current availability.** `demo.hosted: true` means
  the app supports the hosted contract. It does not mean paid capacity or a
  production image is enabled today. Render current availability from the
  site-owned publication state.
- **Never allocate on catalog or overview load.** Cards and overview pages use
  static facts. A live instance starts only after an explicit visitor action;
  otherwise casual page views can create cost.
- **Embedded apps keep their own styling boundary.** Gradio documents web
  components and iframes as supported embed shapes. Parent CSS selectors must
  not leak into the embedded UI; scope site styles to the surrounding shell.

## Customization

- A project may use a light editorial overview and a dark live canvas while
  retaining the same typography, accent, border, status, and navigation
  language. Visual consistency does not require making a robot viewer look
  like article prose.
- A project without hosted capacity still gets an overview and guide. Keep the
  Live tab visibly unavailable or route it to recorded proof rather than
  removing the project identity.
- An evidence-heavy application can add a project-specific section below the
  shared overview. Its evidence references stay in the app or an immutable
  dataset; the website contains presentation code, not copied result truth.

## References

- `references/publication-contract.md`: source ownership, generated surfaces,
  article frontmatter, and the reusable project-shell boundary.
- Upstream: [Hugging Face Spaces overview](https://huggingface.co/docs/hub/spaces-overview)
  (repo-backed app/source pattern), [Hugging Face Spaces configuration](https://huggingface.co/docs/hub/spaces-config-reference)
  (repository metadata), and [Gradio sharing and embedding](https://www.gradio.app/guides/sharing-your-app)
  (web component/iframe integration), checked 2026-08-28. Sibling skills:
  `live-demo` (runtime lifecycle), `testing` (publication entry bar), and
  `skill-author` (skill changes).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.0 (2026-08-28): created from the robium.ai AppRecord/project-shell and
  shared ACT/PushT live-workspace implementation; separates public project and
  article composition from live-demo runtime lifecycle and adds an ID-safe
  case-study starter to app scaffolding.
