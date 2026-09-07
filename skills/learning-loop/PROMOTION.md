# Promoting a learning

Use the evidence ladder to keep cheap signals from becoming permanent advice.

## Queue flag to observation

- A queue flag is only a pointer into a transcript. Discard context-free shell
  noise and expected probes.
- Record a finding only when the source shows what was expected, what happened,
  and which skill or `[none]` is implicated.
- One user correction can be strong evidence. Otherwise prefer two independent
  occurrences or a complete failure/fix/check trail.
- An official source can support mined knowledge when it directly matches the
  claim and current platform.
- Missing proof stays `tentative`; uncertainty is not a reason to rush an edit.

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
  same reviewed change, mark the observation `absorbed YYYY-MM-DD` only after
  the guidance and its relevant checks have landed. The old anchor/version
  delta applier remains only for historical artifacts and experiments.

## Review

- Show the observation, owner, intended edit, and evidence together.
- External contributors and unattended runs stop at a human-reviewed PR.
- A maintainer's direct-edit authorization applies only to the current task and
  does not authorize pushes, publication, deployment, or paid work.
