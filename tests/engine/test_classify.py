import classify


def test_strong_corrections_detected():
    for t in ["no, use foxglove not rviz here",
              "don't touch the launch file",
              "that's wrong, the QoS must be BEST_EFFORT",
              "I told you to keep it in the container",
              "stop. revert that",
              "why did you skip the smoke test"]:
        c = classify.classify_prompt(t)
        assert c and c["type"] == "user-correction", t
        assert c["confidence"] >= 0.8, t


def test_weak_corrections_lower_confidence():
    c = classify.classify_prompt("actually let's mount the workspace instead")
    assert c and c["type"] == "user-correction"
    assert 0.5 <= c["confidence"] < 0.8


def test_remember_is_explicit():
    c = classify.classify_prompt("remember: always source install/setup.bash first")
    assert c and c["type"] == "remember" and c["confidence"] >= 0.9


def test_guardrails_detected():
    c = classify.classify_prompt("only change the params file, nothing else unless I say so")
    assert c and c["type"] == "guardrail"


def test_positive_feedback_detected():
    c = classify.classify_prompt("perfect, that fixed the tf tree")
    assert c and c["type"] == "positive"


def test_false_positives_filtered():
    for t in ["no problem, take your time",
              "can you check why the node dies?",
              "don't we need a QoS override here?",   # question → not a correction
              "please build the workspace"]:
        assert classify.classify_prompt(t) is None, t


def test_long_prompts_penalized():
    long_text = "no, " + "context " * 60  # >300 chars
    c = classify.classify_prompt(long_text)
    assert c is None or c["confidence"] < 0.8


def test_error_result_detection():
    assert classify.is_error_result("colcon build", "stderr: CMake Error at CMakeLists.txt")
    assert classify.is_error_result("ros2 launch nav2_bringup tb3.launch.py",
                                    "[ERROR] [controller_server]: Costmap layer error")
    assert classify.is_error_result("python3 x.py", "Traceback (most recent call last):\n  ...")
    assert not classify.is_error_result("ls -la", "total 8\ndrwxr-xr-x")
    assert not classify.is_error_result("grep -r error docs/", "docs/a.md: no error handling yet")


def test_error_signature_stable_across_noise():
    s1 = classify.error_signature("colcon build --packages-select nav2_bringup",
                                  "CMake Error at /home/a/ws/CMakeLists.txt:14")
    s2 = classify.error_signature("colcon build --packages-select nav2_bringup",
                                  "CMake Error at /home/b/other/CMakeLists.txt:99")
    assert s1 == s2


def test_readonly_command_failures_flagged():
    # readonly heads (cat, find) flag on narrow failure patterns
    assert classify.is_error_result("cat config/params.yaml",
                                    "cat: config/params.yaml: No such file or directory")
    assert classify.is_error_result("find /workspace -name '*.py'",
                                    "find: '/workspace': No such file or directory")
    # but normal content from readonly commands stays unflagged
    assert not classify.is_error_result("ls -la", "total 8\ndrwxr-xr-x")
    assert not classify.is_error_result("grep -r error docs/", "docs/a.md: no error handling yet")


def test_pytest_and_compiler_errors_flagged():
    # pytest: FAILURES header
    assert classify.is_error_result("pytest tests/", "=== FAILURES ===\ntest_foo.py:5: AssertionError")
    # pytest: error line (E   assert ...)
    assert classify.is_error_result("pytest tests/", "E   assert result == expected")
    # compiler: line:col: error: message
    assert classify.is_error_result("gcc foo.cpp", "foo.cpp:10:5: error: 'x' was not declared")
    assert classify.is_error_result("clang++ main.cpp", "main.cpp:42:3: fatal error: expected ';'")


def test_dismissive_phrases_not_corrections():
    # "no worries" at start is dismissive, not a correction
    assert classify.classify_prompt("no worries, take your time") is None
    # "never mind" at start is dismissive, not a correction
    assert classify.classify_prompt("never mind, keep going as is") is None


def test_midtext_fp_phrase_does_not_suppress():
    # a real correction mentioning "no problem" mid-text should not be suppressed
    c = classify.classify_prompt("that's wrong — no problem with redoing the container though")
    assert c and c["type"] == "user-correction"


def test_is_remember_helper():
    # true remember patterns: colon or comma after remember (case-insensitive)
    assert classify.is_remember("remember: check the costmap layer") is True
    assert classify.is_remember("remember, always source setup.bash") is True
    assert classify.is_remember("REMEMBER: use the humble image") is True
    assert classify.is_remember("  Remember:  leading space and caps") is True
    # false remember patterns: no colon/comma after remember
    assert classify.is_remember("remember use uv not pip") is False
    assert classify.is_remember("remembering the demo") is False
    assert classify.is_remember("remind me to check") is False
    # edge cases
    assert classify.is_remember("") is False
    assert classify.is_remember(None) is False


def test_git_read_commands_not_flagged():
    """Read-only git commands (diff, log, show) should not flag on benign error text in output."""
    # git diff with context line containing " error: connection refused"
    assert not classify.is_error_result(
        "git diff HEAD~1 -- app.log",
        "diff --git a/app.log b/app.log\n...\n- error: connection refused\n+\n..."
    )
    # git log with indented commit-body line containing "error: previously ..."
    assert not classify.is_error_result(
        "git log -3",
        "commit abc123def456\n  Author: ...\n    error: previously unknown issue"
    )
    # git show with error word in diff context
    assert not classify.is_error_result(
        "git show HEAD:config.py",
        "# error handling code\nif error:\n    handle()"
    )


def test_git_write_failures_flagged():
    """Write-oriented git commands (commit, push, merge, rebase, cherry-pick) should flag errors."""
    # git push with explicit error message
    assert classify.is_error_result(
        "git push origin main",
        "error: failed to push some refs to 'origin'"
    )
    # git merge with conflict error
    assert classify.is_error_result(
        "git merge feature-branch",
        "error: Your local changes to 'file.py' would be overwritten by merge"
    )
    # git rebase error
    assert classify.is_error_result(
        "git rebase main",
        "error: could not apply abc123..."
    )


def test_git_readonly_narrow_failure():
    """Read-only git commands flag on narrow failure patterns (fatal, no such file, etc)."""
    # git log with fatal: which is a narrow git failure
    assert classify.is_error_result(
        "git log --oneline -- missing/path",
        "fatal: ambiguous argument 'missing/path': unknown revision or path not in the working tree"
    )
    # git show with no such file
    assert classify.is_error_result(
        "git show HEAD:nonexistent.txt",
        "fatal: path 'nonexistent.txt' does not exist in 'HEAD'"
    )
    # git diff with permission denied
    assert classify.is_error_result(
        "git diff /etc/shadow",
        "error: /etc/shadow: Permission denied"
    )


def test_nongit_readonly_fatal_content_not_flagged():
    """Non-git readonly commands should NOT flag on "fatal:" in their content (only narrow failures)."""
    # cat with "fatal:" in file content (successful cat)
    assert not classify.is_error_result(
        "cat build.log",
        "fatal: could not resolve dependency"
    )
    # tail with "fatal:" in log content (successful tail)
    assert not classify.is_error_result(
        "tail -50 app.log",
        "fatal: connection lost"
    )
    # grep searching for "fatal" (successful grep)
    assert not classify.is_error_result(
        "grep -r fatal docs/",
        "docs/errors.md: fatal: unknown error code"
    )
    # But "no such file" still flags for readonly commands
    assert classify.is_error_result(
        "cat missing.txt",
        "cat: missing.txt: No such file or directory"
    )
