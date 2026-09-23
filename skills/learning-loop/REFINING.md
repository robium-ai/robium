# Refining the catalog

Report findings before changing files. A clean pass should produce no churn.

## Remove harmful or unused guidance

- Start with user corrections and observations showing that a rule caused a
  bad decision.
- Remove advice that has no surviving use case rather than surrounding it with
  exceptions.
- Preserve the reason for a deletion in the review or owning skill when it will
  matter again; Git is the undo path.

## Collapse duplication

- Search entrypoints and support files for the same decision stated in several
  places.
- Keep the full guidance at the lowest owner. Leave a short conditional route
  only where another skill genuinely crosses that boundary.
- Merge whole skills only in a dedicated review of their trigger surfaces.

## Re-check volatile facts

- Find dated claims, package versions, flags, APIs, service limits, hardware
  requirements, and current-product statements.
- Verify them against current official sources or change the guidance to check
  the installed environment at use time.
- Do not refresh stable concepts merely to create activity.

## Reduce routine context

- Flag entrypoints that approach the validator limit, repeat their support
  files, or contain command catalogs needed only occasionally.
- Move conditional depth behind descriptive links; then remove the duplicate
  prose from the entrypoint.
- Review descriptions for overlap using realistic neighboring requests, not
  keyword count alone.

Run `uv run scripts/engine/skill_metrics.py` and its `--dupes` view as useful
seeds, then verify every finding by reading the affected skill.
