# Learning-engine guidance

This file applies under `learnings/` and to `scripts/engine/` work. Load the
`learning-loop` skill for consolidation, absorption, refining, experiments, or
retention maintenance.

## Capture without interrupting builds

- Hooks silently queue corrections/errors and archive session transcripts.
- Do not stop implementation to write a learning after every event. At a
  natural milestone, batch meaningful flags into the schema in `README.md` and
  discard context-free noise.
- A retro is useful only when it carries a real signal; clean per-skill score
  lines are not mandatory.
- Project-local facts belong in the owning app/site documentation, not in the
  cross-project learning corpus.

## Promotion and absorption

- Queue flags are pointers, not knowledge. Promote only when the transcript
  establishes expected behavior, actual behavior, and a skill or `[none]`.
- Only `status: ready` observations can be absorbed. Preserve tentative,
  rejected, and absorbed entries as the dedup/audit trail.
- Consolidation may change `learnings/`, observations, evidence, and eval
  sidecars; it never changes `skills/`.
- During an app build, capture and continue. Absorb between builds unless the
  maintainer explicitly requests a skill change in the current conversation.
- Automated/unrequested absorption ends in a PR. A maintainer-authorized direct
  main edit still uses archive/version/changelog/validation mechanics.

## Transcript retention

Transcripts are evidence, never prompt context. Keep a transcript while queue
flags or tentative/ready observations depend on it. After linked observations
are absorbed/rejected and the change lands, run the retention tool to delete
the raw transcript. Unreferenced transcripts expire after 14 days.
