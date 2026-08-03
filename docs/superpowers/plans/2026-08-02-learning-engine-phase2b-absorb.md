# Learning Engine Phase 2b — Consolidate + Absorb + Recall — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the session-side half of the learning engine — recall hook, evidence-ledger tooling, delta format + apply_deltas, trigger-eval runner + flip gate, the learning-loop skill, the meta-skill restructure (skill-updater/skill-refiner retire), and the CLAUDE.md policy rewrite — then run the pipeline acceptance test on the real backlog, producing the Phase 2 exit-criteria PRs. Spec: `docs/superpowers/specs/2026-08-01-learning-engine-design.md` §5–§8, §13, §14, Phase 2 row of §15. Phase 2a (shared core + mining, merged as 0b1d202) is the prerequisite and is done.

**Architecture:** Deterministic scripts hold the pen (apply_deltas applies anchor-targeted ops with no-op fallback, snapshots, version bumps, changelog lines, sidecar updates; the trigger-eval runner + flip gate verify; the recall matcher injects `ready` observations into live sessions from a stdlib hook). LLM roles (consolidate, absorb-drafting) live as workflow prose in the new `learning-loop` umbrella skill and never touch `skills/**` directly — their output flows through the scripts into PRs. The human gate moves to `git merge` (CLAUDE.md rewrite, §7.3).

**Tech Stack:** Hooks stay stdlib-only Python ≥3.10 (they ship in the plugin). Repo-side engine scripts (`scripts/engine/`) may use pyyaml via PEP-723 headers run with `uv run` (same pattern as the validator). Tests: `uv run --with pytest --with pyyaml -m pytest tests/engine -v`. PRs via the authenticated `gh` CLI (robium-owner).

