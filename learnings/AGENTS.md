# Learning-engine guidance

This file applies under `learnings/` and to `scripts/engine/` work. Load the
`learning-loop` skill for consolidation, absorption, refining, experiments, or
retention maintenance.

## Capture without interrupting builds

- Hooks silently queue corrections/errors and archive session transcripts.
- SessionStart may emit one count-only reminder per local day when the queue
  contains a correction, explicit remember/guardrail, or repeated error. It
  must not expose excerpts. Ask before learning, and on approval delegate the
  cycle to a background subagent while the main session continues.
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
- Hooks write `.robium/` in the project where the event happened. Write the
  local, gitignored observation in the editable Robium checkout, never a
  plugin cache. When
  those are different repositories, retain the processed queue record with
  its observation ID until the observation is resolved; it is what keeps
  the app-local transcript from being pruned.
- Only `status: ready` observations can be absorbed. After absorption, move
  every useful snippet, citation, caveat, or dead end into the skill or its
  `references/`, then delete the observation. Delete rejected observations.
- Consolidation may change observations, evidence, and eval sidecars; it
  never changes `skills/`.
- During an app build, capture and continue. Absorb between builds unless the
  maintainer explicitly requests a skill change in the current conversation.
- Automated or unrequested absorption ends in a PR. A maintainer-authorized
  direct-main edit still needs a concrete diff, evidence, and proportional
  validation, but live skills do not use versions or changelogs.

## Working state and durable state

`observations/<skill>.md` is local working state, not repository history. The
durable store is the owning skill and its support files. There is no
dated-learnings tier: capture goes to `.robium/queue.jsonl` during a build and
may become a `tentative` observation between builds. Any remaining
`learnings/YYYY-MM-DD*.md` files are gitignored leftovers — fold what is worth
keeping into an observation or a skill and delete them.

Distillation ends in the skill, not here. Conditional detail, dead ends, and
platform-specific values belong in the owning skill's `references/`. On
absorption, delete the local observation.

## Transcript retention

Transcripts are evidence, never prompt context. Keep a transcript while queue
flags or local observations depend on it — cite it as
`source: transcript <file>.jsonl#turn-N` so the retention tool can see the
link. After the citing observations are absorbed/discarded and deleted, remove
their queue records and run `scripts/engine/prune_transcripts.py` to delete the
raw transcript.
Unreferenced transcripts expire after 14 days.
