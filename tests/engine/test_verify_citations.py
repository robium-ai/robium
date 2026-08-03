import subprocess
import verify_citations as vc


def _mk_repo(tmp_path):
    repo = tmp_path / "repos" / "fixrepo"
    repo.mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "node.py").write_text(
        "import rclpy\n\n\ndef main():\n"
        "    node = rclpy.create_node('demo')\n"
        "    pub = node.create_publisher(String, 'topic', 10)\n"
    )
    env_git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(env_git + ["add", "-A"], check=True)
    subprocess.run(env_git + ["commit", "-qm", "init"], check=True)
    sha = subprocess.run(env_git + ["rev-parse", "--short=7", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return str(tmp_path / "repos"), sha


def _entry(sha, quote="pub = node.create_publisher(String, 'topic', 10)",
           lines="#L5-L6"):
    return {"id": "obs-ros2-001", "title": "t", "line": 1, "fields": {
        "origin": "external",
        "source": f"acme/fixrepo@{sha} src/node.py{lines}",
        "quote": quote,
    }}


def test_valid_citation_passes(tmp_path):
    root, sha = _mk_repo(tmp_path)
    assert vc.verify_entry(_entry(sha), root) is None


def test_reindented_quote_still_passes(tmp_path):
    root, sha = _mk_repo(tmp_path)
    e = _entry(sha, quote="pub   = node.create_publisher(String, 'topic', 10)")
    assert vc.verify_entry(e, root) is None


def test_wrong_quote_fails(tmp_path):
    root, sha = _mk_repo(tmp_path)
    err = vc.verify_entry(_entry(sha, quote="create_subscription(String, 'topic')"), root)
    assert err and "quote not found" in err


def test_wrong_line_range_fails(tmp_path):
    root, sha = _mk_repo(tmp_path)
    err = vc.verify_entry(_entry(sha, lines="#L1-L2"), root)
    assert err and "quote not found" in err


def test_missing_clone_fails(tmp_path):
    err = vc.verify_entry(_entry("ab12cd3"), str(tmp_path / "empty"))
    assert err and "clone not found" in err


def test_non_external_entries_skipped(tmp_path):
    assert vc.verify_entry({"id": "x", "fields": {"status": "ready"}}, "/nowhere") is None


def test_multiline_quote_verifies_end_to_end(tmp_path):
    from observations import parse_file

    root, sha = _mk_repo(tmp_path)
    md = tmp_path / "ros2.md"
    md.write_text(
        "## multi-line quote spans two cited lines <!-- id: obs-ros2-001 -->\n"
        "status: ready\n"
        "proof: 1\n"
        "signal: better-method\n"
        f"sources: [acme/fixrepo@{sha}]\n"
        "target: ros2#example (add) — multi-line quote\n"
        "evidence: official repo, consistent with docs\n"
        "origin: external\n"
        f"source: acme/fixrepo@{sha} src/node.py#L4-L5\n"
        "quote: def main():\n"
        "  node = rclpy.create_node('demo')\n"
    )
    entries = parse_file(str(md))
    assert entries[0]["fields"]["quote"] == (
        "def main():\nnode = rclpy.create_node('demo')"
    )
    assert vc.verify_entry(entries[0], root) is None
