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


def test_render_ellipsis_on_truncation(tmp_path):
    entries = recall.load_observations(_setup(tmp_path))
    hits = recall.match("robot hugs obstacles costmap inflation",
                        [e for e in entries if recall.eligible(e)])
    truncated = recall.render(hits, budget_chars=80)
    assert truncated.endswith("…")
    full = recall.render(hits)
    assert not full.endswith("…")


def test_user_tier_dir_read(tmp_path):
    d = tmp_path / ".robium" / "observations"
    d.mkdir(parents=True)
    (d / "nav2.md").write_text(OBS)
    assert len(recall.load_observations(str(tmp_path))) == 3


def test_malformed_and_binary_files_skipped(tmp_path):
    d = tmp_path / "learnings" / "observations"
    d.mkdir(parents=True)
    # Write one valid file
    (d / "nav2.md").write_text(OBS)
    # Write one file with invalid UTF-8 bytes
    (d / "broken.md").write_bytes(b"## bad \xff\xfe\x00\n")
    # load_observations should return valid entries without raising
    entries = recall.load_observations(str(tmp_path))
    assert len(entries) == 3
    assert all(e["id"] for e in entries)
