import os
import subprocess
import textwrap

import pytest
import yaml

import run_variants as rv

# --- synthetic two-skill catalog (Task-4-of-2b fixture style: see
# test_trigger_evals.py's FOO/BAR) -----------------------------------------
#
# The description line carries an anchor id so apply_deltas `update` ops can
# retarget it deterministically. A blank line separates it from the closing
# `---` so find_anchor_block's paragraph scan stops exactly at that one line
# (real skills never anchor their frontmatter description; this is purely a
# harness-test fixture).
NAV2 = textwrap.dedent("""\
    ---
    name: nav2
    version: 1.0.0
    description: >
      Costmap tuning and obstacle inflation techniques for mobile robot navigation with careful sensor placement guidance, wheel odometry calibration notes, and various additional tuning considerations for smooth indoor and outdoor operation. <!-- id: nav2-desc -->

    ---

    ## When to use this skill

    - Testing routing scenarios.

    ## Key directives

    - Some directive. <!-- id: kd1 -->

    ## Changelog

    - 1.0.0 (2026-07-01): initial.
    """)

OTHER = textwrap.dedent("""\
    ---
    name: other
    version: 1.0.0
    description: >
      Camera calibration and image pipelines for perception stacks.
    ---

    ## Changelog

    - 1.0.0 (2026-07-01): initial.
    """)

EVALS = textwrap.dedent("""\
    triggers:
      positive:
        - phrase: robot hugs obstacles near walls costmap inflation
      negative:
        - phrase: calibrate the camera intrinsics pipeline
          expect: other
    tasks: []
    """)


def mk_catalog(tmp_path):
    for name, text in (("nav2", NAV2), ("other", OTHER)):
        d = tmp_path / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(text)
    (tmp_path / "skills" / "nav2" / "evals.yaml").write_text(EVALS)
    return str(tmp_path / "skills")


def write_deltas(tmp_path, filename, content_line):
    p = tmp_path / filename
    p.write_text(yaml.safe_dump({
        "date": "2026-08-05",
        "deltas": [{
            "skill": "nav2",
            "op": "update",
            "anchor": "nav2-desc",
            "content": f"  {content_line} <!-- id: nav2-desc -->\n",
            "reason": "obs-nav2-003",
        }],
    }))
    return str(p)


def variant_a_deltas(tmp_path):
    # Keeps trigger keywords (costmap, inflation, robot) — shorter than the
    # baseline description too, to exercise the tokens tie-break.
    return write_deltas(tmp_path, "a.yaml",
                        "Costmap obstacle inflation for robot navigation.")


def variant_b_deltas(tmp_path):
    # Drops every trigger keyword.
    return write_deltas(tmp_path, "b.yaml",
                        "General purpose helper scripts and diagnostic utilities "
                        "for miscellaneous engineering tasks.")


def refused_deltas(tmp_path):
    # Content omits the anchor id -> apply_deltas refuses (anchor-mismatch).
    p = tmp_path / "refused.yaml"
    p.write_text(yaml.safe_dump({
        "date": "2026-08-05",
        "deltas": [{
            "skill": "nav2",
            "op": "update",
            "anchor": "nav2-desc",
            "content": "  This content forgot to keep the anchor marker.\n",
            "reason": "obs-nav2-003",
        }],
    }))
    return str(p)


def zero_applied_deltas(tmp_path):
    # Targets a nonexistent anchor -> noop, nothing refused, nothing applied.
    p = tmp_path / "zero.yaml"
    p.write_text(yaml.safe_dump({
        "date": "2026-08-05",
        "deltas": [{
            "skill": "nav2",
            "op": "update",
            "anchor": "does-not-exist",
            "content": "  Doesn't matter. <!-- id: does-not-exist -->\n",
            "reason": "obs-nav2-003",
        }],
    }))
    return str(p)


# --- build_variant -----------------------------------------------------

