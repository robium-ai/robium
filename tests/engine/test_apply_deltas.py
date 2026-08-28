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


def test_mixed_refusal_blocks_whole_batch(tmp_path):
    """C1: Refusals block the entire batch — no file write, no archive, no bump."""
    d = mk_skill(tmp_path)
    before = (d / "SKILL.md").read_text()
    rep = run(tmp_path, [
        # This one is refused: content drops the anchor
        {"skill": "nav2", "op": "update", "anchor": "inflation-layer",
         "content": "- Text without anchor.\n", "reason": "obs-x"},
        # This one would apply (valid add)
        {"skill": "nav2", "op": "add", "section": "Usage patterns",
         "content": "- New pattern. <!-- id: new -->\n", "reason": "obs-y"}])
    # No ops reported as applied (both are refused or blocked)
    assert rep["applied"] == []
    # Both ops appear in report: one with original refused note, one with blocked note
    assert len(rep["refused"]) >= 2
    # At least one refused entry contains "blocked: batch contains a refused op"
    blocked_notes = [item["note"] for item in rep["refused"] if "blocked" in item["note"]]
    assert len(blocked_notes) >= 1, "At least one op should be blocked due to batch refusal"
    # File untouched
    assert (d / "SKILL.md").read_text() == before
    # No archive
    assert not (tmp_path / "archive" / "nav2" / "1.2.3").exists()
    # No version bump
    assert "1.2.3" in (d / "SKILL.md").read_text()


def test_noop_does_not_block_applied_sibling(tmp_path):
    """No-ops (anchor not found) do NOT block the batch."""
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [
        # This is a no-op: anchor doesn't exist
        {"skill": "nav2", "op": "update", "anchor": "nope",
         "content": "- X. <!-- id: nope -->\n", "reason": "obs-a"},
        # This one applies
        {"skill": "nav2", "op": "add", "section": "Usage patterns",
         "content": "- New pattern. <!-- id: new -->\n", "reason": "obs-b"}])
    body = (d / "SKILL.md").read_text()
    # Add succeeded
    assert "New pattern" in body
    # Version bumped
    assert "version: 1.3.0" in body
    # Archive exists
    assert (tmp_path / "archive" / "nav2" / "1.2.3").exists()
    # Noop reported
    assert len(rep["noop"]) == 1
    # Add reported as applied
    assert len(rep["applied"]) == 1


def test_cap_counts_changelog_lines(tmp_path):
    """C2: Body cap is checked AFTER _bump_and_log adds changelog lines."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (tmp_path / "archive").mkdir(exist_ok=True)

    # Build a skill whose body is exactly BODY_CAP - 1 lines after the op
    # This will breach after the changelog insertion (adds 1 line: the new
    # entry — _bump_and_log consumes the pre-existing blank at the insert
    # point and adds exactly one back, so the blank-line count is unchanged)
    from apply_deltas import BODY_CAP
    header = textwrap.dedent("""\
        ---
        name: nav2
        version: 1.0.0
        description: Test
        ---

        # nav2

        ## Key directives
        """)
    # Calculate how many filler lines to reach BODY_CAP - 2
    # (accounting for: 1 new content line + 1 changelog entry line)
    num_fillers = BODY_CAP - 2 - len(header.splitlines())
    filler_lines = ["- Filler bullet."] * num_fillers
    body_content = header + "\n" + "\n".join(filler_lines) + "\n\n## Changelog\n\n- 1.0.0 (2026-07-01): prior."
    (d / "SKILL.md").write_text(body_content)

    # Now apply an op that would add 1 line to the body in Key directives section
    # After changelog insertion, we'll exceed BODY_CAP
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Key directives",
        "content": "- New directive. <!-- id: new-dir -->\n", "reason": "obs-cap"}])

    # The op should be refused due to cap breach
    assert len(rep["refused"]) >= 1
    assert "500-line body cap" in rep["refused"][0]["note"]
    # File untouched
    assert "New directive" not in (d / "SKILL.md").read_text()
    # No archive
    assert not (tmp_path / "archive" / "nav2" / "1.0.0").exists()


def test_changelog_inserts_below_convention_comment(tmp_path):
    """I1: Changelog entry inserts after the convention comment."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (tmp_path / "archive").mkdir(exist_ok=True)

    # Real skill format with convention comment
    skill_md = textwrap.dedent("""\
        ---
        name: nav2
        version: 1.2.0
        description: Test
        ---

        # nav2

        ## Key directives

        - Existing. <!-- id: existing -->

        ## Changelog

        <!-- One dated line per battle-tested change — if many small fixes landed, roll them into one line. -->
        - 1.2.0 (2026-07-01): prior entry.
        """)
    (d / "SKILL.md").write_text(skill_md)

    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "existing",
        "content": "- Updated. <!-- id: existing -->\n", "reason": "obs-new"}])

    text = (d / "SKILL.md").read_text()
    # New entry should come AFTER the convention comment
    changelog_section = text.split("## Changelog")[1]
    comment_pos = changelog_section.index("<!-- One dated line")
    new_entry_pos = changelog_section.index("- 1.3.0")
    assert comment_pos < new_entry_pos
    # And BEFORE the old entry
    old_entry_pos = changelog_section.index("- 1.2.0")
    assert new_entry_pos < old_entry_pos


