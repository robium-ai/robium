"""Regex signal classifiers for capture (spec §5; taxonomy from claude-reflect).

No LLM. Confidence composes from pattern strength plus length heuristics
(<80 chars +0.05, >300 chars −0.15). Threshold for writing a flag: ≥0.55.
"""
import hashlib
import re

_STRONG = [
    re.compile(r"(?i)^\s*no[,.! ]"),
    re.compile(r"(?i)^\s*don'?t\b"),
    re.compile(r"(?i)^\s*(stop|never)\b"),
    re.compile(r"(?i)\bthat'?s (wrong|not right|incorrect)\b"),
    re.compile(r"(?i)\bi (said|meant|told you)\b"),
    re.compile(r"(?i)\buse \S+,? not \S+"),
    re.compile(r"(?i)\bshould (not|never) have\b"),
    re.compile(r"(?i)\bwhy did you\b"),
    re.compile(r"(?i)\brevert (that|this|it)\b"),
]
_STRONG_FALSE_POSITIVE = [
    re.compile(r"(?i)^\s*no (worries|problem)\b"),
    re.compile(r"(?i)^\s*never mind\b"),
]
_WEAK = [re.compile(r"(?i)^\s*(actually|wait)\b")]
_GUARD = [
    re.compile(r"(?i)\bdon'?t .{3,40} unless\b"),
    re.compile(r"(?i)\bonly (change|touch|edit|modify)\b"),
    re.compile(r"(?i)\balways \w+.{0,40}\b(first|before)\b"),
]
_REMEMBER = re.compile(r"(?i)^\s*remember[:,]")
_POSITIVE = [re.compile(r"(?i)^\s*(perfect|great|nice|excellent|that worked|works now|it works)\b")]
_FALSE_POSITIVE = [
    re.compile(r"\?\s*$"),                      # questions are tasks, not corrections
    re.compile(r"(?i)^\s*(please|can you|could you|pls|let'?s)\b"),
    re.compile(r"(?i)^\s*no problem\b"),       # anchor to start; mid-text doesn't suppress
    re.compile(r"(?i)^\s*don'?t worry\b"),     # anchor to start; mid-text doesn't suppress
]

ROBOTICS_KEYWORDS = [
    "ros2", "ros 2", "colcon", "nav2", "gazebo", "gz sim", "mujoco", "lerobot",
    "isaac", "rviz", "foxglove", "rerun", "urdf", "sdf", "moveit", "slam",
    "costmap", "dds", "teleop", "launch file", "rosbag",
]

_ERROR_MARKERS = [
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"(?i)\bcmake error\b"),
    re.compile(r"\[ERROR\]"),
    re.compile(r"(?im)^\s*error(\[|:)"),
    re.compile(r"(?i)\bcommand not found\b"),
    re.compile(r"(?i)\bno such file or directory\b"),
    re.compile(r"(?i)^fatal:", re.MULTILINE),
    re.compile(r"(?i)\bbuild failed\b|\bfailed with exit code\b"),
    re.compile(r"(?i)\bsegmentation fault\b"),
    re.compile(r"^=+ FAILURES =+$", re.MULTILINE),      # pytest: FAILURES header
    re.compile(r"^E\s{3}", re.MULTILINE),                # pytest: error line (E   assert ...)
    re.compile(r"\bAssertionError\b"),                   # pytest: assertion failures
    re.compile(r":\d+:\d+:\s*(fatal\s+)?error:"),        # compiler: foo.cpp:10:5: error: ...
]
_TOOL_HINTS = ("ros2", "colcon", "gz", "ign", "docker", "uv", "pytest", "npm",
               "cmake", "make", "python", "launch", "rosdep", "pip",
               "git commit", "git push", "git merge", "git rebase", "git cherry-pick")
_READONLY_HEADS = ("grep", "rg", "cat", "ls", "find", "head", "tail", "echo", "which")
_READONLY_PREFIXES = ("git diff", "git log", "git show", "git status", "git blame", "git grep")


def is_remember(text: str) -> bool:
    r"""Check if text starts with 'remember' followed by colon or comma (case-insensitive).

    Canonical form shared with user_prompt_submit.py to prevent definition drift.
    Pattern: ^\s*remember[:,] (with optional leading whitespace).
    """
    return bool(_REMEMBER.search(text or ""))


def classify_prompt(text: str):
    text = (text or "").strip()
    if not text:
        return None
    for pat in _FALSE_POSITIVE:
        if pat.search(text):
            return None
    if is_remember(text):
        return {"type": "remember", "confidence": 0.95}

    kind, base = None, 0.0
    if any(p.search(text) for p in _STRONG):
        # check dismissive false positives that shadow strong patterns
        if any(p.search(text) for p in _STRONG_FALSE_POSITIVE):
            return None
        kind, base = "user-correction", 0.85
    elif any(p.search(text) for p in _GUARD):
        kind, base = "guardrail", 0.8
    elif any(p.search(text) for p in _WEAK):
        kind, base = "user-correction", 0.6
    elif any(p.search(text) for p in _POSITIVE):
        kind, base = "positive", 0.6
    if kind is None:
        return None
    if len(text) < 80:
        base += 0.05
    elif len(text) > 300:
        base -= 0.15
    if base < 0.55:
        return None
    return {"type": kind, "confidence": round(min(base, 0.99), 2)}


def _narrow_failure(output: str, extra=None) -> bool:
    """Check if output matches narrow-failure patterns.

    Base patterns: no such file or directory, command not found, permission denied.
    Extra patterns (e.g. git fatal:) are checked only when explicitly provided.
    """
    patterns = [
        re.compile(r"(?i)\bno such file or directory\b"),
        re.compile(r"(?i)\bcommand not found\b"),
        re.compile(r"(?i)\bpermission denied\b"),
    ]
    if extra:
        patterns.extend(extra)
    return any(p.search(output) for p in patterns)


def is_error_result(command: str, output: str) -> bool:
    command, output = command or "", output or ""
    head = command.strip().split()[0] if command.strip() else ""

    # git uses "fatal:" for hard failures (only in git readonly branches)
    _GIT_FATAL = re.compile(r"(?im)^fatal:")

    # readonly command heads (grep, ls, etc.)
    if head in _READONLY_HEADS:
        return _narrow_failure(output)

    # readonly git prefixes (git diff, git log, git show, etc.)
    is_readonly_git = any(command.startswith(p) for p in _READONLY_PREFIXES)
    if is_readonly_git:
        return _narrow_failure(output, extra=[_GIT_FATAL])

    if not any(m.search(output) for m in _ERROR_MARKERS):
        return False
    strong = ("Traceback" in output or "CMake Error" in output.replace("error", "Error")
              or "[ERROR]" in output or re.search(r":\d+:\d+:\s*(fatal\s+)?error:", output))
    return strong or any(h in command for h in _TOOL_HINTS)


def error_signature(command: str, output: str) -> str:
    head = " ".join((command or "").strip().split()[:2])
    first_err = ""
    for m in _ERROR_MARKERS:
        hit = m.search(output or "")
        if hit:
            line = (output or "")[hit.start():].splitlines()[0]
            # normalize paths and numbers so the same failure matches across runs
            first_err = re.sub(r"(/[\w./\-]+|\d+)", "_", line)[:120]
            break
    return hashlib.sha1(f"{head}|{first_err}".encode()).hexdigest()[:12]
