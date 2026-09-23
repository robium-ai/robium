from pathlib import Path

import placement

REPO = Path(__file__).resolve().parents[2]

FOO = """---
name: foo
description: >
  Costmap tuning and obstacle inflation for mobile robot navigation.
---
## Key directives
- Always add the inflation layer or the robot hugs obstacles. <!-- id: inflation-layer -->
"""

BAR = """---
name: bar
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
    assert out == {"skills": [], "anchors": []}


def test_analyze_runs_on_live_catalog():
    """Smoke test only: analyze scores frontmatter descriptions, so which skill
    wins a given query is a property of the live catalog, not of this module."""
    out = placement.analyze("costmap inflation robot hugs obstacles",
                            str(REPO / "skills"))
    names = [name for name, _ in out["skills"]]
    scores = [score for _, score in out["skills"]]
    assert names and all(s > 0 for s in scores)
    assert scores == sorted(scores, reverse=True)
    assert all((REPO / "skills" / name).is_dir() for name in names)