import ledger


def test_retire_removes_block_and_ledger_key(tmp_path):
    d = mk_skill(tmp_path)
    ledger.increment(str(d), "dds-domain-id", "harmful", "lrn-1", "2026-08-01")
    rep = run(tmp_path, [{"skill": "nav2", "op": "retire",
                          "anchor": "dds-domain-id", "reason": "obs-nav2-003"}])
    text = (d / "SKILL.md").read_text()
    assert "<!-- id: dds-domain-id -->" not in text
    assert "Set the DDS domain id per robot." not in text
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
    src_text = (src / "SKILL.md").read_text()
    assert "<!-- id: existing-pattern -->" not in src_text
    assert "Existing pattern." not in src_text
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


def test_annotate_file_targeting_own_skill_md_bumps_and_persists(tmp_path):
    # Regression: annotate+file targeting the skill's OWN SKILL.md used to
    # have its find/replace correctly applied, but a stale disk-read write
    # (file_effects, computed before the bump) unconditionally overwrote
    # the main working-based write afterward — silently discarding the
    # version bump, the changelog line, and any sibling op's edit, while
    # still consuming the archive slot for the un-bumped version (a
    # permanent dead end for that skill's next legitimate bump). Fixed by
    # routing a same-file target through `working` instead of a fresh
    # disk read + file_effects.
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "annotate", "file": "SKILL.md",
        "find": "- Existing pattern. <!-- id: existing-pattern -->",
        "replace": "- Corrected pattern text. <!-- id: existing-pattern -->",
        "reason": "obs-nav2-009",
    }])
    text = (d / "SKILL.md").read_text()
    assert "Corrected pattern text." in text
    assert rep["skills_bumped"]["nav2"] == ("1.2.3", "1.2.4")  # build bump
    assert "version: 1.2.4" in text
    assert "1.2.4 (2026-08-05)" in text  # changelog line actually landed


def test_annotate_file_own_skill_md_composes_with_sibling_anchor_op(tmp_path):
    # A same-batch sibling anchor op must not be discarded by the
    # same-file annotate (the original bug clobbered both).
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "annotate", "file": "SKILL.md",
         "find": "- Existing pattern. <!-- id: existing-pattern -->",
         "replace": "- Corrected pattern text. <!-- id: existing-pattern -->",
         "reason": "obs-nav2-009"},
        {"skill": "nav2", "op": "update", "anchor": "dds-domain-id",
         "content": "- Set the DDS domain id per robot, always. <!-- id: dds-domain-id -->\n",
         "reason": "obs-nav2-010"},
    ])
    text = (d / "SKILL.md").read_text()
    assert "Corrected pattern text." in text
    assert "Set the DDS domain id per robot, always." in text
    # annotate + update together -> minor bump (kinds not <= {"annotate"})
    assert rep["skills_bumped"]["nav2"] == ("1.2.3", "1.3.0")


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


