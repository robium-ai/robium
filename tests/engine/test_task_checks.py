import os
import signal
import textwrap
import time

import pytest

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
        command: python3 -c "import time; print('before-timeout', flush=True); time.sleep(5)"
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
    assert "before-timeout" in res["tail"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group regression")
def test_run_task_timeout_stops_spawned_child_process(tmp_path):
    child = tmp_path / "child.py"
    child.write_text(
        "import signal\nimport time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "time.sleep(30)\n"
    )
    pid_file = tmp_path / "child.pid"
    parent = tmp_path / "parent.py"
    parent.write_text(textwrap.dedent(f"""\
        import subprocess
        import sys
        import time

        child = subprocess.Popen(
            [sys.executable, {str(child)!r}],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        open({str(pid_file)!r}, "w").write(str(child.pid))
        time.sleep(30)
        """))
    task = {
        "name": "child-timeout",
        "command": f"python3 {parent}",
        "pass_criteria": ".*",
        "timeout": 1,
    }

    res = rtc.run_task(task, str(tmp_path))
    child_pid = int(pid_file.read_text())
    try:
        deadline = time.time() + 2
        while True:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            if time.time() >= deadline:
                pytest.fail("spawned child survived the task timeout")
            time.sleep(0.05)
    finally:
        # Prevent a leaking regression from contaminating the test host.
        try:
            os.kill(child_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    assert res["pass"] is False
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


@pytest.mark.parametrize("evals, message", [
    ("tasks: nope\n", "tasks must be a list"),
    ("tasks:\n  - name: Bad_Name\n    command: echo hi\n    pass_criteria: hi\n",
     "kebab-case"),
    ("tasks:\n  - name: okay\n    command: echo hi\n    pass_criteria: hi\n    timeout: 0\n",
     "positive integer"),
    ("tasks:\n  - name: okay\n    command: echo hi\n    pass_criteria: hi\n    app: ../private\n",
     "repo-root-relative"),
])
def test_load_tasks_rejects_invalid_schema(tmp_path, evals, message):
    skills_dir = _mk_skill(tmp_path, evals=evals)
    with pytest.raises(rtc.TaskSchemaError, match=message):
        rtc.load_tasks("lerobot", skills_dir)
