---
name: app-publishing
version: 2.0.0
description: >
  Publish an implemented, smoke-tested Robium application as one coherent
  public project: write or revise its product-lab article, prepare real-run
  media and explanatory assets, apply the Robium editorial cobalt theme, and
  compose catalog, overview, live, guide, and social surfaces from
  repository-owned facts. Use when: 'publish this finished application',
  'make this article sound human', 'unify the demo and guide', 'create article
  assets', 'apply the Robium writing style', or 'turn this tested app into a
  showcase'. Load only after the application smoke passes. Not for: planning
  or coding robot behavior (architect), generic site design, nor gateway,
  orchestrator, or cloud runtime mechanics (live-demo).
---

# app-publishing

Turn a tested reference application into a public project that reads and looks
like Robium without separating its story from its source. The app manifest
owns runtime facts. Its portable case study owns the article and media. The
website composes those sources into overview, live, guide, catalog, and social
surfaces.

## When to use this skill

- Publishing or refreshing a finished application on robium.ai.
- Writing or editing an app-backed article in the Robium product-lab voice.
- Producing a real-run hero, system diagram, social card, or optional
  conceptual illustration for an article.
- Replacing one-off public pages with the shared project identity and visual
  system.
- Cross-references: use `testing` before publication, `live-demo` for hosted
  session mechanics, and `skill-author` when changing this skill itself.

## Key directives

- **Delegation posture: embed + links.** Embed Robium's editorial, visual,
  media, and repository-to-website contract here. Link to upstream project and
  embed patterns where they clarify delivery.
- **Sound like a person who built the thing.** <!-- id: publishing-human-product-lab-voice --> Use direct sentences, specific
  observations, and restrained judgment. Do not use em dashes, inflated
  certainty, generic AI transitions, or repeated conclusions. See
  `references/editorial-system.md`.
- **One app, one identity, several surfaces.** <!-- id: one-app-one-public-identity --> Overview, live workspace,
  guide, cards, metadata, and source links share the app ID, project header,
  typography, color language, and status vocabulary.
- **Real runs establish what happened.** <!-- id: publishing-real-runs-ground-claims --> State the conditions and result
  plainly. Do not call every result proof or evidence. Generated art may
  explain a concept, but it must never resemble or replace application output.
- **Facts stay with their owner.** <!-- id: publishing-facts-stay-with-owner --> Runtime and capability truth comes from
  `robium-app.yaml`. Article framing and media come from
  `docs/case-study.md`. Current public availability comes from the website.
  Do not create a second all-purpose page manifest.
- **A structure is a checklist, not a voice.** <!-- id: publishing-spine-not-template --> Every article covers outcome,
  decision, system, run path, result, Robium's contribution, and limits. Its
  opening, section names, pacing, and emphasis should fit the application.

## Quick start

1. Confirm the normal app smoke is green. Confirm hosted `make demo-smoke` when
   the article discusses a hosted path.
2. Read the app manifest, README, architecture brief, case study, and current
   run artifacts before changing copy.
3. Draft against `references/article-starter.md`, then edit with
   `references/editorial-system.md`. Keep detailed troubleshooting and command
   catalogs in the README.
4. Prepare the standard media set with `references/asset-workflow.md`: one
   real-result hero, one system diagram, one 1200 by 630 social card, useful
   captions, and optional short motion.
5. Apply the tokens and component rules in `references/visual-system.md`.
6. Validate the application metadata and build the website against the current
   sibling apps checkout.
7. Inspect overview, guide, and live routes on desktop and mobile. Deployment,
   paid capacity, image publication, and production changes remain separate
   explicit actions.

## Decision guidance

**Choose the public surface by visitor intent.**

| Visitor intent | Surface | First viewport |
| --- | --- | --- |
| Understand the app | Overview | Outcome, real run, availability, local and live paths |
| Try it | Live | Session state, controls, viewer, or readable unavailable state |
| Learn or reproduce it | Guide | Natural headline, short deck, real result, useful narrative |
| Compare projects | Card | Name, outcome, maturity, requirements, availability |

**Choose the asset role before creating it.** Real-run media shows what the
application did. Explanatory diagrams show how it works. Identity assets make
the project recognizable. If an image could be mistaken for application
output, do not generate it. Use a real capture instead.

**Choose shared code vs an adapter.** Project identity, tabs, typography,
availability, session state, boot log, stop/restart behavior, article prose,
and responsive framing belong in shared components. A special robot viewer or
result panel belongs in a small app adapter. Promote a pattern after a second
consumer exists.

**Choose metadata ownership.** See `references/publication-contract.md`. A
field that changes with the application belongs with the app. A field that
changes with editorial framing belongs in case-study frontmatter. Production
enablement belongs to the site publication registry.

**Choose article depth.** Explain the decisions a reader cannot infer from the
README. Keep one tested quick start. Link to the README for command matrices,
setup variants, and troubleshooting. Remove a section if it only repeats the
deck, a prior section, or the conclusion.

## Platform gotchas

- **Committed fallbacks can hide stale source.** Build with `ROBIUM_APPS_DIR`
  pointed at the current apps repo before accepting a publication change.
- **Hosted capability is not current availability.** A hosted-capable app may
  still have paid capacity paused. The site registry owns that state.
- **Never allocate on catalog or overview load.** Start a paid session only
  after a visitor acts on the live route.
- **Embedded apps keep their styling boundary.** Apply the shared system to
  the surrounding shell. Do not leak parent selectors into Gradio, Foxglove,
  Lichtblick, or other embedded viewers.
- **A successful run has a scope.** Name the simulator or robot, model or
  policy, relevant hardware, scenario, and measurement window when they matter.
  Avoid broader claims than the recorded run supports.

## Customization

- Overview and guide use the light editorial surface. Live workspaces use the
  dark canvas while retaining cobalt, typography, status terms, and project
  navigation.
- App-specific sections and diagrams are welcome. Repeated brand copy,
  duplicated runtime facts, and one-off theme colors are not.
- Optional conceptual art uses the prompt recipe in
  `references/asset-workflow.md`. Save it under a new filename and caption it
  as an illustration. Omit it when a real capture or diagram communicates the
  idea more clearly.
- Editorial consistency is guidance-led. Do not add a publication blocker for
  style conformance unless the maintainer explicitly changes that policy.

## References

- `references/editorial-system.md`: product-lab voice, editing pass, headline,
  caption, and human-sounding examples.
- `references/visual-system.md`: canonical colors, type, shape, page modes,
  and component language.
- `references/asset-workflow.md`: real-run capture, diagram, social-card, and
  optional conceptual-art workflow.
- `references/article-starter.md`: portable frontmatter and flexible article
  spine for a finished application.
- `references/publication-contract.md`: source ownership and generated public
  surfaces.
- Upstream: [Hugging Face Spaces overview](https://huggingface.co/docs/hub/spaces-overview)
  for repository-backed projects and [Gradio sharing and embedding](https://www.gradio.app/guides/sharing-your-app)
  for embedded interfaces, checked 2026-08-28. Sibling skills: `testing`,
  `live-demo`, and `skill-author`.

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 2.0.0 (2026-08-28): expanded the publication contract into the Robium
  product-lab editorial and visual system, added real-run and generated-asset
  boundaries, and established a reusable article and media workflow.
- 1.0.0 (2026-08-28): created from the robium.ai AppRecord/project-shell and
  shared ACT/PushT live-workspace implementation.