def test_two_moves_same_destination(tmp_path):
    """Two move ops in one batch targeting the SAME destination skill must
    merge into a single destination write, not crash on a duplicate
    copytree of an archive dir the first move already created."""
    src = mk_skill(tmp_path, "nav2")
    dst = mk_skill(tmp_path, "ros2")
    ledger.increment(str(src), "existing-pattern", "helpful", "lrn-4", "2026-08-01")
    ledger.increment(str(src), "dds-domain-id", "harmful", "lrn-5", "2026-08-01")
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "move", "anchor": "existing-pattern",
         "to_skill": "ros2", "to_section": "Usage patterns", "reason": "obs-a"},
        {"skill": "nav2", "op": "move", "anchor": "dds-domain-id",
         "to_skill": "ros2", "to_section": "Usage patterns", "reason": "obs-b"},
    ])
    src_text = (src / "SKILL.md").read_text()
    dst_text = (dst / "SKILL.md").read_text()
    assert "<!-- id: existing-pattern -->" not in src_text
    assert "<!-- id: dds-domain-id -->" not in src_text
    assert "<!-- id: existing-pattern -->" in dst_text
    assert "<!-- id: dds-domain-id -->" in dst_text
    src_ledger = ledger.load(str(src))
    dst_ledger = ledger.load(str(dst))
    assert "existing-pattern" not in src_ledger and "dds-domain-id" not in src_ledger
    assert "existing-pattern" in dst_ledger and "dds-domain-id" in dst_ledger
    # one destination snapshot, one destination bump — no crash, nothing dropped
    assert (tmp_path / "archive" / "ros2" / "1.2.3").exists()
    assert set(rep["skills_bumped"]) == {"nav2", "ros2"}
    assert len(rep["applied"]) == 2


def test_noop_move_does_not_phantom_bump_destination(tmp_path):
    """A move whose to_section doesn't exist correctly no-ops — but must
    leave NO trace on the destination, even when a sibling op in the same
    source batch does apply (previously the destination buffer was
    registered before the section check, so it still got snapshotted,
    bumped, and given an empty changelog line)."""
    src = mk_skill(tmp_path, "nav2")
    dst = mk_skill(tmp_path, "ros2")
    before_dst = (dst / "SKILL.md").read_text()
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "move", "anchor": "existing-pattern",
         "to_skill": "ros2", "to_section": "No Such Section", "reason": "obs-a"},
        {"skill": "nav2", "op": "update", "anchor": "inflation-layer",
         "content": "- Updated text. <!-- id: inflation-layer -->\n",
         "reason": "obs-b"},
    ])
    assert len(rep["noop"]) == 1 and "to_section not found" in rep["noop"][0]["note"]
    assert any(item["op"] == "update" for item in rep["applied"])
    # destination completely untouched: no write, no snapshot, no bump
    assert (dst / "SKILL.md").read_text() == before_dst
    assert not (tmp_path / "archive" / "ros2").exists()
    assert set(rep["skills_bumped"]) == {"nav2"}


def test_two_moves_same_destination_blocked_when_dest_slot_taken(tmp_path):
    src = mk_skill(tmp_path, "nav2")
    dst = mk_skill(tmp_path, "ros2")
    (tmp_path / "archive" / "ros2" / "1.2.3").mkdir(parents=True)
    before_src = (src / "SKILL.md").read_text()
    before_dst = (dst / "SKILL.md").read_text()
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "move", "anchor": "existing-pattern",
         "to_skill": "ros2", "to_section": "Usage patterns", "reason": "obs-a"},
        {"skill": "nav2", "op": "move", "anchor": "dds-domain-id",
         "to_skill": "ros2", "to_section": "Usage patterns", "reason": "obs-b"},
    ])
    assert rep["refused"] and not rep["applied"]
    assert (src / "SKILL.md").read_text() == before_src
    assert (dst / "SKILL.md").read_text() == before_dst


