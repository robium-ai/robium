# GitHub presence — design

Date: 2026-07-20
Status: approved (user, in-session)

Modeled on research of huggingface/skills (10.8k★: per-agent install sections,
skills table, contribute section), upstash/context7 (59k★: badge row,
❌ Without / ✅ With opener, per-editor install, community links), and the
upstash org profile (`.github` repo → profile/README.md = the org landing).

## Decisions

1. **Flagship repo = this one, `robium-plugin`** (github.com/robium-ai/
   robium-plugin). ~~Briefly renamed to `robium` on 2026-07-20~~ — reverted
   same day at the user's request; the name stays `robium-plugin`. All
   references (plugin README install line, .claude-plugin manifests, website
   REPO consts/Nav/Footer, org profile, robium-applications READMEs) point at
   robium-ai/robium-plugin.
2. **Org landing = new `robium-ai/.github` repo** with profile/README.md:
   name + one-line pitch, badges, `npx robium-ai install`, repo map table
   (robium, robium-cli, robium-applications, robium-website, robium-docs),
   community links (robium.ai · Discord · Hugging Face org). Pinned repo
   order: robium → robium-cli → robium-applications → robium-website.
3. **Repo metadata on all five repos** (all empty today): description,
   topics, homepage=https://robium.ai.
4. **Flagship README v1 restructure** (context7/HF pattern, honest-content
   rule holds): header + badge row (website, npm robium-ai, MIT, Discord) →
   pitch → per-agent install (Claude Code now; Cursor/Gemini coming-soon,
   mirroring the CLI) → skills table (kept) → reference apps → contributing
   pointer + community links. The ❌/✅ comparison and demo GIF land later
   when real transcript/video assets exist (launch-readiness backlog items
   2–3) — never fabricated for structure's sake.

## Out of scope

CONTRIBUTING.md + issue templates + Discussions + Issues migration (launch
backlog items 7–9, own pass); robium-docs content; star-history chart.
