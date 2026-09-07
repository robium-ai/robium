---
name: learning-loop
description: Turn captured Robium experience into small, evidence-backed skill improvements.
---

# Learning loop

Capture is a lead, not knowledge. Promote it only when the evidence can improve
a future decision without injecting old conversations into new work.

## Capture without recall

- Hooks may queue corrections, failures, and transcript windows silently.
- Never insert queue items, observations, memories, or reminders into a new
  prompt. Read them only during an explicit consolidate, absorb, refine, or
  status task.
- Batch bookkeeping at a natural milestone. A command error or clean skill run
  is not automatically a reusable lesson.
- Keep project-specific facts in the application that owns them.

## Promote evidence

- Read the source transcript before turning a flag into an observation.
- Preserve what was expected, what actually happened, the evidence for the
  fix, and any dead ends that prevent repeating the mistake.
- Absorb only observations marked `ready`; uncertain material stays tentative.
- Deduplicate the finding before carrying it forward.
- Read [PROMOTION.md](PROMOTION.md) when deciding whether evidence is strong
  enough or which skill owns it.

## Change the least

- Put the finding in the lowest skill that owns the decision.
- Prefer correcting or replacing existing guidance over adding another rule.
- Keep the live entrypoint lean. Conditional commands, failures, tuning, and
  platform evidence belong in focused support files.
- Follow the `skill-author` quality bar and show the concrete diff with its
  evidence. Maintainer-authorized edits may land locally; unattended or
  unrequested absorption uses a branch and human-reviewed PR.
- Live skills are versionless and changelog-free. The legacy anchor/version
  delta applier is not the writer for the current skill format.

## Test according to risk

- Run the lightweight skill validator after an edit.
- Re-run an existing trigger or task check only when the changed guidance could
  affect it. Add a test only for a meaningful regression.
- For a contested edit, compare small alternatives against realistic requests
  and let a human choose. Do not preserve variants merely as ceremony.
- Read [TESTING.md](TESTING.md) for the optional eval format and safe task-check
  boundaries.

## Refine and retain

- Refinement starts with findings, not edits. Read [REFINING.md](REFINING.md)
  for the compact catalog review.
- Keep a transcript while a queue flag or nonterminal observation depends on
  it. Once linked observations are absorbed or rejected and the change has
  landed, read [RETENTION.md](RETENTION.md) and prune it deliberately.
- A status request may inspect queue size, ready observations, skill metrics,
  and transcript retention without changing anything.

## Done

- The future decision is clearer or safer with little added context.
- The observation points to evidence and its status reflects what landed.
- Relevant checks pass, and raw transcript evidence is kept only as long as it
  is still needed.