def test_refuses_to_apply_on_main(tmp_path):
    """Branch guard: apply_file refuses all ops on main branch (not dry-run)."""
    import subprocess
    d = mk_skill(tmp_path)

    # Initialize git repo on main branch
    repo_dir = tmp_path
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True,
                   capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir,
                   check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir,
                   check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True,
                   capture_output=True)

    # Apply should refuse everything on main branch
    rep = ad.apply_file(write_deltas(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- Changed. <!-- id: inflation-layer -->\n", "reason": "obs-c"}]),
        skills_dir=str(tmp_path / "skills"),
        archive_dir=str(tmp_path / "archive"), dry_run=False)

    # Check that guard refused everything
    assert rep["refused"]
    assert "branch" in rep["refused"][0]["note"]
    assert rep["applied"] == []
    # File should not be modified
    assert "Changed" not in (d / "SKILL.md").read_text()


def test_applies_normally_on_non_main_branch(tmp_path):
    """Branch guard: apply_file works normally on non-main branches."""
    import subprocess
    d = mk_skill(tmp_path)

    # Initialize git repo on loop/absorb-test branch
    repo_dir = tmp_path
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True,
                   capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir,
                   check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir,
                   check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True,
                   capture_output=True)
    # Create and checkout loop/absorb-test branch
    subprocess.run(["git", "checkout", "-b", "loop/absorb-test"], cwd=repo_dir,
                   check=True, capture_output=True)

    # Apply should work normally on non-main branch
    rep = ad.apply_file(write_deltas(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "inflation-layer",
        "content": "- Changed. <!-- id: inflation-layer -->\n", "reason": "obs-c"}]),
        skills_dir=str(tmp_path / "skills"),
        archive_dir=str(tmp_path / "archive"), dry_run=False)

    # Check that it applied
    assert rep["applied"]
    assert not rep["refused"]
    # File should be modified
    assert "Changed" in (d / "SKILL.md").read_text()
    # Archive should exist
    assert (tmp_path / "archive" / "nav2" / "1.2.3").exists()


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


ORDERED_LIST_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "1. First ordered item with anchor. <!-- id: ordered-anchor -->\n"
    "   Continuation line indented under first item.\n"
    "2. Second sibling item, not part of first block.\n"
    "3. Third item.")


def test_ordered_list_anchor_block_uses_indent_scan(tmp_path):
    """Ordered-list anchors should use indent-based scanning, not paragraph logic."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(ORDERED_LIST_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "ordered-anchor")
    assert "ordered-anchor" in lines[start]
    # Should span: anchor line + continuation line, stop before item 2
    assert end - start == 2
    assert "Second sibling item" not in "\n".join(lines[start:end])


FENCED_PARA_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "**Paragraph with attached fence.** <!-- id: fenced-para -->\n"
    "Opening line before fence.\n"
    "```yaml\n"
    "# This hash inside fence should not break the block\n"
    "key: value\n"
    "```\n"
    "Line after fence, still same paragraph.\n\n"
    "**Next paragraph.** <!-- id: next-para -->\n"
    "Its own content.")


def test_add_changelog_names_new_anchor(tmp_path):
    """Interface: add-op changelog summaries name the new anchor —
    `add <anchor-id> (<section>)` — extracted from the op's content."""
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Usage patterns",
        "content": "- Added pattern. <!-- id: added-pattern -->\n",
        "reason": "obs-nav2-002"}])
    changelog = (d / "SKILL.md").read_text().split("## Changelog")[1]
    assert "add added-pattern (Usage patterns)" in changelog
    assert rep["applied"] and not rep["refused"]


def _changelog_gap(text):
    """Number of blank lines between the convention comment (or heading,
    if no comment) and the first changelog entry."""
    lines = text.splitlines()
    idx = lines.index("## Changelog")
    i = idx + 1
    while lines[i].strip() == "":
        i += 1
    if lines[i].strip().startswith("<!--"):
        i += 1
    blanks = 0
    while lines[i].strip() == "":
        blanks += 1
        i += 1
    return blanks


