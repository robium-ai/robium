# Transcript retention

Transcripts are evidence, never prompt context.

- Keep a transcript while a queue flag, tentative observation, or ready
  observation points to it.
- A transcript becomes eligible for deletion when every linked observation is
  either rejected, or absorbed with its corresponding change landed.
- Unreferenced transcripts expire after the repository's retention window;
  pending evidence always wins over age.
- Run `uv run scripts/engine/prune_transcripts.py --dry-run` first and review
  every keep/delete reason.
- Use `--apply` only after the report identifies the intended files. Retention
  cleanup does not authorize deleting unrelated logs or application data.
