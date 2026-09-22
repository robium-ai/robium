# Transcript and learning retention

Transcripts are evidence, never prompt context. Dated learnings are local
staging — gitignored, and deleted once distilled.

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

Add `--learnings` to classify the dated learning files in the same run. A
learning is eligible only when every `lrn-` entry it defines is cited by an
`absorbed` or `rejected` observation; an uncited entry keeps its file forever.
Before letting one go, confirm what it taught survives somewhere a reader will
reach — the skill body for guidance, a `references/` file for conditional
detail, dead ends, and platform-specific values. A learning is not distilled
just because an observation went terminal.