**Standing decisions (carried from 2a + new):**
- Engine tooling lives at `scripts/engine/` permanently; the learning-loop skill references it there (never relocates it). `skill_metrics.py` moves from the retiring skill-refiner to `scripts/engine/` in Task 8.
- The recall hook cannot import from `scripts/engine/` (installed plugins ship only `hooks/`); it carries its own minimal observation parser (small, deliberate duplication — noted in both files).
- Catalog count: 25 through Task 7, then 24 from Task 8 on (25 − skill-updater − skill-refiner + learning-loop; spec §13's arithmetic lands here).
- The restructure edits in Tasks 7–9 follow the OLD policy mechanics (snapshot + bump + changelog, same commit) — this plan's approval is the user gate for them. The NEW policy applies from Task 9's merge onward.
- Exit criterion "≥1 recall injection observed helping a live session" cannot be forced inside a plan; Task 12 demonstrates a real injection deterministically and the organic observation accrues afterward — recorded as such, not claimed.
- The `.robium/mining/` clones (citation re-verification during absorb) and `.robium/queue.jsonl` (38 flags) live in the MAIN checkout `/Users/robium/repos/robium/.robium/`; a worktree execution must use absolute paths to them.

## Global Constraints

- `hooks/scripts/*`: **stdlib only**, fail-open (`try/except → exit 0`), silent by default, write only under `<cwd>/.robium/` — plus hook-output JSON on stdout when injecting context (spec §5). Millisecond budget: no network, no LLM.
- `scripts/engine/*`: pyyaml allowed via PEP-723 header (`# /// script` + `dependencies = ["pyyaml"]`), executed as `uv run scripts/engine/<tool>.py`; plain `python3` still works for the stdlib-only ones (observations, verify_citations, placement).
- Test command: `uv run --with pytest --with pyyaml -m pytest tests/engine -v` from repo root. Validator after ANY `skills/**` change: `uv run skills/skill-author/scripts/validate_skills.py` → `Checked 25 skills: PASS` through Task 7, `Checked 24 skills: PASS` from Task 8.
- Every SKILL.md edit: archive snapshot of the pre-edit directory to `archive/<name>/<old-version>/` + version bump + changelog line at TOP of `## Changelog`, all in the same commit. Frontmatter stays `name`+`version`+`description` (≤1024 chars).
- Backtick rule and citation honesty (CLAUDE.md rules 1–3) bind all skill/doc prose. Changelog entries in OTHER skills mentioning skill-refiner/skill-updater are frozen history — never edited.
- apply_deltas invariants (spec §3, §7.2, §12): unappliable op → **no-op + report line**, never a partially-written file; full-file LLM rewrites forbidden (the tool only does anchor/section-targeted ops); an op whose result would breach the 500-line body cap refuses the whole skill's batch with a split-to-references suggestion; `retire` of an anchor with `helpful > 0` refuses unless the op carries `force: true`.
- Trigger-eval judge calls are timeboxed (30 s) with a deterministic fallback (placement analyzer); `--no-llm` forces the fallback for tests/CI (spec §12 "timeboxed with regex fallback").
- The seven signal types and the observations schema are as shipped in 2a (`learnings/observations/README.md`); this plan does not change entry schema (deferred 2a conventions — target length, signal taxonomy notes — are addressed only in learning-loop's reference prose, not by relinting old entries).
- Acceptance runs (Tasks 10–11) write PRs, never merge them. Nothing in this plan merges to `main` `skills/**`.

**File structure created/modified by this plan:**

```
scripts/engine/
  ledger.py                    # evidence.yaml read/increment (pyyaml, PEP-723)
  apply_deltas.py              # the delta pipeline (pyyaml, PEP-723)
  run_trigger_evals.py         # trigger evals + flip gate (pyyaml, PEP-723; imports placement)
  skill_metrics.py             # moved from skills/skill-refiner/scripts/ (Task 8)
hooks/
  hooks.json                   # + PreCompact registration
  scripts/recall.py            # stdlib observation matcher for the recall hook
  scripts/user_prompt_submit.py# recall wiring (capture + inject in one pass)
  scripts/pre_compact.py       # queue snapshot before compaction
tests/engine/
  test_ledger.py  test_apply_deltas.py  test_trigger_evals.py  test_recall.py
  test_hook_scripts.py         # extended: recall injection + pre_compact
skills/learning-loop/          # NEW umbrella skill: SKILL.md + references/
  references/delta-format.md  references/promotion-bar.md  references/refine-passes.md
  references/learnings-loop.md # moved from skill-author, updated
skills/skill-author/           # 1.1.3 → 2.0.0 (modes 2+3 removed) + evals.yaml seeded
skills/architect/SKILL.md      # 1.7.0 → 1.8.0 (learning-loop row; updater row removed)
skills/mining/SKILL.md         # 0.1.0 → 0.1.1 (learning-loop pointers land)
archive/skill-updater/1.1.1/   # retirement snapshot (dir moves here)
archive/skill-refiner/1.0.1/   # retirement snapshot (dir moves here)
CLAUDE.md                      # policy rewrite (§7.3) + counts to 24
learnings/README.md            # absorbed-marker note updated
learnings/observations/*.md    # acceptance run A output (session-origin entries; statuses)
skills/*/evidence.yaml         # acceptance run A ledger increments
docs/CHANGELOG.md              # dated Phase 2b entry
+ two PR branches: loop/absorb-<date>-external, loop/absorb-<date>-session
```

---

### Task 1: Evidence-ledger tool (`ledger.py`)

**Files:**
- Create: `scripts/engine/ledger.py`
- Test: `tests/engine/test_ledger.py`

**Interfaces:**
- Produces (used by apply_deltas Task 3 and the consolidate workflow Task 10):
  - `load(skill_dir: str) -> dict` — parsed evidence.yaml or `{}` if absent
  - `save(skill_dir: str, data: dict) -> None` — writes with the do-not-hand-edit header comment
  - `increment(skill_dir: str, anchor: str, kind: str, source: str, date: str) -> dict` — kind ∈ {helpful, harmful}; creates the anchor entry if missing; appends source if new; sets `last_verified` to date when kind == helpful; returns the updated entry
  - CLI: `uv run scripts/engine/ledger.py --skill skills/nav2 --anchor costmap-inflation --kind helpful --source learnings/2026-07-10.md#lrn-0710-03` (date defaults to today via `--date`)

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_ledger.py`:

```python
import ledger


def test_load_missing_returns_empty(tmp_path):
    assert ledger.load(str(tmp_path)) == {}


def test_increment_creates_entry_and_appends_sources(tmp_path):
    e = ledger.increment(str(tmp_path), "costmap-inflation", "helpful",
                         "learnings/2026-07-10.md#lrn-0710-03", "2026-08-05")
    assert e["helpful"] == 1 and e["harmful"] == 0
    assert e["last_verified"] == "2026-08-05"
    e = ledger.increment(str(tmp_path), "costmap-inflation", "harmful",
                         "learnings/2026-07-24.md#lrn-0724-02", "2026-08-06")
    assert e["helpful"] == 1 and e["harmful"] == 1
    assert len(e["sources"]) == 2
    # duplicate source is not appended twice
    ledger.increment(str(tmp_path), "costmap-inflation", "harmful",
                     "learnings/2026-07-24.md#lrn-0724-02", "2026-08-06")
    data = ledger.load(str(tmp_path))
    assert len(data["costmap-inflation"]["sources"]) == 2


def test_harmful_does_not_touch_last_verified(tmp_path):
    ledger.increment(str(tmp_path), "a", "helpful", "s1", "2026-08-01")
    e = ledger.increment(str(tmp_path), "a", "harmful", "s2", "2026-08-09")
    assert e["last_verified"] == "2026-08-01"


def test_save_writes_header_comment(tmp_path):
    ledger.increment(str(tmp_path), "a", "helpful", "s1", "2026-08-01")
    text = (tmp_path / "evidence.yaml").read_text()
    assert text.startswith("# ") and "do not hand-edit" in text


def test_bad_kind_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        ledger.increment(str(tmp_path), "a", "great", "s", "2026-08-01")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_ledger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ledger'`

- [ ] **Step 3: Implement `scripts/engine/ledger.py`**

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Evidence ledger (spec §4.2) — per-skill evidence.yaml, engine-written only.

helpful++ on ✓/attributed successes; harmful++ on wrong-guidance,
user-corrections, misfires. Counters carry sources — every increment is
auditable back to a dated learning entry or observation.
"""
import argparse
import datetime
import os
import sys

import yaml

_HEADER = ("# evidence ledger — maintained by the learning engine; "
           "do not hand-edit (spec §4.2)\n")
FILENAME = "evidence.yaml"


def _path(skill_dir):
    return os.path.join(skill_dir, FILENAME)


def load(skill_dir):
    p = _path(skill_dir)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save(skill_dir, data):
    with open(_path(skill_dir), "w", encoding="utf-8") as f:
        f.write(_HEADER)
        yaml.safe_dump(data, f, sort_keys=True, allow_unicode=True)


def increment(skill_dir, anchor, kind, source, date=None):
    if kind not in ("helpful", "harmful"):
        raise ValueError(f"kind must be helpful|harmful, got {kind!r}")
    date = date or datetime.date.today().isoformat()
    data = load(skill_dir)
    entry = data.setdefault(anchor, {"helpful": 0, "harmful": 0, "sources": []})
    entry[kind] = int(entry.get(kind, 0)) + 1
    if kind == "helpful":
        entry["last_verified"] = date
    sources = entry.setdefault("sources", [])
    if source and source not in sources:
        sources.append(source)
    save(skill_dir, data)
    return entry


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--anchor", required=True)
    ap.add_argument("--kind", required=True, choices=["helpful", "harmful"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--date")
    args = ap.parse_args(argv)
    entry = increment(args.skill, args.anchor, args.kind, args.source, args.date)
    print(f"{args.anchor}: helpful={entry['helpful']} harmful={entry['harmful']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_ledger.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/ledger.py tests/engine/test_ledger.py
git commit -m "feat(engine): evidence-ledger tool — engine-written evidence.yaml increments"
```

---

### Task 2: apply_deltas — core ops (add/update, snapshot, bump, changelog, dry-run)

**Files:**
- Create: `scripts/engine/apply_deltas.py`
- Test: `tests/engine/test_apply_deltas.py`

**Interfaces:**
- Deltas file (YAML) consumed by both apply_deltas tasks — the format learning-loop documents (Task 6):

```yaml
date: 2026-08-05            # optional; default today
deltas:
  - skill: nav2             # dirname under --skills-dir
    op: update              # add | update | retire | move | annotate
    anchor: costmap-inflation
    content: |
      - Nav2's default costmap YAML omits the inflation_layer block — add it
        (cost_scaling_factor: 3.0 worked) or the robot hugs obstacles. <!-- id: costmap-inflation -->
    reason: obs-nav2-007    # observation id; drives absorbed-marking + changelog
  - skill: ros2
    op: add
    section: Usage patterns # required for add; anchor comes from content
    position: bottom        # top | bottom (default bottom)
    content: |
      - New pattern text. <!-- id: new-anchor -->
    reason: obs-ros2-001
bump: {nav2: minor}         # optional per-skill override: build|minor|major
evals_confirmed: []         # skills whose major bump has had evals.yaml re-confirmed
```

- Produces (Task 3 extends the same module; Tasks 6/11 consume the CLI):
  - `find_anchor_block(lines: list[str], anchor: str) -> tuple[int,int] | None` — [start,end) of the anchored bullet + its indented continuation lines
  - `apply_file(deltas_path: str, skills_dir: str = "skills", archive_dir: str = "archive", dry_run: bool = False, date: str | None = None) -> dict` — returns `{"applied": [...], "noop": [...], "refused": [...], "skills_bumped": {skill: (old, new)}}`; each report item `{"skill","op","anchor","note"}`
  - CLI: `uv run scripts/engine/apply_deltas.py <deltas.yaml> [--dry-run] [--skills-dir …] [--archive-dir …]` — prints a markdown report table (for PR bodies); exit 0 unless the deltas file itself is invalid (refusals/no-ops are report content, not errors — spec §12)
- Version-bump inference: any applied add/update/move/retire → minor; only annotate ops applied → build; major only via the `bump:` override. Snapshot to `archive/<skill>/<old-version>/` happens once per touched skill BEFORE its first edit; if that archive dir already exists → refuse the skill's whole batch (means a version wasn't bumped upstream — never overwrite archives).
- Changelog: new line inserted directly under the `## Changelog` heading: `- <new-version> (<date>): <op summaries> [reasons: <comma-joined>] (applied by apply_deltas)`.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_apply_deltas.py` (fixture builder used by Task 3's tests too):

```python
import os
import textwrap

import yaml

import apply_deltas as ad

SKILL_MD = textwrap.dedent("""\
    ---
    name: {name}
    version: 1.2.3
    description: >
      Test skill about costmaps and navigation tuning.
    ---

    # {name}

    ## When to use this skill

    - Testing.

    ## Key directives

    - Always add the inflation layer or the robot hugs obstacles. <!-- id: inflation-layer -->
      Continuation line with detail that belongs to the same item.
    - Set the DDS domain id per robot. <!-- id: dds-domain-id -->

    ## Usage patterns

    - Existing pattern. <!-- id: existing-pattern -->

    ## Changelog

    - 1.2.3 (2026-07-01): prior line.
    """)


def mk_skill(tmp_path, name="nav2"):
    d = tmp_path / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(SKILL_MD.format(name=name))
    (tmp_path / "archive").mkdir(exist_ok=True)
    return d


def write_deltas(tmp_path, deltas, **extra):
    p = tmp_path / "deltas.yaml"
    p.write_text(yaml.safe_dump({"date": "2026-08-05", "deltas": deltas, **extra}))
    return str(p)


def run(tmp_path, deltas, **extra):
    return ad.apply_file(write_deltas(tmp_path, deltas, **extra),
                         skills_dir=str(tmp_path / "skills"),
                         archive_dir=str(tmp_path / "archive"))


def test_find_anchor_block_spans_continuation(tmp_path):
    d = mk_skill(tmp_path)
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "inflation-layer")
    assert "inflation-layer" in lines[start]
    assert end - start == 2  # bullet + one continuation line


def test_update_replaces_block_and_bumps_minor(tmp_path):
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- New text for the item. <!-- id: inflation-layer -->\n",
        "reason": "obs-nav2-001"}])
    text = (d / "SKILL.md").read_text()
    assert "New text for the item." in text
    assert "Continuation line" not in text
    assert "version: 1.3.0" in text
    assert rep["skills_bumped"]["nav2"] == ("1.2.3", "1.3.0")
    assert "- 1.3.0 (2026-08-05):" in text.split("## Changelog")[1]
    # archive snapshot has the OLD content and version
    old = (tmp_path / "archive" / "nav2" / "1.2.3" / "SKILL.md").read_text()
    assert "Continuation line" in old and "version: 1.2.3" in old


def test_update_content_must_carry_same_anchor(tmp_path):
    mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- Text without the anchor.\n", "reason": "obs-x"}])
    assert len(rep["refused"]) == 1 and rep["applied"] == []


def test_add_inserts_into_section_bottom(tmp_path):
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Usage patterns",
        "content": "- Added pattern. <!-- id: added-pattern -->\n",
        "reason": "obs-nav2-002"}])
    body = (d / "SKILL.md").read_text()
    section = body.split("## Usage patterns")[1].split("## ")[0]
    assert section.index("existing-pattern") < section.index("added-pattern")
    assert rep["applied"] and not rep["refused"]


def test_missing_anchor_and_missing_section_are_noops(tmp_path):
    d = mk_skill(tmp_path)
    before = (d / "SKILL.md").read_text()
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "update", "anchor": "nope",
         "content": "- X. <!-- id: nope -->\n", "reason": "obs-a"},
        {"skill": "nav2", "op": "add", "section": "No Such Section",
         "content": "- Y. <!-- id: y -->\n", "reason": "obs-b"}])
    assert len(rep["noop"]) == 2 and rep["applied"] == []
    # nothing applied → no bump, no snapshot, file untouched
    assert (d / "SKILL.md").read_text() == before
    assert not (tmp_path / "archive" / "nav2").exists()


def test_dry_run_changes_nothing(tmp_path):
    d = mk_skill(tmp_path)
    before = (d / "SKILL.md").read_text()
    rep = ad.apply_file(write_deltas(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- Changed. <!-- id: inflation-layer -->\n", "reason": "obs-c"}]),
        skills_dir=str(tmp_path / "skills"),
        archive_dir=str(tmp_path / "archive"), dry_run=True)
    assert rep["applied"]  # reported as would-apply
    assert (d / "SKILL.md").read_text() == before


def test_existing_archive_dir_refuses_batch(tmp_path):
    mk_skill(tmp_path)
    (tmp_path / "archive" / "nav2" / "1.2.3").mkdir(parents=True)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- Z. <!-- id: inflation-layer -->\n", "reason": "obs-d"}])
    assert rep["refused"] and not rep["applied"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_apply_deltas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apply_deltas'`

- [ ] **Step 3: Implement `scripts/engine/apply_deltas.py` (core)**

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Apply anchor-targeted delta ops to skills (spec §7.2).

Deterministic: archive snapshot → apply ops (no-op fallback) → bump version
→ changelog line → sidecar updates. An unappliable op degrades to a no-op +
report line, never a corrupted file. Refusals (anchor-mismatch content,
existing archive dir, cap breach, protected retire) block without writing.
"""
import argparse
import datetime
import os
import re
import shutil
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_ANCHOR = "<!-- id: {} -->"
_VER_RE = re.compile(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$")
BODY_CAP = 500


def find_anchor_block(lines, anchor):
    marker = _ANCHOR.format(anchor)
    for i, line in enumerate(lines):
        if marker in line:
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= indent:
                    break
                j += 1
            return (i, j)
    return None


def _find_section(lines, section):
    heading = f"## {section}"
    for i, line in enumerate(lines):
        if line.strip() == heading:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            return (i, j)
    return None


def _version(lines):
    for i, line in enumerate(lines):
        m = _VER_RE.match(line)
        if m:
            return ".".join(m.groups()), i
    raise ValueError("no version: line in frontmatter")


def bump_version(ver, kind):
    major, minor, build = (int(x) for x in ver.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{build + 1}"


def _body_line_count(lines):
    seen = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            seen += 1
            if seen == 2:
                return len(lines) - i - 1
    return len(lines)


def _content_lines(content):
    return content.rstrip("\n").split("\n")


def _apply_one(lines, op, report):
    """Return new lines or None (no change). Appends to report."""
    kind = op["op"]
    if kind in ("update", "annotate") and "anchor" in op:
        loc = find_anchor_block(lines, op["anchor"])
        if loc is None:
            report["noop"].append(_item(op, "anchor not found"))
            return None
        if _ANCHOR.format(op["anchor"]) not in op.get("content", ""):
            report["refused"].append(_item(op, "content drops the anchor id"))
            return None
        start, end = loc
        return lines[:start] + _content_lines(op["content"]) + lines[end:]
    if kind == "add":
        sec = _find_section(lines, op.get("section", ""))
        if sec is None:
            report["noop"].append(_item(op, "section not found"))
            return None
        s, e = sec
        insert_at = s + 1 if op.get("position") == "top" else e
        while insert_at > s + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        return lines[:insert_at] + _content_lines(op["content"]) + lines[insert_at:]
    report["refused"].append(_item(op, f"unknown op {kind!r} (core)"))
    return None


def _item(op, note):
    return {"skill": op.get("skill", "?"), "op": op.get("op", "?"),
            "anchor": op.get("anchor", op.get("section", "-")), "note": note}


def apply_file(deltas_path, skills_dir="skills", archive_dir="archive",
               dry_run=False, date=None):
    with open(deltas_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    date = date or spec.get("date") or datetime.date.today().isoformat()
    overrides = spec.get("bump") or {}
    report = {"applied": [], "noop": [], "refused": [], "skills_bumped": {}}

    by_skill = {}
    for op in spec.get("deltas", []):
        by_skill.setdefault(op["skill"], []).append(op)

    for skill, ops in by_skill.items():
        skill_dir = os.path.join(skills_dir, skill)
        md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(md):
            for op in ops:
                report["refused"].append(_item(op, "skill not found"))
            continue
        lines = open(md, encoding="utf-8").read().splitlines()
        old_ver, _ = _version(lines)
        snap = os.path.join(archive_dir, skill, old_ver)
        if os.path.exists(snap):
            for op in ops:
                report["refused"].append(_item(op, f"archive {snap} exists — bump upstream first"))
            continue

        working, applied_here, kinds = lines, [], set()
        pending = {"applied": [], "noop": [], "refused": []}
        for op in ops:
            new = _apply_one(working, op, pending)
            if new is not None:
                working = new
                applied_here.append(op)
                kinds.add(op["op"])
                pending["applied"].append(_item(op, "applied"))
        if not applied_here:
            for k in ("applied", "noop", "refused"):
                report[k].extend(pending[k])
            continue
        if _body_line_count(working) >= BODY_CAP:
            report["refused"].extend(
                _item(op, "would breach 500-line body cap — split to references/")
                for op in ops)
            continue

        bump_kind = overrides.get(skill) or (
            "build" if kinds <= {"annotate"} else "minor")
        new_ver = bump_version(old_ver, bump_kind)
        working = _bump_and_log(working, old_ver, new_ver, date, applied_here)

        if not dry_run:
            shutil.copytree(skill_dir, snap)
            with open(md, "w", encoding="utf-8") as f:
                f.write("\n".join(working) + "\n")
        report["skills_bumped"][skill] = (old_ver, new_ver)
        for k in ("applied", "noop", "refused"):
            report[k].extend(pending[k])
    return report


def _bump_and_log(lines, old_ver, new_ver, date, applied_ops):
    out = []
    ver_done = False
    for line in lines:
        if not ver_done and _VER_RE.match(line):
            out.append(f"version: {new_ver}")
            ver_done = True
        else:
            out.append(line)
    reasons = ", ".join(sorted({op.get("reason", "?") for op in applied_ops}))
    summary = "; ".join(f"{op['op']} {op.get('anchor', op.get('section', ''))}"
                        for op in applied_ops)
    entry = f"- {new_ver} ({date}): {summary} [reasons: {reasons}] (applied by apply_deltas)"
    final = []
    inserted = False
    for line in out:
        final.append(line)
        if not inserted and line.strip() == "## Changelog":
            final.append("")
            final.append(entry)
            inserted = True
    return final


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("deltas")
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--archive-dir", default="archive")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    rep = apply_file(args.deltas, args.skills_dir, args.archive_dir, args.dry_run)
    print("| skill | op | anchor | status | note |")
    print("|---|---|---|---|---|")
    for status in ("applied", "noop", "refused"):
        for item in rep[status]:
            print(f"| {item['skill']} | {item['op']} | {item['anchor']} "
                  f"| {status} | {item['note']} |")
    for skill, (old, new) in rep["skills_bumped"].items():
        print(f"\nbumped {skill}: {old} -> {new}"
              + (" (dry-run: not written)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: in `_apply_one`, `annotate` with an `anchor` behaves like `update` for now; Task 3 adds `retire`, `move`, file-targeted `annotate`, and the refusal rules that need the ledger. The double changelog-blank-line handling: entry inserted with one empty line after the heading — matches existing skill formatting (blank line, then newest entry first).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_apply_deltas.py -v`
Expected: 8 PASS. If `test_add_inserts_into_section_bottom` fails on blank-line placement, adjust the insert-at backtrack loop, not the test.

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/apply_deltas.py tests/engine/test_apply_deltas.py
git commit -m "feat(engine): apply_deltas core — anchor-targeted add/update, snapshot+bump+changelog, dry-run"
```

---

### Task 3: apply_deltas — retire/move/annotate, refusals, sidecar updates

**Files:**
- Modify: `scripts/engine/apply_deltas.py`
- Modify: `tests/engine/test_apply_deltas.py` (append tests)

**Interfaces:**
- Consumes: `ledger.load/save` (Task 1).
- Adds to the module:
  - `retire`: removes the anchor block AND deletes the anchor's key from the live `evidence.yaml` (the pre-edit archive snapshot preserves the ledger history — the only legal delete, spec §4.1/§7.2). Refused when the ledger shows `helpful > 0` unless the op has `force: true`.
  - `move`: op fields `skill` (source), `anchor`, `to_skill`, `to_section`; removes from source, inserts the same content (same anchor id) into the destination section; moves the ledger entry to the destination's evidence.yaml; BOTH skills snapshot+bump (minor).
  - `annotate` with `file:`/`find:`/`replace:` (no anchor): replaces the first occurrence of `find` in `<skill_dir>/<file>` (path must stay inside the skill dir; used to promote `status: unverified` markers in examples). Counts as build-level.
  - **Co-evolving-evals rule** (spec §7.2): a `major` bump (only reachable via `bump:` override) is refused unless the skill is listed in `evals_confirmed`.
  - `mark_absorbed(reasons: list[str], observations_dir: str, date: str) -> list[str]` — for each reason matching `obs-<stem>-NNN`, sets that entry's `status:` line to `absorbed <date>` in `learnings/observations/<stem>.md`; returns notes for unfound ids. Called by `apply_file` for applied ops only (skipped in dry-run).

- [ ] **Step 1: Append the failing tests**

Append to `tests/engine/test_apply_deltas.py`:

```python
import ledger


def test_retire_removes_block_and_ledger_key(tmp_path):
    d = mk_skill(tmp_path)
    ledger.increment(str(d), "dds-domain-id", "harmful", "lrn-1", "2026-08-01")
    rep = run(tmp_path, [{"skill": "nav2", "op": "retire",
                          "anchor": "dds-domain-id", "reason": "obs-nav2-003"}])
    text = (d / "SKILL.md").read_text()
    assert "dds-domain-id" not in text
    assert "dds-domain-id" not in ledger.load(str(d))
    assert rep["applied"]
    # archive snapshot still carries the pre-retire ledger
    snap = tmp_path / "archive" / "nav2" / "1.2.3" / "evidence.yaml"
    assert "dds-domain-id" in snap.read_text()


def test_retire_with_helpful_history_refused_without_force(tmp_path):
    d = mk_skill(tmp_path)
    ledger.increment(str(d), "inflation-layer", "helpful", "lrn-2", "2026-08-01")
    rep = run(tmp_path, [{"skill": "nav2", "op": "retire",
                          "anchor": "inflation-layer", "reason": "obs-x"}])
    assert rep["refused"] and "helpful" in rep["refused"][0]["note"]
    rep2 = run(tmp_path, [{"skill": "nav2", "op": "retire", "force": True,
                           "anchor": "inflation-layer", "reason": "obs-x"}])
    assert rep2["applied"]


def test_move_relocates_anchor_and_ledger(tmp_path):
    src = mk_skill(tmp_path, "nav2")
    dst = mk_skill(tmp_path, "ros2")
    ledger.increment(str(src), "existing-pattern", "helpful", "lrn-3", "2026-08-01")
    rep = run(tmp_path, [{"skill": "nav2", "op": "move",
                          "anchor": "existing-pattern", "to_skill": "ros2",
                          "to_section": "Usage patterns", "reason": "obs-nav2-004"}])
    assert "existing-pattern" not in (src / "SKILL.md").read_text()
    assert "existing-pattern" in (dst / "SKILL.md").read_text()
    assert "existing-pattern" in ledger.load(str(dst))
    assert "existing-pattern" not in ledger.load(str(src))
    assert set(rep["skills_bumped"]) == {"nav2", "ros2"}


def test_annotate_file_marker(tmp_path):
    d = mk_skill(tmp_path)
    (d / "examples").mkdir()
    (d / "examples" / "x.yaml").write_text("# status: unverified\nkey: v\n")
    rep = run(tmp_path, [{"skill": "nav2", "op": "annotate",
                          "file": "examples/x.yaml",
                          "find": "status: unverified",
                          "replace": "status: verified 2026-08-05",
                          "reason": "obs-nav2-005"}])
    assert "verified 2026-08-05" in (d / "examples" / "x.yaml").read_text()
    assert rep["skills_bumped"]["nav2"] == ("1.2.3", "1.2.4")  # build bump


def test_annotate_file_escaping_skill_dir_refused(tmp_path):
    mk_skill(tmp_path)
    rep = run(tmp_path, [{"skill": "nav2", "op": "annotate",
                          "file": "../../CLAUDE.md", "find": "x", "replace": "y",
                          "reason": "obs-x"}])
    assert rep["refused"] and not rep["applied"]


def test_major_bump_requires_evals_confirmed(tmp_path):
    mk_skill(tmp_path)
    rep = run(tmp_path, [{"skill": "nav2", "op": "update",
                          "anchor": "inflation-layer",
                          "content": "- T. <!-- id: inflation-layer -->\n",
                          "reason": "obs-x"}], bump={"nav2": "major"})
    assert rep["refused"] and "evals" in rep["refused"][0]["note"]
    rep2 = run(tmp_path, [{"skill": "nav2", "op": "update",
                           "anchor": "inflation-layer",
                           "content": "- T. <!-- id: inflation-layer -->\n",
                           "reason": "obs-x"}],
               bump={"nav2": "major"}, evals_confirmed=["nav2"])
    assert rep2["skills_bumped"]["nav2"] == ("1.2.3", "2.0.0")


def test_mark_absorbed_updates_observation_status(tmp_path):
    obs_dir = tmp_path / "learnings" / "observations"
    obs_dir.mkdir(parents=True)
    (obs_dir / "nav2.md").write_text(
        "## finding <!-- id: obs-nav2-007 -->\nstatus: ready\nproof: 2\n")
    notes = ad.mark_absorbed(["obs-nav2-007", "obs-gone-001"],
                             str(obs_dir), "2026-08-05")
    assert "status: absorbed 2026-08-05" in (obs_dir / "nav2.md").read_text()
    assert any("obs-gone-001" in n for n in notes)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_apply_deltas.py -v`
Expected: the 8 core tests PASS, the 7 new ones FAIL (missing ops/functions).

- [ ] **Step 3: Extend `apply_deltas.py`**

Add to the module (integrating into `_apply_one`/`apply_file`; `import ledger` at top with the existing sys.path insert):

```python
_OBS_ID_RE = re.compile(r"^obs-(.+)-\d{3}$")


def mark_absorbed(reasons, observations_dir, date):
    notes = []
    for rid in sorted(set(reasons)):
        m = _OBS_ID_RE.match(rid or "")
        if not m:
            continue
        path = os.path.join(observations_dir, f"{m.group(1)}.md")
        if not os.path.exists(path):
            notes.append(f"{rid}: observations file not found")
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        hit = None
        for i, line in enumerate(lines):
            if f"<!-- id: {rid} -->" in line:
                hit = i
                break
        if hit is None:
            notes.append(f"{rid}: entry not found")
            continue
        for j in range(hit + 1, min(hit + 12, len(lines))):
            if lines[j].startswith("status:"):
                lines[j] = f"status: absorbed {date}"
                break
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return notes
```

Behavior changes in `apply_file` / `_apply_one` (implement exactly):
1. `retire` (anchor op): look up `ledger.load(skill_dir)`; if entry's `helpful > 0` and not `op.get("force")` → refused with note `"anchor has helpful>0 — retire needs force: true"`. Otherwise remove the block; after the skill's file is written, delete the key via `data = ledger.load(...); data.pop(anchor, None); ledger.save(...)` (only when not dry-run; the snapshot was taken before, preserving history).
2. `move`: validate `to_skill` exists and destination section exists (else no-op with note). Execute as: capture the source block's text, retarget it unchanged into the destination (same anchor id), remove from source. Ledger entry moves: pop from source evidence.yaml, insert into destination's. Both skills get snapshot+bump; the destination's changelog line reads `move-in <anchor> from <skill>`, the source's `move-out <anchor> to <to_skill>`.
3. `annotate` with `file`: resolve `os.path.realpath(os.path.join(skill_dir, op["file"]))`; if it doesn't start with `realpath(skill_dir) + os.sep` → refused (`"file escapes skill dir"`). If `find` not present → no-op. Replace first occurrence only. Contributes `annotate` to the bump-kind set (build).
4. Major-bump guard: in `apply_file`, when `bump_kind == "major"` and skill not in `spec.get("evals_confirmed", [])` → refuse the skill's batch with note `"major bump without evals_confirmed (co-evolving-evals rule)"`.
5. `apply_file` calls `mark_absorbed(...)` after all skills are written (not in dry-run) with the reasons of APPLIED ops only, `observations_dir` defaulting to `learnings/observations` beside `skills_dir`'s parent (add an `observations_dir=None` parameter: `observations_dir or os.path.join(os.path.dirname(os.path.abspath(skills_dir)), "learnings", "observations")`); its notes are appended to the report under a `"notes"` key (add the key to the report dict and print it in `main`).
6. Snapshot ordering with sidecars: `shutil.copytree` happens BEFORE the ledger delete/move so the archive carries the pre-op evidence.yaml (the retire test asserts this).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_apply_deltas.py -v`
Expected: 15 PASS. Then the full suite: `uv run --with pytest --with pyyaml -m pytest tests/engine -q` — no regressions.

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/apply_deltas.py tests/engine/test_apply_deltas.py
git commit -m "feat(engine): apply_deltas — retire/move/annotate, ledger-aware refusals, absorbed-marking, co-evolving evals"
```

---

### Task 4: Trigger-eval runner + flip gate (`run_trigger_evals.py`)

**Files:**
- Create: `scripts/engine/run_trigger_evals.py`
- Test: `tests/engine/test_trigger_evals.py`

**Interfaces:**
- Consumes: `placement.load_catalog` + `placement.analyze` (2a) for the deterministic fallback; `skills/<name>/evals.yaml` (schema from spec §4.3: `triggers.positive[].phrase`, `triggers.negative[].phrase` + optional `expect`).
- Produces:
  - `judge(phrase: str, catalog: dict, no_llm: bool, timeout_s: int = 30) -> str` — returns the selected skill name. LLM path: `claude -p "<judge prompt>"` via subprocess with timeout, parsing the reply for a known skill name; ANY failure (missing CLI, timeout, unparseable) falls back to the deterministic path: `placement.analyze(phrase, ...)` top skill (spec §12: timeboxed with fallback).
  - `run_skill(skill: str, skills_dir: str, no_llm: bool, catalog_override: dict | None = None) -> dict` — `{"cases": [{"phrase","kind","expected","selected","pass"}], "skipped": bool}`; positive passes when selected == skill; negative passes when selected != skill; `skipped: True` when the skill has no evals.yaml or no cases (spec §8: skipped-and-said, not silently green).
  - `flip_gate(skill: str, skills_dir: str, baseline_dir: str, no_llm: bool) -> list[dict]` — runs the suite twice: once with the catalog as-is, once with the skill's description replaced by the baseline copy's (`<baseline_dir>/SKILL.md`, i.e. the archive snapshot); returns cases that passed on baseline and fail now (the blocking set, spec §8 layer 3).
  - CLI: `uv run scripts/engine/run_trigger_evals.py --skills nav2 ros2 [--no-llm] [--flip-gate-baseline archive/nav2/1.2.3 --flip-skill nav2]` → per-case lines, summary `Trigger evals: P passed, F failed, S skipped-skills`, exit 1 on any failure or any flip; exit 0 when all pass or all skipped (skips are announced).
- Judge prompt (LLM path), verbatim:
  `"You route user requests to exactly one skill. Skills (name: description): <name>: <first 200 chars of description> [one per line]. User phrasing: '<phrase>'. Reply with ONLY the single best skill name."`

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_trigger_evals.py` (deterministic — always `no_llm=True`; reuses the synthetic-catalog idea from test_placement):

```python
import textwrap

import run_trigger_evals as rte

FOO = textwrap.dedent("""\
    ---
    name: foo
    version: 1.0.0
    description: >
      Costmap tuning and obstacle inflation for mobile robot navigation.
    ---
    ## Changelog
    """)
BAR = textwrap.dedent("""\
    ---
    name: bar
    version: 1.0.0
    description: >
      Camera calibration and image pipelines for perception stacks.
    ---
    ## Changelog
    """)
EVALS = textwrap.dedent("""\
    triggers:
      positive:
        - phrase: robot hugs obstacles near walls costmap inflation
      negative:
        - phrase: calibrate the camera intrinsics pipeline
          expect: bar
    tasks: []
    """)


def mk_catalog(tmp_path):
    for name, text in (("foo", FOO), ("bar", BAR)):
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(text)
    (tmp_path / "skills" / "foo" / "evals.yaml").write_text(EVALS)
    return str(tmp_path / "skills")


def test_positive_and_negative_pass(tmp_path):
    skills = mk_catalog(tmp_path)
    out = rte.run_skill("foo", skills, no_llm=True)
    assert not out["skipped"]
    assert all(c["pass"] for c in out["cases"]), out["cases"]


def test_no_evals_is_skipped_not_green(tmp_path):
    skills = mk_catalog(tmp_path)
    out = rte.run_skill("bar", skills, no_llm=True)
    assert out["skipped"] and out["cases"] == []


def test_positive_fails_when_description_loses_keywords(tmp_path):
    skills = mk_catalog(tmp_path)
    md = tmp_path / "skills" / "foo" / "SKILL.md"
    md.write_text(FOO.replace(
        "Costmap tuning and obstacle inflation for mobile robot navigation.",
        "General helper utilities."))
    out = rte.run_skill("foo", skills, no_llm=True)
    positives = [c for c in out["cases"] if c["kind"] == "positive"]
    assert positives and not positives[0]["pass"]


def test_flip_gate_catches_regression(tmp_path):
    skills = mk_catalog(tmp_path)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "SKILL.md").write_text(FOO)  # good old description
    md = tmp_path / "skills" / "foo" / "SKILL.md"
    md.write_text(FOO.replace(
        "Costmap tuning and obstacle inflation for mobile robot navigation.",
        "General helper utilities."))
    flips = rte.flip_gate("foo", skills, str(baseline), no_llm=True)
    assert flips and flips[0]["kind"] == "positive"


def test_flip_gate_clean_when_unchanged(tmp_path):
    skills = mk_catalog(tmp_path)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "SKILL.md").write_text(FOO)
    assert rte.flip_gate("foo", skills, str(baseline), no_llm=True) == []


def test_judge_falls_back_without_llm(tmp_path):
    skills = mk_catalog(tmp_path)
    import placement
    cat = placement.load_catalog(skills)
    assert rte.judge("costmap inflation obstacles", cat, no_llm=True,
                     skills_dir=skills) == "foo"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_trigger_evals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_trigger_evals'`

- [ ] **Step 3: Implement `scripts/engine/run_trigger_evals.py`**

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Trigger evals + flip gate (spec §8 layers 2–3).

Judge: `claude -p` timeboxed at 30 s; ANY failure falls back to the
deterministic placement analyzer (spec §12). Blocking when eval cases
exist for a touched skill; skipped-and-said when none exist yet.
"""
import argparse
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement  # noqa: E402

TIMEOUT_S = 30


def _load_cases(skill, skills_dir):
    path = os.path.join(skills_dir, skill, "evals.yaml")
    if not os.path.exists(path):
        return []
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    triggers = data.get("triggers") or {}
    cases = []
    for kind in ("positive", "negative"):
        for case in triggers.get(kind) or []:
            cases.append({"phrase": case["phrase"], "kind": kind,
                          "expected": case.get("expect", skill)})
    return cases


def judge(phrase, catalog, no_llm, timeout_s=TIMEOUT_S, skills_dir="skills"):
    if not no_llm:
        listing = "\n".join(f"{n}: {d['description'][:200]}"
                            for n, d in sorted(catalog.items()))
        prompt = ("You route user requests to exactly one skill. Skills "
                  f"(name: description):\n{listing}\nUser phrasing: "
                  f"'{phrase}'. Reply with ONLY the single best skill name.")
        try:
            out = subprocess.run(["claude", "-p", prompt],
                                 capture_output=True, text=True,
                                 timeout=timeout_s).stdout.lower()
            for name in sorted(catalog, key=len, reverse=True):
                if name in out:
                    return name
        except Exception:
            pass
    hits = placement.analyze(phrase, skills_dir)["skills"]
    return hits[0][0] if hits else ""


def run_skill(skill, skills_dir, no_llm, catalog_override=None):
    cases = _load_cases(skill, skills_dir)
    if not cases:
        return {"cases": [], "skipped": True}
    catalog = catalog_override or placement.load_catalog(skills_dir)
    out = []
    for c in cases:
        selected = judge(c["phrase"], catalog, no_llm, skills_dir=skills_dir)
        ok = (selected == skill) if c["kind"] == "positive" else (selected != skill)
        out.append({**c, "selected": selected, "pass": ok})
    return {"cases": out, "skipped": False}


def flip_gate(skill, skills_dir, baseline_dir, no_llm):
    now = run_skill(skill, skills_dir, no_llm)
    if now["skipped"]:
        return []
    baseline_text = open(os.path.join(baseline_dir, "SKILL.md"),
                         encoding="utf-8").read()
    catalog = placement.load_catalog(skills_dir)
    baseline_catalog = dict(catalog)
    baseline_catalog[skill] = {
        "description": placement._frontmatter_description(baseline_text),
        "anchors": catalog.get(skill, {}).get("anchors", {}),
    }
    # baseline run: judge with the OLD description in the catalog, but the
    # fallback analyzer reads files on disk — so restrict the baseline run to
    # the catalog-driven judge by scoring phrases against baseline_catalog.
    flips = []
    for case in now["cases"]:
        old_sel = _catalog_judge(case["phrase"], baseline_catalog)
        old_ok = (old_sel == skill) if case["kind"] == "positive" else (old_sel != skill)
        if old_ok and not case["pass"]:
            flips.append(case)
    return flips


def _catalog_judge(phrase, catalog):
    q = placement.tokens(phrase)
    best, best_s = "", 0.0
    for name, data in catalog.items():
        s = len(q & placement.tokens(data["description"]))
        s = s / (max(len(q), 1) ** 0.5)
        if s > best_s:
            best, best_s = name, s
    return best


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", nargs="+", required=True)
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--flip-gate-baseline")
    ap.add_argument("--flip-skill")
    args = ap.parse_args(argv)
    passed = failed = skipped = 0
    for skill in args.skills:
        res = run_skill(skill, args.skills_dir, args.no_llm)
        if res["skipped"]:
            skipped += 1
            print(f"{skill}: SKIPPED (no eval cases yet — say so in the PR)")
            continue
        for c in res["cases"]:
            ok = "PASS" if c["pass"] else "FAIL"
            print(f"{skill} [{c['kind']}] '{c['phrase']}' -> {c['selected']}: {ok}")
            passed, failed = passed + c["pass"], failed + (not c["pass"])
    flips = []
    if args.flip_gate_baseline and args.flip_skill:
        flips = flip_gate(args.flip_skill, args.skills_dir,
                          args.flip_gate_baseline, args.no_llm)
        for c in flips:
            print(f"FLIP: {args.flip_skill} [{c['kind']}] '{c['phrase']}' "
                  "passed on baseline, fails now — BLOCKING")
    print(f"Trigger evals: {passed} passed, {failed} failed, "
          f"{skipped} skipped-skills, {len(flips)} flips")
    return 1 if (failed or flips) else 0


if __name__ == "__main__":
    sys.exit(main())
```

Note on `flip_gate`'s current-run consistency: the "now" side uses the same `_catalog_judge`-vs-`judge` asymmetry only through `run_skill` (full judge). If `test_flip_gate_clean_when_unchanged` fails because the two judges disagree on identical descriptions, make BOTH sides use `_catalog_judge` for the flip comparison (change `run_skill`'s results only inside `flip_gate` by re-scoring with `_catalog_judge` on the current catalog) — determinism beats judge fidelity inside the gate; document the choice in the module docstring.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_trigger_evals.py -v`
Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/run_trigger_evals.py tests/engine/test_trigger_evals.py
git commit -m "feat(engine): trigger-eval runner + flip gate — timeboxed judge with deterministic fallback"
```

---

### Task 5: Recall matcher (`hooks/scripts/recall.py`)

**Files:**
- Create: `hooks/scripts/recall.py`
- Test: `tests/engine/test_recall.py`

**Interfaces:**
- **stdlib only** (ships in the plugin; cannot import scripts/engine — carries its own ~30-line observation parser, noted in both files' docstrings).
- Produces (Task 6 wires it into the UserPromptSubmit hook):
  - `load_observations(cwd: str) -> list[dict]` — reads `<cwd>/learnings/observations/*.md` and `<cwd>/.robium/observations/*.md` (whichever exist; user tier uses the latter, spec §5 eligibility note); each entry `{"id","title","status","proof","fields"}`
  - `eligible(entry) -> bool` — `status == "ready"`, or `tentative` with `proof >= 2`; `absorbed`/`rejected` excluded (spec §5 guardrails)
  - `match(prompt: str, entries: list[dict], top_k: int = 3) -> list[tuple[entry, float]]` — deterministic keyword overlap of the prompt against title + target + skill stem; entries scoring < 0.15 dropped; sorted desc
  - `render(hits, budget_chars: int = 2000) -> str` — starts with `[robium-recall]`, one line per hit: `- (<id>) <title>: <first 200 chars of target>`, cites ids so misfires are traceable (spec §5); hard-truncated to budget (≈500 tokens); empty string when no hits — the budget is a cap, not a target
- Marker contract: the existing UserPromptSubmit capture path already ignores prompts starting with `[robium-recall]` (Phase 1) — render()'s prefix is exactly that marker, closing the reflection loop.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_recall.py`:

```python
import recall

OBS = """## costmap inflation missing from quick start <!-- id: obs-nav2-007 -->
status: ready
proof: 2
signal: wrong-guidance
sources: [lrn-0710-03]
target: nav2#costmap-inflation (update) — add inflation_layer block, robot hugs obstacles otherwise
evidence: x ✓ y ✓ z ✓

## something absorbed already <!-- id: obs-nav2-008 -->
status: absorbed 2026-08-01
proof: 3
signal: verified
sources: [lrn-1]
target: nav2#other (update) — done
evidence: ✓✓✓

## weak single sighting <!-- id: obs-nav2-009 -->
status: tentative
proof: 1
signal: better-method
sources: [lrn-2]
target: nav2#thing (update) — maybe
evidence: thin
"""


def _setup(tmp_path):
    d = tmp_path / "learnings" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(OBS)
    return str(tmp_path)


def test_load_and_eligibility(tmp_path):
    entries = recall.load_observations(_setup(tmp_path))
    assert len(entries) == 3
    ok = [e for e in entries if recall.eligible(e)]
    assert [e["id"] for e in ok] == ["obs-nav2-007"]


def test_tentative_with_proof2_is_eligible(tmp_path):
    root = _setup(tmp_path)
    d = tmp_path / "learnings" / "observations"
    (d / "nav2.md").write_text(OBS.replace(
        "status: tentative\nproof: 1", "status: tentative\nproof: 2"))
    ok = [e for e in recall.load_observations(root) if recall.eligible(e)]
    assert {e["id"] for e in ok} == {"obs-nav2-007", "obs-nav2-009"}


def test_match_scores_relevant_prompt(tmp_path):
    entries = recall.load_observations(_setup(tmp_path))
    hits = recall.match("the robot hugs obstacles near walls — costmap issue?",
                        [e for e in entries if recall.eligible(e)])
    assert hits and hits[0][0]["id"] == "obs-nav2-007"
    assert recall.match("write me a poem about turtles",
                        [e for e in entries if recall.eligible(e)]) == []


def test_render_marker_ids_and_budget(tmp_path):
    entries = recall.load_observations(_setup(tmp_path))
    hits = recall.match("robot hugs obstacles costmap inflation",
                        [e for e in entries if recall.eligible(e)])
    text = recall.render(hits)
    assert text.startswith("[robium-recall]")
    assert "obs-nav2-007" in text
    assert recall.render([]) == ""
    assert len(recall.render(hits, budget_chars=80)) <= 80


def test_user_tier_dir_read(tmp_path):
    d = tmp_path / ".robium" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(OBS)
    assert len(recall.load_observations(str(tmp_path))) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_recall.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'recall'`
(conftest.py already puts `hooks/scripts` on sys.path — Phase 1.)

- [ ] **Step 3: Implement `hooks/scripts/recall.py`**

```python
"""Recall matcher for the UserPromptSubmit hook (spec §5, "the short loop").

Deterministic keyword matching only — no LLM, no embeddings, fail-open,
millisecond budget. Carries its own minimal observations parser because
installed plugins ship only hooks/ (scripts/engine/observations.py is the
repo-side canonical parser; keep the field semantics in sync with
learnings/observations/README.md).
"""
import glob
import os
import re

MARKER = "[robium-recall]"
_ID_RE = re.compile(r"<!-- id: (obs-[a-z0-9-]+-\d{3}) -->")
_HEAD_RE = re.compile(r"^## (.+?)\s*<!-- id: ")
_FIELD_RE = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")
_STOP = frozenset(
    "the a an and or of to in for with on is are be this that it as at by "
    "from use when not you your how what why can could should".split())


def _tokens(text):
    return {t for t in re.findall(r"[a-z0-9_]+", (text or "").lower())
            if len(t) > 2 and t not in _STOP}


def load_observations(cwd):
    entries = []
    for base in (os.path.join(cwd, "learnings", "observations"),
                 os.path.join(cwd, ".robium", "observations")):
        for path in sorted(glob.glob(os.path.join(base, "*.md"))):
            if os.path.basename(path) == "README.md":
                continue
            current = None
            for line in open(path, encoding="utf-8"):
                line = line.rstrip("\n")
                if line.startswith("## "):
                    m_id = _ID_RE.search(line)
                    m_head = _HEAD_RE.match(line)
                    current = {"id": m_id.group(1) if m_id else "",
                               "title": m_head.group(1) if m_head else "",
                               "status": "", "proof": 0, "fields": {}}
                    if current["id"]:
                        entries.append(current)
                elif current is not None:
                    m = _FIELD_RE.match(line)
                    if m:
                        current["fields"][m.group(1)] = m.group(2).strip()
                        if m.group(1) == "status":
                            current["status"] = m.group(2).strip()
                        elif m.group(1) == "proof" and m.group(2).strip().isdigit():
                            current["proof"] = int(m.group(2).strip())
    return entries


def eligible(entry):
    status = entry.get("status", "")
    if status == "ready":
        return True
    return status == "tentative" and entry.get("proof", 0) >= 2


def match(prompt, entries, top_k=3):
    q = _tokens(prompt)
    if not q:
        return []
    scored = []
    for e in entries:
        skill_stem = e["id"].rsplit("-", 1)[0].replace("obs-", "", 1)
        hay = _tokens(e.get("title", "")) | _tokens(
            e.get("fields", {}).get("target", "")) | {skill_stem}
        s = len(q & hay) / (max(len(q), 1) ** 0.5 * max(len(hay), 1) ** 0.5)
        if s >= 0.15:
            scored.append((e, round(s, 3)))
    scored.sort(key=lambda x: -x[1])
    return scored[:top_k]


def render(hits, budget_chars=2000):
    if not hits:
        return ""
    lines = [MARKER + " Possibly relevant prior findings (engine recall; "
             "cite the id if one helps or misleads):"]
    for e, _ in hits:
        target = e.get("fields", {}).get("target", "")[:200]
        lines.append(f"- ({e['id']}) {e['title']}: {target}")
    return "\n".join(lines)[:budget_chars]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_recall.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/recall.py tests/engine/test_recall.py
git commit -m "feat(engine): recall matcher — deterministic ready-observation lookup for the hook path"
```

---

### Task 6: Recall wiring + PreCompact snapshot hook

**Files:**
- Modify: `hooks/scripts/user_prompt_submit.py`
- Create: `hooks/scripts/pre_compact.py`
- Modify: `hooks/hooks.json`
- Modify: `tests/engine/test_hook_scripts.py` (append tests)

**Interfaces:**
- Consumes: `recall.load_observations/eligible/match/render` (Task 5); existing capture flow (classify/scrub/append_flag).
- UserPromptSubmit new flow: (1) `[robium-recall]`-prefixed prompts return immediately (unchanged guard); (2) capture runs exactly as today (including the >500-char remember exception and early classify miss) but NO LONGER `return`s before recall; (3) recall runs on every non-marker prompt: hits → `emit_context("UserPromptSubmit", render(hits))`. Zero matches → no stdout (silent default preserved).
- PreCompact hook (spec §12 compaction-loss defense): copies `<cwd>/.robium/queue.jsonl` to `<cwd>/.robium/queue-precompact.jsonl` (single rolling snapshot — latest wins, matching the archiver's idempotent style). Stdin: `{session_id, cwd, trigger}`. Fail-open, silent.

- [ ] **Step 1: Append the failing tests**

Append to `tests/engine/test_hook_scripts.py` (reuses its `run_hook`/`read_queue` helpers):

```python
OBS_READY = """## costmap inflation missing <!-- id: obs-nav2-007 -->
status: ready
proof: 2
signal: wrong-guidance
sources: [lrn-1]
target: nav2#costmap-inflation (update) — robot hugs obstacles without inflation_layer
evidence: ✓ ✓ ✓
"""


def _seed_obs(tmp_path):
    d = tmp_path / "learnings" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(OBS_READY)


def test_ups_injects_recall_on_match(tmp_path):
    _seed_obs(tmp_path)
    r = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "why does the robot hug obstacles? costmap inflation maybe"})
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert ctx.startswith("[robium-recall]") and "obs-nav2-007" in ctx


def test_ups_capture_and_recall_coexist(tmp_path):
    _seed_obs(tmp_path)
    r = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "no, the costmap inflation obstacles fix was wrong"})
    assert read_queue(tmp_path)  # correction captured
    assert "obs-nav2-007" in r.stdout  # and recall injected


def test_ups_silent_when_no_match_or_marker(tmp_path):
    _seed_obs(tmp_path)
    r1 = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path), "prompt": "please write a launch file for the lidar"})
    assert r1.stdout.strip() == ""
    r2 = run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path),
        "prompt": "[robium-recall] costmap inflation obstacles"})
    assert r2.stdout.strip() == "" and read_queue(tmp_path) == []


def test_pre_compact_snapshots_queue(tmp_path):
    run_hook("user_prompt_submit.py", {
        "hook_event_name": "UserPromptSubmit", "session_id": "s9",
        "cwd": str(tmp_path), "prompt": "no, wrong distro again"})
    r = run_hook("pre_compact.py", {"hook_event_name": "PreCompact",
                 "session_id": "s9", "cwd": str(tmp_path), "trigger": "auto"})
    assert r.returncode == 0
    snap = tmp_path / ".robium" / "queue-precompact.jsonl"
    assert snap.exists()
    assert snap.read_text() == (tmp_path / ".robium" / "queue.jsonl").read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v -k "recall or coexist or pre_compact or no_match"`
Expected: FAIL (no injection / no script).

- [ ] **Step 3: Rewrite `hooks/scripts/user_prompt_submit.py` main() and add `pre_compact.py`**

`user_prompt_submit.py` — replace `main()` with (keep the module docstring, imports pattern, and the fail-open `__main__` block exactly as they are; docstring gains one line: "Also injects recall context (spec §5) — the short loop."):

```python
def main() -> None:
    from classify import classify_prompt, is_remember
    from recall import eligible, load_observations, match, render
    from robium_hooks import append_flag, emit_context, excerpt, read_event
    from scrub import scrub

    event = read_event()
    prompt = event.get("prompt") or ""
    cwd = event.get("cwd") or ""
    if prompt.startswith("[robium-recall]"):   # engine-injected content is never re-captured
        return

    if len(prompt) <= 500 or is_remember(prompt):
        hit = classify_prompt(prompt)
        if hit:
            append_flag(cwd, {
                "type": hit["type"],
                "confidence": hit["confidence"],
                "session": event.get("session_id", ""),
                "excerpt": excerpt(scrub(prompt)),
            })

    try:
        entries = [e for e in load_observations(cwd) if eligible(e)]
        text = render(match(prompt, entries))
        if text:
            emit_context("UserPromptSubmit", text)
    except Exception:
        pass  # recall is best-effort; capture must not be harmed by it
```

`hooks/scripts/pre_compact.py`:

```python
#!/usr/bin/env python3
"""PreCompact hook — snapshot the queue before compaction (spec §12).

The queue file lives outside the context window, but a snapshot is cheap
insurance against any compaction-adjacent loss. Latest wins. Fail-open.
"""
import os
import shutil
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from robium_hooks import read_event

    event = read_event()
    cwd = event.get("cwd") or ""
    q = os.path.join(cwd, ".robium", "queue.jsonl")
    if os.path.exists(q) and os.path.getsize(q) > 0:
        shutil.copy2(q, os.path.join(cwd, ".robium", "queue-precompact.jsonl"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

`hooks/hooks.json` — add alongside the existing five registrations:

```json
"PreCompact": [
  {
    "hooks": [
      { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/pre_compact.py\"" }
    ]
  }
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v`
Expected: all PASS (13 Phase-1 + 4 new). Then full suite green, and:
`python3 -c "import json; json.load(open('hooks/hooks.json')); print('OK')"` → OK.

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/user_prompt_submit.py hooks/scripts/pre_compact.py hooks/hooks.json tests/engine/test_hook_scripts.py
git commit -m "feat(engine): recall injection in UserPromptSubmit + PreCompact queue snapshot"
```

---

### Task 7: The `learning-loop` skill

**Files:**
- Create: `skills/learning-loop/SKILL.md`
- Create: `skills/learning-loop/references/delta-format.md`
- Create: `skills/learning-loop/references/promotion-bar.md` (adapted from skill-updater)
- Create: `skills/learning-loop/references/refine-passes.md` (adapted from skill-refiner)

**Interfaces:**
- Consumes: every engine tool by prose reference (scripts/engine/…, hooks recall). The retirements happen in Task 8 — this task only ADDS (validator goes to 26 temporarily; that is expected and Task 8 brings it to 24; do not update CLAUDE.md counts in this task).
- Produces: the pipeline's user surface — modes status / consolidate / absorb / refine — that Tasks 10–11 execute.

- [ ] **Step 1: Write `skills/learning-loop/SKILL.md`**

Exact content (validator section order; description ≤1024 chars):

````markdown
---
name: learning-loop
version: 0.1.0
description: >
  The session-side surface of robium's learning engine: consolidate captured
  flags and learnings into evidence-counted observations, absorb ready
  observations into anchor-targeted skill-edit PRs via the deterministic
  delta pipeline, refine (prune/dedup/staleness) through the same pipeline,
  and report loop health. Use when: 'consolidate', 'absorb', 'run the loop',
  'update my skills', 'absorb these learnings', 'refine the skills',
  'learning loop status', end-of-block retros, promoting .robium/queue.jsonl
  flags, or drafting an absorb/refine PR. Everything before git merge may run
  autonomously; nothing lands on main skills/** without a human merge. Not
  for: mining external repos (mining), fresh skill authoring or the quality
  bar (skill-author), building robot applications (architect).
---

# Learning loop — consolidate, absorb, refine

The engine's session-side pipeline (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md
§5–§8). Capture happens automatically (plugin hooks); this skill turns what
was captured into observations, and observations into reviewable skill-edit
PRs. The human gate is git merge.

## When to use this skill

- Promoting queue flags and completing dated learnings entries ("consolidate",
  a Stop-hook nudge, end of a work block).
- Drafting skill edits from ready observations ("absorb", "update my skills",
  "run the loop") — output is always a PR branch, never a direct edit.
- Catalog hygiene passes ("refine the skills") — prune/dedup/staleness through
  the same delta pipeline, report-first.
- Loop health ("learning loop status"): queue depth, unabsorbed backlog,
  eval-suite size, ledger totals.
- For distilling external repos, use the mining skill; for authoring a new
  skill from scratch, skill-author.

## Key directives

- Delegation posture: **embed** — the workflows live here; the deterministic
  tools live at scripts/engine/ (apply_deltas.py, run_trigger_evals.py,
  ledger.py, mine_transcripts.py, skill_metrics.py, observations.py) and in
  the plugin hooks (recall).
- **Scripts hold the pen.** <!-- id: scripts-hold-the-pen --> LLM roles draft
  deltas and diagnose; apply_deltas.py applies them (snapshot, bump,
  changelog, sidecars). Never hand-edit a skill during absorb; never bypass
  the script's refusals — a refusal is a design signal, not an obstacle.
- **Consolidation never touches skills/ content.** <!-- id: consolidate-write-surface -->
  Its write surface is learnings/, learnings/observations/, and the
  evidence/evals sidecars — that boundary is what makes it autonomous-safe.
- **Absorb consumes status: ready only.** <!-- id: absorb-ready-only --> The
  ready bar (proof ≥ 2 | user-correction | three-part evidence | external
  official) is enforced by the observations lint; do not absorb around it.
- **Merge is the gate.** <!-- id: merge-is-the-gate --> Every absorb/refine
  run ends in a PR with the evidence table; no agent merges to main
  skills/**. Mid-build sessions capture; they never edit skills directly.
- **Dedup against everything seen** <!-- id: dedup-against-rejected --> —
  including absorbed and rejected observations — or judged-rejected findings
  reappear forever.
- **One self-check round** <!-- id: one-self-check-round --> on consolidator
  and absorber output: re-read the draft against the source transcript
  window for misattribution, missed dead-ends, wrong anchors, before writing.

## Quick start

Consolidate (autonomous-safe), then absorb to a PR:

```bash
# status: what's pending?
wc -l .robium/queue.jsonl                 # flags
grep -rc "status: ready" learnings/observations/*.md
uv run scripts/engine/skill_metrics.py    # catalog health

# consolidate: promote flags + complete entries + merge into observations
# (LLM workflow — see Decision guidance; writes learnings/ + sidecars only)

# absorb: draft deltas from ready observations, then:
uv run scripts/engine/apply_deltas.py deltas.yaml --dry-run   # review the report
git checkout -b loop/absorb-$(date +%F)
uv run scripts/engine/apply_deltas.py deltas.yaml
uv run skills/skill-author/scripts/validate_skills.py
uv run scripts/engine/run_trigger_evals.py --skills <touched...> \
  --flip-gate-baseline archive/<skill>/<old-version> --flip-skill <skill>
gh pr create --title "loop: absorb <topic>" --body-file report.md
```

## Decision guidance

**Consolidate** (spec §6) — inputs: queue flags, miner output
(scripts/engine/mine_transcripts.py over .robium/transcripts/), unconsolidated
learnings entries; each resolved to its archived-transcript window and read in
full context. Steps: promote flags that clear the noise bar into schema-v2
entries (verbatim text preserved); complete hand-written entries (evidence,
skill tags, recurrence); merge into observations per the schema README's
merge-on-same-finding and evolve-don't-overwrite rules; increment ledgers
(scripts/engine/ledger.py) with sources; harvest eval cases (no-skill-fired →
triggers.positive of the right skill, misfires → triggers.negative); draft
the end-of-block retro for human sign-off; attribute successes (green blocks
credit helpful to the anchors whose guidance shaped the actions — best-effort,
neutral by default). Then the self-check round.

**Absorb** (spec §7.1) — on ready observations: branch loop/absorb-YYYY-MM-DD;
draft deltas feedback-conditioned (current SKILL.md + observation's symptom/
fix/dead-ends + smallest-edit directive + placement rule — run
scripts/engine/placement.py per finding); apply via apply_deltas.py; verify
(validator → trigger evals → flip gate); scoped dup check over touched skills;
PR with the evidence table (per edit: skill, anchor, op, observation link,
sources, eval results). See the delta-format reference for op semantics.

**Refine** — the five passes (see the refine-passes reference) re-armed on
ledgers: prune harmful>0 ∧ helpful=0 first; dedup seeds from
skill_metrics.py --dupes; staleness (90-day windows) unchanged; usage reads
retro lines; growth review reads the archive. Output: retire/move/annotate
deltas through the same pipeline → PR. Scoped refine after every absorb; full
refine ~monthly.

**Recall** runs without invocation (UserPromptSubmit hook): ready
observations matching the prompt inject as [robium-recall] context, citing
ids. A wrong recall is capture signal — name the id and correct it; the
consolidator counts it harmful.

## Platform gotchas

- apply_deltas refuses an op whose archive dir already exists — that means a
  prior run bumped without merging. Rebase/merge the pending PR first.
- The trigger-eval judge shells to the claude CLI; offline or in CI without
  a key, pass --no-llm for the deterministic fallback (results are then
  keyword-based — good for gating, weaker for judging close calls).
- evidence.yaml and evals.yaml are engine-written; hand-edits will be
  overwritten and break increment audit trails.

## Customization

- User tier (Phase 4): same modes with observations under .robium/ and the
  absorb destination an overlay under .claude/skills/ — the workflows are
  path-parameterized, nothing else changes.
- Eval-case harvest thresholds and the recall budget are constants in the
  hook scripts; tune per install, not per session.

## References

- `references/delta-format.md` — op semantics, deltas.yaml schema, refusal rules.
- `references/promotion-bar.md` — queue→facts→observations promotion criteria.
- `references/refine-passes.md` — the five hygiene passes, evidence-armed.
- `references/learnings-loop.md` — the pre-engine hardening process (history + the manual fallback).
- Engine tools (repo root): scripts/engine/ — apply_deltas.py,
  run_trigger_evals.py, ledger.py, mine_transcripts.py, skill_metrics.py.
- Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §5–§8, §10.

## Changelog

- 0.1.0 (2026-08-XX): initial skill — consolidate/absorb/refine/status modes
  over the Phase 2b delta pipeline; absorbs skill-updater's promotion bar and
  skill-refiner's five passes as references (learning-engine Phase 2b, §13).
````

- [ ] **Step 2: Write `references/delta-format.md`**

Author fresh (~60 lines): the deltas.yaml schema exactly as Task 2's interface block documents it (copy that YAML example verbatim), the five ops with one-paragraph semantics each (add/update/retire/move/annotate — including retire's ledger rule, move's two-skill bump, annotate's file variant), the refusal table (anchor-drop content, existing archive dir, 500-line cap, helpful>0 retire, major-without-evals_confirmed), bump inference (add/update/move/retire → minor; annotate-only → build; major only by override), and the dry-run + report-table contract.

- [ ] **Step 3: Write `references/promotion-bar.md` and `references/refine-passes.md`**

Adapt (do not invent): promotion-bar.md carries skill-updater's promotion criteria — read `skills/skill-updater/SKILL.md` (the sections covering which learnings qualify for absorption, the two-gate rationale, and the smallest-edit directive) and restate them as the engine's promotion bar: queue→Tier-1 noise bar, Tier-1→observation evidence bar (already in the observations README — cite it, don't duplicate the field table), observation→delta placement rule. refine-passes.md carries skill-refiner's five passes — read `skills/skill-refiner/SKILL.md` and restate each pass (prune, dedup, staleness, usage/retirement, growth review) with its new evidence arm (ledger counters, retro lines, archive stats) per spec §10. Both files: single-topic, 5–10 KB, prose references to other skills' files without backticks, each ending with a provenance line "Adapted from skill-updater 1.1.1 / skill-refiner 1.0.1 at retirement (2026-08-XX)."

- [ ] **Step 4: Validator + backtick check + commit**

```bash
uv run skills/skill-author/scripts/validate_skills.py   # expect: Checked 26 skills: PASS (temporary — Task 8 lands 24)
grep -nE '`[^`]*(/|\.md|\.py|\.yaml)[^`]*`' skills/learning-loop/SKILL.md  # only same-skill references/ paths + fenced blocks
git add skills/learning-loop
git commit -m "feat(skills): learning-loop skill — consolidate/absorb/refine surface over the delta pipeline"
```

(Replace 2026-08-XX in the changelog/provenance lines with the actual date at execution.)

---

### Task 8: Meta-skill restructure — retire skill-updater + skill-refiner

**Files:**
- Move: `skills/skill-updater/` → `archive/skill-updater/1.1.1/`
- Move: `skills/skill-refiner/` → `archive/skill-refiner/1.0.1/`
- Move: `skills/skill-refiner/scripts/skill_metrics.py` → also copied to `scripts/engine/skill_metrics.py` (live home; archive keeps its copy)
- Move: `skills/skill-author/references/learnings-loop.md` → `skills/learning-loop/references/learnings-loop.md`
- Modify: `skills/skill-author/` (1.1.3 → 2.0.0 + evals.yaml seeded), `skills/architect/SKILL.md` (1.7.0 → 1.8.0), `skills/mining/SKILL.md` (0.1.0 → 0.1.1)
- Create: `archive/skill-author/1.1.3/`, `archive/architect/1.7.0/`, `archive/mining/0.1.0/` (pre-edit snapshots)
- Modify: `README.md`, `CONTRIBUTING.md` (counts + table rows)

**Interfaces:** catalog lands at 24 (25 − 2 + 1); spec §13 executed in full.

- [ ] **Step 1: Retirements and moves (order matters — snapshots of edited skills first)**

```bash
mkdir -p archive/skill-author archive/architect archive/mining
cp -R skills/skill-author archive/skill-author/1.1.3
cp -R skills/architect archive/architect/1.7.0
cp -R skills/mining archive/mining/0.1.0
git mv skills/skill-updater archive/skill-updater/1.1.1
git mv skills/skill-refiner archive/skill-refiner/1.0.1
cp archive/skill-refiner/1.0.1/scripts/skill_metrics.py scripts/engine/skill_metrics.py
git mv skills/skill-author/references/learnings-loop.md skills/learning-loop/references/learnings-loop.md
```

Then edit `scripts/engine/skill_metrics.py`'s usage docstring: the two `python3 skills/skill-refiner/scripts/skill_metrics.py …` lines become `uv run scripts/engine/skill_metrics.py …`; and edit the moved learnings-loop.md's opening line to state it is the pre-engine manual process, kept as history + fallback (one sentence; content otherwise unchanged).

- [ ] **Step 2: skill-author 2.0.0 (major — loses Modes 2 and 3, per spec §13)**

In `skills/skill-author/SKILL.md`:
(a) Description rewrite (keep ≤1024 chars): capability = fresh authoring + quality bar + validator custody ONLY. New description:

```
Author new robium skills and enforce the catalog quality bar. Owns the
authoring workflow from skills/_TEMPLATE, the quality bar
(references/quality-bar.md: template compliance, trigger-surface
descriptions, <500-line bodies, stated delegation posture, upstream links,
no invented syntax), and scripts/validate_skills.py — run it after ANY
skills/ change. Use when: 'write a new robium skill', 'new skill for X',
template compliance questions, description/trigger-surface tuning, or
validator failures. Wraps Claude's skill-creator skill for evals and
description tuning instead of reinventing it. Not for: absorbing learnings
or refining the catalog (learning-loop), mining example repos (mining),
building robot applications (architect and the domain skills).
```

(b) Body: delete the Mode 2 and Mode 3 sections entirely; delete the intro's "three ways skill content enters the catalog" sentence (now: "the authoring machinery: fresh authoring against the quality bar; absorption and refining live in the learning-loop skill, mining in the mining skill"); update the References section (learnings-loop.md is gone — remove its line; keep mining-guide.md with a note "pattern-recognition heuristics — consumed by the mining skill"; quality-bar.md unchanged); When-to-use cross-refs updated to learning-loop/mining. (c) Frontmatter `version: 2.0.0`. (d) Changelog top line:

```markdown
- 2.0.0 (2026-08-XX): restructure — Modes 2 (mining) and 3 (hardening) moved
  to the mining and learning-loop skills; skill-author is authoring + quality
  bar + validator custody only (learning-engine Phase 2b, spec §13).
```

(e) Seed `skills/skill-author/evals.yaml` (co-evolving-evals rule for a major bump):

```yaml
triggers:
  positive:
    - phrase: write a new robium skill for depth cameras
      source: learning-engine Phase 2b restructure
  negative:
    - phrase: absorb these learnings into the skills
      expect: learning-loop
    - phrase: mine the nav2 tutorials repo for patterns
      expect: mining
tasks: []
```

- [ ] **Step 3: architect 1.8.0 and mining 0.1.1**

architect (routing table, Verification & meta): remove the `skill-updater` row; add after the `mining` row:

```markdown
| `learning-loop` | Consolidating captured learnings into observations and absorbing them into skill-edit PRs — the engine's session-side pipeline. Not an app-building skill. |
```

Changelog top line: `- 1.8.0 (2026-08-XX): routing — learning-loop added; skill-updater row removed (retired to archive; learning-engine Phase 2b).`

mining SKILL.md (three pointer updates, build bump 0.1.0 → 0.1.1): description's "absorbing robium's own session learnings (skill-author hardening, until the learning-loop skill lands)" → "absorbing robium's own session learnings (learning-loop)"; the When-to-use bullet "use skill-author hardening (learning-loop supersedes it in Phase 2b)" → "use the learning-loop skill"; References' "skill-author skill's mining-guide reference" line stays (the file still lives there). Changelog: `- 0.1.1 (2026-08-XX): pointers updated — learning-loop landed; hardening references retargeted.`

- [ ] **Step 4: Counts and tables**

README.md: "25 skills: 13 umbrellas and 12 tool skills" → "24 skills: 12 umbrellas and 12 tool skills"; remove the skill-updater and skill-refiner table rows; add a learning-loop row after mining (one line, description paraphrasing the frontmatter). CONTRIBUTING.md: "Checked 25 skills: PASS" → 24. (CLAUDE.md is Task 9's — do not touch it here.)

- [ ] **Step 5: Sweep + verify + commit**

```bash
# live stale refs to the retired skills (changelog lines in other skills are frozen history — leave)
grep -rn "skill-updater\|skill-refiner" skills/ README.md CONTRIBUTING.md cli/ website/ --include="*.md" | grep -v "Changelog\|changelog\|- 1\.\|- 0\." 
uv run skills/skill-author/scripts/validate_skills.py     # Checked 24 skills: PASS
uv run --with pytest --with pyyaml -m pytest tests/engine -q
uv run scripts/engine/skill_metrics.py --skills-dir skills | tail -3   # moved tool runs
git add -A
git commit -m "feat(skills): meta restructure — retire skill-updater/skill-refiner, skill-author 2.0.0, architect 1.8.0, catalog at 24"
```

Any live hit from the grep (outside frozen changelog lines and archive/) gets fixed in this commit — expected hits: skill-author's References mention of updater/refiner (rewritten in Step 2), possibly cli/ or website/ prose. Investigate each; CLAUDE.md hits are expected and deferred to Task 9.

---

### Task 9: CLAUDE.md policy rewrite + doc pointers

**Files:**
- Modify: `CLAUDE.md`
- Modify: `learnings/README.md` (absorbed-marker note)

**Interfaces:** spec §7.3 executed: the STRICT policy's intent (no unsupervised skill mutation) is preserved; its mechanism becomes merge-protection + the engine pipeline. This is the plan's most sensitive edit — the text below is the exact replacement; deviations need a reviewer flag.

- [ ] **Step 1: CLAUDE.md — Modes section**

The "Authoring / hardening skills" bullet becomes two:

```markdown
- **Authoring skills** → you are producing new `skills/**` content with the `skill-author` skill (quality bar + validator). The engine-era update policy below governs how edits land.
- **Running the learning engine** → consolidate/absorb/refine with the `learning-loop` skill, mine external repos with `mining`. Everything up to a PR may run autonomously; nothing merges to `main` `skills/**` without a human.
```

- [ ] **Step 2: CLAUDE.md — "Two hats, one rule" section becomes "Two hats, one gate"**

Replace the section body (the four bullets under "### Two hats, one rule") with:

```markdown
- **During a build**: use the skills as a client would. Do NOT edit robium's skills mid-build and do NOT quietly substitute your own knowledge — capture the learning (hooks catch most of it; write the entry when it's nuanced), then proceed however the build needs. Same-session skill edits are forbidden even when the fix looks obvious.
- **Capture is automatic; consolidation is autonomous-safe.** The `learning-loop` skill's consolidate mode may run without asking: its write surface is `learnings/`, `learnings/observations/`, and the evidence/evals sidecars — never SKILL.md or references content.
- **Absorption runs to a PR, never to main.** "Absorb", "update my skills", "run the loop" → the learning-loop skill drafts anchor-targeted deltas, `scripts/engine/apply_deltas.py` applies them on a `loop/absorb-*` branch (archive snapshot + version bump + changelog, enforced by the script), verification gates run (validator, trigger evals, flip gate), and the result is a PR with an evidence table. Merging is the human gate — Gate 1 is the observation `status:` field (visible and editable in git), Gate 2 is PR review. If you prefer the old conversational gates, invoke the modes interactively and approve each step; the pipeline doesn't schedule itself.
- **Between builds**: full refine passes (`learning-loop` refine mode) and mining runs (`mining`) — same PR gate.
```

- [ ] **Step 3: CLAUDE.md — "Skill update policy (STRICT — no exceptions)" section**

Replace the four numbered items with (title becomes "## Skill update policy (engine era — merge is the gate)"):

```markdown
1. **No agent merges to `main` `skills/**`. Ever.** The engine may capture, consolidate, and draft absorb/refine PRs autonomously; a human merges. Mid-build sessions never edit skills directly — they capture; the pipeline absorbs. This holds in fully autonomous runs: autonomy extends to the PR, never past it.
2. **Direct skill edits outside the pipeline** (hand-fixing a typo, restructuring a section in conversation) still require the user's explicit ask, and still follow the mechanics: archive snapshot to `archive/<name>/<old-version>/`, version bump, changelog line, same commit. When in doubt, route through the pipeline — apply_deltas does the mechanics for you.
3. **Version + archive on every change** — unchanged from day one, now script-enforced: apply_deltas refuses to run without a clean snapshot slot; bump semantics (build/minor/major) per the quality bar; a major bump requires re-confirming the skill's `evals.yaml` in the same PR (co-evolving evals).
4. The canonical process lives in the `learning-loop` skill (delta format, promotion bar, refine passes) and `skills/skill-author/references/quality-bar.md` item 9 (versioning). If any doc contradicts this policy, this policy wins — fix the doc.
```

- [ ] **Step 4: CLAUDE.md — remaining pointer sweep**

Update in place: the capture section's line "promote flagged items into a dated entry at the next natural break" gains "— or say 'consolidate' (learning-loop)"; the plugin-architecture bullet's skill count 25 → 24 and umbrella list swaps `skill-updater, skill-refiner` for `learning-loop`; the commands comment "Checked 25 skills: PASS" → 24; the line "the `skill-updater` skill wraps the same rules for session-end use" is gone with the section rewrite (verify no other live `skill-updater`/`skill-refiner` references remain: `grep -n "skill-updater\|skill-refiner" CLAUDE.md` → zero hits).

- [ ] **Step 5: learnings/README.md**

The absorption-marking rule bullet ("Absorption marking: entries stay in place; `<!-- absorbed: YYYY-MM-DD -->` markers continue until the observations tier (Phase 2) replaces them.") becomes:

```markdown
- Absorption marking: the observations tier is canonical — an absorbed
  finding is `status: absorbed YYYY-MM-DD` in learnings/observations/
  (written by apply_deltas). Legacy `<!-- absorbed -->` markers in old
  entries remain as history; don't add new ones.
```

- [ ] **Step 6: Verify + commit**

```bash
grep -n "skill-updater\|skill-refiner\|STRICT" CLAUDE.md   # expect: no live refs; STRICT only if quoted intentionally — should be zero
uv run skills/skill-author/scripts/validate_skills.py
git add CLAUDE.md learnings/README.md
git commit -m "docs: policy rewrite — merge is the gate; engine-era skill update policy (spec §7.3)"
```

---

### Task 10: Acceptance run A — consolidate the real backlog

**Files:**
- Modify: `learnings/observations/*.md` (session-origin entries join the external ones)
- Create/modify: `skills/*/evidence.yaml`, `skills/*/evals.yaml` (harvest)
- Modify: `learnings/*.md` (entry completion only — verbatim content is never rewritten)
- Produce (gitignored): a retro draft at `.robium/retro-draft.md`

**Interfaces:** the learning-loop skill's consolidate mode (Task 7), run for real on: the 38 flags in `/Users/robium/repos/robium/.robium/queue.jsonl`, the archived transcripts, and the 12 dated `learnings/*.md` files. This is an agent-workflow task; the deterministic gates are the observations lint, the validator (sidecar schemas), and the review.

- [ ] **Step 1: Inventory pass** — list every unconsolidated signal: flags by type/session; learnings entries without `<!-- absorbed -->` markers; entries WITH markers get dedup-checked against observations only (never re-absorbed). Write the inventory to the task report before writing anything.
- [ ] **Step 2: Consolidate per the skill's Decision guidance** — promote above-noise flags to schema-v2 entries in the correct dated files (create `learnings/2026-08-XX.md` for newly-promoted items, citing `source: transcript <session>#…`); complete existing entries (evidence fields, recurrence counts); merge into `learnings/observations/<skill>.md` per merge-on-same-finding (session-origin entries have NO `origin: external` and need no quote; the ready bar applies as-is). Cap: quality over coverage — an entry that can't cite its transcript window stays tentative with a note.
- [ ] **Step 3: Ledger + eval harvest** — `uv run scripts/engine/ledger.py …` per attributable signal (✓ entries and user-corrections naming an anchor); no-skill-fired phrasings → the target skill's `evals.yaml` `triggers.positive` with `source:`; misfires → `triggers.negative`. Only entries with a real anchor or phrase — no padding.
- [ ] **Step 4: Self-check round** (skill directive): re-read every new observation against its transcript window; fix misattributions; note the check in the task report.
- [ ] **Step 5: Verify + commit**

```bash
python3 scripts/engine/observations.py --check learnings/observations/*.md
uv run skills/skill-author/scripts/validate_skills.py    # sidecar schemas checked; still 24
uv run --with pytest --with pyyaml -m pytest tests/engine -q
git add learnings skills/*/evidence.yaml skills/*/evals.yaml
git commit -m "feat(loop): acceptance run A — backlog consolidated to observations; ledgers + eval harvest"
```

---

### Task 11: Acceptance run B — absorb to the exit-criteria PRs

**Files:**
- Create: deltas files (committed to the PR branches for auditability), PR branches `loop/absorb-<date>-external` and `loop/absorb-<date>-session`
- Modify (on branches, via apply_deltas only): touched `skills/**`, `archive/**`, observation statuses

**Interfaces:** learning-loop absorb mode end-to-end, twice: (1) **external** — the strongest `ready` observations from the 2a mining pilots (obs-ros2-001/003, obs-nav2-001/002, obs-gazebo-001/003 are the candidates; pick 3–5 by evidence strength) → the spec's "≥1 merged evidence-bearing skill PR sourced from an external repo" candidate; (2) **session** — `ready` observations from run A → the "backlog processed end-to-end into ≥1 merged PR" candidate. Merging is the user's act after this plan; the PRs must be merge-ready.

Per branch, exactly the skill's absorb flow:

- [ ] **Step 1: Draft deltas** — feedback-conditioned per observation (smallest edit; placement tool consulted; for external observations re-verify citations first: `python3 scripts/engine/verify_citations.py --repos /Users/robium/repos/robium/.robium/mining learnings/observations/<file>.md` must PASS on the entries being absorbed). Write `deltas-<topic>.yaml`; run `--dry-run` and review the report — every no-op/refusal must be understood before applying.
- [ ] **Step 2: Apply + verify**

```bash
git checkout -b loop/absorb-<date>-<topic>
uv run scripts/engine/apply_deltas.py deltas-<topic>.yaml
uv run skills/skill-author/scripts/validate_skills.py
uv run scripts/engine/run_trigger_evals.py --skills <touched…> --no-llm   # + LLM run if key available; say which ran
# flip gate per touched skill with its fresh archive snapshot:
uv run scripts/engine/run_trigger_evals.py --skills <skill> --no-llm \
  --flip-gate-baseline archive/<skill>/<pre-bump-version> --flip-skill <skill>
uv run --with pytest --with pyyaml -m pytest tests/engine -q
```

- [ ] **Step 3: Scoped dup check** — grep the touched skills for near-duplicates of the new content (fresh absorption is where duplication enters); fold or drop.
- [ ] **Step 4: PR** — `git push -u origin <branch>`; `gh pr create` with the evidence table (per edit: skill, anchor, op, observation id + link, sources, eval/flip results, and the apply_deltas report table verbatim); body ends with the standard generation footer. The PR body states plainly which gates ran LLM-judged vs `--no-llm` fallback (citation-honesty rule applies to the PR too).
- [ ] **Step 5: Repeat for the second branch** (each PR stands alone; the second branches from main, not from the first).
- [ ] **Step 6: Record PR URLs in the task report.** Do NOT merge.

---

### Task 12: Recall demonstration + exit checklist + changelog

**Files:**
- Modify: `docs/CHANGELOG.md`

- [ ] **Step 1: Recall demo (deterministic)** — with run A's observations in place:

```bash
echo '{"hook_event_name":"UserPromptSubmit","session_id":"demo","cwd":"'$PWD'","prompt":"<a phrase matching a real ready observation>"}' \
  | python3 hooks/scripts/user_prompt_submit.py
```

Expected: hook JSON on stdout whose additionalContext starts `[robium-recall]` and cites a real obs id. Record the exact command + output in the task report. (The organic "helped a live session" criterion accrues after merge — the report says so; no claim beyond the demo.)

- [ ] **Step 2: Exit checklist (spec §15 Phase 2 row, 2b slice)**

- [ ] Delta pipeline: apply_deltas + ledger + trigger evals + flip gate shipped with green suites.
- [ ] Recall hook live in the plugin (UserPromptSubmit injection + PreCompact snapshot), demo recorded.
- [ ] learning-loop in the catalog; skill-updater + skill-refiner retired to archive/; catalog at 24; validator green.
- [ ] CLAUDE.md policy rewritten (merge is the gate); no live STRICT-era references.
- [ ] Backlog processed: 12 files + 38 flags consolidated (run A commit); observations lint green.
- [ ] Two absorb PRs open with evidence tables — one external-sourced, one session-sourced — awaiting human merge (the two merge-dependent exit criteria complete at merge; the plan's deliverable is the merge-ready PRs).
- [ ] Full battery: engine tests, validator, observations lint, citation verify (with --repos absolute path), manifests.

- [ ] **Step 3: Changelog + commit** — append under a new dated heading (HISTORY ONLY — no forward-looking sentences; the Phase-2a review caught exactly this):

```markdown
## 2026-08-XX — Learning engine Phase 2b: consolidate + absorb + recall

Delta pipeline (apply_deltas: anchor-targeted ops, snapshot/bump/changelog,
ledger-aware refusals, co-evolving evals), evidence-ledger tool, trigger-eval
runner + flip gate, recall injection in the UserPromptSubmit hook + PreCompact
queue snapshot. learning-loop skill lands; skill-updater and skill-refiner
retired to archive/ (catalog at 24); skill-author 2.0.0 (authoring + quality
bar only); CLAUDE.md policy rewritten — merge is the gate. Backlog (12
learnings files + 38 flags) consolidated to observations with ledger and
eval harvest; two absorb PRs opened (external-sourced and session-sourced)
with evidence tables. Recall demonstrated end-to-end.
Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §5–§8, §13.
```

```bash
git add docs/CHANGELOG.md
git commit -m "docs: changelog — learning engine Phase 2b (consolidate + absorb + recall)"
```

---

## Self-review notes (performed at plan-writing time)

- **Spec coverage (Phase 2 row remainder):** consolidator incl. success attribution + self-check → Task 7 (workflow prose) + Task 10 (execution); recall hook → Tasks 5–6 (incl. §5 guardrails: deterministic, budget-capped, eligibility, marker, misfire-traceable ids); delta format + apply_deltas incl. co-evolving evals → Tasks 2–3; trigger-eval runner + flip gate → Task 4; absorb→PR flow → Task 7 (workflow) + Task 11 (execution); CLAUDE.md policy rewrite → Task 9 (exact text); meta restructure → Tasks 7–8 (learning-loop + mining land — mining landed in 2a, its pointers update here; updater/refiner retire; 24 = 25 − 2 + 1). §14's pipeline acceptance test → Tasks 10–11 on the real backlog. §12 items shipped here: PreCompact snapshot (Task 6), timeboxed judge with fallback (Task 4), no-op delta fallback + cap + retire rules (Tasks 2–3).
- **Known simplifications (deliberate, recorded):** success attribution (spec §6 step 7) ships as workflow guidance executed best-effort in Task 10, not as a script — the transcript-reading judgment is the LLM's role by design. GitHub branch-protection for `skills/**` is an ops setting the user flips in repo settings; the policy text governs agent behavior regardless. `annotate`-on-anchor shares update's code path (build-level via the bump-kind set only when it is the sole op kind — matching §7.2's "status/verification marker change" intent).
- **Type consistency:** report dict keys (`applied/noop/refused/skills_bumped/notes`) consistent between Tasks 2–3 and the CLI printer; `find_anchor_block` returns `(start, end)` and both update and retire consume it; ledger entry shape (`helpful/harmful/last_verified/sources`) matches spec §4.2's example and the validator's existing sidecar schema check; recall's parser field names mirror observations.py's (`id/title/fields` + status/proof pulled up) — divergence is one-directional simplification, documented in both docstrings.
- **Placeholder scan:** all engine code and tests complete; Task 7's two adapted references specify exact source files and required content rather than embedding 400 lines of prose that already exists in-repo — the per-task reviewer compares output against the named sources; Task 9 embeds the exact CLAUDE.md replacement text; acceptance tasks are agent-workflow tasks gated by the deterministic checkers plus content review, same pattern the 2a pilots proved.
- **Ordering constraint verified:** Task 7 (learning-loop) precedes Task 8 (retirements) so the catalog never lacks an owner for absorption guidance; validator counts are explicit per task (25 → 26 → 24). Task 9 lands before the acceptance runs so runs A/B execute under the policy they demonstrate.
