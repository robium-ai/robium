# Transcript retention

Transcripts are evidence, never prompt context.

- Keep a transcript while a queue flag or a local observation points to
  it. An observation links a transcript by citing it in `source:`.
- Run retention from the project that owns `.robium/transcripts`. If its
  observations live in the separate Robium checkout, keep the queue record
  annotated with the observation ID until that observation is resolved; this
  is the cross-repository retention link.
- When a finding is absorbed or discarded, delete its observation and remove
  the processed queue record. The transcript is then unreferenced and eligible
  for cleanup.
- Unreferenced transcripts expire after the repository's retention window;
  pending evidence always wins over age.
- From the Robium checkout, run
  `uv run scripts/engine/prune_transcripts.py --root <capture-project> --dry-run`
  first and review every keep/delete reason.
- To clean resolved evidence immediately, add `--max-age-days 0`; unresolved
  observations and queue records still protect their transcripts.
- Use `--apply` only after the report identifies the intended files. Retention
  cleanup does not authorize deleting unrelated logs or application data.

Before letting evidence go, confirm what it taught survives somewhere a reader
will reach — the skill body for guidance, or a `references/` file for
conditional detail, dead ends, citations, and platform-specific values.
