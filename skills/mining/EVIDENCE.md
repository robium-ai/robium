# Mining evidence and provenance

## Evidence strength

- **Official or vendor repository:** a pattern consistent with current official
  documentation may be ready immediately. Record how and when documentation
  was checked.
- **Independent community convergence:** the same pattern in at least two
  reputable, independent repositories can be ready through convergence.
- **Single community repository:** keep the observation tentative until another
  source or a Robium trial supports it.
- **Extracted example file:** keep it unverified until a Robium trial or focused
  verification runs it successfully, regardless of source authority.

Do not turn repository popularity or repeated forks of the same code into
independent evidence.

## Citation contract

- Pin a full commit for the crawl and use its short form in human-facing source
  labels only when unambiguous.
- Cite repository, commit, path, and line range plus a verbatim excerpt.
- Keep enough surrounding context to establish the decision without copying a
  large copyrighted section.
- Run `scripts/engine/verify_citations.py` against the pinned local clone. A
  failed match invalidates the candidate until corrected.

## Placement

- A better reusable approach maps to a better-method observation.
- Confirmation of current guidance maps to verified.
- A contradiction maps to wrong-guidance and preserves both sources.
- A finding with no owning skill maps to the new-skills observation area.
- Use `scripts/engine/placement.py` to expose overlaps, then choose the lowest
  skill that owns the decision.

When field-tested Robium guidance differs from an upstream idiom, keep the
field-tested path in the lead, explain the conditions under which upstream
failed, and flag the divergence for re-verification. Upstream may have changed.

## License boundary

- Prefer citations and links over copied code.
- Before vendoring, check the repository root and the specific subtree for
  additional licenses.
- Vendor only short, adapted material under a compatible permissive license
  such as MIT, BSD, or Apache, with attribution, upstream URL, and pinned
  commit.
- Do not vendor GPL code into the plugin.
- A vendored example starts unverified until exercised by Robium.

## New-skill findings

When no live skill owns a coherent set of findings, create an observation-level
proposal containing:

- the uncovered decision point;
- overlap with current skills;
- likely trigger boundary;
- the available evidence and its strength.

The proposal does not create the skill. Catalog expansion and authoring remain
separate human decisions.
