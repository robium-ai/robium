# Application publication contract

The public project is composed from existing repository-owned sources. Do not
add another all-purpose page manifest.

## Source ownership

| Source | Owns | Does not own |
| --- | --- | --- |
| App `robium-app.yaml` | ID, name, outcome summary, maturity, tags, runtime, requirements, hosted capability, startup/session limits | Current production enablement, article prose |
| App `docs/case-study.md` | Article title/summary, kind, voice, author, dates, tags, hero/social media, portable prose | Runtime limits or production capacity |
| Website publication registry | Approved app/article/demo IDs and current live availability | Application capability or evidence results |
| Orchestrator registry | Derived provider/runtime configuration | Editorial copy and catalog presentation |

## Generated application record

At website build time, merge the application metadata and matching article
frontmatter on the app ID. The resulting typed record feeds:

- application and demo catalog cards;
- the overview hero and local/live choices;
- shared project identity and Overview / Live / Guide navigation;
- canonical URLs, social images, and structured metadata;
- the live-workspace adapter configuration; and
- article-to-demo/source cross-links.

Build failure is preferable to silently joining mismatched IDs or missing
required media. Site publication state can intentionally omit a valid app.

## Article frontmatter

The portable case study uses the Robium editorial fields already established
by the article voice standard:

```yaml
---
title: A specific article headline
summary: One or two sentences for cards and metadata.
kind: tutorial
voice: technical
author: Robium team
app: application-id
date: 2026-08-28
tested: 2026-08-28
tags: [robotics, simulator]
hero: assets/gifs/verified-run.gif
hero_alt: What the verified run visibly demonstrates
social_image: assets/stills/result.png
featured: false
---
```

Keep the body portable Markdown. Relative app asset references are rewritten by
the website ingestion step; site components, HTML layout, and publication-only
copy do not belong in the source article.

## Reusable UI boundary

The shared layer owns project identity, tabs, availability, try-live/run-local
cards, lifecycle status, boot logs, restart/stop behavior, and responsive frame
layout. A viewer adapter owns only how to form and render its capability URL.
Optional evidence sections are application-specific consumers of the shared
shell, not forks of it.

The live page can use a darker working canvas than the overview and article.
Carry the same typography, accent, border treatment, status vocabulary, and
navigation through both modes so the user stays inside one project.