def test_repeated_bumps_do_not_accrete_blank_lines(tmp_path):
    """_bump_and_log inserts the entry followed by exactly ONE blank line
    and consumes one pre-existing blank at the insert point if present —
    no accretion across repeated bumps."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (tmp_path / "archive").mkdir(exist_ok=True)
    skill_md = textwrap.dedent("""\
        ---
        name: nav2
        version: 1.2.0
        description: Test
        ---

        # nav2

        ## Key directives

        - Existing. <!-- id: existing -->

        ## Changelog

        <!-- One dated line per battle-tested change — if many small fixes landed, roll them into one line. -->
        - 1.2.0 (2026-07-01): prior entry.
        """)
    (d / "SKILL.md").write_text(skill_md)

    run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "existing",
        "content": "- Updated once. <!-- id: existing -->\n", "reason": "obs-1"}])
    gap1 = _changelog_gap((d / "SKILL.md").read_text())

    run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "existing",
        "content": "- Updated twice. <!-- id: existing -->\n", "reason": "obs-2"}])
    gap2 = _changelog_gap((d / "SKILL.md").read_text())

    assert gap1 == gap2 == 1


def test_null_reason_does_not_crash(tmp_path):
    """Reasons join must tolerate `reason: null` mixed with string reasons
    in the same batch without a TypeError from sorting None with str."""
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [
        {"skill": "nav2", "op": "update", "anchor": "inflation-layer",
         "content": "- Updated line. <!-- id: inflation-layer -->\n", "reason": None},
        {"skill": "nav2", "op": "update", "anchor": "dds-domain-id",
         "content": "- Updated dds. <!-- id: dds-domain-id -->\n",
         "reason": "obs-nav2-001"},
    ])
    changelog = (d / "SKILL.md").read_text().split("## Changelog")[1]
    assert "?" in changelog
    assert rep["applied"] and not rep["refused"]


def test_paragraph_anchor_fence_aware(tmp_path):
    """Paragraph anchors must be fence-aware: # and blanks inside fences don't terminate the block."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(FENCED_PARA_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "fenced-para")
    assert "fenced-para" in lines[start]
    # Should span: anchor line + 1 (before fence) + 4 (fence) + 1 (after fence),
    # stopping at the blank line after fence. Total: 7 lines.
    block_text = "\n".join(lines[start:end])
    assert "Opening line before fence" in block_text
    assert "This hash inside fence" in block_text
    assert "Line after fence" in block_text
    assert "next-para" not in block_text  # Next paragraph not included


# --- Finding 1: wrapped-bullet continuation / table-row / indented-orphan anchors ---
# Mirrors real catalog shapes: skills/nav2/SKILL.md:250-252 (bold lead-in wraps,
# marker lands on the INDENTED continuation line of a bullet) and
# skills/live-demo/SKILL.md:122-124 (marker lands inside a TABLE ROW).

WRAPPED_BULLET_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "- **Preceding unrelated bullet, own gotcha.** <!-- id: preceding-gotcha -->\n"
    "  Its own detail line.\n"
    "- **Composed (`use_composition:=true`) vs standalone nodes change crash\n"
    "  behavior.** <!-- id: composition-vs-standalone --> nav2_bringup defaults to component-container composition; a\n"
    "  crash inside one composed node can take down the whole container process,\n"
    "  whereas standalone nodes (`use_composition:=false`, with\n"
    "  `use_respawn:=true`) restart independently. Prefer standalone + respawn.\n"
    "- **`/cmd_vel` may be `TwistStamped`, not `Twist`.** <!-- id: cmd-vel-twiststamped -->\n"
    "  Modern gz robot integrations subscribe TwistStamped.")


