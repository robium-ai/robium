# Promoting a finding

Use the evidence ladder to keep cheap signals from becoming permanent advice.

## Queue flag to observation

- Capture lives under `.robium/` in the project where the hook ran. Local
  observations live in the editable Robium checkout; discover it with
  `npx robium-ai workspace --json` when it is not already the current repo.
  They are gitignored working files; never edit a plugin cache.
- A queue flag is only a pointer into a transcript. Discard context-free shell
  noise and expected probes.
- Queue types are capture hints, not observation signals. Preserve
  `user-correction`; classify `remember`, `guardrail`, `error`, and `positive`
  from the actual evidence as one of the schema's legal signals, or discard
  them when they do not express reusable knowledge.
- Record a finding only when the source shows what was expected, what happened,
  and which skill or `[none]` is implicated.
- One user correction can be strong evidence. Otherwise prefer two independent
  occurrences or a complete failure/fix/check trail.
- An official source can support mined knowledge when it directly matches the
  claim and current platform.
- Missing proof stays `tentative`; uncertainty is not a reason to rush an edit.

An observation must carry enough quote, source, and conditions for review.
Anything worth keeping after absorption must move into the skill body or a
focused reference before the observation and raw transcript are deleted.

When capture and observations live in different repositories, keep the
processed queue record and add `"observation": "obs-..."` until that
observation is absorbed or discarded. The queue record protects the app-local
transcript from age and size pruning. Remove that record when the observation
is deleted; an unmarked record remains pending work.

The observation schema and legal statuses in `learnings/observations/README.md`
are the source of truth.

## Observation to skill

- Only `status: ready` is eligible for absorption.
- Re-read the cited transcript or source; do not absorb a summary from memory.
- Find the lowest skill that owns the decision. Split a finding when routing
  belongs to an umbrella skill but mechanics belong to a tool skill.
- Make the smallest edit that carries the knowledge, and remove superseded or
  duplicated guidance in the same change when safe.
- Keep exact values attached to their observed robot, platform, workload, and
  verification conditions.
- Edit the live skill directly with the normal repository editing tools. In the
  same learning run, validate the guidance, move any reusable supporting
  material into the skill, and then delete the absorbed observation. If the
  finding is rejected, delete it without changing the skill.

## Review

- Show the observation, owner, intended edit, and evidence together.
- External contributors and unattended runs stop at a human-reviewed PR.
- A maintainer's direct-edit authorization applies only to the current task and
  does not authorize pushes, publication, deployment, or paid work.
