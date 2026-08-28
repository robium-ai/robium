# Application publication contract

The public project is composed from repository-owned sources. Do not add a
second all-purpose page manifest.

## Source ownership

| Source | Owns | Does not own |
| --- | --- | --- |
| App `robium-app.yaml` | ID, name, summary, maturity, tags, runtime, requirements, hosted capability, limits | Current production enablement, article prose |
| App `docs/case-study.md` | Headline, deck, voice, audience, dates, hero, social image, portable prose | Runtime limits or paid capacity |
| App media and run records | Captures, diagrams, timings, conditions, result details | Marketing interpretation |
| Website publication registry | Approved IDs and current live availability | App capability or run results |
| Orchestrator registry | Derived provider and runtime configuration | Editorial copy and catalog presentation |

## Case-study frontmatter

Use app-relative media paths. `date` is the last substantive article revision;
`tested` records when the described application path last ran.

```yaml
---
title: A natural headline about the result or decision
summary: One compact sentence for cards and metadata.
collection: blog
category: tutorial
kind: tutorial
voice: product-lab
author: Robium team
audience: robotics-developer
level: intermediate
app: application-id
date: 2026-08-28
tested: 2026-08-28
tags: [robotics, simulator]
hero: assets/gifs/real-run.gif
hero_alt: What the recorded run visibly shows
social_image: assets/social/card.png
featured: false
---
```

The body remains portable Markdown. Relative app media references are rewritten
by website ingestion. Astro components, site-only HTML, and current production
availability do not belong in the source article.

## Generated application record

At website build time, join the app metadata and matching article frontmatter
on the app ID. The typed record feeds catalog cards, overview choices, project
navigation, canonical URLs, social metadata, and live-workspace adapters.

Build failure is preferable to silently joining mismatched IDs or missing
declared media. Site publication state may intentionally omit a valid app.

## Shared UI boundary

The shared layer owns project identity, tabs, availability, local/live choices,
lifecycle status, boot logs, restart/stop behavior, article typography, callout
language, and responsive framing. A viewer adapter owns only how it forms and
renders its capability URL. App-specific result sections consume the shared
shell rather than forking it.
