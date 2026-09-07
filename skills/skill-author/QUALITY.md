# A practical quality bar

Use this as a review guide, not as a writing template. Skills can have different
shapes when their work calls for it.

## Discovery

- `name` matches the directory and uses lowercase kebab-case.
- `description` is short, specific, and discriminates the nearest adjacent
  skill.
- A likely user request can select the skill without an exhaustive keyword
  list.

## Entrypoint

- One organizing idea makes the guidance easy to remember and extend.
- The common path and important boundaries are visible without opening another
  file.
- Every instruction changes a capable agent's decision; generic coding advice
  and repeated repository policy are removed.
- Bullets sound like useful directions, not a compliance questionnaire.
- The entrypoint stays comfortably below the mechanical limit. Passing the
  limit is not evidence that the file is lean.

## Conditional depth

- Commands, failures, tuning, platform profiles, schemas, and long examples
  live in focused files when only some tasks need them.
- Each support file has a clear reason to load and is linked from a relevant
  decision point.
- Support files do not duplicate the entrypoint or reproduce an upstream
  manual.
- Existing examples and scripts remain only when they are reusable and their
  provenance or validation status is clear.

## Evidence and scope

- Stable concepts may be stated directly. Version-sensitive syntax and APIs
  point to current official documentation.
- Observed values name the robot, platform, version, workload, or measurement
  that produced them. They are never silently promoted into defaults.
- One proven application may justify a narrowly scoped platform or
  compatibility note. Require recurrence before turning it into common-path
  advice or a universal default.
- Adjacent skills are reached only after the relevant subsystem boundary has
  been identified.

## Testing

- The validator checks frontmatter, size, links, and optional eval structure.
  It deliberately does not prescribe headings or prose.
- Routing evals cover meaningful ambiguity, not every synonym in the
  description.
- Task checks verify user-visible behavior or a fragile reusable artifact, not
  Markdown wording.
- Manual review asks whether the skill helps a capable agent act better while
  loading less context.

## Repository contract

- Live skill frontmatter contains only `name` and `description`.
- Live skills do not carry versions or changelogs. Git history is the normal
  record of change.
- A skill may contain `SKILL.md` alone or the smallest set of support files it
  actually needs. No README or empty placeholder directories are required.
- Robium provides practical knowledge and real reusable examples, never an
  invented robotics DSL.
