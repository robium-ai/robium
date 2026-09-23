# Repository mining workflow

Use the smallest run that answers the learning question.

## Survey one approved repository

- Clone into an ignored `.robium/mining/<org>/<repo>` directory and
  record the exact HEAD commit before reading.
- Inspect the tree, active build/run path, examples, tests, documentation, and
  license. For a large repository, a blobless clone keeps the survey cheap.
- Write a short ignored survey note naming only the areas that merit a deep
  read and why.
- Mark the source as exploring while work is active.

Typical git operations use the real upstream interfaces:

```bash
git clone --depth 1 <repo-url> .robium/mining/<org>/<repo>
git -C .robium/mining/<org>/<repo> rev-parse HEAD
```

Use `git clone --filter=blob:none` instead for a large tree when lazy blob
fetching is acceptable.

## Deep-read selected areas

- Trace a behavior through its entrypoint, configuration, implementation, and
  tests rather than collecting isolated snippets.
- Ask what decision the source made, what constraint explains it, and what
  observable evidence supports it.
- Compare the candidate with the current Robium catalog before choosing an
  observation target.
- Use `scripts/engine/placement.py` when ownership is ambiguous.

Draft external observations under the gitignored
`learnings/observations/<skill>.md` using the repository's current observation
schema. Include the pinned source commit, path, line range, and exact excerpt.

## Comparative run

- Select sibling repositories that independently address the same question.
- Record the shared pattern and meaningful divergences rather than producing a
  separate summary of each repository.
- Treat convergence as stronger evidence only when the implementations are
  genuinely independent.
- Route divergences to the umbrella skill that owns the decision surface.

## Re-crawl

- Fetch the previously recorded commit if a shallow clone no longer contains
  it, then compare it with the new pinned HEAD.
- Re-read only changed areas and any observation whose cited lines moved or
  disappeared.
- Mark affected observations for recheck rather than silently updating their
  citations.

## Verify and record

Run the repository's observation and citation checks against the exact draft
files. Discard a candidate whose source excerpt cannot be verified.

```bash
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining \
  learnings/observations/*.md
```

Update `learnings/SOURCES.md` with:

- crawl date and pinned commit;
- exploring, distilled, dropped, or recheck status;
- for `distilled`, the skill or reference files that retained the findings;
- any recheck needed because upstream changed.

Temporary clones and survey reports stay in `.robium/mining/` and out of the
committed plugin.

Finish by reporting: "Mining complete: saved N local observations (R ready, T
tentative). Next step: run the learning loop to distill the ready findings into
existing skills, or review any justified new-skill proposal." Offer to run that
next step in a background subagent, but wait for user approval.
