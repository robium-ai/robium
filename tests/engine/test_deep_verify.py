import textwrap

import yaml

import apply_deltas as ad
import deep_verify as dv

PASS_TASK = {
    "name": "x-runs",
    "example": "examples/x.py",
    "command": "python3 -c \"import sys; print('marker-ok'); sys.exit(0)\"",
    "pass_criteria": "marker-ok",
}

FAIL_TASK = {
    "name": "x-fails",
    "example": "examples/x.py",
    "command": "python3 -c \"import sys; print('nope'); sys.exit(1)\"",
    "pass_criteria": "marker-ok",
}

SKILL_MD = textwrap.dedent("""\
    ---
    name: nav2
    version: 1.2.3
    description: >
      Test skill about costmaps and navigation tuning.
    ---

    # nav2

    ## When to use this skill

    - Testing.

    ## Key directives

    - Something. <!-- id: something -->

    ## Changelog

    - 1.2.3 (2026-07-01): prior line.
    """)


def _mk_examples_skill(tmp_path, name="nav2", tasks=None, unverified_text="# status: unverified\nprint('hi')\n"):
    d = tmp_path / "skills" / name
    (d / "examples").mkdir(parents=True)
    (d / "examples" / "x.py").write_text(unverified_text)
    if tasks is not None:
        (d / "evals.yaml").write_text(yaml.safe_dump({"tasks": tasks}))
    return d


# ---------------------------------------------------------------------------
# run_for_skill
# ---------------------------------------------------------------------------

def test_run_for_skill_pass_emits_exactly_one_annotate_op(tmp_path):
    _mk_examples_skill(tmp_path, tasks=[PASS_TASK])
    res = dv.run_for_skill("nav2", str(tmp_path / "skills"), str(tmp_path), "2026-08-05")
    assert len(res["deltas"]) == 1
    assert res["deltas"][0] == {
        "skill": "nav2",
        "op": "annotate",
        "file": "examples/x.py",
        "find": "status: unverified",
        "replace": "status: verified 2026-08-05 (deep-verify: x-runs)",
        "reason": "deep-verify-x-runs",
    }
    assert res["passed"] == [{"skill": "nav2", "file": "examples/x.py", "task": "x-runs"}]
    assert res["failed"] == []
    assert res["unfixtured"] == []


def test_run_for_skill_fail_emits_no_delta_records_tail(tmp_path):
    _mk_examples_skill(tmp_path, tasks=[FAIL_TASK])
    res = dv.run_for_skill("nav2", str(tmp_path / "skills"), str(tmp_path), "2026-08-05")
    assert res["deltas"] == []
    assert res["passed"] == []
    assert len(res["failed"]) == 1
    failure = res["failed"][0]
    assert failure["skill"] == "nav2"
    assert failure["file"] == "examples/x.py"
    assert failure["task"] == "x-fails"
    assert "tail" in failure and failure["tail"]
    assert res["unfixtured"] == []


def test_run_for_skill_no_fixture_listed_unfixtured(tmp_path):
    _mk_examples_skill(tmp_path, tasks=None)  # no evals.yaml at all
    res = dv.run_for_skill("nav2", str(tmp_path / "skills"), str(tmp_path), "2026-08-05")
    assert res["deltas"] == []
    assert res["passed"] == []
    assert res["failed"] == []
    assert res["unfixtured"] == [{"skill": "nav2", "file": "examples/x.py"}]


def test_run_for_skill_task_with_no_matching_example_leaves_file_unfixtured(tmp_path):
    # A task exists but its `example:` points elsewhere — the join fails,
    # so the file is still unfixtured (not silently matched to the wrong task).
    other_task = dict(PASS_TASK, example="examples/other.py")
    _mk_examples_skill(tmp_path, tasks=[other_task])
    res = dv.run_for_skill("nav2", str(tmp_path / "skills"), str(tmp_path), "2026-08-05")
    assert res["unfixtured"] == [{"skill": "nav2", "file": "examples/x.py"}]
    assert res["deltas"] == []


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------

def test_inventory_counts_across_two_skills_examples_and_references(tmp_path):
    skills_dir = tmp_path / "skills"

    d1 = skills_dir / "nav2"
    (d1 / "examples").mkdir(parents=True)
    (d1 / "examples" / "x.py").write_text("# status: unverified\n")
    (d1 / "evals.yaml").write_text(yaml.safe_dump({"tasks": [PASS_TASK]}))

    d2 = skills_dir / "lerobot"
    (d2 / "references").mkdir(parents=True)
    (d2 / "references" / "z.md").write_text("status: unverified\n")
    (d2 / "examples").mkdir(parents=True)
    (d2 / "examples" / "verified.py").write_text("# status: verified 2026-01-01\n")

    items = dv.inventory(str(skills_dir))
    by_file = {(i["skill"], i["file"]): i["fixture"] for i in items}
    assert by_file == {
        ("nav2", "examples/x.py"): "x-runs",
        ("lerobot", "references/z.md"): None,
    }