def test_build_variant_produces_applied_copy(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    out = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    assert out == os.path.join(workdir, "A", "skills")
    text = (tmp_path / "work" / "A" / "skills" / "nav2" / "SKILL.md").read_text()
    assert "Costmap obstacle inflation for robot navigation" in text
    assert "version: 1.1.0" in text
    # baseline catalog untouched
    assert "Costmap tuning and obstacle inflation techniques for mobile robot navigation" in (
        tmp_path / "skills" / "nav2" / "SKILL.md").read_text()


def test_build_variant_reused_workdir_succeeds_on_second_call(tmp_path):
    """Regression: build_variant used to rmtree only the skills/ subdir,
    leaving the stale archive/ dir behind from a prior build -- so
    apply_deltas' archive-slot check refused the second build and a reused
    --workdir made every variant "build failed" (the Task 7 pilot hit this
    live for the --archive-losers rerun). Removing the ENTIRE
    <workdir>/<name> dir before building must make consecutive builds on
    the same workdir/name succeed."""
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    out1 = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    text1 = (tmp_path / "work" / "A" / "skills" / "nav2" / "SKILL.md").read_text()
    assert "version: 1.1.0" in text1

    # Second build_variant call on the SAME workdir/name must succeed, not
    # raise VariantBuildError from apply_deltas' archive-slot refusal.
    out2 = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    assert out2 == out1
    text2 = (tmp_path / "work" / "A" / "skills" / "nav2" / "SKILL.md").read_text()
    assert "version: 1.1.0" in text2


def test_build_variant_raises_on_refusal(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    with pytest.raises(rv.VariantBuildError):
        rv.build_variant("bad", refused_deltas(tmp_path), skills, workdir)
    # No workdir entry must survive a refused build -- archive_losers walks
    # every non-winner subdirectory of the workdir and would otherwise
    # archive this broken candidate as if it were a scored loser.
    assert not (tmp_path / "work" / "bad").exists()


def test_build_variant_raises_on_zero_applied_ops(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    with pytest.raises(rv.VariantBuildError):
        rv.build_variant("noop", zero_applied_deltas(tmp_path), skills, workdir)
    assert not (tmp_path / "work" / "noop").exists()


def test_cli_cleans_automatically_created_workdir(tmp_path, monkeypatch):
    skills = mk_catalog(tmp_path)
    spec = tmp_path / "spec.yaml"
    spec.write_text(yaml.safe_dump({
        "skill": "nav2",
        "variants": [{"name": "A", "deltas": variant_a_deltas(tmp_path)}],
    }))
    owned = tmp_path / "owned-work"

    def fake_mkdtemp(prefix):
        owned.mkdir()
        return str(owned)

    monkeypatch.setattr(rv.tempfile, "mkdtemp", fake_mkdtemp)
    rc = rv.main([str(spec), "--no-llm", "--skills-dir", skills])
    assert rc == 0
    assert not owned.exists()


def test_cli_preserves_explicit_workdir(tmp_path):
    skills = mk_catalog(tmp_path)
    spec = tmp_path / "spec.yaml"
    spec.write_text(yaml.safe_dump({
        "skill": "nav2",
        "variants": [{"name": "A", "deltas": variant_a_deltas(tmp_path)}],
    }))
    explicit = tmp_path / "explicit-work"
    rc = rv.main([
        str(spec), "--no-llm", "--skills-dir", skills,
        "--workdir", str(explicit),
    ])
    assert rc == 0
    assert (explicit / "A" / "skills" / "nav2" / "SKILL.md").exists()


def test_cli_cleans_automatic_workdir_when_run_raises(tmp_path, monkeypatch):
    spec = tmp_path / "spec.yaml"
    spec.write_text(yaml.safe_dump({"skill": "nav2", "variants": []}))
    owned = tmp_path / "owned-work"

    def fake_mkdtemp(prefix):
        owned.mkdir()
        return str(owned)

    monkeypatch.setattr(rv.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(rv, "_run_main", lambda *args: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        rv.main([str(spec), "--no-llm"])
    assert not owned.exists()


# --- score_variant -------------------------------------------------------

def test_score_variant_a_beats_b_on_triggers(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    a_dir = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    b_dir = rv.build_variant("B", variant_b_deltas(tmp_path), skills, workdir)

    score_a = rv.score_variant("A", "nav2", a_dir, skills, no_llm=True)
    score_b = rv.score_variant("B", "nav2", b_dir, skills, no_llm=True)

    assert score_a["triggers"]["passed"] >= score_b["triggers"]["passed"]
    assert score_a["triggers"]["failed"] == 0
    assert score_b["triggers"]["failed"] >= 1
    assert score_a["tasks"] is None  # with_tasks off by default
    assert score_b["flips"] >= 1  # B regresses the positive case vs baseline
    assert score_a["flips"] == 0


def test_score_variant_tokens_reflect_file_size(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    a_dir = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    score_a = rv.score_variant("A", "nav2", a_dir, skills, no_llm=True)
    text = (tmp_path / "work" / "A" / "skills" / "nav2" / "SKILL.md").read_text()
    assert score_a["tokens"] == len(text) // 4


# --- rank ------------------------------------------------------------------

def test_rank_orders_a_first_baseline_beats_b_via_tokens(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    a_dir = rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    b_dir = rv.build_variant("B", variant_b_deltas(tmp_path), skills, workdir)

    baseline_score = rv.score_variant("baseline", "nav2", skills, skills, no_llm=True)
    score_a = rv.score_variant("A", "nav2", a_dir, skills, no_llm=True)
    score_b = rv.score_variant("B", "nav2", b_dir, skills, no_llm=True)

    # baseline and A both pass every trigger case (tie) -> tokens decides;
    # A's description is shorter, so A must win the tie.
    assert score_a["tokens"] < baseline_score["tokens"]

    ranked = rv.rank([baseline_score, score_a, score_b])
    assert [s["name"] for s in ranked] == ["A", "baseline", "B"]


def test_rank_treats_none_tasks_as_equal(tmp_path):
    # Two scores identical except tasks: one None, one a real dict -- the
    # None side must not crash the comparator and falls through to tokens.
    s1 = {"name": "x", "triggers": {"passed": 2, "failed": 0, "skipped": False},
          "flips": 0, "tasks": None, "tokens": 50}
    s2 = {"name": "y", "triggers": {"passed": 2, "failed": 0, "skipped": False},
          "flips": 0, "tasks": {"passed": 1, "failed": 0, "skipped": 0}, "tokens": 40}
    ranked = rv.rank([s1, s2])
    assert {r["name"] for r in ranked} == {"x", "y"}  # doesn't raise, both present


# --- archive_losers ----------------------------------------------------

def test_archive_losers_layout_and_winner_untouched(tmp_path):
    skills = mk_catalog(tmp_path)
    workdir = str(tmp_path / "work")
    rv.build_variant("A", variant_a_deltas(tmp_path), skills, workdir)
    rv.build_variant("B", variant_b_deltas(tmp_path), skills, workdir)
    # scores.md is written by the CLI flow normally; stage it manually here
    # to test archive_losers as a standalone unit.
    (tmp_path / "work" / "A" / "scores.md").write_text("# scores: A\n")
    (tmp_path / "work" / "B" / "scores.md").write_text("# scores: B\n")

    archive_dir = str(tmp_path / "archive")
    copied = rv.archive_losers("nav2", "2026-08-05", "A", workdir, archive_dir)

    assert copied == ["B"]
    loser_dir = tmp_path / "archive" / "nav2" / "variants" / "2026-08-05" / "B"
    assert (loser_dir / "skill" / "SKILL.md").exists()
    assert (loser_dir / "deltas.yaml").exists()
    assert (loser_dir / "scores.md").exists()
    # winner never archived
    winner_dir = tmp_path / "archive" / "nav2" / "variants" / "2026-08-05" / "A"
    assert not winner_dir.exists()


# --- blind_judge -----------------------------------------------------------

def test_blind_judge_returns_none_on_subprocess_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("claude binary missing")
    monkeypatch.setattr(subprocess, "run", boom)
    result = rv.blind_judge("some finding", {"A": "text a", "B": "text b"})
    assert result is None


def test_blind_judge_returns_none_on_timeout(monkeypatch):
    def boom(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=45)
    monkeypatch.setattr(subprocess, "run", boom)
    result = rv.blind_judge("some finding", {"A": "text a", "B": "text b"})
    assert result is None


def test_blind_judge_returns_none_on_nonzero_exit(monkeypatch):
    class FakeProc:
        returncode = 1
        stdout = "A"
        stderr = "error"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    result = rv.blind_judge("some finding", {"A": "text a", "B": "text b"})
    assert result is None


def test_blind_judge_returns_none_on_unparseable_reply(monkeypatch):
    class FakeProc:
        returncode = 0
        stdout = "  ...   \n"
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    result = rv.blind_judge("some finding", {"A": "text a", "B": "text b"})
    assert result is None


def test_blind_judge_picks_a_labeled_candidate(monkeypatch):
    class FakeProc:
        returncode = 0
        stdout = ""
        stderr = ""

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["prompt"] = cmd[-1]
        proc = FakeProc()
        proc.stdout = "B"  # arbitrary single-letter reply
        return proc

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = rv.blind_judge("finding text", {"A": "text a", "B": "text b"})
    assert result is not None
    assert result["pick"] in {"A", "B"}
    assert set(result["mapping"].values()) == {"A", "B"}
    assert "finding text" in captured["prompt"]


def test_blind_judge_rejects_prose_reply_with_embedded_letter(monkeypatch):
    """Regression: a reply that merely CONTAINS a letter (because a sentence
    starts with a capitalized word) must never be treated as a pick. Old
    code took re.search(r"[A-Za-z]", reply) — the FIRST alphabetic char
    anywhere — so "Candidate B is the best integration." parsed as "C" (the
    first letter of "Candidate"), a fabricated, misattributed pick even
    though the prose actually names B."""
    monkeypatch.setattr(rv.random, "shuffle", lambda seq: None)  # keep label order stable

    class FakeProc:
        returncode = 0
        stdout = "Candidate B is the best integration."
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    result = rv.blind_judge("finding text", {"cand1": "t1", "cand2": "t2", "cand3": "t3"})
    assert result is None


@pytest.mark.parametrize("reply,expected_label", [
    ("B", "B"),
    (" b.", "B"),
    ("**B**", "B"),
    ("b\n", "B"),
    ("B!", "B"),
])
def test_blind_judge_parses_strict_single_letter_replies(monkeypatch, reply, expected_label):
    """A reply that IS exactly one letter (after stripping whitespace,
    markdown emphasis, and one trailing sentence punctuation mark) parses,
    regardless of case, surrounding bold markers, or a trailing '.'/'!'."""
    monkeypatch.setattr(rv.random, "shuffle", lambda seq: None)

    class FakeProc:
        returncode = 0
        stdout = reply
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())
    result = rv.blind_judge("finding text", {"A": "text a", "B": "text b"})
    assert result is not None
    assert result["label"] == expected_label
    assert result["pick"] == "B"


# --- CLI ---------------------------------------------------------------

def write_spec(tmp_path, skills):
    spec = {
        "skill": "nav2",
        "observation": "obs-nav2-003",
        "baseline": {},
        "variants": [
            {"name": "A", "deltas": variant_a_deltas(tmp_path)},
            {"name": "B", "deltas": variant_b_deltas(tmp_path)},
        ],
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec))
    return str(p)


def test_cli_prints_judge_evidence_line_when_judge_ran(tmp_path, capsys, monkeypatch):
    """When the content judge actually ran and picked a candidate, the CLI
    must print an evidence line naming the pick, its label, and the raw
    reply — not just the skip line (which only fires on failure)."""
    skills = mk_catalog(tmp_path)
    spec_path = write_spec(tmp_path, skills)
    monkeypatch.setattr(rv.random, "shuffle", lambda seq: None)

    class FakeProc:
        returncode = 0
        stdout = "A"
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc())

    rc = rv.main([spec_path, "--skills-dir", skills, "--workdir", str(tmp_path / "work")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "content judge: picked" in out
    assert 'raw reply: "A"' in out
    assert "content judge: skipped" not in out


def test_cli_table_has_row_per_variant_including_baseline(tmp_path, capsys):
    skills = mk_catalog(tmp_path)
    spec_path = write_spec(tmp_path, skills)
    rc = rv.main([spec_path, "--no-llm", "--skills-dir", skills,
                 "--workdir", str(tmp_path / "work")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "baseline" in out
    assert "| A " in out or "| A |" in out
    assert "| B " in out or "| B |" in out
    assert "recommendation:" in out
    assert "engine ranks; the human picks by merging" in out


def test_cli_exit_zero_even_with_refused_variant(tmp_path, capsys):
    skills = mk_catalog(tmp_path)
    spec = {
        "skill": "nav2",
        "observation": "obs-nav2-003",
        "baseline": {},
        "variants": [
            {"name": "bad", "deltas": refused_deltas(tmp_path)},
        ],
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec))
    rc = rv.main([str(p), "--no-llm", "--skills-dir", skills,
                 "--workdir", str(tmp_path / "work")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "bad" in out
    assert "build failed" in out.lower()


def test_cli_archive_losers_flow(tmp_path, capsys):
    skills = mk_catalog(tmp_path)
    spec_path = write_spec(tmp_path, skills)
    workdir = str(tmp_path / "work")
    rc = rv.main([spec_path, "--no-llm", "--skills-dir", skills,
                 "--workdir", workdir, "--archive-losers", "--winner", "A",
                 "--date", "2026-08-05", "--archive-dir", str(tmp_path / "archive")])
    assert rc == 0
    loser_dir = tmp_path / "archive" / "nav2" / "variants" / "2026-08-05" / "B"
    assert (loser_dir / "skill" / "SKILL.md").exists()
    winner_dir = tmp_path / "archive" / "nav2" / "variants" / "2026-08-05" / "A"
    assert not winner_dir.exists()


def test_cli_archive_losers_excludes_build_failed_variant(tmp_path, capsys):
    # Regression test (Task 4 review, Important finding): a variant whose
    # deltas file is refused must NOT show up under the variants archive
    # at all -- not as a "loser" with a skill dir/deltas but no scores.md,
    # and not under its own name either. Only variants that actually built
    # and scored may appear there.
    skills = mk_catalog(tmp_path)
    spec = {
        "skill": "nav2",
        "observation": "obs-nav2-003",
        "baseline": {},
        "variants": [
            {"name": "A", "deltas": variant_a_deltas(tmp_path)},
            {"name": "bad", "deltas": refused_deltas(tmp_path)},
        ],
    }
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec))
    workdir = str(tmp_path / "work")
    archive_dir = str(tmp_path / "archive")

    # baseline wins (arbitrary choice here) so both A and bad are "losers"
    # from archive_losers's point of view -- bad must still never appear.
    rc = rv.main([str(p), "--no-llm", "--skills-dir", skills, "--workdir", workdir,
                 "--archive-losers", "--winner", "baseline", "--date", "2026-08-05",
                 "--archive-dir", archive_dir])
    out = capsys.readouterr().out

    assert rc == 0
    assert "bad" in out
    assert "build failed" in out.lower()

    variants_root = tmp_path / "archive" / "nav2" / "variants" / "2026-08-05"
    archived_names = {p.name for p in variants_root.iterdir()} if variants_root.exists() else set()
    assert archived_names == {"A"}
    assert "bad" not in archived_names
    assert not (variants_root / "bad").exists()
    # no leftover workdir trace either
    assert not (tmp_path / "work" / "bad").exists()
