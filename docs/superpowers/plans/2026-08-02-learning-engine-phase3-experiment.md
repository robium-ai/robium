# Learning Engine Phase 3 — Verify Deep + Experiment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the experimentation engine (blind variant A/B with scored PRs, losing variants archived) and the deep-verify lane (unverified examples run in pinned fixtures → ✓-promotion annotate deltas), plus the two engine-hardening fixes that gate them (issues #80, #81) — then run both pilots to meet the Phase 3 exit criteria. Spec: `docs/superpowers/specs/2026-08-01-learning-engine-design.md` §8 layer 4, §9, Phase 3 row of §15. Phases 1–2b are merged (main at the website-repositioning merge; engine at 155 tests, catalog 24).

**Architecture:** Variants are whole-catalog tmp copies: apply each candidate deltas file to a scratch `skills/` tree via the existing apply_deltas (its branch guard fails open outside git — by design), score deterministically (trigger accuracy → task completion → −token length, the spec's fitness ordering), optionally blind-judge content quality via a timeboxed `claude -p` with shuffled labels and an honest fallback, and emit a ranked score table for the PR — the engine recommends, the human picks by merging. Deep-verify reuses the new task-check runner: `evals.yaml` gains `tasks:` fixtures ({name, command, pass_criteria, app, example, timeout}); a passing run against an unverified example emits (never applies) an annotate delta promoting it to ✓ with date + fixture name. Contrastive rollouts ship as a documented recipe in learning-loop's new experiment reference — deliberately not executed in this phase (the exit criteria don't require them; spec §9 reserves them for high-stakes questions).

**Tech Stack:** Same as 2b — `scripts/engine/` Python with pyyaml via PEP-723 (`uv run`), hooks untouched, tests via `uv run --with pytest --with pyyaml -m pytest tests/engine -v`. Pilots use `gh` (authenticated) and, for deep-verify, `uv run --with 'lerobot[dataset]'` (primary fixture) or Docker `ros:` images (fallback fixture) on this host.

**Standing decisions:**
- **Precondition for Task 7 (A/B pilot):** PRs #78 and #79 must be MERGED first — they carry `archive/nav2/1.2.1` and `archive/environments/1.6.1`; an experiment branch consuming the same slots would conflict. The task checks `gh pr view 78 79` and STOPS (BLOCKED, ask the user) if either is open. No workaround — merging them is the human gate working as designed.
- The contested edit for exit criterion 1 is **obs-nav2-003** (ready, deliberately held from PR #78 "for editorial care" — correction-dense, structurally contestable: exactly §9's "competing fixes" case). Resolving it via blind A/B also closes the held-observation loose end from issue #83.
- The deep-verify pilot's primary fixture is **skills/lerobot/examples/load-dataset-snippet.py** (pure Python, runs on this macOS host via uv; network+disk for the `lerobot/pusht` download, timeout 900). Fallback if the download/API fails at execution time: the **ros2 package-ament-python example** built and run inside a Docker `ros:` container (Docker 29 confirmed on this host). The executor picks per host reality and says which ran.
- Contrastive rollouts (§9) and the Workflow orchestration for them: **recipe-only this phase** — documented in learning-loop's experiment reference with the breadth/depth model split and fitness ordering; execution is on-demand for a future high-stakes question. Recorded so it isn't re-litigated.
- Committed deltas files now live under `learnings/deltas/YYYY-MM-DD-<topic>.yaml` (the convention issue #81 item 4 asked for; documented in delta-format.md in Task 2).
- Validator edits are skill-author content: any `validate_skills.py` change carries a skill-author build bump + archive snapshot in the same commit.

## Global Constraints

- Test command: `uv run --with pytest --with pyyaml -m pytest tests/engine -v`. Validator after any `skills/**` change: `Checked 24 skills: PASS` throughout this plan (no skills added/removed).
- Every SKILL.md edit: pre-edit archive snapshot + version bump + changelog line at TOP, same commit. Sidecar-only additions (evals.yaml `tasks:` entries) do NOT bump versions (2a rule).
- apply_deltas invariants from 2b hold and must not regress (batch-blocking refusals, no-ops degrade, cap on final content, branch guard, same-file annotate, same-destination move merging) — the existing 21-test suite is the regression net; every task here ends with the FULL suite green.
- Subprocess-running tools (task checks, variants) are timeboxed with explicit timeouts and never run as root/altering state outside their cwd; task-check commands execute with `cwd` = the named app dir or repo root — never inside `skills/`.
- Blind-judge calls: `claude -p`, timeboxed 45 s per call, shuffled variant labels, ANY failure → the score table says "content judge: skipped (<reason>)" — never a fabricated ranking (citation honesty).
- Pilots write PRs, never merge. Experiment branches: `loop/experiment-YYYY-MM-DD-<topic>`; deep-verify branch: `loop/deep-verify-YYYY-MM-DD`.
- Path discipline (standing from 2b): all work in the plan's worktree; verify `pwd` + branch before every commit; external fixtures may read the MAIN checkout's `.robium/` by absolute path only.

**File structure created/modified by this plan:**

```
scripts/engine/
  apply_deltas.py             # Task 1: find_anchor_block paragraph blocks; Task 2: polish
  run_task_checks.py          # Task 3: evals.yaml tasks runner
  run_variants.py             # Task 4: variant A/B harness
  deep_verify.py              # Task 5: unverified-example verification lane
hooks/scripts/recall.py       # Task 2: truncation ellipsis
skills/skill-author/          # Task 3: validator tasks-schema check (build bump + archive)
skills/learning-loop/         # Task 6: 0.2.0 — experiment + deep-verify modes,
  references/experiment-recipes.md    # incl. contrastive-rollouts recipe
skills/learning-loop/references/delta-format.md  # Task 2: learnings/deltas/ convention
learnings/deltas/             # pilot deltas files (new convention)
skills/lerobot/evals.yaml     # Task 8: deep-verify fixture task (sidecar, no bump)
archive/nav2/variants/<date>/ # Task 7: losing variants + scores
tests/engine/test_task_checks.py  test_variants.py  test_deep_verify.py
docs/CHANGELOG.md             # Task 9
+ two PR branches (Tasks 7–8)
```

---

### Task 1: `find_anchor_block` paragraph-block support (issue #80)

**Files:**
- Modify: `scripts/engine/apply_deltas.py` (`find_anchor_block` only)
- Modify: `tests/engine/test_apply_deltas.py` (append tests)

**Interfaces:**
- `find_anchor_block(lines, anchor) -> (start, end) | None` — unchanged signature. New behavior: when the anchor line is NOT a list item (its lstrip doesn't start with `- ` or `* `), the block is a PARAGRAPH: it extends from the anchor line down to (exclusive) the first blank line or `#`-heading line. List-item behavior is byte-identical to today (existing tests must pass unmodified).
- This makes the four bold-paragraph anchors added by PR #78 (and any future ones) safely updatable/retirable — an `update`/`retire` op replaces/removes the whole paragraph, not just its first line.

- [ ] **Step 1: Append the failing tests**

Append to `tests/engine/test_apply_deltas.py`:

```python
PARA_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->\n\n"
    "**Custom planner plugin (rolling API).** <!-- id: para-anchor -->\n"
    "First continuation line at indent zero explaining the pattern.\n"
    "Second continuation line, still the same paragraph.\n\n"
    "**Next unrelated paragraph.** <!-- id: para-two -->\n"
    "Its own body line.")


def test_paragraph_anchor_block_spans_to_blank_line(tmp_path):
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(PARA_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "para-anchor")
    assert "para-anchor" in lines[start]
    assert end - start == 3  # anchor line + two continuation lines
    assert "para-two" not in "\n".join(lines[start:end])


def test_update_replaces_whole_paragraph(tmp_path):
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(PARA_SKILL.format(name="nav2"))
    (tmp_path / "archive").mkdir()
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "para-anchor",
        "content": "**Rewritten paragraph.** <!-- id: para-anchor -->\nNew single body line.\n",
        "reason": "obs-nav2-100"}])
    text = (d / "SKILL.md").read_text()
    assert rep["applied"]
    assert "First continuation line" not in text
    assert "Second continuation line" not in text
    assert "Rewritten paragraph." in text
    assert "para-two" in text  # neighbor untouched


def test_bullet_anchor_behavior_unchanged(tmp_path):
    d = mk_skill(tmp_path)
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "inflation-layer")
    assert end - start == 2  # bullet + indented continuation, exactly as before
```

- [ ] **Step 2: Run to verify the new tests fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_apply_deltas.py -v -k "paragraph or whole_paragraph or behavior_unchanged"`
Expected: the two paragraph tests FAIL (block ends at the anchor line today); the bullet test PASSES (guard).

- [ ] **Step 3: Implement**

Replace `find_anchor_block`'s body:

```python
def find_anchor_block(lines, anchor):
    marker = _ANCHOR.format(anchor)
    for i, line in enumerate(lines):
        if marker in line:
            stripped = line.lstrip()
            if stripped.startswith("- ") or stripped.startswith("* "):
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
            # paragraph anchor (bold-paragraph or plain-prose item):
            # block runs to the first blank line or heading (exclusive)
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip() or nxt.startswith("#"):
                    break
                j += 1
            return (i, j)
    return None
```

- [ ] **Step 4: Full apply_deltas suite + engine suite green**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine -q`
Expected: 158 passed (155 + 3), zero regressions.

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/apply_deltas.py tests/engine/test_apply_deltas.py
git commit -m "fix(engine): find_anchor_block — paragraph anchors resolve as full blocks (closes #80)"
```

---

### Task 2: Polish bundle (issue #81) — changelog anchor naming, blank-line accretion, null-reason sort, recall ellipsis, deltas convention

**Files:**
- Modify: `scripts/engine/apply_deltas.py`, `hooks/scripts/recall.py`
- Modify: `skills/learning-loop/references/delta-format.md` (deltas-location convention — reference-only edit inside learning-loop; no bump: engine-doc precedent from 2b in-branch fixes does NOT apply post-merge, so bump learning-loop 0.1.0 → 0.1.1 with archive snapshot; changelog line "- 0.1.1 (<date>): delta-format documents the learnings/deltas/ location convention (#81)")
- Modify: `tests/engine/test_apply_deltas.py`, `tests/engine/test_recall.py` (append tests)

**Interfaces (behavior changes):**
- add-op changelog summaries name the new anchor: `add <anchor-id> (<section>)` — anchor id extracted from the op's content via the existing `<!-- id: … -->` regex; falls back to the current `add <section>` when content carries no anchor.
- `_bump_and_log` inserts the entry followed by exactly ONE blank line and consumes one pre-existing blank at the insert point if present (no accretion on repeated bumps — test bumps twice and asserts the gap stays constant).
- Reasons join: `sorted({str(op.get("reason") or "?") for op in applied_ops})` — a batch mixing `reason: null` with strings must not TypeError (test).
- `recall.render`: a truncated target gets a trailing `…` (test: budget forces truncation → rendered line ends with `…`; untruncated lines don't).
- delta-format.md gains a short "Where deltas files live" paragraph: committed deltas go to `learnings/deltas/YYYY-MM-DD-<topic>.yaml`; scratch/dry-run experiments may live anywhere gitignored.

- [ ] **Step 1: Write the failing tests** — four tests: `test_add_changelog_names_new_anchor` (apply an add; changelog line contains the content's anchor id), `test_repeated_bumps_do_not_accrete_blank_lines` (two sequential apply runs on the same skill — second needs the first's version bumped so use two deltas files; assert the blank-line count between the convention comment and the first entry is identical after each), `test_null_reason_does_not_crash` (two ops, one `reason: null` → applies, changelog contains `?`), `test_render_ellipsis_on_truncation` (in test_recall.py).
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement the four changes + the delta-format paragraph + learning-loop bump mechanics (snapshot `archive/learning-loop/0.1.0/` FIRST).**
- [ ] **Step 4: Full suite green** (`162 passed` expected: 158 + 4); validator 24 PASS.
- [ ] **Step 5: Commit**

```bash
git add scripts/engine/apply_deltas.py hooks/scripts/recall.py skills/learning-loop archive/learning-loop tests/engine
git commit -m "fix(engine): apply_deltas + recall polish — anchor-named changelogs, stable spacing, null reasons, ellipsis (closes #81 items 1-3,5); learning-loop 0.1.1 documents learnings/deltas/"
```

---

### Task 3: Task-check runner (`run_task_checks.py`) + evals `tasks:` schema

**Files:**
- Create: `scripts/engine/run_task_checks.py`
- Modify: `skills/skill-author/scripts/validate_skills.py` (tasks-entry schema check) + skill-author 2.0.0 → 2.0.1 (snapshot `archive/skill-author/2.0.0/` first; changelog line)
- Test: `tests/engine/test_task_checks.py` (+ append one validator test to `tests/engine/test_validator_extensions.py`)

**Interfaces:**
- evals.yaml `tasks:` schema (spec §4.3's deep checks, finalized):

```yaml
tasks:
  - name: pusht-dataset-loads          # required, kebab-case, unique per skill
    command: "uv run --with 'lerobot[dataset]' skills/lerobot/examples/load-dataset-snippet.py"  # required
    pass_criteria: "observation\\.image"  # required — regex the combined stdout+stderr must match (exit 0 also required)
    app: apps/vla-trial                   # optional cwd, repo-root-relative; default repo root
    example: examples/load-dataset-snippet.py  # optional — the skill artifact this verifies (deep-verify joins on it)
    timeout: 900                          # optional seconds, default 300
```

- Module (PEP-723 pyyaml):
  - `load_tasks(skill, skills_dir) -> list[dict]` — [] when absent
  - `run_task(task, repo_root, dry_run=False) -> dict` — `{"name","pass":bool,"exit":int|None,"matched":bool,"seconds":float,"tail":str}`; PASS = exit 0 AND regex matches combined output; timeout → pass False with `"exit": None`, tail notes the timeout; dry_run prints the command and returns pass None (skipped)
  - CLI: `uv run scripts/engine/run_task_checks.py --skills <names…> [--task <name>] [--dry-run] [--repo-root .]` → per-task PASS/FAIL lines + `Task checks: P passed, F failed, S skipped-skills`, exit 1 on failure, skipped-and-said when a skill has no tasks
- Validator addition (inside the existing `check_sidecars`): each `tasks:` entry must be a mapping with non-empty string `name`, `command`, `pass_criteria`; `timeout` int if present; unknown keys allowed. Malformed → `FAIL:` line.

- [ ] **Step 1: Write the failing tests** — fixture skill in tmp with an evals.yaml whose tasks run hermetic `python3 -c` commands: pass (exit 0 + regex hit), fail-regex (exit 0, no match), fail-exit (`sys.exit(2)`), timeout (`time.sleep(5)` with `timeout: 1` — assert seconds < 4), no-tasks-skip, `--task` name filter, dry-run runs nothing. Validator test: a tasks entry missing `pass_criteria` → `FAIL:` line mentioning it.
- [ ] **Step 2: Run to verify they fail** (ModuleNotFoundError / validator passes where it shouldn't).
- [ ] **Step 3: Implement runner + validator check (+ skill-author 2.0.1 snapshot/bump/changelog).**
- [ ] **Step 4: Full suite + validator green** (~170 tests).
- [ ] **Step 5: Commit**

```bash
git add scripts/engine/run_task_checks.py tests/engine/test_task_checks.py tests/engine/test_validator_extensions.py skills/skill-author archive/skill-author/2.0.0
git commit -m "feat(engine): task-check runner — evals.yaml tasks fixtures with validator schema (skill-author 2.0.1)"
```

---

### Task 4: Variant A/B harness (`run_variants.py`)

**Files:**
- Create: `scripts/engine/run_variants.py`
- Test: `tests/engine/test_variants.py`

**Interfaces:**
- Variants spec YAML:

```yaml
skill: nav2
observation: obs-nav2-003
baseline: {}                      # baseline = current catalog, always scored
variants:
  - name: A
    deltas: learnings/deltas/2026-08-XX-nav2-ab-A.yaml
  - name: B
    deltas: learnings/deltas/2026-08-XX-nav2-ab-B.yaml
```

- Module:
  - `build_variant(name, deltas_path, skills_dir, workdir) -> str` — copies the whole skills tree to `<workdir>/<name>/skills`, runs `apply_deltas.apply_file(deltas, skills_dir=copy, archive_dir=<workdir>/<name>/archive)`; raises if the report has refusals or zero applied ops (a variant that doesn't apply is a broken candidate, not a scored one)
  - `score_variant(name, skill, variant_skills_dir, baseline_skills_dir, no_llm) -> dict` — `{"name","triggers": {passed,failed,skipped}, "flips": int, "tasks": {passed,failed,skipped}|None, "tokens": int}`: triggers via `run_trigger_evals.run_skill` against the variant catalog; flips via `run_trigger_evals.flip_gate` with the baseline skill dir; tasks via `run_task_checks` IF the skill has tasks AND `--with-tasks` given (they're expensive — off by default, said in the report); tokens = `len(SKILL.md text)//4`
  - `blind_judge(observation_text, variant_texts: dict[label, text], timeout_s=45) -> dict|None` — labels shuffled (mapping recorded), `claude -p` prompt: "Given this finding: <observation>. Which candidate skill-text integrates it most accurately and leanly? Reply the single letter." ANY failure → None (table says skipped + reason)
  - Fitness ordering (spec §9): rank by (trigger pass-rate desc, task pass-rate desc treating None as equal, tokens asc). `rank(scores) -> list`
  - `archive_losers(skill, date, winner, variants_workdir, archive_dir)` — copies each losing variant's applied skill dir + its deltas file + `scores.md` to `archive/<skill>/variants/<date>/<name>/`
  - CLI: `uv run scripts/engine/run_variants.py spec.yaml [--no-llm] [--with-tasks] [--workdir …] [--archive-losers --winner <name> --date <date>]` → markdown score table (one row per variant incl. baseline, columns: triggers, flips, tasks, ~tokens, judge pick) + `recommendation: <name> (engine ranks; the human picks by merging)`; exit 0 always (scores are information, not gates)
- The branch guard inside apply_deltas fails open in the non-git workdir — expected and correct (document in the module docstring).

- [ ] **Step 1: Write the failing tests** — synthetic two-skill catalog (reuse the Task-4-of-2b fixture style) with an evals.yaml on the target skill; variant A's deltas update the description-adjacent anchored bullet keeping trigger keywords; variant B's deltas replace it dropping the keywords → deterministic assertions: `build_variant` produces an applied copy (and raises on a refused deltas file); `score_variant` gives A ≥ triggers than B; `rank` puts A first and baseline beats B on triggers ties via tokens; `archive_losers` lays out `archive/<skill>/variants/<date>/<loser>/` with the skill dir + deltas + scores.md; `blind_judge` returns None with no_llm-style failure (monkeypatch subprocess to raise). All `--no-llm`-path deterministic.
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Full suite green** (~176 tests).
- [ ] **Step 5: Commit**

```bash
git add scripts/engine/run_variants.py tests/engine/test_variants.py
git commit -m "feat(engine): variant A/B harness — tmp-catalog builds, fitness-ranked scores, blind judge with honest fallback, loser archiving"
```

---

### Task 5: Deep-verify lane (`deep_verify.py`)

**Files:**
- Create: `scripts/engine/deep_verify.py`
- Test: `tests/engine/test_deep_verify.py`

**Interfaces:**
- `inventory(skills_dir) -> list[dict]` — every file under `skills/*/examples/` and `skills/*/references/` containing `status: unverified`; each `{"skill","file","fixture": task-name|None}` where fixture joins on an evals.yaml task whose `example:` matches the file's skill-relative path
- `run_for_skill(skill, skills_dir, repo_root, date) -> dict` — for each unverified example WITH a fixture: run the task (via run_task_checks.run_task); on PASS append an annotate op to the emitted deltas: `{skill, op: annotate, file: <example-rel-path>, find: "status: unverified", replace: "status: verified <date> (deep-verify: <task-name>)", reason: deep-verify-<task-name>}`; on FAIL record the tail. Returns `{"deltas": [...], "passed": [...], "failed": [...], "unfixtured": [...]}`
- CLI: `uv run scripts/engine/deep_verify.py --inventory` (table incl. unfixtured count — no silent caps) | `--run --skills <names…> [--date …] [--out learnings/deltas/<date>-deep-verify.yaml]` — writes the deltas file (never applies; apply_deltas is the only writer of skills content), prints the report, exit 0 with failures reported (scheduled-lane semantics: a failing example is a finding, not an error)
- The emitted reason ids intentionally do NOT match `obs-*` — mark_absorbed skips them (no observation to flip); the changelog reason string still records the fixture name.

- [ ] **Step 1: Write the failing tests** — fixture skill with `examples/x.py` marked unverified + a matching task (`example: examples/x.py`, hermetic passing command) → run_for_skill emits exactly one annotate op with the right find/replace/date; failing command → no delta, failure recorded with tail; example with no fixture → listed unfixtured; inventory counts across two skills; end-to-end: emitted deltas file applied via apply_deltas flips the marker in the copy and bumps build.
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Full suite green** (~181 tests).
- [ ] **Step 5: Commit**

```bash
git add scripts/engine/deep_verify.py tests/engine/test_deep_verify.py
git commit -m "feat(engine): deep-verify lane — fixture-run unverified examples emit annotate promotions"
```

---

### Task 6: learning-loop 0.2.0 — experiment + deep-verify modes

**Files:**
- Modify: `skills/learning-loop/SKILL.md` (0.1.1 → 0.2.0; snapshot `archive/learning-loop/0.1.1/` first)
- Create: `skills/learning-loop/references/experiment-recipes.md`

**Content requirements (author against the implemented tools — the Task 4/5 CLIs are ground truth):**
- Description: append the two mode surfaces, staying ≤1024 chars: "…run blind variant A/B on contested edits ('experiment', 'A/B this edit', 'try competing fixes'), and deep-verify unverified examples in pinned fixtures ('deep verify', 'verify the examples')."
- When-to-use: two new bullets (contested edit → experiment; scheduled example verification → deep-verify).
- Decision guidance: two new subsections. **Experiment** (spec §9): trigger = contested/structural edits (description rewrites, restructures, competing fixes); flow = 2–3 feedback-conditioned DELTA variants (never rewrites) + baseline → run_variants → score table in the PR → human picks by merging → `--archive-losers` (archive is branch-points, not garbage); fitness ordering stated; the engine recommends, never selects unattended. **Deep-verify**: scheduled lane, not per-PR; fixtures live in evals.yaml `tasks:` with `example:` joins; output is an emitted deltas file absorbed through the normal pipeline.
- Key directives: one new anchored bullet — "**Variants are deltas, never rewrites.** <!-- id: variants-are-deltas --> Full-file candidate rewrites are forbidden (context collapse); a variant that apply_deltas refuses is a broken candidate, not a contender."
- References: the two new tools + `references/experiment-recipes.md` line.
- experiment-recipes.md (~6–8 KB): a worked variant-A/B walkthrough (spec commands, score-table reading, loser archiving); the **contrastive-rollouts recipe** (spec §9: N parallel agents attempt the same scripted app task with/without the candidate variant; pass-vs-fail diff distilled into observations; reserved for high-stakes questions — new skill structure, disputed best-known-method; breadth/depth model split: cheap models draft variants and run rollouts, the strong model judges and distills; orchestrate via the harness's workflow/subagent fan-out where available); when NOT to experiment (single obvious fix → plain absorb).
- Changelog: `- 0.2.0 (<date>): experiment + deep-verify modes land (run_variants, deep_verify, task checks); experiment-recipes reference incl. contrastive-rollouts recipe (Phase 3, spec §9).`

- [ ] **Steps:** snapshot → edit → `grep -nE '`[^`]*(/|\.md|\.py|\.yaml)[^`]*`' skills/learning-loop/**` backtick check → validator 24 PASS → full suite → commit `feat(skills): learning-loop 0.2.0 — experiment + deep-verify modes (Phase 3)`.

---

### Task 7: Pilot — blind A/B resolves obs-nav2-003 (exit criterion 1)

**PRECONDITION (hard):** `gh pr view 78 79 --json state` both MERGED. If either is OPEN: STOP, report BLOCKED — the user merges (or explicitly re-scopes the pilot). After merge, rebase the plan's worktree branch on updated main before proceeding.

**Flow (learning-loop experiment mode, executed for real):**
1. Branch `loop/experiment-<date>-nav2-cmdvel` from the rebased worktree HEAD.
2. Read obs-nav2-003 (learnings/observations/nav2.md — ready, held; the TwistStamped plugin-API-vs-wire-format decoupling with its correction notes) + the post-#78 nav2 skill. Draft THREE structurally competing delta variants, feedback-conditioned, each a deltas file under learnings/deltas/: (A) a standalone Usage-patterns paragraph entry; (B) an update extending the existing `cmd-vel-twiststamped` anchor block to carry the decoupling; (C) a minimal two-sentence annotate adjacent to the anchor + cross-ref. Every variant MUST carry the observation's guard ("plugin returns TwistStamped ⇒ /cmd_vel is TwistStamped is not a valid inference") — a variant that drops it is disqualified before scoring.
3. `uv run scripts/engine/run_variants.py <spec> ` — attempt the blind judge (real `claude -p`, 45 s box); honest fallback noted. nav2 has no evals.yaml cases post-#78? Check; if trigger evals skip, the table says so and ranking falls to flips/tokens/judge — state it.
4. Apply the WINNER's deltas on the branch via apply_deltas (this consumes obs-nav2-003 → absorbed); `--archive-losers` into `archive/nav2/variants/<date>/`; validator + suite + observations lint green.
5. PR `--base main`: title "loop: experiment — nav2 cmd_vel decoupling (blind A/B)"; body = the full score table + judge status + per-variant one-line rationale + losing-variant archive paths + "the engine recommends <X>; merging accepts it — comment to pick another variant and I'll re-apply." Footer per convention. Record the URL.
6. Return to the worktree branch.

**Exit evidence:** a contested edit resolved by blind A/B with scores in the PR (criterion complete at the user's merge, framed as such).

---

### Task 8: Pilot — deep-verify promotes an example to ✓ (exit criterion 2)

1. On the worktree branch: add the fixture task to `skills/lerobot/evals.yaml` (sidecar, no bump):

```yaml
tasks:
  - name: pusht-dataset-loads
    example: examples/load-dataset-snippet.py
    command: "uv run --with 'lerobot[dataset]' python skills/lerobot/examples/load-dataset-snippet.py"
    pass_criteria: "observation\\.image"
    timeout: 900
```

   (Adjust the command to the snippet's actual invocation — read the file first; it may need `--with torch` extras. Dry-run the command manually once before wiring it.)
2. `uv run scripts/engine/deep_verify.py --inventory` — record the full unfixtured count (no silent caps: the report names how many unverified examples still lack fixtures).
3. `uv run scripts/engine/deep_verify.py --run --skills lerobot --out learnings/deltas/<date>-deep-verify.yaml`. If the pusht download/execution fails for environmental reasons: fall back to the ros2 package-ament-python fixture (task: docker run `ros:<current distro per the ros2 skill>` mounting the example, `colcon build` + run the talker, pass_criteria on its published output — consult the ros2 skill for the distro tag, don't hardcode from memory) and SAY which fixture ran.
4. Branch `loop/deep-verify-<date>` → apply the emitted deltas (lerobot build bump via annotate) → validator + suite → PR `--base main` with the run log tail as evidence + the inventory table (fixtured vs unfixtured). Record URL. Return to worktree branch.

**Exit evidence:** ≥1 example promoted to ✓ by automated deep-verify (completes at merge; framed as such).

---

### Task 9: Exit checklist + changelog

1. Full battery (engine suite, validator, observations lint, citation verify with absolute --repos, manifests).
2. Checklist: engine additions shipped with green suites (#80/#81 closed by commits — note "closes" only fires on merge to main); learning-loop 0.2.0 in catalog; A/B pilot PR open with score table (criterion 1 at merge); deep-verify PR open with promotion (criterion 2 at merge); contrastive recipe documented (deliberately recipe-only, recorded).
3. docs/CHANGELOG.md entry at TOP, dated, HISTORY ONLY (no forward-looking sentences): engine additions, learning-loop 0.2.0, both pilot PRs by number, the #80/#81 fixes. Commit.

---

## Self-review notes (performed at plan-writing time)

- **Spec coverage (Phase 3 row of §15):** Variant A/B → Tasks 4+7 (blind judging, scores-in-PR, losing variants archived with scores per §9); contrastive rollouts → recipe-only in Task 6 (standing decision — exit criteria don't require execution; §9 reserves them); deep-verify sim/app lane → Tasks 5+8 (§8 layer 4: unverified → annotate promotion with date+fixture, scheduled not per-PR); eval task checks → Task 3 (§4.3 `tasks:` shape). Fitness ordering and breadth/depth split land in Task 4 code + Task 6 prose. Engine-hardening issues #80/#81 front-load because absorb-adjacent tooling (Task 7 applies deltas to paragraph anchors #78 minted).
- **Sequencing risks addressed:** Task 7's hard precondition on #78/#79 merging (archive-slot conflicts); rebase-after-merge step explicit; Task 8's fixture has a named fallback with a don't-hardcode-distro instruction.
- **Type consistency:** run_task_checks.run_task's result dict is consumed by deep_verify and (optionally) run_variants; run_trigger_evals.run_skill/flip_gate signatures unchanged from 2b; find_anchor_block signature unchanged (Task 1 is behavior-widening only, guarded by the unchanged-bullet test).
- **Placeholder scan:** Tasks 1 code complete; Tasks 2–5 specify exact tests-first contracts with full schemas/signatures and hermetic fixtures (implementation follows the established module patterns — apply_deltas/run_trigger_evals are in-repo templates; the per-task reviewer verifies against the stated contracts); Task 6 lists exact content requirements incl. the anchored directive text; pilots are agent-workflow tasks gated by the deterministic tools they exercise, per the 2a/2b pattern.
- **No catalog-count churn:** 24 throughout; bumps limited to learning-loop (0.1.1, 0.2.0), skill-author (2.0.1), nav2 (winner variant), lerobot (annotate build).
