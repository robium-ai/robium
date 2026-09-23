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


def test_negative_expect_rejects_the_wrong_neighbor(tmp_path, monkeypatch):
    skills = mk_catalog(tmp_path)
    monkeypatch.setattr(
        rte, "judge_details", lambda *_args, **_kwargs: ("not-bar", "semantic")
    )
    out = rte.run_skill("foo", skills, no_llm=True)
    negative = [c for c in out["cases"] if c["kind"] == "negative"]
    assert negative and not negative[0]["pass"]


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


def test_lexical_fallback_is_marked_inconclusive(tmp_path):
    skills = mk_catalog(tmp_path)
    out = rte.run_skill("foo", skills, no_llm=True)
    assert out["cases"] and all(not case["conclusive"] for case in out["cases"])


def test_cli_lexical_miss_is_diagnostic_not_blocking(tmp_path, capsys):
    skills = mk_catalog(tmp_path)
    md = tmp_path / "skills" / "foo" / "SKILL.md"
    md.write_text(FOO.replace(
        "Costmap tuning and obstacle inflation for mobile robot navigation.",
        "General helper utilities."))
    result = rte.main(["--skills", "foo", "--skills-dir", skills, "--no-llm"])
    assert result == 0
    assert "DIAGNOSTIC MISS" in capsys.readouterr().out


def test_cli_flip_gate_requires_both_flags(capsys):
    """CLI should error if only --flip-gate-baseline or --flip-skill is provided."""
    # Only --flip-gate-baseline
    result = rte.main(["--skills", "foo", "--flip-gate-baseline", "/tmp"])
    assert result == 1
    captured = capsys.readouterr()
    assert "flip gate NOT run: both --flip-gate-baseline and --flip-skill are required" in captured.out

    # Only --flip-skill
    result = rte.main(["--skills", "foo", "--flip-skill", "foo"])
    assert result == 1
    captured = capsys.readouterr()
    assert "flip gate NOT run: both --flip-gate-baseline and --flip-skill are required" in captured.out
