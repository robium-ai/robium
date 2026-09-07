from pathlib import Path

import validate_skills as vs


def _make_skill(base: Path, name="navigation", description="Build robot navigation.", body="# Navigation\n\nUse evidence.", evals=None):
    skill = base / name
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n",
        encoding="utf-8",
    )
    if evals is not None:
        (skill / "evals.yaml").write_text(evals, encoding="utf-8")
    return skill


def test_lean_skill_passes(tmp_path):
    assert vs.check_skill(_make_skill(tmp_path)) == []


def test_frontmatter_is_name_and_description_only(tmp_path):
    skill = _make_skill(tmp_path)
    path = skill / "SKILL.md"
    path.write_text(path.read_text().replace("description:", "version: 1.0.0\ndescription:"))
    errors = vs.check_skill(skill)
    assert any("unsupported frontmatter fields: version" in error for error in errors)


def test_missing_description_fails(tmp_path):
    skill = _make_skill(tmp_path)
    path = skill / "SKILL.md"
    path.write_text(path.read_text().replace("description: Build robot navigation.\n", ""))
    assert any("frontmatter missing description" in error for error in vs.check_skill(skill))


def test_description_and_body_limits_are_small(tmp_path):
    skill = _make_skill(tmp_path, description="x" * (vs.MAX_DESCRIPTION_CHARS + 1))
    errors = vs.check_skill(skill)
    assert any("description" in error and "chars" in error for error in errors)

    path = skill / "SKILL.md"
    path.write_text(
        "---\nname: navigation\ndescription: Build robot navigation.\n---\n"
        + "\n".join("line" for _ in range(vs.MAX_BODY_LINES + 1))
    )
    assert any("move conditional depth" in error for error in vs.check_skill(skill))


def test_changelog_is_rejected(tmp_path):
    skill = _make_skill(tmp_path, body="# Navigation\n\n## Changelog\n\n- old")
    assert any("do not carry changelogs" in error for error in vs.check_skill(skill))


def test_local_markdown_links_are_checked(tmp_path):
    skill = _make_skill(tmp_path, body="# Navigation\n\nRead [failures](FAILURES.md).")
    assert any("missing link target: FAILURES.md" in error for error in vs.check_skill(skill))
    (skill / "FAILURES.md").write_text("# Failures\n")
    assert vs.check_skill(skill) == []


def test_example_links_inside_fenced_code_are_not_packaging_links(tmp_path):
    skill = _make_skill(
        tmp_path,
        body="# Navigation\n\n```markdown\n![replace me](assets/example.png)\n```",
    )
    assert vs.check_skill(skill) == []


def test_repo_relative_evidence_link_can_leave_skill(tmp_path):
    skills = tmp_path / "skills"
    skills.mkdir()
    learnings = tmp_path / "learnings"
    learnings.mkdir()
    (learnings / "observed.md").write_text("evidence\n")
    skill = _make_skill(
        skills,
        body="# Navigation\n\nRead [evidence](../../learnings/observed.md).",
    )
    assert vs.check_skill(skill) == []


def test_evals_remain_optional_and_structural(tmp_path):
    good = (
        "triggers:\n  positive:\n    - phrase: robot will not move\n"
        "  negative:\n    - phrase: tune a manipulator\n      expect: lerobot\n"
        "tasks: []\n"
    )
    _make_skill(tmp_path, name="lerobot")
    assert vs.check_skill(_make_skill(tmp_path, name="a", evals=good)) == []
    errors = vs.check_skill(_make_skill(tmp_path, name="b", evals="triggers: nope\n"))
    assert any("evals.yaml invalid" in error for error in errors)


def test_negative_expect_must_name_an_existing_neighbor(tmp_path):
    evals = "triggers:\n  negative:\n    - phrase: tune a manipulator\n      expect: missing\n"
    errors = vs.check_skill(_make_skill(tmp_path, name="a", evals=evals))
    assert any("unknown or current skill" in error for error in errors)


def test_root_support_files_must_be_linked_from_entrypoint(tmp_path):
    skill = _make_skill(tmp_path)
    (skill / "FAILURES.md").write_text("# Failures\n", encoding="utf-8")
    assert any("not linked from SKILL.md" in error for error in vs.check_skill(skill))


def test_angle_bracket_link_with_spaces_is_checked(tmp_path):
    skill = _make_skill(tmp_path, body="# Navigation\n\nRead [platform](<Platform Notes.md>).")
    assert any("missing link target" in error for error in vs.check_skill(skill))
    (skill / "Platform Notes.md").write_text("# Platform\n", encoding="utf-8")
    assert vs.check_skill(skill) == []


def test_readme_check_is_case_insensitive(tmp_path):
    skill = _make_skill(tmp_path)
    (skill / "readme.md").write_text("extra navigation\n", encoding="utf-8")
    assert any("not README.md" in error for error in vs.check_skill(skill))


def test_task_checks_keep_safety_validation(tmp_path):
    evals = "tasks:\n  - name: my-task\n    command: echo hi\n    pass_criteria: hi\n    timeout: 0\n"
    errors = vs.check_skill(_make_skill(tmp_path, name="task", evals=evals))
    assert any("positive integer" in error for error in errors)


def test_task_example_must_exist_inside_its_skill(tmp_path):
    evals = (
        "tasks:\n  - name: my-task\n    command: echo hi\n"
        "    pass_criteria: hi\n    example: examples/missing.py\n"
    )
    errors = vs.check_skill(_make_skill(tmp_path, name="task", evals=evals))
    assert any("example does not exist" in error for error in errors)
