# Learning Engine Phase 2a — Shared Core + Mining — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the learning engine's shared core (observations tier + extraction schema + citation verifier + overlap/placement analyzer) and the new `mining` catalog skill, then pilot mining on three SOURCES.md repos — per spec `docs/superpowers/specs/2026-08-01-learning-engine-design.md` §4.5, §6a, and the "shared core first, mining goes first" ordering in the Phase 2 row of §15.

**Architecture:** Deterministic tooling (stdlib Python at `scripts/engine/`) gives both experience sources — sessions and external repos — one observation format with lintable rules, grep-verified citations, and a keyword-overlap placement report. The `mining` skill is a new umbrella skill (natural-language workflow, no invented syntax) that drives registry-approved survey→deep and comparative runs, writing observations with `origin: external` and engine-maintained crawl records into learnings/SOURCES.md. No skill-content edits come out of mining — that is Phase 2b's absorb pipeline.

**Tech Stack:** Python ≥3.10 stdlib only for `scripts/engine/` (same bar as the Phase 1 hooks); `uv run --with pytest --with pyyaml -m pytest tests/engine -v` for tests; git CLI for pinned clones and `git show`-based citation checks.

**Phase 2 split (standing decision for this plan and the next):** the spec's Phase 2 row ships in two plans. **2a (this plan):** shared core + `mining` skill + 3 pilots — exit: verified, evidence-cited `ready` observations from external repos sitting in the observations tier. **2b (next plan):** consolidator, recall hook, delta format + apply_deltas, trigger-eval runner + flip gate, absorb→PR flow, CLAUDE.md policy rewrite, meta-skill restructure (learning-loop lands; skill-updater/skill-refiner retire) — exit: the spec's Phase 2 exit criteria, including the first merged external-sourced skill PR. Rationale: each plan produces working, testable software; the absorb pipeline consumes what 2a produces.

**Standing decisions recorded (Phase 1 self-review carry-over + new):**
- Engine tooling **stays at `scripts/engine/`** (miner already lives there). The Phase 2b learning-loop skill will reference it there; nothing relocates.
- The three pilots in Tasks 7–9 are **pre-authorized `survey+deep`** by approval of this plan (spec §6a.2 allows registry pre-authorization; the plan review is the human approval act). Survey reports are still written for audit.
- The back-mining outputs from Phase 1 (`.robium/queue.jsonl`, `.robium/mining-report.md`) were lost with the removed worktree (gitignored files). Task 1 regenerates them from the 21 archived transcripts — the miner is deterministic, so nothing is lost.

## Global Constraints

- `scripts/engine/` scripts: **stdlib only**, `python3` ≥3.10, no third-party imports (they must run on any user machine; same bar as Phase 1 hooks).
- Test command for all code in this plan: `uv run --with pytest --with pyyaml -m pytest tests/engine -v` from the repo root.
- Validator after ANY `skills/**` change: `uv run skills/skill-author/scripts/validate_skills.py` — expected `Checked 24 skills: PASS` through Task 4, `Checked 25 skills: PASS` from Task 5 onward (the script counts non-`_TEMPLATE` dirs dynamically; nothing hardcodes the count).
- Every SKILL.md edit follows the STRICT policy mechanics: archive snapshot to `archive/<name>/<old-version>/` **before** the first edit, `version:` bump (build = small fix, minor = content addition, major = restructure), changelog line starting with the new version — all in the same commit.
- Frontmatter stays `name` + `version` + `description` only; description ≤1024 chars.
- **Backtick rule:** backticks around a path/filename only for files inside the same skill's directory; other skills' files and repo-root paths are prose. Grep every new/edited skill file manually — the validator only catches `references/|scripts/|examples/`-prefixed tokens.
- **Citation honesty:** every mined fact carries `repo@short-sha path#Lines`; every docs-consistency claim states how it was checked (direct fetch vs search synthesis — docs.ros.org is chronically bot-blocked; say so when it blocks and add a re-verify prompt). Never write version facts from memory.
- Observations follow the schema in `learnings/observations/README.md` (Task 2). The seven signal types are fixed vocabulary (learnings/README.md): wrong-guidance | no-skill-fired | figured-out-from-scratch | better-method | noise | verified | user-correction.
- Pilot output is capped at **3–6 observations per single-repo run** (quality over bulk; the generic-vs-specific triage of spec §6a.3 applies — transferable patterns distill, project-local choices don't).
- Mining writes **only** `learnings/observations/*.md` + `learnings/SOURCES.md` (+ gitignored `.robium/mining/`). It never touches `skills/**` — the only `skills/**` edits in this plan are the skill-authoring Tasks 5–6 themselves.
- Repo clones live under `.robium/mining/<repo-name>/` (gitignored via the `.robium/` convention); never committed; shallow (`--depth 1`) is fine — the recorded SHA is the clone's HEAD, which `git show` can read.
- New-skill findings from mining are **proposals only** (spec §6a.6): an entry in `learnings/observations/new-skills.md` — no new skill gets authored from pilot findings in this phase.

**File structure created/modified by this plan:**

```
scripts/engine/
  observations.py               # Tier-2 parser + lint (+ --check CLI)
  verify_citations.py           # external-citation verifier (git show + normalized grep)
  placement.py                  # overlap/placement analyzer over the skill catalog
tests/engine/
  test_observations.py  test_verify_citations.py  test_placement.py
learnings/observations/
  README.md                     # Tier-2 schema doc (format contract)
  ros2.md  nav2.md  simulation.md  … (pilot output; per-skill files as placed)
skills/mining/SKILL.md          # NEW skill (thin: SKILL.md only, deepened later)
skills/architect/SKILL.md       # +1 routing row, 1.6.1 → 1.7.0 (archive snapshot)
skills/skill-author/SKILL.md    # Mode-2 narrowing pointer, 1.1.1 → 1.1.2 (archive snapshot)
learnings/SOURCES.md            # pilot rows: status flips + crawl records
CLAUDE.md                       # skill counts 23/24 → 25; umbrella list gains mining
docs/CHANGELOG.md               # dated Phase 2a entry
.robium/queue.jsonl             # regenerated (gitignored, Task 1)
.robium/mining-report.md        # regenerated (gitignored, Task 1)
```

---

### Task 1: Regenerate the back-mining queue (lost with the worktree)

**Files:**
- Read: `.robium/transcripts/*.jsonl` (21 archived files)
- Produce: `.robium/queue.jsonl` + `.robium/mining-report.md` (both gitignored — no commit)

**Interfaces:**
- Consumes: `scripts/engine/mine_transcripts.py` (Phase 1).
- Produces: the flag backlog Phase 2b's consolidator will consume (the spec's "38-flag backlog"; the miner is deterministic so the regenerated count should land in the same range).

- [ ] **Step 1: Confirm the queue is actually absent**

Run: `ls .robium/`
Expected: only `transcripts` (if `queue.jsonl` already exists, skip this task).

- [ ] **Step 2: Re-run the back-mining pass**

```bash
python3 scripts/engine/mine_transcripts.py .robium/transcripts/*.jsonl \
  --queue .robium/queue.jsonl --report .robium/mining-report.md
```

