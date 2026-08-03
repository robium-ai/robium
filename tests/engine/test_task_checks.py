import textwrap
import time

import run_task_checks as rtc

EVALS = textwrap.dedent("""\
    tasks:
      - name: pass-task
        command: python3 -c "import sys; print('marker-ok'); sys.exit(0)"
        pass_criteria: marker-ok
      - name: fail-regex-task
        command: python3 -c "print('nothing-here')"
        pass_criteria: marker-ok
      - name: fail-exit-task
        command: python3 -c "import sys; sys.exit(2)"
        pass_criteria: ".*"
      - name: timeout-task
        command: python3 -c "import time; time.sleep(5)"
        pass_criteria: ".*"
        timeout: 1
    """)


def _mk_skill(tmp_path, dirname="lerobot", evals=EVALS):
    d = tmp_path / "skills" / dirname
    d.mkdir(parents=True)
    (d / "evals.yaml").write_text(evals)
    return str(tmp_path / "skills")


def _find(tasks, name):
    return next(t for t in tasks if t["name"] == name)


def test_load_tasks_empty_when_evals_absent(tmp_path):
    d = tmp_path / "skills" / "empty-skill"
    d.mkdir(parents=True)
    assert rtc.load_tasks("empty-skill", str(tmp_path / "skills")) == []


def test_load_tasks_reads_entries(tmp_path):
    skills_dir = _mk_skill(tmp_path)
    tasks = rtc.load_tasks("lerobot", skills_dir)
    assert [t["name"] for t in tasks] == [
        "pass-task", "fail-regex-task", "fail-exit-task", "timeout-task",
    ]


def test_run_task_pass(tmp_path):
    skills_dir = _mk_skill(tmp_path)
    task = _find(rtc.load_tasks("lerobot", skills_dir), "pass-task")
    res = rtc.run_task(task, str(tmp_path))
    assert res["pass"] is True
    assert res["exit"] == 0
    assert res["matched"] is True


def test_run_task_fail_regex_no_match(tmp_path):
    skills_dir = _mk_skill(tmp_path)
    task = _find(rtc.load_tasks("lerobot", skills_dir), "fail-regex-task")
    res = rtc.run_task(task, str(tmp_path))
    assert res["pass"] is False
    assert res["exit"] == 0
    assert res["matched"] is False


def test_run_task_fail_nonzero_exit(tmp_path):
    skills_dir = _mk_skill(tmp_path)
    task = _find(rtc.load_tasks("lerobot", skills_dir), "fail-exit-task")
    res = rtc.run_task(task, str(tmp_path))
    assert res["pass"] is False
    assert res["exit"] == 2


def test_run_task_timeout(tmp_path):
    skills_dir = _mk_skill(tmp_path)
    task = _find(rtc.load_tasks("lerobot", skills_dir), "timeout-task")
    start = time.time()
    res = rtc.run_task(task, str(tmp_path))
    elapsed = time.time() - start
    assert elapsed < 4, f"timeout task took {elapsed}s, should abort near timeout=1"
    assert res["pass"] is False
    assert res["exit"] is None
    assert "timeout" in res["tail"].lower()


def test_run_task_dry_run_executes_nothing(tmp_path):
    sentinel = tmp_path / "sentinel.txt"
    task = {
        "name": "sentinel-task",
        "command": f"python3 -c \"open(r'{sentinel}', 'w').close()\"",
        "pass_criteria": ".*",
    }
    res = rtc.run_task(task, str(tmp_path), dry_run=True)
    assert res["pass"] is None
    assert not sentinel.exists(), "dry-run must not execute the command"


def test_cli_no_tasks_skip(tmp_path, capsys):
    d = tmp_path / "skills" / "bare"
    d.mkdir(parents=True)
    rc = rtc.main(["--skills", "bare", "--skills-dir", str(tmp_path / "skills"),
                   "--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert "SKIPPED" in out
    assert rc == 0


def test_cli_task_filter(tmp_path, capsys):
    skills_dir = _mk_skill(tmp_path)
    rc = rtc.main(["--skills", "lerobot", "--skills-dir", skills_dir,
                   "--repo-root", str(tmp_path), "--task", "pass-task"])
    out = capsys.readouterr().out
    assert "pass-task" in out
    assert "fail-exit-task" not in out
    assert rc == 0


def test_cli_exit_code_on_failure(tmp_path, capsys):
    skills_dir = _mk_skill(tmp_path)
    rc = rtc.main(["--skills", "lerobot", "--skills-dir", skills_dir,
                   "--repo-root", str(tmp_path), "--task", "fail-exit-task"])
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert rc == 1


def test_cli_all_pass_exit_zero(tmp_path, capsys):
    skills_dir = _mk_skill(tmp_path)
    rc = rtc.main(["--skills", "lerobot", "--skills-dir", skills_dir,
                   "--repo-root", str(tmp_path), "--task", "pass-task"])
    out = capsys.readouterr().out
    assert "Task checks: 1 passed, 0 failed, 0 skipped-skills" in out
    assert rc == 0


def test_cli_task_filter_miss_is_error_not_skip(tmp_path, capsys):
    # A skill that HAS tasks but --task names one that doesn't exist must be
    # a distinct, failing outcome — not the genuine "no tasks at all" skip
    # message, which would mask a CI-invocation typo as a clean pass.
    skills_dir = _mk_skill(tmp_path)
    rc = rtc.main(["--skills", "lerobot", "--skills-dir", skills_dir,
                   "--repo-root", str(tmp_path), "--task", "nonexistent-task"])
    out = capsys.readouterr().out
    assert "no task named 'nonexistent-task'" in out
    assert "SKIPPED (no tasks yet" not in out
    assert rc == 1
