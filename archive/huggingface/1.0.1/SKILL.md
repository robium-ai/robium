---
name: huggingface
version: 1.0.1
description: >
  HuggingFace ecosystem for robotics projects: hub datasets and models for
  robot learning, and demo Spaces. DELEGATES: for hub mechanics
  (download/upload/auth/jobs), install HuggingFace's own skills — /plugin
  marketplace add huggingface/skills, then /plugin install
  hf-cli@huggingface-skills — and defer to them; this skill adds only the
  robotics-specific layer (which datasets and models matter for manipulation
  and navigation, robotics dataset conventions on the hub). Use when: HF hub
  operations inside a robotics project, 'huggingface dataset for robots',
  'upload the policy to the hub', and the HF skills aren't installed yet.
  Pairs with lerobot and data.
---

# huggingface

The robotics-specific Hub layer for robium — this skill deliberately does
*not* teach Hub mechanics itself. HuggingFace ships and maintains its own
skill catalog (`huggingface/skills` on GitHub, 25 skills as of 2026-07-10
— counted directly from the repo's README skills table, fetched directly
on 2026-07-10) covering
auth, download/upload, repo management, Jobs, and every other Hub operation
in depth and kept current with the live `hf` CLI. Re-teaching any of that
here would drift out of sync with the upstream catalog almost immediately —
so the first thing this skill does, every time, is make sure that catalog is
actually installed, then get out of the way. What's left for this skill to
own is narrow: which datasets and models matter for robium's two verticals
(manipulation, navigation), and the Hub-side conventions robotics data
follows there.

## When to use this skill

- Any Hub operation inside a robotics project where the HuggingFace skills
  aren't installed yet — install them first (see Key directives), then use
  them directly rather than working around this skill.
- Deciding *which* dataset or model on the Hub fits a manipulation or
  navigation task, or understanding the Hub-side conventions
  (`LeRobot` tag, dataset card fields) a robotics dataset follows.
- The trigger phrases in the description: HF hub operations inside a
  robotics project, 'huggingface dataset for robots', 'upload the policy to
  the hub'.
- Cross-references — go to the sibling skill instead when the question is:
  - **Any actual Hub mechanic** — auth, `hf download`/`hf upload`, repo
    creation, Jobs, Spaces deployment — → the installed HuggingFace skills
    (`hf-cli` and whichever others `hf skills add` pulls in). This skill
    only gets you there; it does not re-teach the commands.
  - **The LeRobotDataset format itself** (directory layout, recording,
    training/eval CLI) → `lerobot`. This skill only covers the Hub-side
    conventions a LeRobot dataset follows once it's there, not the format's
    internals.
  - **Whether to source data from the Hub at all vs. sim-generation or
    teleop** → the `data` umbrella skill. This skill assumes "use the Hub"
    is already the answer and covers what to look for once there.
  - **The whole-stack decision this feeds into** → `architect` (routes
    here).

## Key directives

- **Delegation posture: delegate.** This is robium's delegation showcase —
  install HuggingFace's own skill catalog before doing any Hub mechanic, and
  defer to it completely rather than approximating a command from memory.
  This skill's own content is limited to the robotics-specific layer on top
  (Usage patterns below); it is not a substitute for the upstream skills.
- **Install the upstream catalog before any Hub operation, if not already
  present:**

  ```
  /plugin marketplace add huggingface/skills
  /plugin install hf-cli@huggingface-skills
  ```

  `hf-cli` is the recommended bootstrap skill — it's generated from the
  locally installed `hf` CLI, so it stays current across CLI releases rather
  than going stale the way a hand-written command list would. Confirmed via
  direct fetch of the `huggingface/skills` repo's README and its
  `.claude-plugin/marketplace.json` on 2026-07-10 — the marketplace manifest's
  `name` field is `huggingface-skills`, which is the identifier the
  `@huggingface-skills` suffix above resolves against once the marketplace is
  registered (the README's own prose examples elsewhere in that repo show
  `@huggingface/skills`, the GitHub path, instead — the manifest's `name`
  field is the one that actually resolves, and the 2026-07-10 session's own
  environment, which already has that marketplace's skills installed, shows
  them namespaced `huggingface-skills:<skill>` rather than
  `huggingface/skills:<skill>`, corroborating it; re-verify against the live
  manifest before relying on either form in a script).
- **Pull in additional upstream skills on demand, not all at once.** Once
  `hf-cli` is installed, `hf skills add <skill-name>` installs any other
  skill from the same catalog (e.g. a Spaces or dataset-viewer skill) —
  confirmed via direct fetch of the upstream README on 2026-07-10. Install
  only what a given task needs rather than the whole catalog up front.
- **Never re-teach Hub auth, transfer, or Jobs mechanics in this skill.**
  If a task needs `hf auth login`, `hf download`, `hf upload`, or a Jobs
  invocation, that command comes from the installed upstream skill, not from
  this one — even a single-line example here would drift out of sync with
  the CLI faster than the upstream generated skill does.
