# Learning-engine guidance

This file applies under `learnings/` and to `scripts/engine/` work. Load the
`learning-loop` skill for consolidation, absorption, refining, experiments, or
retention maintenance.

## Capture without interrupting builds

- Hooks silently queue corrections/errors and archive session transcripts.
- Do not stop implementation to write a finding after every event. At a
  natural milestone, batch meaningful flags into `observations/<skill>.md` as
  `tentative` entries and discard context-free noise. A tentative entry needs
  only a status and a signal; consolidation completes it.
- A retro is useful only when it carries a real signal; clean per-skill score
  lines are not mandatory.
- Project-local facts belong in the owning app/site documentation, not in the
  cross-project learning corpus.

## Promotion and absorption

- Queue flags are pointers, not knowledge. Promote only when the transcript
  establishes expected behavior, actual behavior, and a skill or `new-skills`.
- Only `status: ready` observations can be absorbed. Preserve tentative,
  rejected, and absorbed entries as the dedup/audit trail.
- Consolidation may change observations, evidence, and eval sidecars; it
  never changes `skills/`.
- During an app build, capture and continue. Absorb between builds unless the
  maintainer explicitly requests a skill change in the current conversation.
- Automated or unrequested absorption ends in a PR. A maintainer-authorized
  direct-main edit still needs a concrete diff, evidence, and proportional
  validation, but live skills do not use versions or changelogs.

## One store

`observations/<skill>.md` is the only durable findings store. There is no
dated-learnings tier: capture goes to `.robium/queue.jsonl` during a build and
becomes a `tentative` observation between builds. Any remaining
`learnings/YYYY-MM-DD*.md` files are gitignored leftovers — fold what is worth
keeping into an observation or a skill and delete them.

Distillation ends in the skill, not here. Conditional detail, dead ends, and
platform-specific values belong in the owning skill's `references/`. On
absorption, compact the observation to its dedup stub per
`observations/README.md`.

## Transcript retention

Transcripts are evidence, never prompt context. Keep a transcript while queue
flags or nonterminal observations depend on it — cite it as
`source: transcript <file>.jsonl#turn-N` so the retention tool can see the
link. After the citing observations are absorbed/rejected and the change
lands, run `scripts/engine/prune_transcripts.py` to delete the raw transcript.
Unreferenced transcripts expire after 14 days.