def test_inventory_skips_skill_dirs_with_no_examples_or_references(tmp_path):
    skills_dir = tmp_path / "skills"
    d = skills_dir / "bare"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: bare\nversion: 1.0.0\n---\n")
    assert dv.inventory(str(skills_dir)) == []


# ---------------------------------------------------------------------------
# End-to-end: emitted deltas file applied via apply_deltas
# ---------------------------------------------------------------------------

def test_end_to_end_emitted_deltas_applied_flips_marker_and_bumps_build(tmp_path):
    skills_dir = tmp_path / "skills"
    d = skills_dir / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(SKILL_MD)
    (d / "examples").mkdir()
    (d / "examples" / "x.py").write_text("# status: unverified\nprint('hi')\n")
    (d / "evals.yaml").write_text(yaml.safe_dump({"tasks": [PASS_TASK]}))
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()

    res = dv.run_for_skill("nav2", str(skills_dir), str(tmp_path), "2026-08-05")
    assert len(res["deltas"]) == 1

    deltas_path = tmp_path / "deltas.yaml"
    deltas_path.write_text(yaml.safe_dump({"date": "2026-08-05", "deltas": res["deltas"]}))

    rep = ad.apply_file(str(deltas_path), skills_dir=str(skills_dir), archive_dir=str(archive_dir))
    assert rep["refused"] == []
    assert rep["skills_bumped"]["nav2"] == ("1.2.3", "1.2.4")  # build bump

    text = (d / "examples" / "x.py").read_text()
    assert "status: verified 2026-08-05 (deep-verify: x-runs)" in text
    assert "status: unverified" not in text
    md_text = (d / "SKILL.md").read_text()
    assert "version: 1.2.4" in md_text
    assert "deep-verify-x-runs" in md_text  # reason recorded in changelog


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_inventory_table_reports_unfixtured_count_no_cap(tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    d = skills_dir / "nav2"
    (d / "examples").mkdir(parents=True)
    (d / "examples" / "x.py").write_text("# status: unverified\n")
    (d / "examples" / "y.py").write_text("# status: unverified\n")
    rc = dv.main(["--inventory", "--skills-dir", str(skills_dir)])
    out = capsys.readouterr().out
    assert "examples/x.py" in out
    assert "examples/y.py" in out
    assert "unfixtured: 2" in out
    assert rc == 0


def test_cli_run_writes_deltas_file_and_reports(tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    _mk_examples_skill(tmp_path, tasks=[PASS_TASK])
    out_path = tmp_path / "out.yaml"
    rc = dv.main([
        "--run", "--skills", "nav2",
        "--skills-dir", str(skills_dir),
        "--repo-root", str(tmp_path),
        "--date", "2026-08-05",
        "--out", str(out_path),
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PASS" in out
    written = yaml.safe_load(out_path.read_text())
    assert written["date"] == "2026-08-05"
    assert len(written["deltas"]) == 1
    assert written["deltas"][0]["reason"] == "deep-verify-x-runs"


def test_cli_run_exit_zero_on_failures_scheduled_lane_semantics(tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    _mk_examples_skill(tmp_path, tasks=[FAIL_TASK])
    out_path = tmp_path / "out.yaml"
    rc = dv.main([
        "--run", "--skills", "nav2",
        "--skills-dir", str(skills_dir),
        "--repo-root", str(tmp_path),
        "--out", str(out_path),
    ])
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert rc == 0  # a failing example is a finding, not an error
    written = yaml.safe_load(out_path.read_text())
    assert written["deltas"] == []


def test_cli_run_never_applies_only_writes_out_path(tmp_path, capsys):
    # deep_verify must never touch skills/ content itself — only the --out file.
    skills_dir = tmp_path / "skills"
    d = _mk_examples_skill(tmp_path, tasks=[PASS_TASK])
    before = (d / "examples" / "x.py").read_text()
    out_path = tmp_path / "out.yaml"
    dv.main([
        "--run", "--skills", "nav2",
        "--skills-dir", str(skills_dir),
        "--repo-root", str(tmp_path),
        "--date", "2026-08-05",
        "--out", str(out_path),
    ])
    after = (d / "examples" / "x.py").read_text()
    assert before == after  # file under skills/ is untouched
    assert out_path.exists()