Expected: `mined N flags from 21 transcript(s)` with N > 0 (Phase 1's run produced ~38; a zero here means a regression in `mine_file` — debug against one transcript before proceeding).

- [ ] **Step 3: Scrub spot-check**

Run: `grep -icE "token=|secret|passw" .robium/queue.jsonl || true`
Expected: 0 sensitive-looking hits (pattern hits inside `[REDACTED]` text are fine — eyeball any matches).

No commit — both outputs are gitignored deliverables for Phase 2b.

---

### Task 2: Observations tier — schema doc + parser/lint (`observations.py`)

**Files:**
- Create: `learnings/observations/README.md`
- Create: `scripts/engine/observations.py`
- Test: `tests/engine/test_observations.py`

**Interfaces:**
- Produces (used by Tasks 3, 7–9 and by Phase 2b's consolidator/absorber):
  - `parse_file(path: str) -> list[dict]` — each entry `{"id": str, "title": str, "line": int, "fields": dict[str, str]}`
  - `lint_file(path: str, known_skills: set[str] | None = None) -> list[str]` — human-readable error strings, empty = clean
  - `SIGNALS: frozenset[str]` — the seven signal types
  - CLI: `python3 scripts/engine/observations.py --check <files…> [--skills-dir skills]` → prints `FAIL: …` lines then `Checked N observation file(s): PASS|FAIL`, exit 0/1 (same output contract as the validator)

- [ ] **Step 1: Write `learnings/observations/README.md`**

```markdown
# learnings/observations/

Tier 2 of the learning engine — canonical, proof-counted, absorption-ready
findings (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md
§4.5 + §6a.3). One file per target skill (`<skill>.md`, stem must be a real
skill directory); cross-catalog proposals go in `new-skills.md`. Lint:
`python3 scripts/engine/observations.py --check learnings/observations/*.md`.

## Entry template

    ## costmap inflation missing from quick start <!-- id: obs-nav2-007 -->
    status: ready
    proof: 2
    signal: wrong-guidance
    sources: [lrn-0710-03, lrn-0726-01]
    target: nav2#costmap-inflation (update) — add inflation_layer block to Quick start YAML
    evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓

External (mined) entries add three fields:

    ## single-node composition uses NodeOptions everywhere <!-- id: obs-ros2-001 -->
    status: ready
    proof: 1
    signal: better-method
    sources: [ros2/examples@ab12cd3]
    target: ros2#composition-node-options (add) — composition idiom for rclcpp components
    evidence: official repo, consistent with docs (search-synthesis 2026-08-01 — docs.ros.org fetch blocked; re-verify on absorb)
    origin: external
    source: ros2/examples@ab12cd3 rclcpp/composition/src/manual_composition.cpp#L28-L34
    quote: rclcpp::NodeOptions options;

## Rules (lint-enforced where deterministic)

- **id**: `<!-- id: obs-<file-stem>-NNN -->` at the end of the `##` heading;
  three digits; unique within the file; prefix must match the filename stem.
- **status**: `tentative` | `ready` | `absorbed YYYY-MM-DD` | `rejected (<reason>)`.
  `absorbed`/`rejected` entries stay in place — they are the audit trail and the
  dedup memory (dedup against everything *seen*, spec §6 rule 3).
- **proof**: integer ≥ 1 — count of independent occurrences/sources.
- **signal**: one of the seven types from learnings/README.md. Mined entries
  map: new transferable pattern → better-method; confirms existing skill
  content → verified; contradicts skill content → wrong-guidance; domain no
  skill owns → no-skill-fired (routes to new-skills.md).
- **sources**: non-empty `[a, b, …]` list — `lrn-…` entry ids and/or
  `repo@short-sha` refs (convergence witnesses; only `source:` is quote-verified).
- **target**: `<skill>#<anchor> (add|update|retire|move|annotate) — <what>` for
  anchor-level intents, `<skill> (new-section) — <what>` when no anchor exists
  yet, or in new-skills.md: `new-skill: <proposed-name> — <what>`.
- **ready bar** (spec §4.5 + §6a.4): `status: ready` requires proof ≥ 2, OR
  signal = user-correction, OR the three-part evidence bar (three ✓ marks in
  evidence), OR origin external with the word "official" in evidence (the
  official-source bar — vendor repo consistent with current docs).
- **external contract** (spec §6a.3): `origin: external` requires `source:`
  (`<org>/<repo>@<short-sha> <path>#L<a>[-L<b>]`) and `quote:` (verbatim text
  from those lines). A quote that fails scripts/engine/verify_citations.py is
  a discarded candidate — fix the citation or drop the entry.
- **Merge-on-same-finding**: one canonical entry per finding; new occurrences
  append to sources and bump proof — never sibling entries. Contradictions
  evolve in place: "now X (previously Y per lrn-…)".
```

- [ ] **Step 2: Write the failing tests**

`tests/engine/test_observations.py`:

```python
import observations as obs


GOOD = """## costmap inflation missing from quick start <!-- id: obs-nav2-001 -->
status: ready
proof: 2
signal: wrong-guidance
sources: [lrn-0710-03, lrn-0726-01]
target: nav2#costmap-inflation (update) — add inflation_layer block
evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓

## rotation shim behavior needs tuning flag <!-- id: obs-nav2-002 -->
status: tentative
proof: 1
signal: better-method
sources: [lrn-0724-02]
target: nav2#rpp-rotate-to-heading (update) — note the shim flag
evidence: single occurrence, no check yet
"""

EXTERNAL = """## composition uses NodeOptions <!-- id: obs-ros2-001 -->
status: ready
proof: 1
signal: better-method
sources: [ros2/examples@ab12cd3]
target: ros2#composition-node-options (add) — composition idiom
evidence: official repo, consistent with docs (direct fetch 2026-08-01)
origin: external
source: ros2/examples@ab12cd3 rclcpp/composition/src/manual_composition.cpp#L28-L34
quote: rclcpp::NodeOptions options;
"""


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def test_parse_file_extracts_entries_and_fields(tmp_path):
    entries = obs.parse_file(_write(tmp_path, "nav2.md", GOOD))
    assert [e["id"] for e in entries] == ["obs-nav2-001", "obs-nav2-002"]
    assert entries[0]["fields"]["status"] == "ready"
    assert entries[0]["fields"]["proof"] == "2"
    assert entries[0]["title"].startswith("costmap inflation")


def test_clean_file_lints_clean(tmp_path):
    assert obs.lint_file(_write(tmp_path, "nav2.md", GOOD), {"nav2"}) == []


def test_external_entry_lints_clean(tmp_path):
    assert obs.lint_file(_write(tmp_path, "ros2.md", EXTERNAL), {"ros2"}) == []


def test_id_prefix_must_match_stem(tmp_path):
    errs = obs.lint_file(_write(tmp_path, "gazebo.md", GOOD), {"gazebo", "nav2"})
    assert any("prefix" in e for e in errs)


def test_duplicate_id_rejected(tmp_path):
    errs = obs.lint_file(_write(tmp_path, "nav2.md", GOOD + GOOD), {"nav2"})
    assert any("duplicate" in e for e in errs)


def test_bad_status_and_signal_rejected(tmp_path):
    bad = GOOD.replace("status: ready", "status: pending").replace(
        "signal: wrong-guidance", "signal: bug")
    errs = obs.lint_file(_write(tmp_path, "nav2.md", bad), {"nav2"})
    assert any("status" in e for e in errs) and any("signal" in e for e in errs)


def test_ready_bar_enforced(tmp_path):
    weak = GOOD.replace("proof: 2", "proof: 1").replace(
        "evidence: symptom verbatim ✓ · passing check ✓ · dead-end ruled out ✓",
        "evidence: looked plausible")
    errs = obs.lint_file(_write(tmp_path, "nav2.md", weak), {"nav2"})
    assert any("ready" in e for e in errs)


def test_external_requires_source_and_quote(tmp_path):
    noquote = EXTERNAL.replace("quote: rclcpp::NodeOptions options;\n", "")
    errs = obs.lint_file(_write(tmp_path, "ros2.md", noquote), {"ros2"})
    assert any("quote" in e for e in errs)


def test_unknown_skill_stem_rejected_but_new_skills_allowed(tmp_path):
    errs = obs.lint_file(_write(tmp_path, "notaskill.md", GOOD.replace("nav2", "notaskill")),
                         {"nav2"})
    assert any("skill" in e for e in errs)
    ns = GOOD.replace("obs-nav2", "obs-new-skills").replace(
        "target: nav2#costmap-inflation (update) — add inflation_layer block",
        "target: new-skill: ros2-control — hardware-interface patterns")
    assert obs.lint_file(_write(tmp_path, "new-skills.md", ns), {"nav2"}) == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_observations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'observations'`

- [ ] **Step 4: Implement `scripts/engine/observations.py`**

```python
#!/usr/bin/env python3
"""Observations tier (Tier 2) — parse + lint learnings/observations/*.md.

Schema: learnings/observations/README.md (spec §4.5 + §6a.3). stdlib only.
Exit contract mirrors the skill validator: FAIL lines, summary line, exit 0/1.
"""
import argparse
import os
import re
import sys

SIGNALS = frozenset([
    "wrong-guidance", "no-skill-fired", "figured-out-from-scratch",
    "better-method", "noise", "verified", "user-correction",
])
_ID_RE = re.compile(r"<!-- id: (obs-[a-z0-9-]+-\d{3}) -->\s*$")
_HEAD_RE = re.compile(r"^## (.+?)\s*<!-- id: ")
_FIELD_RE = re.compile(r"^([a-z][a-z-]*):\s*(.*)$")
_STATUS_RE = re.compile(r"^(tentative|ready|absorbed \d{4}-\d{2}-\d{2}|rejected \(.+\))$")
_SOURCE_RE = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{7,40}\s+\S+#L\d+(-L\d+)?$")


def parse_file(path):
    entries, current = [], None
    for lineno, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if line.startswith("## "):
            m_id = _ID_RE.search(line)
            m_head = _HEAD_RE.match(line)
            current = {
                "id": m_id.group(1) if m_id else None,
                "title": m_head.group(1) if m_head else line[3:].strip(),
                "line": lineno,
                "fields": {},
            }
            entries.append(current)
        elif current is not None:
            m = _FIELD_RE.match(line)
            if m:
                current["fields"][m.group(1)] = m.group(2).strip()
    return entries


def _sources_list(value):
    value = (value or "").strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [s.strip() for s in value[1:-1].split(",") if s.strip()]


def _ready_ok(fields):
    try:
        proof = int(fields.get("proof", "0"))
    except ValueError:
        proof = 0
    evidence = fields.get("evidence", "")
    return (
        proof >= 2
        or fields.get("signal") == "user-correction"
        or evidence.count("✓") >= 3
        or (fields.get("origin") == "external" and "official" in evidence.lower())
    )


def lint_file(path, known_skills=None):
    errs = []
    stem = os.path.splitext(os.path.basename(path))[0]
    if known_skills is not None and stem not in known_skills and stem != "new-skills":
        errs.append(f"{path}: filename stem '{stem}' is not a known skill (or new-skills)")
    seen = set()
    for e in parse_file(path):
        where = f"{path}:{e['line']}"
        if not e["id"]:
            errs.append(f"{where}: heading missing '<!-- id: obs-{stem}-NNN -->'")
            continue
        if e["id"] in seen:
            errs.append(f"{where}: duplicate id '{e['id']}'")
        seen.add(e["id"])
        if not e["id"].startswith(f"obs-{stem}-"):
            errs.append(f"{where}: id '{e['id']}' prefix must match filename stem '{stem}'")
        f = e["fields"]
        for req in ("status", "proof", "signal", "sources", "target", "evidence"):
            if not f.get(req):
                errs.append(f"{where}: missing field '{req}'")
        if f.get("status") and not _STATUS_RE.match(f["status"]):
            errs.append(f"{where}: bad status '{f['status']}'")
        if f.get("signal") and f["signal"] not in SIGNALS:
            errs.append(f"{where}: bad signal '{f['signal']}'")
        if f.get("proof") and not f["proof"].isdigit():
            errs.append(f"{where}: proof must be an integer")
        if f.get("sources") and not _sources_list(f["sources"]):
            errs.append(f"{where}: sources must be a non-empty [list]")
        if f.get("status") == "ready" and not _ready_ok(f):
            errs.append(f"{where}: status ready but no ready-bar met "
                        "(proof>=2 | user-correction | 3x ✓ | external+official)")
        if f.get("origin") == "external":
            if not f.get("source") or not _SOURCE_RE.match(f.get("source", "")):
                errs.append(f"{where}: external entry needs source "
                            "'<org>/<repo>@<sha> <path>#L<a>[-L<b>]'")
            if not f.get("quote"):
                errs.append(f"{where}: external entry needs a verbatim quote")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="+", required=True)
    ap.add_argument("--skills-dir", default="skills")
    args = ap.parse_args(argv)
    known = None
    if os.path.isdir(args.skills_dir):
        known = {d for d in os.listdir(args.skills_dir)
                 if not d.startswith("_")
                 and os.path.exists(os.path.join(args.skills_dir, d, "SKILL.md"))}
    all_errs = []
    for path in args.check:
        if os.path.basename(path) == "README.md":
            continue
        all_errs.extend(lint_file(path, known))
    for e in all_errs:
        print(f"FAIL: {e}")
    n = len([p for p in args.check if os.path.basename(p) != "README.md"])
    print(f"Checked {n} observation file(s): {'FAIL' if all_errs else 'PASS'}")
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_observations.py -v`
Expected: 9 PASS

- [ ] **Step 6: Commit**

```bash
git add learnings/observations/README.md scripts/engine/observations.py tests/engine/test_observations.py
git commit -m "feat(engine): observations tier — Tier-2 schema doc + parser/lint"
```

---

### Task 3: Citation verifier (`verify_citations.py`)

**Files:**
- Create: `scripts/engine/verify_citations.py`
- Test: `tests/engine/test_verify_citations.py`

**Interfaces:**
- Consumes: `observations.parse_file` (Task 2).
- Produces (used by Tasks 7–9 and Phase 2b absorb):
  - `verify_entry(entry: dict, repos_root: str) -> str | None` — error string or None; non-external entries return None (skipped)
  - CLI: `python3 scripts/engine/verify_citations.py --repos <dir> <files…>` → per-citation `PASS`/`FAIL` lines + summary, exit 0/1. `<dir>/<repo-name>` must be a git clone containing the cited sha.
- Matching is whitespace-normalized substring: the quote (with all runs of whitespace collapsed to single spaces) must appear in the similarly-normalized text of the cited line range. This tolerates re-indentation but nothing else — a paraphrase fails, per the anti-hallucination rule of spec §6a.3.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_verify_citations.py`:

```python
import subprocess
import verify_citations as vc


def _mk_repo(tmp_path):
    repo = tmp_path / "repos" / "fixrepo"
    repo.mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "node.py").write_text(
        "import rclpy\n\n\ndef main():\n"
        "    node = rclpy.create_node('demo')\n"
        "    pub = node.create_publisher(String, 'topic', 10)\n"
    )
    env_git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(env_git + ["add", "-A"], check=True)
    subprocess.run(env_git + ["commit", "-qm", "init"], check=True)
    sha = subprocess.run(env_git + ["rev-parse", "--short=7", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return str(tmp_path / "repos"), sha


def _entry(sha, quote="pub = node.create_publisher(String, 'topic', 10)",
           lines="#L5-L6"):
    return {"id": "obs-ros2-001", "title": "t", "line": 1, "fields": {
        "origin": "external",
        "source": f"acme/fixrepo@{sha} src/node.py{lines}",
        "quote": quote,
    }}


def test_valid_citation_passes(tmp_path):
    root, sha = _mk_repo(tmp_path)
    assert vc.verify_entry(_entry(sha), root) is None


def test_reindented_quote_still_passes(tmp_path):
    root, sha = _mk_repo(tmp_path)
    e = _entry(sha, quote="pub   = node.create_publisher(String, 'topic', 10)")
    assert vc.verify_entry(e, root) is None


def test_wrong_quote_fails(tmp_path):
    root, sha = _mk_repo(tmp_path)
    err = vc.verify_entry(_entry(sha, quote="create_subscription(String, 'topic')"), root)
    assert err and "quote not found" in err


def test_wrong_line_range_fails(tmp_path):
    root, sha = _mk_repo(tmp_path)
    err = vc.verify_entry(_entry(sha, lines="#L1-L2"), root)
    assert err and "quote not found" in err


def test_missing_clone_fails(tmp_path):
    err = vc.verify_entry(_entry("ab12cd3"), str(tmp_path / "empty"))
    assert err and "clone not found" in err


def test_non_external_entries_skipped(tmp_path):
    assert vc.verify_entry({"id": "x", "fields": {"status": "ready"}}, "/nowhere") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_verify_citations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'verify_citations'`

- [ ] **Step 3: Implement `scripts/engine/verify_citations.py`**

```python
#!/usr/bin/env python3
"""Verify external-observation citations against pinned clones (spec §6a.3).

Anti-hallucination rule, deterministic: every cited quote must exist at
repo@sha path#lines — a citation that doesn't grep is a discarded candidate.
stdlib only.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SOURCE_RE = re.compile(
    r"^(?P<org>[\w.-]+)/(?P<repo>[\w.-]+)@(?P<sha>[0-9a-f]{7,40})"
    r"\s+(?P<path>\S+)#L(?P<a>\d+)(?:-L(?P<b>\d+))?$")


def _norm(text):
    return " ".join((text or "").split())


def verify_entry(entry, repos_root):
    fields = entry.get("fields", {})
    if fields.get("origin") != "external":
        return None
    eid = entry.get("id", "?")
    m = _SOURCE_RE.match(fields.get("source", ""))
    if not m:
        return f"{eid}: unparseable source '{fields.get('source', '')}'"
    clone = os.path.join(repos_root, m.group("repo"))
    if not os.path.isdir(clone):
        return f"{eid}: clone not found at {clone}"
    try:
        blob = subprocess.run(
            ["git", "-C", clone, "show", f"{m.group('sha')}:{m.group('path')}"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as exc:
        return f"{eid}: git show failed: {(exc.stderr or '').strip()[:160]}"
    a = int(m.group("a"))
    b = int(m.group("b") or m.group("a"))
    region = "\n".join(blob.splitlines()[a - 1:b])
    if not fields.get("quote"):
        return f"{eid}: external entry has no quote"
    if _norm(fields["quote"]) not in _norm(region):
        return (f"{eid}: quote not found at {m.group('path')}"
                f"#L{a}-L{b} @ {m.group('sha')}")
    return None


def main(argv=None):
    from observations import parse_file

    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", required=True)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args(argv)
    checked, errs = 0, []
    for path in args.files:
        if os.path.basename(path) == "README.md":
            continue
        for entry in parse_file(path):
            if entry.get("fields", {}).get("origin") != "external":
                continue
            checked += 1
            err = verify_entry(entry, args.repos)
            if err:
                errs.append(err)
                print(f"FAIL: {err}")
            else:
                print(f"PASS: {entry['id']} — {entry['fields'].get('source', '')}")
    print(f"Verified {checked} external citation(s): {'FAIL' if errs else 'PASS'}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_verify_citations.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/verify_citations.py tests/engine/test_verify_citations.py
git commit -m "feat(engine): external-citation verifier — quotes must grep at repo@sha"
```

---

### Task 4: Overlap/placement analyzer (`placement.py`)

**Files:**
- Create: `scripts/engine/placement.py`
- Test: `tests/engine/test_placement.py`

**Interfaces:**
- Produces (used by Tasks 7–9; Phase 2b's absorber and the new-skill overlap analysis reuse it):
  - `load_catalog(skills_dir: str) -> dict[str, dict]` — per skill: `{"description": str, "anchors": dict[anchor_id, line_text]}`
  - `analyze(text: str, skills_dir: str, top: int = 5) -> dict` — `{"skills": [(name, score)], "anchors": [("skill#anchor", score)]}`, both ranked desc, zero-score entries dropped
  - CLI: `python3 scripts/engine/placement.py --text "…" [--skills-dir skills]` (or `--file <path>`) → two-line report: `target skills:` and `similar anchors:`
- Scoring is deterministic keyword overlap (cosine-style: `|q∩t| / (sqrt(|q|)·sqrt(|t|))`); it **reports**, the agent decides — the placement rule (lowest skill that can hold it, spec §7.1) and near-duplicate calls stay judgment.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_placement.py`:

```python
from pathlib import Path

import placement

REPO = Path(__file__).resolve().parents[2]

FOO = """---
name: foo
version: 1.0.0
description: >
  Costmap tuning and obstacle inflation for mobile robot navigation.
---
## Key directives
- Always add the inflation layer or the robot hugs obstacles. <!-- id: inflation-layer -->
"""

BAR = """---
name: bar
version: 1.0.0
description: >
  Camera calibration and image pipelines for perception stacks.
---
## Key directives
- Calibrate intrinsics before extrinsics. <!-- id: intrinsics-first -->
"""


def _catalog(tmp_path):
    for name, text in (("foo", FOO), ("bar", BAR)):
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(text)
    (tmp_path / "skills" / "_TEMPLATE").mkdir()
    return str(tmp_path / "skills")


def test_load_catalog_reads_descriptions_and_anchors(tmp_path):
    cat = placement.load_catalog(_catalog(tmp_path))
    assert set(cat) == {"foo", "bar"}
    assert "costmap" in cat["foo"]["description"].lower()
    assert "inflation-layer" in cat["foo"]["anchors"]


def test_analyze_ranks_right_skill_first(tmp_path):
    skills = _catalog(tmp_path)
    out = placement.analyze("robot hugs obstacles — costmap inflation missing", skills)
    assert out["skills"][0][0] == "foo"
    assert out["anchors"][0][0] == "foo#inflation-layer"


def test_analyze_drops_zero_scores(tmp_path):
    skills = _catalog(tmp_path)
    out = placement.analyze("quaternion slerp interpolation maths", skills)
    assert all(s > 0 for _, s in out["skills"])


def test_analyze_runs_on_live_catalog():
    out = placement.analyze("costmap inflation robot hugs obstacles",
                            str(REPO / "skills"))
    assert "nav2" in [name for name, _ in out["skills"]][:2]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_placement.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'placement'`

- [ ] **Step 3: Implement `scripts/engine/placement.py`**

```python
#!/usr/bin/env python3
"""Overlap/placement analyzer — which skill/anchor already covers this finding?

Deterministic keyword-overlap report over skill descriptions + anchored lines.
Used by mining (target selection, near-dup detection) and the Phase 2b
absorber/new-skill overlap analysis. stdlib only.
"""
import argparse
import math
import os
import re
import sys

_STOP = frozenset(
    "the a an and or of to in for with on is are be this that it as at by "
    "from use when not you your skill skills robium".split())
_ANCHOR_RE = re.compile(r"<!-- id: ([a-z0-9][a-z0-9-]*) -->")


def tokens(text):
    return {t for t in re.findall(r"[a-z0-9_]+", (text or "").lower())
            if len(t) > 2 and t not in _STOP}


def _frontmatter_description(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    out, in_desc = [], False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if re.match(r"^description:", line):
            in_desc = True
            out.append(line.split(":", 1)[1].strip().lstrip(">").strip())
        elif in_desc and (line.startswith(" ") or line.startswith("\t")):
            out.append(line.strip())
        elif in_desc:
            break
    return " ".join(x for x in out if x)


def load_catalog(skills_dir):
    catalog = {}
    for d in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, d, "SKILL.md")
        if d.startswith("_") or not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        anchors = {}
        for line in text.splitlines():
            m = _ANCHOR_RE.search(line)
            if m:
                anchors[m.group(1)] = line
        catalog[d] = {"description": _frontmatter_description(text),
                      "anchors": anchors}
    return catalog


def _score(q, t):
    if not q or not t:
        return 0.0
    return len(q & t) / (math.sqrt(len(q)) * math.sqrt(len(t)))


def analyze(text, skills_dir, top=5):
    q = tokens(text)
    catalog = load_catalog(skills_dir)
    skills, anchors = [], []
    for name, data in catalog.items():
        s = _score(q, tokens(data["description"]))
        if s > 0:
            skills.append((name, round(s, 3)))
        for aid, line in data["anchors"].items():
            a = _score(q, tokens(line))
            if a > 0:
                anchors.append((f"{name}#{aid}", round(a, 3)))
    skills.sort(key=lambda x: -x[1])
    anchors.sort(key=lambda x: -x[1])
    return {"skills": skills[:top], "anchors": anchors[:top]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--file")
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    text = args.text if args.text else open(args.file, encoding="utf-8").read()
    out = analyze(text, args.skills_dir, args.top)
    print("target skills:   " + (" · ".join(f"{n} {s}" for n, s in out["skills"]) or "(none)"))
    print("similar anchors: " + (" · ".join(f"{n} {s}" for n, s in out["anchors"]) or "(none)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_placement.py -v`
Expected: 4 PASS. If `test_analyze_ranks_right_skill_first` fails on tie-ordering, the fixture texts are distinct enough that a real bug is more likely than a tie — debug scoring, don't loosen the assertion. If the live-catalog test fails because nav2's description wording drifted, widen only that assertion to top-3.

- [ ] **Step 5: Full engine suite + commit**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine -v`
Expected: all PASS (Phase 1 suites + the three new files).

```bash
git add scripts/engine/placement.py tests/engine/test_placement.py
git commit -m "feat(engine): overlap/placement analyzer over skill descriptions + anchors"
```

---

### Task 5: The `mining` skill

**Files:**
- Create: `skills/mining/SKILL.md`

**Interfaces:**
- Consumes: everything from Tasks 2–4 (referenced in prose — repo-root paths, no backticks per the backtick rule... exception: the rule allows backticks only for same-skill files, so engine script paths appear as plain prose).
- Produces: the workflow contract Tasks 7–9 execute. Catalog count becomes 25.

- [ ] **Step 1: Write `skills/mining/SKILL.md`**

Exact content (validator requires the section order used here; description must stay ≤1024 chars):

````markdown
---
name: mining
version: 0.1.0
description: >
  Registry-driven mining of external example repos — the learning engine's
  second experience source. Surveys, deep-reads, and comparatively analyzes
  approved repos (vendor demos, framework samples, community robot apps) into
  evidence-cited observations (origin: external) that harden robium skills or
  propose new ones; maintains crawl records for drift re-checks. Use when:
  'mine repo X', 'survey this repo', 'run a comparative run', 'learn from
  external repos', 'distill patterns from a repo', 'crawl SOURCES.md',
  triaging or re-crawling entries in learnings/SOURCES.md. Discovery is
  autonomous; mining spends only on human-approved registry entries. Output
  is observations plus registry updates — never direct skill edits. Not for:
  absorbing robium's own session learnings (skill-author hardening, until the
  learning-loop skill lands) or fresh skill authoring mechanics (skill-author).
---

# Mining — learning from external examples

Working external repos encode more accumulated judgment than our own sessions
can generate. This skill turns approved example repos into evidence-cited
observations in the learnings observations tier, sharing one pipeline with
session learning (spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §6a).

## When to use this skill

- A repo in learnings/SOURCES.md is approved for exploration (status flip or
  the user says "mine repo X" — a direct naming is itself approval).
- A comparative question needs settling across sibling repos ("how do TB3 and
  TB4 sims differ on bringup?") — run a comparative set.
- A distilled repo drifted (status recheck, or a major upstream release) — re-crawl.
- Candidate repos need triage into the registry (discovery — filing rows is
  autonomous; mining them is not).
- For absorbing robium's own session learnings, use skill-author hardening
  (learning-loop supersedes it in Phase 2b). For authoring mechanics and the
  quality bar, use skill-author.

## Key directives

- Delegation posture: **embed** — the mining workflow lives here; it consumes
  the engine tools at scripts/engine/ (observations.py, verify_citations.py,
  placement.py) and the registry at learnings/SOURCES.md.
- **Spend only on approval.** <!-- id: spend-gated-registry --> Discovery
  (filing candidate rows with a one-line why) is autonomous; survey and deep
  passes run only on rows the human approved or repos the user named directly.
- **Every citation must grep.** <!-- id: citation-must-grep --> External
  observations carry source (repo@short-sha path#lines) and a verbatim quote;
  run the citation verifier before committing — a citation that fails is a
  discarded candidate, never a "close enough".
- **Observations, never skill edits.** <!-- id: observations-not-edits -->
  Mining output lands in learnings/observations/ and the registry. Skill
  content changes go through the absorb pipeline (Phase 2b) with its human
  merge gate — even for obviously-right findings.
- **Generic distills, specific doesn't.** <!-- id: generic-vs-specific -->
  Transferable patterns (idioms, orderings, workarounds, config shapes, how
  large apps are structured) become observations; project-local choices
  (names, ports, one-off tunings) are noise — drop them.
- **License gates vendoring.** <!-- id: permissive-license-only --> Check the
  repo license during survey. Pointer-first always (cite repo + path + commit);
  vendor a snippet only if short and adapted or materially modified, only from
  Apache/BSD/MIT (attribution header + upstream link + commit), never GPL into
  the plugin. Vendored files enter status unverified.
- **Code only.** <!-- id: code-only-no-history --> No issue-tracker crawling;
  commit-history mining (reverts, fix-chains) is considered-and-deferred
  (spec §6a.2) — do not re-litigate it mid-run.

## Quick start

Single-repo run, end to end (repo already approved in learnings/SOURCES.md):

```bash
# 1. pin a clone (shallow is fine — the recorded SHA is the clone's HEAD)
git clone --depth 1 https://github.com/ros2/examples .robium/mining/examples
git -C .robium/mining/examples rev-parse --short=7 HEAD   # record this SHA

# 2. survey: map the tree, check LICENSE, inventory candidate areas →
#    write .robium/mining/examples-survey.md proposing which areas earn deep reads

# 3. deep pass (approved areas only): read, triage generic-vs-specific,
#    place each candidate:
python3 scripts/engine/placement.py --text "composition via NodeOptions idiom"

# 4. draft observations in learnings/observations/<skill>.md
#    (origin: external, source: repo@sha path#lines, quote: verbatim)

# 5. verify — both must PASS before commit:
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/*.md

# 6. update the SOURCES.md row: status → distilled, add the crawl record:
#    crawled: YYYY-MM-DD @ <sha> → fed: <obs ids>
```

Flip the row to exploring when the survey starts; survey report stays in
.robium/mining/ (gitignored) as the audit trail.

## Decision guidance

**Run type.**

| Situation | Run |
|---|---|
| One approved repo, unknown value | Survey first; deep pass only on areas the survey report proposes (or pre-authorized survey+deep in the registry row) |
| Sibling repos answering the same need (e.g. TB3 sim vs TB4 sim) | Comparative: readers fan out across all members; distill the **common/divergent split** — commons arrive pre-verified (convergence bar met by construction), divergences become decision-surface candidates for umbrella skills |
| Distilled repo with upstream drift | Re-crawl: diff against the recorded SHA, re-mine only what changed, flag distillations whose source lines changed as recheck |

Every comparative run also diffs against **our own catalog and learnings** —
where the ecosystem contradicts a skill, route it as wrong-guidance or
better-method, not as a silent overwrite.

**Evidence bar by source authority** (spec §6a.4):

| Source | Bar |
|---|---|
| Official/vendor repo, consistent with the tool's current docs | ready outright — evidence line says "official" + how docs were checked (direct fetch vs search synthesis) + date; enters the 90-day staleness sweep like any dated claim |
| Community repos, same pattern in ≥2 independent reputable ones | ready via convergence (a comparative common-split satisfies this by construction) |
| Single community repo | tentative — stays until a second witness or a robium trial |
| Extracted example files | status unverified regardless of source; promoted only by a robium trial or the deep-verify lane (Phase 3) |

**Signal mapping for mined findings:** new transferable pattern →
better-method; confirms existing skill content → verified; contradicts skill
content → wrong-guidance; domain no skill owns → no-skill-fired (route to the
new-skills observations file).

**Conflicts — record both, field-tested leads.** <!-- id: field-tested-leads -->
When mined guidance contradicts session-verified knowledge, the observation
carries both with provenance: our field-tested guidance leads, the official
idiom is noted alongside with why it bit us, and the divergence is flagged
for re-verification (upstream may have fixed the original reason).

**New-skill path** (spec §6a.6): when mining surfaces a domain no skill owns,
file a proposal in the new-skills observations file — overlap analysis (run
the placement tool over the finding set), trigger-surface sketch, evidence
inventory. The human approves the *concept* before any authoring starts;
authoring then follows skill-author. Two gates, because new skills change
catalog shape.

## Platform gotchas

- Shallow clones (`--depth 1`) satisfy citation verification for the HEAD
  commit only. For a re-crawl diff, fetch the recorded SHA first:
  `git -C <clone> fetch --depth 1 origin <sha>`.
- Big repos (navigation2, IsaacLab): use a blobless clone to survey cheaply —
  `git clone --filter=blob:none <url>` — blobs download lazily on read.
- Prefer git clones over the GitHub API for reading (no rate-limit surprises;
  the clone is also what the citation verifier needs).
- Licenses live in LICENSE/LICENSE.md at the repo root but subdirectories can
  carry their own (vendored third-party dirs) — check the directory you are
  actually citing from.

## Customization

- Comparison sets are defined in the registry: list the member repos in one
  row's Notes (or a dedicated subsection) and mine them in a single run.
- User tier (Phase 4 preview): the same flow with a private registry at
  .robium/sources.md, observations in the user's repo, and overlay skills as
  the absorb destination — mined-from-private content gets an extra provenance
  review before any upstream contribution.

## References

- Registry: learnings/SOURCES.md — statuses, crawl records, discovery inbox.
- Observations contract: the README in learnings/observations/ (schema, ready
  bar, external-entry fields).
- Engine tools (repo root): scripts/engine/observations.py (lint),
  scripts/engine/verify_citations.py (citation check),
  scripts/engine/placement.py (target/overlap report).
- Pattern-recognition heuristics: the skill-author skill's mining-guide
  reference (what makes a pattern worth distilling) — still the judgment core.
- Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §6a.

## Changelog

- 0.1.0 (2026-08-XX): initial skill — registry-driven survey→deep and
  comparative runs, extraction contract, source-authority evidence bar,
  conflict policy, new-skill proposal path (learning-engine Phase 2a, spec §6a).
````

- [ ] **Step 2: Run the validator**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 25 skills: PASS`. Fix any `FAIL:` lines (likely candidates: section order, description length, anchor format).

- [ ] **Step 3: Backtick-rule self-check**

Run: `grep -nE '`[^`]*(/|\.md|\.py|\.yaml)[^`]*`' skills/mining/SKILL.md`
Expected: hits only for the Quick start code block and same-skill references (a fenced code block is fine — the rule targets inline backticked path tokens). Confirm no inline backticks around learnings/SOURCES.md, scripts/engine/ paths, or other skills' files outside code fences.

- [ ] **Step 4: Commit**

```bash
git add skills/mining/SKILL.md
git commit -m "feat(skills): new mining skill — external-example exploration engine (spec §6a)"
```

---

### Task 6: Catalog integration — routing, cross-refs, counts

**Files:**
- Modify: `skills/architect/SKILL.md` (routing table + version 1.6.1 → 1.7.0)
- Create: `archive/architect/1.6.1/` (snapshot before edit)
- Modify: `skills/skill-author/SKILL.md` (Mode-2 narrowing + version 1.1.1 → 1.1.2)
- Create: `archive/skill-author/1.1.1/` (snapshot before edit)
- Modify: `CLAUDE.md` (counts + umbrella list)

**Interfaces:**
- Consumes: the mining skill (Task 5).
- Produces: bidirectional, consistent cross-references (CLAUDE.md plugin-architecture rule) so no stale qualifier survives.

- [ ] **Step 1: Snapshot both skills before editing**

```bash
mkdir -p archive/architect archive/skill-author
cp -R skills/architect archive/architect/1.6.1
cp -R skills/skill-author archive/skill-author/1.1.1
```

- [ ] **Step 2: Edit `skills/architect/SKILL.md`**

(a) In the "Verification & meta" table, insert after the `cloud-run` row:

```markdown
| `mining` | Learning from external example repos — registry-driven survey/deep/comparative runs over learnings/SOURCES.md, distilling evidence-cited observations. Not an app-building skill. |
```

(b) Replace the `skill-author` row's parenthetical `(fresh authoring, mining, hardening from learnings)` with `(fresh authoring, hardening from learnings; external-repo mining moved to \`mining\`)`.

(c) Frontmatter: `version: 1.6.1` → `version: 1.7.0`.

(d) Changelog, new first line:

```markdown
- 1.7.0 (2026-08-XX): routing table (Verification & meta) gains the new
  mining skill; skill-author row narrowed (external-repo mining moved out).
```

- [ ] **Step 3: Edit `skills/skill-author/SKILL.md`**

(a) Change the Mode 2 heading line from:

```markdown
**Mode 2 — Mining** (extract patterns from an existing repo):
```

to:

```markdown
**Mode 2 — Mining** (extract patterns from this repo's own apps; for external
example repos use the `mining` skill, which owns the registry-driven flow):
```

(b) In the frontmatter description, replace `or when distilling patterns from an existing robotics repo into a skill` with `or when distilling patterns from this repo's own apps into a skill (external repos: mining skill)`. Re-check the description is still ≤1024 chars.

(c) Frontmatter: `version: 1.1.1` → `version: 1.1.2`.

(d) Changelog, new first line:

```markdown
- 1.1.2 (2026-08-XX): Mode 2 narrowed to in-repo apps — external-repo mining
  moved to the new mining skill (learning-engine Phase 2a).
```

- [ ] **Step 4: Update CLAUDE.md counts and lists**

(a) Repo-layout line: `skills/            23 robium skills (the plugin's core deliverable)` → `skills/            25 robium skills (the plugin's core deliverable)`.

(b) Test-suite comment: `Must print "Checked 24 skills: PASS"` → `Must print "Checked 25 skills: PASS"`.

(c) Plugin-architecture bullet: `— 24 skills.` → `— 25 skills.`, and in the umbrella list insert `mining` after `skill-refiner`: `…skill-author, skill-updater, skill-refiner, mining, data,…`.

- [ ] **Step 5: Stale-qualifier sweep (CLAUDE.md rule 4)**

Run (newline-flattened, per the rule):

```bash
python3 - <<'EOF'
import pathlib, re
for p in pathlib.Path(".").rglob("*.md"):
    s = str(p)
    if any(x in s for x in ("archive/", "node_modules", "docs/superpowers", ".robium")):
        continue
    text = re.sub(r"\s+", " ", p.read_text(errors="ignore"))
    for pat in (r"no mining skill", r"mining (is|isn'?t| not) yet",
                r"2[34] skills", r"Checked 2[34] skills"):
        if re.search(pat, text, re.I):
            print(p, "→", pat)
EOF
```

Expected: no hits outside frozen history (archive/, docs/superpowers/ plans+specs, docs/CHANGELOG.md are history — leave them). Fix any live hit (skills/, README, REGISTRY, cli/, website/ docs).

- [ ] **Step 6: Validator + full suite**

```bash
uv run skills/skill-author/scripts/validate_skills.py
uv run --with pytest --with pyyaml -m pytest tests/engine -v
```

Expected: `Checked 25 skills: PASS` · all tests PASS.

- [ ] **Step 7: Commit (archive snapshots + edits together, per the STRICT policy)**

```bash
git add archive/architect/1.6.1 archive/skill-author/1.1.1 \
        skills/architect/SKILL.md skills/skill-author/SKILL.md CLAUDE.md
git commit -m "feat(skills): route the mining skill — architect 1.7.0, skill-author 1.1.2, counts to 25"
```

---

### Task 7: Mining pilot A — ros2/examples (single-repo, survey→deep)

**Files:**
- Create: `learnings/observations/ros2.md` (3–6 entries)
- Modify: `learnings/SOURCES.md` (ros2/examples row: status + crawl record)
- Produce (gitignored): `.robium/mining/examples/` clone + `.robium/mining/examples-survey.md`

**Interfaces:**
- Consumes: the mining skill workflow (Task 5), engine tools (Tasks 2–4). Pre-authorized survey+deep (plan header).
- Produces: the first `origin: external` observations; the pattern Tasks 8–9 repeat.

- [ ] **Step 1: Flip the registry row and pin the clone**

In `learnings/SOURCES.md`, ros2/examples row: `todo` → `exploring`.

```bash
git clone --depth 1 https://github.com/ros2/examples .robium/mining/examples
git -C .robium/mining/examples rev-parse --short=7 HEAD
cat .robium/mining/examples/LICENSE | head -3
```

Record the SHA; confirm the license is Apache-2.0 (expected for ros2 org repos — if not, note it in the survey report and apply the license gate).

- [ ] **Step 2: Survey pass**

Read the repo top-down (README, directory tree, one example per family). Write `.robium/mining/examples-survey.md` with: repo map (the rclpy/rclcpp example families), license, ROS distro targeted by the default branch (state how verified — branch name and package.xml, not memory), and 2–3 proposed deep areas ranked by expected value to the ros2 skill. Suggested candidates to evaluate (survey decides): rclpy pub/sub + QoS idioms, executors/callback-group patterns, composition idioms, launch usage in examples.

- [ ] **Step 3: Deep pass on the proposed areas**

For each area: read the example files fully; triage generic-vs-specific; for each surviving candidate run

```bash
python3 scripts/engine/placement.py --text "<finding title + one-line body>"
```

to pick the target skill/anchor and catch near-duplicates against existing ros2-skill anchors. Compare each candidate against the ros2 skill's current content: confirms → signal verified; contradicts → wrong-guidance (record both sides per the conflict policy); new → better-method.

- [ ] **Step 4: Write `learnings/observations/ros2.md`**

3–6 entries per the observations README schema — every entry: `origin: external`, `source: ros2/examples@<sha> <path>#L<a>-L<b>`, verbatim `quote:`, evidence line stating "official" + how docs-consistency was checked (direct fetch vs search synthesis — docs.ros.org is chronically bot-blocked; if synthesis, say so and add "re-verify on absorb") + the date. Status per the evidence bar (official + docs-consistent → ready; unverifiable against docs → tentative).

- [ ] **Step 5: Verify**

```bash
python3 scripts/engine/observations.py --check learnings/observations/ros2.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/ros2.md
uv run skills/skill-author/scripts/validate_skills.py
```

Expected: `PASS` on all three (validator untouched by this task but run anyway — it is the invariant).

- [ ] **Step 6: Registry crawl record + commit**

ros2/examples row: `exploring` → `distilled`, append crawl record: `crawled: 2026-08-XX @ <sha> → fed: obs-ros2-001..obs-ros2-NNN`.

```bash
git add learnings/observations/ros2.md learnings/SOURCES.md
git commit -m "feat(mining): pilot A — ros2/examples distilled to verified external observations"
```

---

### Task 8: Mining pilot B — navigation2_tutorials (single-repo, survey→deep)

**Files:**
- Create: `learnings/observations/nav2.md` (3–6 entries)
- Modify: `learnings/SOURCES.md` (navigation2_tutorials row)
- Produce (gitignored): `.robium/mining/navigation2_tutorials/` + `.robium/mining/navigation2_tutorials-survey.md`

**Interfaces:**
- Consumes: same tools and workflow as Task 7.
- Produces: nav2-targeted external observations — the highest-evidence skill in the catalog, so catalog-diff findings (confirms/contradicts) are expected here, not just new patterns.

- [ ] **Step 1: Flip the registry row and pin the clone**

`learnings/SOURCES.md` navigation2_tutorials row: `todo` → `exploring`.

```bash
git clone --depth 1 https://github.com/ros-navigation/navigation2_tutorials .robium/mining/navigation2_tutorials
git -C .robium/mining/navigation2_tutorials rev-parse --short=7 HEAD
head -3 .robium/mining/navigation2_tutorials/LICENSE 2>/dev/null || ls .robium/mining/navigation2_tutorials
```

Record SHA + license (per-package licenses possible — check the package you cite from).

- [ ] **Step 2: Survey pass**

Write `.robium/mining/navigation2_tutorials-survey.md`: package inventory (custom planner/controller/behavior/navigator tutorials, SLAM integration, etc.), license(s), targeted distro (from package.xml / branch — state how verified), 2–3 proposed deep areas. Candidates to evaluate: custom-plugin structure (planner/controller/costmap-layer plugin boilerplate and registration), params/bringup conventions, anything the nav2 skill's Usage patterns already covers (catalog-diff material).

- [ ] **Step 3: Deep pass with explicit catalog-diff**

Same flow as Task 7 Step 3, plus: for every area that overlaps the nav2 skill's existing content (grep nav2's SKILL.md and references for the topic first), record the comparison outcome explicitly — verified (matches), wrong-guidance (contradicts — carry both sides, field-tested leads), or better-method (upstream shows a cleaner way).

- [ ] **Step 4: Write `learnings/observations/nav2.md`**

3–6 entries, same contract as Task 7 Step 4 (official-org repo → ready when docs-consistent; note that nav2 docs live at docs.nav2.org — try a direct fetch before falling back to synthesis, and say which happened).

- [ ] **Step 5: Verify**

```bash
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/nav2.md
```

Expected: `PASS` on both.

- [ ] **Step 6: Registry crawl record + commit**

Row → `distilled` + crawl record (same format as Task 7).

```bash
git add learnings/observations/nav2.md learnings/SOURCES.md
git commit -m "feat(mining): pilot B — navigation2_tutorials distilled; catalog-diff against nav2 skill"
```

---

### Task 9: Mining pilot C — comparative run: turtlebot3_simulations vs turtlebot4_simulator

**Files:**
- Create: `learnings/observations/simulation.md` (divergence findings; 2–5 entries)
- Modify: `learnings/observations/nav2.md` and/or create `learnings/observations/gazebo.md` (common-split findings, as placed)
- Modify: `learnings/SOURCES.md` (both rows + comparison-set note)
- Produce (gitignored): clones of both repos + `.robium/mining/tb-sims-comparative.md` (the split report)

**Interfaces:**
- Consumes: Tasks 2–5 tools/workflow; our own prior work as the third comparator (apps nav-trial and tb4-teleop — read their briefs/learnings, don't rebuild anything).
- Produces: the comparative run type exercised end-to-end — commons pre-verified by convergence, divergences as decision-surface candidates, catalog-diff against our own approach.

- [ ] **Step 1: Flip both registry rows and pin both clones**

Both rows (`ROBOTIS-GIT/turtlebot3_simulations`, `turtlebot4/turtlebot4_simulator`): `todo` → `exploring`, and add a Notes line on either row: `comparison set: tb3-sim + tb4-sim (run 2026-08-XX)`.

```bash
git clone --depth 1 https://github.com/ROBOTIS-GIT/turtlebot3_simulations .robium/mining/turtlebot3_simulations
git clone --depth 1 https://github.com/turtlebot4/turtlebot4_simulator .robium/mining/turtlebot4_simulator
for d in turtlebot3_simulations turtlebot4_simulator; do git -C .robium/mining/$d rev-parse --short=7 HEAD; done
```

Record both SHAs; check both licenses.

- [ ] **Step 2: Per-member reads (fan out if subagents are available; sequential otherwise)**

For each member, read with the same lens so the split is honest: bringup/launch structure (entry launch file, argument surface), sim integration (which Gazebo, how ros_gz is wired), world/model organization, nav integration (how Nav2 is brought up against the sim), package layout. Notes per member into `.robium/mining/tb-sims-comparative.md`.

- [ ] **Step 3: Distill the common/divergent split**

In the same report: **Common** — patterns present in both (these meet the convergence bar by construction → observations with `status: ready`, evidence line "convergence: present in both members", sources listing both repo@sha refs, `source:`+`quote:` citing ONE member — the contract verifies one quote; the second member ref in sources is the convergence witness). **Divergent** — where the two differ (launch-argument philosophy, world organization, distro/Gazebo pairing, bringup composition): these become decision-surface observations targeting the simulation umbrella (or nav2/gazebo where specific), `status: tentative`, framed as "TB3 does X, TB4 does Y — decision surface for <situation>".

- [ ] **Step 4: Catalog-diff against our own work**

Read apps/nav-trial and apps/tb4-teleop briefs + the gazebo/nav2/simulation skills' relevant sections; where the ecosystem's converged pattern contradicts what a skill teaches or what we did, add a wrong-guidance/better-method observation (field-tested leads — record both sides).

- [ ] **Step 5: Write observations + verify**

Place entries per the placement tool (expected: commons → gazebo.md/nav2.md, divergences → simulation.md; follow the tool's report, not this guess, but keep file stems = real skills). Then:

```bash
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/*.md
```

Expected: `PASS` on both.

- [ ] **Step 6: Registry crawl records + commit**

Both rows → `distilled` (or `dropped` with a why, if a member yielded nothing — say so honestly) + crawl records.

```bash
git add learnings/observations/ learnings/SOURCES.md
git commit -m "feat(mining): pilot C — comparative TB3/TB4 sim run; common/divergent split + catalog diff"
```

---

### Task 10: Phase 2a exit checklist + changelog

**Files:**
- Modify: `docs/CHANGELOG.md`

- [ ] **Step 1: Full verification battery**

```bash
uv run --with pytest --with pyyaml -m pytest tests/engine -v
uv run skills/skill-author/scripts/validate_skills.py
python3 scripts/engine/observations.py --check learnings/observations/*.md
python3 scripts/engine/verify_citations.py --repos .robium/mining learnings/observations/*.md
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); json.load(open('hooks/hooks.json')); print('OK')"
```

Expected: all PASS · `Checked 25 skills: PASS` · `OK`.

- [ ] **Step 2: Exit checklist**

- [ ] `mining` skill in the catalog; validator green at 25.
- [ ] Three pilot runs committed; every pilot produced ≥1 `ready` observation; all external citations verify.
- [ ] All three run mechanics exercised: survey→deep (A, B), comparative common/divergent split (C), catalog-diff (B, C).
- [ ] SOURCES.md rows carry crawl records (`crawled: date @ sha → fed: …`) for all four mined repos.
- [ ] `.robium/queue.jsonl` regenerated (Task 1) — the Phase 2b backlog exists.
- [ ] No wrong-guidance finding was "fixed" directly in a skill — mining stayed observations-only (grep the diff: `git log --stat -- skills/` shows only Tasks 5–6 commits).

- [ ] **Step 3: Changelog + commit**

Append to `docs/CHANGELOG.md` under a new dated heading:

```markdown
## 2026-08-XX — Learning engine Phase 2a: shared core + mining

Observations tier (schema, parser/lint) at learnings/observations/; external
citation verifier (quotes must grep at repo@sha); overlap/placement analyzer;
new mining skill (catalog at 25; architect 1.7.0 routes it, skill-author 1.1.2
narrowed). Pilots: ros2/examples and navigation2_tutorials (survey→deep),
TB3/TB4 sims (comparative common/divergent split + catalog diff) — all
observations origin: external with verified citations; SOURCES.md rows carry
crawl records. Back-mining queue regenerated after worktree loss. Phase 2b
(consolidate/recall/absorb) is the next plan.
Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §4.5, §6a.
```

```bash
git add docs/CHANGELOG.md
git commit -m "docs: changelog — learning engine Phase 2a (shared core + mining)"
```

---

## Self-review notes (performed at plan-writing time)

- **Spec coverage (Phase 2 row of §15, 2a slice):** observations tier → Task 2; extraction schema (§6a.3, origin/source/quote + anti-hallucination) → Tasks 2–3; overlap/placement analyzer → Task 4; mining skill (§6a.1–6a.7: registry, run types, evidence bar, conflict policy, vendoring, new-skill path, re-crawl) → Task 5; pilot "on 2–3 SOURCES.md repos" → Tasks 7–9 (four repos across three runs, exercising every run type). Deliberately deferred to 2b (recorded in the header): consolidator, recall hook, delta format + apply_deltas, trigger-eval runner + flip gate, absorb→PR, CLAUDE.md policy rewrite, meta-skill restructure — the spec's own ordering puts them after the mining pilot.
- **Why the mining skill lands before the meta-restructure:** the spec ships mining as "the pipeline's first consumer". Interim overlap with skill-author Mode 2 is resolved by narrowing (Task 6) rather than retiring — retirement is 2b's restructure, where updater/refiner also go and the count returns to 24 (24 − 2 + 2 per §13; this plan's 25 is the documented interim).
- **Type consistency:** `parse_file` returns `{"id","title","line","fields"}` and both `verify_citations.verify_entry` and the lint consume exactly that shape; `fields` values are strings (lint parses `proof` itself); `SOURCE_RE` in observations.py (lint) and `_SOURCE_RE` in verify_citations.py accept the same grammar `<org>/<repo>@<sha> <path>#L<a>[-L<b>]`.
- **Placeholder scan:** all code complete; pilot tasks are agent-workflow tasks whose "tests" are the deterministic checkers (lint + citation verify + validator) — the plan names suggested deep areas but delegates the final pick to the survey report, which is the spec's own survey→deep contract, not a placeholder.
- **Comparative-entry citation semantics** (one verified quote + convergence witnesses in sources) is defined once in the observations README (Task 2) and restated in Task 9 Step 3 — kept identical.
- **Validator count**: nothing hardcodes 24/25 in scripts or tests (verified by grep at plan-writing time); CLAUDE.md prose counts are updated in Task 6.