def test_wrapped_bullet_continuation_anchor_resolves_to_enclosing_bullet(tmp_path):
    """A marker sitting on an INDENTED continuation line of a wrapped bold
    lead-in (nav2:250-252 shape) must resolve to the enclosing bullet's own
    block, excluding sibling bullets before and after it."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(WRAPPED_BULLET_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "composition-vs-standalone")
    # Block must start AT the bullet line ("- **Composed..."), not the marker line.
    assert lines[start].lstrip().startswith("- **Composed")
    block_text = "\n".join(lines[start:end])
    assert "composition-vs-standalone" in block_text
    assert "Prefer standalone + respawn" in block_text
    # Sibling bullets excluded on both sides.
    assert "preceding-gotcha" not in block_text
    assert "Its own detail line" not in block_text
    assert "cmd-vel-twiststamped" not in block_text
    assert "TwistStamped" not in block_text


TABLE_ROW_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "| Flow | What the visitor gets | When |\n"
    "| --- | --- | --- |\n"
    "| **Mission-control page** (proven) | Start/Stop buttons | Default.<!-- id: flow-mission-control-default --> |\n"
    "| Deep-link only | One link | Minimal page work.<!-- id: flow-deep-link-minimal --> |")


def test_table_row_anchor_is_single_line(tmp_path):
    """A marker embedded in a markdown TABLE ROW (live-demo:122-124 shape)
    must resolve to exactly that one row, never swallowing sibling rows."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(TABLE_ROW_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "flow-mission-control-default")
    assert end - start == 1
    assert "flow-mission-control-default" in lines[start]
    assert "flow-deep-link-minimal" not in lines[start]


INDENTED_ORPHAN_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "  Orphan indented line with no enclosing bullet. <!-- id: orphan-anchor -->\n"
    "  Another indented continuation line.\n\n"
    "- Normal bullet after, unrelated. <!-- id: after-orphan -->")


def test_indented_marker_with_no_enclosing_bullet_falls_back_to_single_line(tmp_path):
    """An indented marker line with no enclosing list item above it (before a
    blank line/heading) must fall back to a conservative single-line block."""
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(INDENTED_ORPHAN_SKILL.format(name="nav2"))
    lines = (d / "SKILL.md").read_text().splitlines()
    start, end = ad.find_anchor_block(lines, "orphan-anchor")
    assert end - start == 1
    assert "orphan-anchor" in lines[start]


# --- Finding 4: bottom-insert add op must not glue a new paragraph onto a
# preceding non-blank (prose) block. Reproduces the shape of
# learnings/deltas/2026-08-02-nav2-ab-A.yaml (an "add" op landing a bold-
# lead-in paragraph at the bottom of "Usage patterns" whose existing last
# block is prose, not a bullet).

PROSE_TAIL_SKILL = SKILL_MD.replace(
    "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
    "## Usage patterns\n\n"
    "- Existing pattern. <!-- id: existing-pattern -->\n\n"
    "**Existing paragraph tail.** <!-- id: prose-tail --> Some explanatory\n"
    "prose text that ends the section, mirroring real skill content shape.")


def test_add_paragraph_after_prose_tail_inserts_separating_blank_line(tmp_path):
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(PROSE_TAIL_SKILL.format(name="nav2"))
    (tmp_path / "archive").mkdir(exist_ok=True)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Usage patterns", "position": "bottom",
        "content": "**New paragraph.** <!-- id: new-para -->\nBody line for new paragraph.\n",
        "reason": "obs-nav2-200"}])
    assert rep["applied"] and not rep["refused"]
    text = (d / "SKILL.md").read_text()
    lines = text.splitlines()

    # Exactly one blank line between the old tail and the new paragraph.
    tail_idx = next(i for i, l in enumerate(lines) if "mirroring real skill content shape." in l)
    assert lines[tail_idx + 1].strip() == ""
    assert lines[tail_idx + 2].strip() != ""
    assert "new-para" in lines[tail_idx + 2] or "New paragraph" in lines[tail_idx + 2]

    # find_anchor_block on the preceding anchor must exclude the new paragraph.
    start, end = ad.find_anchor_block(lines, "prose-tail")
    block_text = "\n".join(lines[start:end])
    assert "new-para" not in block_text
    assert "New paragraph" not in block_text


def test_add_bullet_after_bullet_tail_unchanged(tmp_path):
    """Bullet adds must remain unaffected by the paragraph-separation fix:
    bullets chain directly with no inserted blank line, exactly as before."""
    d = mk_skill(tmp_path)
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Usage patterns",
        "content": "- Added pattern. <!-- id: added-pattern -->\n",
        "reason": "obs-nav2-002"}])
    assert rep["applied"] and not rep["refused"]
    text = (d / "SKILL.md").read_text()
    section = text.split("## Usage patterns")[1].split("## ")[0]
    lines = [l for l in section.splitlines() if l.strip() != ""]
    # last two non-blank lines are the two bullets, directly adjacent
    assert lines[-2].lstrip().startswith("- Existing pattern")
    assert lines[-1].lstrip().startswith("- Added pattern")
    # and no blank line actually separates them in the raw section text
    raw = section.split("- Existing pattern. <!-- id: existing-pattern -->", 1)[1]
    assert not raw.startswith("\n\n")


