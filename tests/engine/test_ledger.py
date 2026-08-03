import ledger


def test_load_missing_returns_empty(tmp_path):
    assert ledger.load(str(tmp_path)) == {}


def test_increment_creates_entry_and_appends_sources(tmp_path):
    e = ledger.increment(str(tmp_path), "costmap-inflation", "helpful",
                         "learnings/2026-07-10.md#lrn-0710-03", "2026-08-05")
    assert e["helpful"] == 1 and e["harmful"] == 0
    assert e["last_verified"] == "2026-08-05"
    e = ledger.increment(str(tmp_path), "costmap-inflation", "harmful",
                         "learnings/2026-07-24.md#lrn-0724-02", "2026-08-06")
    assert e["helpful"] == 1 and e["harmful"] == 1
    assert len(e["sources"]) == 2
    # duplicate source is not appended twice
    ledger.increment(str(tmp_path), "costmap-inflation", "harmful",
                     "learnings/2026-07-24.md#lrn-0724-02", "2026-08-06")
    data = ledger.load(str(tmp_path))
    assert len(data["costmap-inflation"]["sources"]) == 2


def test_harmful_does_not_touch_last_verified(tmp_path):
    ledger.increment(str(tmp_path), "a", "helpful", "s1", "2026-08-01")
    e = ledger.increment(str(tmp_path), "a", "harmful", "s2", "2026-08-09")
    assert e["last_verified"] == "2026-08-01"


def test_save_writes_header_comment(tmp_path):
    ledger.increment(str(tmp_path), "a", "helpful", "s1", "2026-08-01")
    text = (tmp_path / "evidence.yaml").read_text()
    assert text.startswith("# ") and "do not hand-edit" in text


def test_bad_kind_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        ledger.increment(str(tmp_path), "a", "great", "s", "2026-08-01")