- **Never write dataset/model facts (episode counts, licensing, which
  datasets exist under a tag) from memory.** Hub content changes constantly
  — confirm a specific dataset or model's current state against its Hub page
  or the searches below before planning a project around it, the same
  standard `data` holds sourcing decisions to.

## Quick start

**1. Check whether the upstream HuggingFace skills are already installed**
for this project/session — if `hf-cli` (or another `huggingface-skills:*`
skill) is already available, skip straight to step 3.

**2. If not installed, run the two commands in Key directives** to register
the marketplace and install `hf-cli`.

**3. Use the installed skill directly** for the actual Hub operation (auth,
download, upload, search) — this skill's job ends here for mechanics.

**4. For the robotics-specific question** ("which dataset/model fits this
task", "what does a LeRobot dataset's Hub listing look like") — see Usage
patterns below.

## Usage patterns

**Finding a manipulation dataset or model.** Search the Hub's `LeRobot` tag
(`huggingface.co/datasets?other=LeRobot` — confirmed via direct fetch this
session to be a live, populated filter) for datasets already in the
LeRobotDataset format; Open X-Embodiment datasets converted to that format
are collected under the `lerobot/open-x-embodiment` collection specifically
(confirmed via direct fetch of that collection page on 2026-07-10 — roughly
60 contributed datasets from multiple institutions, in LeRobot format).
Pretrained manipulation policies (ACT, Diffusion, Pi0-family, SmolVLA and
others) are hosted the same way, under repo IDs like `lerobot/diffusion_pusht`
— the exact policy families and hub-hosted checkpoints are `lerobot`'s
territory to enumerate (see that skill's Quick start); this skill's job is
pointing at the tag/collection, not re-listing every checkpoint.

**Finding a navigation dataset.** Navigation has no single equivalent of the
`LeRobot` tag — search the Hub's general robotics/SLAM-tagged datasets
instead, and check embodiment/sensor fit before committing, per `data`'s
embodiment-match directive. Don't assume a manipulation-oriented search
pattern (the `LeRobot` tag, a single owning collection) transfers directly.

**Reading a robotics dataset's Hub-side shape before pulling it.** A
LeRobotDataset repo on the Hub carries its `info.json`/dataset-card metadata
(robot type, fps, camera/state/action feature shapes) alongside the
Parquet+MP4 data files — inspect that metadata (via the installed
`huggingface-datasets`/`hf-cli` skill, or the Hub's own dataset viewer)
before assuming a dataset's action space matches the target robot; `lerobot`
owns the format's internals once you're inside it.

**Uploading a trained policy or dataset.** Once a policy or dataset exists
locally, the actual push is a Hub mechanic — use the installed `hf-cli`
skill's upload command. This skill's only addition on top is: tag it so it's
discoverable the way the datasets above were found (the `LeRobot` tag for a
LeRobotDataset-format push, a clear model card for a policy checkpoint).

## Platform gotchas

- **The upstream skill catalog is a separate plugin install, not bundled
  with robium.** A fresh environment needs the two commands in Key
  directives run once before any Hub mechanic works through skills at all —
  don't assume `hf-cli` is present just because this skill is.
- **Auth is entirely the upstream skill's territory.** Whether Hub access
  needs a token, which scopes it needs, and how it's configured locally are
  all `hf-cli`'s concerns — this skill has no auth guidance of its own to
  fall back on if that skill isn't installed.

## Customization

- **Different embodiment or task:** re-run the `LeRobot`-tag/Open
  X-Embodiment search (manipulation) or the general robotics/SLAM search
  (navigation) for the new target, and re-check embodiment fit — a dataset
  found for one robot/task pairing is not assumed to transfer, per `data`'s
  embodiment-match directive.
- **Private or org-scoped datasets/models:** access and visibility are Hub
  auth mechanics — handled entirely by the installed upstream skills, not
  by anything in this one.

## References

- Upstream: [huggingface/skills GitHub
  repo](https://github.com/huggingface/skills) (install story, skill
  catalog, and marketplace manifest — fetched directly on 2026-07-10,
  including its `.claude-plugin/marketplace.json`), [Hub dataset filter:
  LeRobot tag](https://huggingface.co/datasets?other=LeRobot) (fetched
  directly on 2026-07-10), [Open X-Embodiment (LeRobot format)
  collection](https://huggingface.co/collections/lerobot/open-x-embodiment)
  (fetched directly on 2026-07-10), [Hugging Face Hub dataset docs](https://huggingface.co/docs/hub/en/datasets-adding)
  (upload/format conventions, fetched directly on 2026-07-10). Sibling
  skills: `lerobot` (LeRobotDataset format, training/eval, and the policies
  hosted under the `lerobot` Hub org), `data` (sourcing strategy — decides
  *whether* the Hub is the right source before this skill's search patterns
  apply), `architect` (routes here).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.0.1 (2026-07-12): skill-refiner run 1 — provenance claims date-stamped ('this session' → 2026-07-10, the authoring session) so the staleness sweep can age them.
