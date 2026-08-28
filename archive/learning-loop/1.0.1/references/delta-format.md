# deltas.yaml: the absorb/refine delta format

The only way absorb or refine touches skills/**: a deltas.yaml file fed to
scripts/engine/apply_deltas.py, which does the writing. Drafting agents
never edit a SKILL.md directly; they write this file and let the script
apply it. This reference documents the schema and the op semantics **as
implemented** (scripts/engine/apply_deltas.py), which evolved past the
original plan sketch during fix rounds; the differences are called out
below where they matter.

## Schema

```yaml
date: 2026-08-05            # optional; default today
deltas:
  - skill: nav2             # dirname under --skills-dir
    op: update              # add | update | retire | move | annotate
    anchor: costmap-inflation
    content: |
      - Nav2's default costmap YAML omits the inflation_layer block: add it
        (cost_scaling_factor: 3.0 worked) or the robot hugs obstacles. <!-- id: costmap-inflation -->
    reason: obs-nav2-007    # observation id; drives absorbed-marking + changelog
  - skill: ros2
    op: add
    section: Usage patterns # required for add; anchor comes from content
    position: bottom        # top | bottom (default bottom)
    content: |
      - New pattern text. <!-- id: new-anchor -->
    reason: obs-ros2-001
  - skill: nav2             # move is grouped under its SOURCE skill
    op: move
    anchor: dds-domain-id
    to_skill: ros2           # destination skill dirname
    to_section: Key directives # destination section (must already exist)
    force: false             # optional; only meaningful on retire
    reason: obs-nav2-012
  - skill: nav2
    op: annotate
    file: examples/costmap.yaml   # path stays inside the skill dir
    find: "status: unverified"
    replace: "status: verified (2026-08-27, robium-apps/robot-navigation)"
    reason: obs-nav2-013
bump: {nav2: minor}         # optional per-skill override: build|minor|major
evals_confirmed: []         # skills whose major bump has had evals.yaml re-confirmed
```

Ops are grouped by `skill` into one batch per skill; a `move` op is grouped
under its **source** skill like any other op, even though it also writes a
destination.

## The five ops

- **add**: inserts `content` into an existing `## <section>` at `position`
  (top or bottom of the section, default bottom; at `position: bottom`,
  trailing blank lines before the next heading are skipped so new content
  lands right after existing content rather than after the gap). No
  `anchor` field; the anchor id lives inside `content` itself. Missing
  section → no-op.
- **update**: replaces the full anchor block (the bulleted line plus any
  more-indented continuation lines) found by `anchor`. `content` **must**
  still carry that same anchor id comment; dropping it is a refusal, not
  a no-op, because it would silently orphan the ledger entry. Missing
  anchor → no-op.
- **retire**: deletes an anchor block outright. Refused when the skill's
  evidence.yaml shows `helpful > 0` for that anchor, unless the op sets
  `force: true`; a block with proven value can't be silently deleted.
  Ledger key is removed on apply.
- **move**: relocates an anchor block (and its ledger entry) from the
  source skill to the `to_skill` and `to_section` fields. Every move in a batch that shares
  a `to_skill` merges into **one** destination write: one archive snapshot,
  one version bump, one changelog line, no matter how many anchors land
  there. If `to_skill` or `to_section` doesn't exist, that move degrades to
  a no-op and leaves **zero** destination artifacts; nothing is written to
  the destination just because a sibling move in the batch succeeded.
- **annotate**: two shapes. Anchor-targeted (`anchor` + `content`) behaves
  like `update` but is bump-classified separately (see below). File-targeted
  (`file` + `find` + `replace`, no anchor) does a plain find/replace inside
  another file in the same skill directory, e.g. promoting an example's
  `status: unverified` marker. The path is resolved with `os.path.realpath`
  and refused if it would escape the skill directory.

## Refusals vs no-ops

A **no-op** means the op's target wasn't there (missing anchor, missing
section, missing to_skill or to_section): reported, nothing written,
never blocks anything else. A **refusal** is different: content dropping
its anchor id, an existing archive snapshot at the skill's current version
(a prior run bumped without merging; rebase first), a retire against
`helpful > 0` without `force`, the merged body (SKILL.md content *including
the new changelog line*) hitting the 500-line cap, or a major bump on a
skill not listed in `evals_confirmed` (the co-evolving-evals rule).

**A refusal blocks its whole skill's batch**: every sibling op for that
skill, even ones that applied cleanly, gets reported as "blocked: batch
contains a refused op" and nothing for that skill is written. No-ops never
block; they just sit in the report as their own rows. A move's destination
problem (missing to_skill/to_section is a no-op; a taken archive slot or a
cap breach at the destination is a refusal) refuses the **entire source
batch**, not just the move; a move is atomic across both skills, so
nothing on either side is written unless every side is clean.

## Bump inference and the changelog

Any batch where an add/update/move/retire actually applied bumps **minor**;
a batch where only `annotate` ops applied bumps **build**; **major** is only
reachable via the `bump:` override, and is itself refused unless the skill
appears in `evals_confirmed`. The changelog line is inserted directly below
the `## Changelog` heading (any blank lines or the standing
`<!-- One dated line per battle-tested change... -->` convention comment
already there are skipped over first, so the new entry lands right after
that comment rather than jumping in front of it), and names each retired
or moved anchor in plain text (`retire costmap-inflation`, `move-out
dds-domain-id to ros2`, `move-in dds-domain-id from nav2`), never in
backticks. Same-destination moves get one changelog line covering every
anchor that landed there in that run. The entry's shape is fixed:
`- <new-version> (<date>): <op summaries, semicolon-joined> [reasons:
<comma-joined reason ids>] (applied by apply_deltas)`; the trailing
`(applied by apply_deltas)` marker is what lets a later growth-review pass
tell an engine-authored bump from a hand-authored one at a glance.

Late refusals (a batch that got past every op-level check but then breaches
the 500-line cap, fails the `evals_confirmed` major-bump rule, or hits a
destination-side breach on a move) do **not** use the "blocked: batch
contains a refused op" wording (that phrasing is reserved for op-level
refusals, C1 in the source). Instead every op in the batch is re-reported
with the specific breach note attached directly (e.g. "would breach
500-line body cap: split to references/", or "major bump without
evals_confirmed (co-evolving-evals rule)"); read the note text, not just
the refused/applied split, to tell which check actually failed.

## Dry-run and the report table

Running apply_deltas.py deltas.yaml --dry-run runs every check (refusals, no-ops,
cap, evals_confirmed) and prints the same markdown table
(`| skill | op | anchor | status | note |`) an absorb/refine PR body embeds,
plus a `bumped <skill>: old -> new (dry-run: not written)` line per skill,
without touching any file. A real run prints the identical table (without
the dry-run suffix) and, for any reason id that could **not** be resolved
(the observations file for that id's skill stem doesn't exist, or the id
isn't found in it), an "absorption notes" list naming the failure; no
notes section means every reason id was marked absorbed cleanly.
`mark_absorbed` only ever writes on success and only ever reports on
failure; reading an empty notes list as "nothing was marked" is backwards
and risks a hand-edit of an observation's status, which absorb must never
do. Always dry-run before a real apply; the report is the thing to read
before committing to a branch.

## Where deltas files live

Committed deltas go to learnings/deltas/YYYY-MM-DD-<topic>.yaml; scratch or
dry-run experiments (throwaway drafts while iterating on a batch) may live
anywhere gitignored; they don't need the dated-topic naming since they
never land in a PR.

Adapted from scripts/engine/apply_deltas.py at Task 7 authoring (2026-08-02).