def test_add_paragraph_at_section_top_has_canonical_spacing(tmp_path):
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(PARA_SKILL.format(name="nav2"))
    (tmp_path / "archive").mkdir()
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "add", "section": "Usage patterns",
        "position": "top",
        "content": "**New first paragraph.** <!-- id: first-para -->\nIts body.\n",
        "reason": "obs-nav2-201",
    }])
    assert rep["applied"] and not rep["refused"]
    section = (d / "SKILL.md").read_text().split("## Usage patterns", 1)[1].split("## ", 1)[0]
    assert section.startswith("\n\n**New first paragraph.**")
    assert "Its body.\n\n- Existing pattern." in section


def test_update_paragraph_before_heading_inserts_separator(tmp_path):
    skill = SKILL_MD.replace(
        "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->\n\n## Changelog",
        "## Usage patterns\n\n**Old paragraph.** <!-- id: old-para -->\n"
        "Body immediately before heading.\n## Changelog",
    )
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(skill.format(name="nav2"))
    (tmp_path / "archive").mkdir()
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "update", "anchor": "old-para",
        "content": "**New paragraph.** <!-- id: old-para -->\nNew body.\n",
        "reason": "obs-nav2-202",
    }])
    assert rep["applied"] and not rep["refused"]
    text = (d / "SKILL.md").read_text()
    assert "New body.\n\n## Changelog" in text


def test_retire_middle_paragraph_does_not_leave_double_blank(tmp_path):
    skill = SKILL_MD.replace(
        "## Usage patterns\n\n- Existing pattern. <!-- id: existing-pattern -->",
        "## Usage patterns\n\n"
        "**First paragraph.** <!-- id: first-para -->\nFirst body.\n\n"
        "**Retire paragraph.** <!-- id: retire-para -->\nRetire body.\n\n"
        "**Last paragraph.** <!-- id: last-para -->\nLast body.",
    )
    d = tmp_path / "skills" / "nav2"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(skill.format(name="nav2"))
    (tmp_path / "archive").mkdir()
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "retire", "anchor": "retire-para",
        "reason": "obs-nav2-203",
    }])
    assert rep["applied"] and not rep["refused"]
    section = (d / "SKILL.md").read_text().split("## Usage patterns", 1)[1].split("## ", 1)[0]
    assert "Retire paragraph" not in section
    assert "First body.\n\n**Last paragraph.**" in section
    assert "\n\n\n" not in section


def test_move_paragraph_preserves_source_and_destination_spacing(tmp_path):
    src = tmp_path / "skills" / "nav2"
    dst = tmp_path / "skills" / "ros2"
    src.mkdir(parents=True)
    dst.mkdir(parents=True)
    src.joinpath("SKILL.md").write_text(PARA_SKILL.format(name="nav2"))
    dst.joinpath("SKILL.md").write_text(SKILL_MD.format(name="ros2"))
    (tmp_path / "archive").mkdir()
    rep = run(tmp_path, [{
        "skill": "nav2", "op": "move", "anchor": "para-anchor",
        "to_skill": "ros2", "to_section": "Usage patterns",
        "reason": "obs-nav2-204",
    }])
    assert rep["applied"] and not rep["refused"]
    src_section = src.joinpath("SKILL.md").read_text().split(
        "## Usage patterns", 1)[1].split("## ", 1)[0]
    dst_text = dst.joinpath("SKILL.md").read_text()
    dst_section = dst_text.split("## Usage patterns", 1)[1].split("## ", 1)[0]
    assert "\n\n\n" not in src_section
    assert "existing-pattern -->\n\n**Custom planner plugin" in dst_section
    assert "same paragraph.\n\n## Changelog" in dst_text
