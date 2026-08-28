from pathlib import Path

import validate_skills as vs


def _mk_skill(base_dir, dirname="nav2", body_extra="", evidence=None, evals=None):
    d = base_dir / dirname
    d.mkdir()
    body = "\n".join([
        "## When to use this skill", "x",
        "## Key directives", "- posture. <!-- id: posture -->",
        "## Quick start", "y",
        "## Platform gotchas", "z",
        "## Customization", "c",
        "## References", "r",
        body_extra,
    ])
    (d / "SKILL.md").write_text(
        f"---\nname: {dirname}\nversion: 1.0.0\ndescription: d\n---\n" + body)
    if evidence is not None:
        (d / "evidence.yaml").write_text(evidence)
    if evals is not None:
        (d / "evals.yaml").write_text(evals)
    return d


def test_valid_anchors_pass(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- fact one. <!-- id: costmap-inflation -->")
    assert vs.check_skill(d) == []


def test_duplicate_anchor_fails(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- a. <!-- id: posture -->")
    errs = vs.check_skill(d)
    assert any("duplicate anchor" in e for e in errs)


def test_malformed_anchor_fails(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- a. <!-- id: Bad_Name -->")
    errs = vs.check_skill(d)
    assert any("malformed anchor" in e for e in errs)


def test_malformed_anchor_missing_space(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- a. <!-- id:missing-space -->")
    errs = vs.check_skill(d)
    assert any("malformed anchor" in e for e in errs)


def test_malformed_anchor_uppercase_id(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- a. <!-- ID: foo -->")
    errs = vs.check_skill(d)
    assert any("malformed anchor" in e for e in errs)


def test_malformed_anchor_double_space(tmp_path):
    d = _mk_skill(tmp_path, body_extra="- a. <!--  id: double-space -->")
    errs = vs.check_skill(d)
    assert any("malformed anchor" in e for e in errs)


def test_evidence_schema_enforced(tmp_path):
    good = "posture:\n  helpful: 2\n  harmful: 0\n  sources: [learnings/2026-07-10.md#lrn-1]\n"
    assert vs.check_skill(_mk_skill(tmp_path, dirname="a", evidence=good)) == []
    bad = "posture:\n  helpful: many\n"
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="b", evidence=bad))
    assert any("evidence.yaml" in e for e in errs)


def test_evidence_unknown_anchor_fails(tmp_path):
    ev = "ghost-anchor:\n  helpful: 1\n  harmful: 0\n  sources: []\n"
    errs = vs.check_skill(_mk_skill(tmp_path, evidence=ev))
    assert any("unknown anchor" in e for e in errs)


def test_evals_schema_enforced(tmp_path):
    good = ("triggers:\n  positive:\n    - phrase: robot hugs walls\n"
            "      source: learnings/2026-07-10.md\n  negative:\n"
            "    - phrase: simulate lidar\n      expect: gazebo\ntasks: []\n")
    assert vs.check_skill(_mk_skill(tmp_path, dirname="a2", evals=good)) == []
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="b2", evals="triggers: nope\n"))
    assert any("evals.yaml" in e for e in errs)


def test_missing_sidecars_are_fine(tmp_path):
    assert vs.check_skill(_mk_skill(tmp_path)) == []


def test_tasks_entry_missing_pass_criteria_fails(tmp_path):
    evals = ("tasks:\n  - name: my-task\n    command: echo hi\n")
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c3", evals=evals))
    assert any("pass_criteria" in e for e in errs)


def test_tasks_entry_duplicate_name_fails(tmp_path):
    evals = (
        "tasks:\n"
        "  - name: my-task\n    command: echo hi\n    pass_criteria: hi\n"
        "  - name: my-task\n    command: echo bye\n    pass_criteria: bye\n"
    )
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c4", evals=evals))
    assert any("duplicate" in e.lower() and "my-task" in e for e in errs)


def test_tasks_entry_non_kebab_name_fails(tmp_path):
    evals = "tasks:\n  - name: Foo_Bar\n    command: echo hi\n    pass_criteria: hi\n"
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c5", evals=evals))
    assert any("kebab" in e.lower() and "Foo_Bar" in e for e in errs)


def test_tasks_entry_invalid_regex_pass_criteria_fails(tmp_path):
    """pass_criteria is used as a regex pattern (re.search) by
    run_task_checks.py; an unbalanced/invalid pattern must fail validation
    with a clear message, not surface as a runtime re.error later."""
    evals = "tasks:\n  - name: my-task\n    command: echo hi\n    pass_criteria: '[unclosed'\n"
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c6", evals=evals))
    assert any("pass_criteria" in e and "regex" in e.lower() for e in errs)


def test_tasks_entry_valid_regex_pass_criteria_passes(tmp_path):
    evals = "tasks:\n  - name: my-task\n    command: echo hi\n    pass_criteria: '^OK$'\n"
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c7", evals=evals))
    assert errs == []


def test_tasks_entry_nonpositive_timeout_fails_consistently(tmp_path):
    evals = ("tasks:\n  - name: my-task\n    command: echo hi\n"
             "    pass_criteria: hi\n    timeout: 0\n")
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c8", evals=evals))
    assert any("positive integer" in e for e in errs)


def test_tasks_entry_parent_app_path_fails_consistently(tmp_path):
    evals = ("tasks:\n  - name: my-task\n    command: echo hi\n"
             "    pass_criteria: hi\n    app: ../private\n")
    errs = vs.check_skill(_mk_skill(tmp_path, dirname="c9", evals=evals))
    assert any("repo-root-relative" in e for e in errs)
