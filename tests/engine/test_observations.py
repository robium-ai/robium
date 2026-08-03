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


MULTILINE_QUOTE = """## multi-line quote example <!-- id: obs-ros2-999 -->
status: ready
proof: 1
signal: better-method
sources: [ros2/examples@ab12cd3]
target: ros2#example (add) — multi-line quote test
evidence: official repo, consistent with docs (direct fetch 2026-08-01)
origin: external
source: ros2/examples@ab12cd3 path/to/file.py#L1-L3
quote: arguments=[
  '/world/', world,
  '/model/', robot_name,
  ]

## composition uses NodeOptions <!-- id: obs-ros2-001 -->
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


def test_multiline_quote_captured_across_continuation_lines(tmp_path):
    entries = obs.parse_file(_write(tmp_path, "ros2.md", MULTILINE_QUOTE))
    assert entries[0]["fields"]["quote"] == (
        "arguments=[\n'/world/', world,\n'/model/', robot_name,\n]"
    )
    # exercised via the 2-space indented continuation lines above; the ']'
    # line is indented too (mirrors real-repo formatting), so it stays part
    # of the same field instead of closing it early.


def test_single_line_quote_unaffected_by_continuation_support(tmp_path):
    entries = obs.parse_file(_write(tmp_path, "ros2.md", MULTILINE_QUOTE))
    assert entries[1]["fields"]["quote"] == "rclcpp::NodeOptions options;"


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
