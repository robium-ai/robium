# Transcript retention

Transcripts are evidence, never prompt context.

- Keep a transcript while a queue flag or a nonterminal observation points to
  it. An observation links a transcript by citing it in `source:`.
- A transcript becomes eligible for deletion when every linked observation is
  either rejected, or absorbed with its corresponding change landed.
- Unreferenced transcripts expire after the repository's retention window;
  pending evidence always wins over age.
- Run `uv run scripts/engine/prune_transcripts.py --dry-run` first and review
  every keep/delete reason.
- Use `--apply` only after the report identifies the intended files. Retention
  cleanup does not authorize deleting unrelated logs or application data.

Before letting evidence go, confirm what it taught survives somewhere a reader
will reach — the skill body for guidance, a `references/` file for conditional
detail, dead ends, and platform-specific values. A terminal observation does
not by itself mean the knowledge landed.
