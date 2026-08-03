# Learning Engine Phase 1 — Substrate + Capture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the learning engine's substrate (anchors, evidence/evals sidecars, learnings schema v2) and its capture layer (plugin hooks incl. transcript archiver, secret scrubber, transcript miner, back-mining), per spec `docs/superpowers/specs/2026-08-01-learning-engine-design.md` §4–5, Phase 1 row of §15.

**Architecture:** Deterministic capture: five Claude Code plugin hooks (stdlib Python, regex-only, fail-open) write pointer-flags into a gitignored `.robium/` workspace and archive session transcripts before retention prunes them. An offline miner extracts rejections/repeated-errors/no-skill-fired events from archived JSONL. The skill catalog gains stable anchor IDs (HTML comments) plus per-skill `evidence.yaml`/`evals.yaml` data sidecars, enforced by validator extensions. No LLM anywhere in Phase 1.

**Tech Stack:** Python ≥3.10 stdlib only for hooks + miner (they must run on any user machine with no installs); `uv run --with pytest --with pyyaml` for the test suite; existing PEP-723 validator (pyyaml).

## Global Constraints

- Hooks and miner: **stdlib only**, `python3` ≥3.10, no third-party imports.
- Every hook entry script **fails open**: top-level `try/except: pass` then `sys.exit(0)`. A hook must never break a session, even on malformed stdin.
- Hooks are **silent by default** — no stdout except valid hook-output JSON (`hookSpecificOutput`), per spec §5 ("nag fatigue" anti-pattern).
- Hooks write **only** under `<cwd>/.robium/` — plus exactly one idempotent `.robium/` line in `.git/info/exclude` (untracked git metadata; human ruling 2026-08-01) — never to `learnings/`, never to `skills/` (spec §5, §7.3).
- All text written to the queue passes `scrub()` first (spec §12).
- Queue flags are **pointers** (session, ts, excerpt ≤400 chars), not full copies (spec §4.0).
- Anchor syntax exactly: `<!-- id: kebab-case -->` — regex `<!-- id: [a-z0-9][a-z0-9-]* -->`, unique per skill (spec §4.1). No new frontmatter fields (frontmatter stays `name`+`version`+`description`; `compatibility` only for isaac-sim).
- Validator output contract preserved: prints `FAIL: …` lines then `Checked N skills: PASS|FAIL`, exit 0/1.
- Every SKILL.md edit follows the STRICT policy mechanics: archive snapshot to `archive/<name>/<old-version>/` + build-version bump + changelog line, same commit. Sidecar-only additions (`evidence.yaml`, `evals.yaml`) do **not** bump versions (engine data, not skill content — rule stated in spec §4.2/4.3 tooling ownership).
- `skill-updater` and `skill-refiner` are **not** anchored/seeded (they retire in Phase 2 — pointless churn).
- Test command for everything in this plan: `uv run --with pytest --with pyyaml -m pytest tests/engine -v` from the repo root.
- Final check after any `skills/**` change: `uv run skills/skill-author/scripts/validate_skills.py` → `Checked 24 skills: PASS` (24 non-`_TEMPLATE` dirs; the script counts them).

**File structure created by this plan:**

```
hooks/
  hooks.json                    # plugin hook registration (${CLAUDE_PLUGIN_ROOT})
  scripts/
    robium_hooks.py             # shared lib: event IO, .robium paths, queue, excerpts
    scrub.py                    # secret scrubbing (patterns + env-value redaction)
    classify.py                 # correction/error classifiers (regex taxonomy)
    user_prompt_submit.py       # hook: correction/remember capture
    post_tool_use.py            # hook: bash-error capture + post-commit nudge
    stop_nudge.py               # hook: throttled pending-flags nudge
    session_start.py            # hook: .robium init + queue summary
    session_end.py              # hook: transcript archiver + archive pruning
scripts/engine/
  mine_transcripts.py           # offline miner over archived JSONL (Phase 2 may relocate into learning-loop skill)
tests/engine/
  conftest.py
  test_scrub.py  test_classify.py  test_robium_hooks.py
  test_hook_scripts.py  test_session_end.py
  test_validator_extensions.py  test_miner.py
skills/<name>/evals.yaml        # seeded only where learnings provide cases
learnings/README.md             # schema v2 (rewrite)
skills/skill-author/scripts/validate_skills.py   # extended (anchors + sidecars)
```

---

### Task 1: Shared hook library (`robium_hooks.py`)

**Files:**
- Create: `hooks/scripts/robium_hooks.py`
- Create: `tests/engine/conftest.py`
- Test: `tests/engine/test_robium_hooks.py`

**Interfaces:**
- Produces (used by every later task):
  - `read_event() -> dict` — parse hook JSON from stdin, `{}` on any failure
  - `robium_dir(cwd: str) -> str` — ensure `<cwd>/.robium/` + `transcripts/` exist, ensure git-exclude, return path
  - `append_flag(cwd: str, flag: dict) -> None` — append one JSON line to `<cwd>/.robium/queue.jsonl`, auto-adding `ts` (ISO-8601 UTC) and `project` (basename of cwd) if absent
  - `count_flags(cwd: str) -> int`
  - `read_flags(cwd: str) -> list[dict]`
  - `excerpt(text: str, n: int = 400) -> str`
  - `now_iso() -> str`
  - `emit_context(event_name: str, text: str) -> None` — print `{"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": text}}`

- [ ] **Step 1: Write the failing tests**

`tests/engine/conftest.py`:

```python
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hooks" / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "engine"))
sys.path.insert(0, str(REPO / "skills" / "skill-author" / "scripts"))
```

`tests/engine/test_robium_hooks.py`:

```python
import json
import subprocess
import robium_hooks as rh


def test_robium_dir_creates_workspace(tmp_path):
    d = rh.robium_dir(str(tmp_path))
    assert (tmp_path / ".robium" / "transcripts").is_dir()
    assert d == str(tmp_path / ".robium")


def test_robium_dir_adds_git_exclude(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    rh.robium_dir(str(tmp_path))
    exclude = (tmp_path / ".git" / "info" / "exclude").read_text()
    assert ".robium/" in exclude
    # idempotent — second call must not duplicate the line
    rh.robium_dir(str(tmp_path))
    assert exclude.count(".robium/") == (tmp_path / ".git" / "info" / "exclude").read_text().count(".robium/")


def test_append_and_count_flags(tmp_path):
    rh.append_flag(str(tmp_path), {"type": "error", "excerpt": "boom"})
    rh.append_flag(str(tmp_path), {"type": "user-correction", "excerpt": "no, use X"})
    assert rh.count_flags(str(tmp_path)) == 2
    flags = rh.read_flags(str(tmp_path))
    assert flags[0]["type"] == "error"
    assert "ts" in flags[0] and "project" in flags[0]


def test_read_flags_skips_corrupt_lines(tmp_path):
    rh.append_flag(str(tmp_path), {"type": "error"})
    with open(tmp_path / ".robium" / "queue.jsonl", "a") as f:
        f.write("not json\n")
    assert rh.count_flags(str(tmp_path)) == 1


def test_excerpt_truncates():
    assert rh.excerpt("x" * 1000) == "x" * 400 + "…"
    assert rh.excerpt("short") == "short"


def test_emit_context_shape(capsys):
    rh.emit_context("SessionStart", "hello")
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert out["hookSpecificOutput"]["additionalContext"] == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_robium_hooks.py -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'robium_hooks'`

- [ ] **Step 3: Implement `hooks/scripts/robium_hooks.py`**

```python
"""Shared helpers for robium capture hooks.

stdlib only. Every consumer wraps main() in try/except and exits 0 —
capture must never break a session (spec §12: fail-open).
"""
import datetime
import json
import os
import sys

QUEUE = "queue.jsonl"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_event() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def _ensure_git_exclude(cwd: str) -> None:
    info = os.path.join(cwd, ".git", "info")
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return
    os.makedirs(info, exist_ok=True)
    exclude = os.path.join(info, "exclude")
    line = ".robium/"
    try:
        existing = open(exclude, encoding="utf-8").read() if os.path.exists(exclude) else ""
    except Exception:
        existing = ""
    if line not in existing.splitlines():
        with open(exclude, "a", encoding="utf-8") as f:
            f.write(("" if existing.endswith("\n") or not existing else "\n") + line + "\n")


def robium_dir(cwd: str) -> str:
    cwd = cwd or os.getcwd()
    d = os.path.join(cwd, ".robium")
    os.makedirs(os.path.join(d, "transcripts"), exist_ok=True)
    _ensure_git_exclude(cwd)
    return d


def append_flag(cwd: str, flag: dict) -> None:
    d = robium_dir(cwd)
    flag.setdefault("ts", now_iso())
    flag.setdefault("project", os.path.basename(os.path.abspath(cwd or os.getcwd())))
    with open(os.path.join(d, QUEUE), "a", encoding="utf-8") as f:
        f.write(json.dumps(flag, ensure_ascii=False) + "\n")


def read_flags(cwd: str) -> list:
    path = os.path.join(cwd or os.getcwd(), ".robium", QUEUE)
    flags = []
    if not os.path.exists(path):
        return flags
    for line in open(path, encoding="utf-8"):
        try:
            flags.append(json.loads(line))
        except Exception:
            continue
    return flags


def count_flags(cwd: str) -> int:
    return len(read_flags(cwd))


def excerpt(text: str, n: int = 400) -> str:
    text = text or ""
    return text if len(text) <= n else text[:n] + "…"


def emit_context(event_name: str, text: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    }))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_robium_hooks.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/robium_hooks.py tests/engine/conftest.py tests/engine/test_robium_hooks.py
git commit -m "feat(engine): shared hook library — .robium workspace, queue flags, git-exclude"
```

---

### Task 2: Secret scrubber (`scrub.py`)

**Files:**
- Create: `hooks/scripts/scrub.py`
- Test: `tests/engine/test_scrub.py`

**Interfaces:**
- Produces: `scrub(text: str, env: dict | None = None) -> str` — replaces secret-shaped substrings with `[REDACTED]`; `env` defaults to `os.environ`. Used by Tasks 4, 5, 14.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_scrub.py`:

```python
from scrub import scrub


def test_scrubs_key_value_assignments():
    assert "hunter2secret" not in scrub("export API_KEY=hunter2secret && run")
    assert "[REDACTED]" in scrub("DOPPLER_TOKEN=dp.st.abc123def456")


def test_scrubs_known_token_shapes():
    for tok in ["sk-abcdefghijklmnop1234", "ghp_" + "a" * 24, "AKIA" + "A" * 16,
                "xoxb-1234567890-abcdef"]:
        assert tok not in scrub(f"using {tok} here")


def test_scrubs_bearer_and_cli_password_args():
    assert "eyJhbGciOi12345678" not in scrub("Authorization: Bearer eyJhbGciOi12345678")
    assert "s3cr3tpass" not in scrub("mysql --password=s3cr3tpass -u root")


def test_scrubs_userinfo_urls():
    out = scrub("git clone https://user:p4ssw0rd@github.com/x/y.git")
    assert "p4ssw0rd" not in out


def test_scrubs_sensitive_env_values():
    env = {"MY_SECRET_TOKEN": "topsecretvalue99", "PATH": "/usr/bin:/bin", "HOME": "/Users/x"}
    out = scrub("error: auth failed for topsecretvalue99", env=env)
    assert "topsecretvalue99" not in out
    # non-sensitive env vars are NOT redacted (PATH would destroy every log line)
    assert "/usr/bin" in scrub("looked in /usr/bin:/bin", env=env)


def test_short_env_values_ignored():
    env = {"API_KEY": "short"}  # <8 chars — too collision-prone to redact
    assert scrub("short circuit", env=env) == "short circuit"


def test_plain_text_untouched():
    s = "colcon build failed: package 'nav2_bringup' not found"
    assert scrub(s, env={}) == s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_scrub.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scrub'`

- [ ] **Step 3: Implement `hooks/scripts/scrub.py`**

```python
"""Secret scrubbing for capture flags (spec §12).

Two passes: (1) pattern-based for secret-shaped strings, (2) exact-value
redaction of sensitive-named environment variables (Doppler-injected values
land here without needing Doppler awareness). stdlib only.
"""
import os
import re

_PATTERNS = [
    # KEY=value assignments (env-style, ≥3-char upper name, ≥6-char value)
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}=(['\"]?)[^\s'\"]{6,}\1"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._\-]{12,}"),
    # well-known token prefixes
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
               r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}"
               r"|xox[bap]-[A-Za-z0-9\-]{10,}|dp\.st\.[A-Za-z0-9._\-]{8,})\b"),
    # --password foo / --token=foo style CLI args
    re.compile(r"(?i)(--?(password|passwd|token|api-?key|secret)[= ])[^\s]+"),
    # credentials embedded in URLs
    re.compile(r"://[^/\s:@]+:[^/\s@]+@"),
]

_SENSITIVE_NAME = re.compile(r"(?i)(key|token|secret|pass|cred|auth)")


def scrub(text: str, env: "dict | None" = None) -> str:
    if not text:
        return text
    for pat in _PATTERNS:
        text = pat.sub("[REDACTED]", text)
    env = os.environ if env is None else env
    for name, value in env.items():
        if len(value or "") >= 8 and _SENSITIVE_NAME.search(name):
            text = text.replace(value, "[REDACTED]")
    return text
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_scrub.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/scrub.py tests/engine/test_scrub.py
git commit -m "feat(engine): secret scrubber — pattern + sensitive-env-value redaction"
```

---

### Task 3: Signal classifiers (`classify.py`)

**Files:**
- Create: `hooks/scripts/classify.py`
- Test: `tests/engine/test_classify.py`

**Interfaces:**
- Produces:
  - `classify_prompt(text: str) -> dict | None` — returns `{"type": "user-correction"|"guardrail"|"remember"|"positive", "confidence": float}` or `None`. Types map to the CLAUDE.md capture taxonomy: user-correction → *User-corrected approach*; positive → *Worked as documented ✓*; remember/guardrail → explicit instruction.
  - `is_error_result(command: str, output: str) -> bool` — bash-result error detector, robotics/tooling scoped.
  - `error_signature(command: str, output: str) -> str` — stable dedup key (Tasks 5, 14).
  - `ROBOTICS_KEYWORDS: list[str]` (Task 14 uses it for no-skill-fired detection).

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_classify.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_classify.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classify'`

- [ ] **Step 3: Implement `hooks/scripts/classify.py`**

```python
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
    re.compile(r"(?i)\bno problem\b"),
    re.compile(r"(?i)\bdon'?t worry\b"),
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
]
_TOOL_HINTS = ("ros2", "colcon", "gz", "ign", "docker", "uv", "pytest", "npm",
               "cmake", "make", "python", "launch", "rosdep", "pip")
_READONLY_HEADS = ("grep", "rg", "cat", "ls", "find", "head", "tail", "echo", "which")


def classify_prompt(text: str):
    text = (text or "").strip()
    if not text:
        return None
    for pat in _FALSE_POSITIVE:
        if pat.search(text):
            return None
    if _REMEMBER.search(text):
        return {"type": "remember", "confidence": 0.95}

    kind, base = None, 0.0
    if any(p.search(text) for p in _STRONG):
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


def is_error_result(command: str, output: str) -> bool:
    command, output = command or "", output or ""
    head = command.strip().split()[0] if command.strip() else ""
    if head in _READONLY_HEADS:
        return False
    if not any(m.search(output) for m in _ERROR_MARKERS):
        return False
    strong = ("Traceback" in output or "CMake Error" in output.replace("error", "Error")
              or "[ERROR]" in output)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_classify.py -v`
Expected: 10 PASS. If a specific phrase test fails, tighten/loosen the single offending regex — do not weaken the false-positive filters.

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/classify.py tests/engine/test_classify.py
git commit -m "feat(engine): regex signal classifiers — corrections, guardrails, bash errors"
```

---

### Task 4: UserPromptSubmit hook (`user_prompt_submit.py`)

**Files:**
- Create: `hooks/scripts/user_prompt_submit.py`
- Test: `tests/engine/test_hook_scripts.py` (created here, extended in Tasks 5–6)

**Interfaces:**
- Consumes: `read_event/append_flag/excerpt` (Task 1), `scrub` (Task 2), `classify_prompt` (Task 3).
- Produces: queue flags `{"type", "confidence", "session", "excerpt", "ts", "project"}`. Stdin: hook JSON with `prompt`, `session_id`, `cwd`. No stdout ever (silent capture).

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_hook_scripts.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "hooks" / "scripts"


def run_hook(name, event, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        input=json.dumps(event), capture_output=True, text=True, timeout=10,
    )


def read_queue(tmp_path):
    q = tmp_path / ".robium" / "queue.jsonl"
    if not q.exists():
        return []
    return [json.loads(l) for l in q.read_text().splitlines() if l.strip()]


def test_ups_captures_correction(tmp_path):
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
          "cwd": str(tmp_path), "prompt": "no, use the humble image not jazzy"}
    r = run_hook("user_prompt_submit.py", ev)
    assert r.returncode == 0 and r.stdout.strip() == ""
    flags = read_queue(tmp_path)
    assert len(flags) == 1
    assert flags[0]["type"] == "user-correction"
    assert flags[0]["session"] == "s1"
    assert "humble" in flags[0]["excerpt"]


def test_ups_ignores_plain_task_prompt(tmp_path):
    ev = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
          "cwd": str(tmp_path), "prompt": "please add a launch file for the lidar"}
    run_hook("user_prompt_submit.py", ev)
    assert read_queue(tmp_path) == []


def test_ups_skips_long_prompt_unless_remember(tmp_path):
    long = "no, " + "x" * 600
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path), "prompt": long})
    assert read_queue(tmp_path) == []
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": "remember: " + "x" * 600})
    assert len(read_queue(tmp_path)) == 1


def test_ups_scrubs_secrets(tmp_path):
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s1", "cwd": str(tmp_path),
             "prompt": "no, the token is HF_TOKEN=hf_abcdef123456 use that"})
    flags = read_queue(tmp_path)
    assert flags and "hf_abcdef123456" not in flags[0]["excerpt"]


def test_ups_fails_open_on_garbage_stdin():
    r = subprocess.run([sys.executable, str(SCRIPTS / "user_prompt_submit.py")],
                       input="{{{not json", capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v`
Expected: FAIL with `FileNotFoundError` (script doesn't exist)

- [ ] **Step 3: Implement `hooks/scripts/user_prompt_submit.py`**

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook — flag corrections/guardrails/remember/positive signals.

Silent: writes queue flags only, never stdout (spec §5). Fail-open.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from classify import classify_prompt
    from robium_hooks import append_flag, excerpt, read_event
    from scrub import scrub

    event = read_event()
    prompt = event.get("prompt") or ""
    if prompt.startswith("[robium-recall]"):   # engine-injected content is never re-captured
        return
    is_remember = prompt.strip().lower().startswith("remember")
    if len(prompt) > 500 and not is_remember:
        return
    hit = classify_prompt(prompt)
    if not hit:
        return
    append_flag(event.get("cwd") or "", {
        "type": hit["type"],
        "confidence": hit["confidence"],
        "session": event.get("session_id", ""),
        "excerpt": scrub(excerpt(prompt)),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/user_prompt_submit.py tests/engine/test_hook_scripts.py
git commit -m "feat(engine): UserPromptSubmit capture hook — corrections to queue flags"
```

---

### Task 5: PostToolUse hook (`post_tool_use.py`)

**Files:**
- Create: `hooks/scripts/post_tool_use.py`
- Modify: `tests/engine/test_hook_scripts.py` (append tests)

**Interfaces:**
- Consumes: Task 1–3 helpers. Stdin: hook JSON with `tool_name`, `tool_input` (`{"command": …}`), `tool_response` (str or dict with `stdout`/`stderr`), `session_id`, `cwd`.
- Produces: error flags `{"type": "error", "session", "command", "signature", "excerpt"}`; on `git commit` with ≥3 pending flags, emits PostToolUse `additionalContext` nudge. Session-scoped dedup file: `.robium/.seen-<session_id>`.

- [ ] **Step 1: Append the failing tests**

Append to `tests/engine/test_hook_scripts.py`:

```python
def test_ptu_captures_bash_error(tmp_path):
    ev = {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "colcon build --packages-select nav2_bringup"},
          "tool_response": {"stdout": "", "stderr": "CMake Error at CMakeLists.txt:14"}}
    r = run_hook("post_tool_use.py", ev)
    assert r.returncode == 0
    flags = read_queue(tmp_path)
    assert len(flags) == 1 and flags[0]["type"] == "error"
    assert flags[0]["command"].startswith("colcon build")
    assert "CMake Error" in flags[0]["excerpt"]


def test_ptu_dedupes_same_error_in_session(tmp_path):
    ev = {"hook_event_name": "PostToolUse", "session_id": "s2", "cwd": str(tmp_path),
          "tool_name": "Bash",
          "tool_input": {"command": "colcon build"},
          "tool_response": "CMake Error at /a/CMakeLists.txt:14"}
    run_hook("post_tool_use.py", ev)
    run_hook("post_tool_use.py", ev)
    assert len(read_queue(tmp_path)) == 1


def test_ptu_ignores_clean_output_and_other_tools(tmp_path):
    run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
             "cwd": str(tmp_path), "tool_name": "Bash",
             "tool_input": {"command": "ls"}, "tool_response": "file.txt"})
    run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
             "cwd": str(tmp_path), "tool_name": "Read",
             "tool_input": {"file_path": "/x"}, "tool_response": "ERROR text in a file"})
    assert read_queue(tmp_path) == []


def test_ptu_commit_nudge_when_flags_pending(tmp_path):
    for i in range(3):
        run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
                 "session_id": "s2", "cwd": str(tmp_path),
                 "prompt": f"no, fix the {i} param not that one"})
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit -m 'feat: x'"},
                 "tool_response": "1 file changed"})
    out = json.loads(r.stdout)
    assert "pending learning" in out["hookSpecificOutput"]["additionalContext"]


def test_ptu_no_nudge_on_amend_or_empty_queue(tmp_path):
    r = run_hook("post_tool_use.py", {"hook_event_name": "PostToolUse", "session_id": "s2",
                 "cwd": str(tmp_path), "tool_name": "Bash",
                 "tool_input": {"command": "git commit --amend"},
                 "tool_response": "ok"})
    assert r.stdout.strip() == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v -k ptu`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Implement `hooks/scripts/post_tool_use.py`**

```python
#!/usr/bin/env python3
"""PostToolUse(Bash) hook — flag error-bearing commands; nudge after git commit.

Dedup: one flag per (command-head, error-signature) per session. Fail-open.
"""
import json
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

NUDGE_THRESHOLD = 3


def _response_text(resp) -> str:
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        return "\n".join(str(resp.get(k) or "") for k in ("stdout", "stderr", "output", "error"))
    try:
        return json.dumps(resp)
    except Exception:
        return str(resp)


def main() -> None:
    from classify import error_signature, is_error_result
    from robium_hooks import append_flag, count_flags, emit_context, excerpt, read_event, robium_dir
    from scrub import scrub

    event = read_event()
    if event.get("tool_name") != "Bash":
        return
    cwd = event.get("cwd") or ""
    command = (event.get("tool_input") or {}).get("command", "")
    output = _response_text(event.get("tool_response"))

    if "git commit" in command and "--amend" not in command:
        n = count_flags(cwd)
        if n >= NUDGE_THRESHOLD:
            emit_context("PostToolUse",
                         f"robium: {n} pending learning flag(s) in .robium/queue.jsonl — "
                         "end-of-block retro due; consider promoting them to learnings/.")
        return

    if not is_error_result(command, output):
        return

    sig = error_signature(command, output)
    seen_path = os.path.join(robium_dir(cwd), f".seen-{event.get('session_id', 'na')}")
    seen = set()
    if os.path.exists(seen_path):
        seen = set(open(seen_path, encoding="utf-8").read().split())
    if sig in seen:
        return
    with open(seen_path, "a", encoding="utf-8") as f:
        f.write(sig + "\n")

    append_flag(cwd, {
        "type": "error",
        "session": event.get("session_id", ""),
        "command": scrub(excerpt(command, 200)),
        "signature": sig,
        "excerpt": scrub(excerpt(output[-2000:], 400)),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v`
Expected: 10 PASS (5 from Task 4 + 5 new)

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/post_tool_use.py tests/engine/test_hook_scripts.py
git commit -m "feat(engine): PostToolUse capture hook — bash errors + commit nudge"
```

---

### Task 6: SessionStart + Stop hooks (`session_start.py`, `stop_nudge.py`)

**Files:**
- Create: `hooks/scripts/session_start.py`
- Create: `hooks/scripts/stop_nudge.py`
- Modify: `tests/engine/test_hook_scripts.py` (append tests)

**Interfaces:**
- Consumes: Task 1 helpers. SessionStart stdin: `{session_id, cwd, source}`. Stop stdin: `{session_id, cwd, stop_hook_active}`.
- Produces: SessionStart emits `additionalContext` queue summary (or nothing when queue empty) and initializes `.robium/`. Stop prints a plain one-line stdout nudge, throttled via `.robium/.last-nudge` (≥900 s between nudges), never when `stop_hook_active` is true.

- [ ] **Step 1: Append the failing tests**

Append to `tests/engine/test_hook_scripts.py`:

```python
def test_session_start_initializes_and_summarizes(tmp_path):
    r = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                 "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    assert r.returncode == 0
    assert (tmp_path / ".robium" / "transcripts").is_dir()
    assert r.stdout.strip() == ""  # empty queue → silent
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s3", "cwd": str(tmp_path), "prompt": "no, wrong distro"})
    r2 = run_hook("session_start.py", {"hook_event_name": "SessionStart",
                  "session_id": "s3", "cwd": str(tmp_path), "source": "startup"})
    out = json.loads(r2.stdout)
    assert "1 pending" in out["hookSpecificOutput"]["additionalContext"]


def test_stop_nudge_throttles(tmp_path):
    run_hook("user_prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
             "session_id": "s4", "cwd": str(tmp_path), "prompt": "no, wrong port"})
    r1 = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                  "cwd": str(tmp_path), "stop_hook_active": False})
    assert "pending" in r1.stdout
    r2 = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                  "cwd": str(tmp_path), "stop_hook_active": False})
    assert r2.stdout.strip() == ""  # throttled


def test_stop_nudge_respects_stop_hook_active(tmp_path):
    r = run_hook("stop_nudge.py", {"hook_event_name": "Stop", "session_id": "s4",
                 "cwd": str(tmp_path), "stop_hook_active": True})
    assert r.stdout.strip() == "" and r.returncode == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v -k "session_start or stop_nudge"`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Implement both scripts**

`hooks/scripts/session_start.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook — init .robium/ workspace; summarize pending flags."""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])


def main() -> None:
    from robium_hooks import emit_context, read_event, read_flags, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    robium_dir(cwd)
    flags = read_flags(cwd)
    if not flags:
        return
    by_type = {}
    for f in flags:
        by_type[f.get("type", "?")] = by_type.get(f.get("type", "?"), 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(by_type.items(), key=lambda x: -x[1]))
    emit_context("SessionStart",
                 f"robium learning engine: {len(flags)} pending flag(s) in "
                 f".robium/queue.jsonl ({summary}). Promote to learnings/ at the "
                 "next natural break; details: spec §5.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

`hooks/scripts/stop_nudge.py`:

```python
#!/usr/bin/env python3
"""Stop hook — throttled one-line nudge when flags are pending. Never blocks."""
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])

THROTTLE_S = 900


def main() -> None:
    from robium_hooks import count_flags, read_event, robium_dir

    event = read_event()
    if event.get("stop_hook_active"):
        return
    cwd = event.get("cwd") or ""
    n = count_flags(cwd)
    if n == 0:
        return
    marker = os.path.join(robium_dir(cwd), ".last-nudge")
    now = time.time()
    try:
        last = os.path.getmtime(marker)
    except OSError:
        last = 0.0
    if now - last < THROTTLE_S:
        return
    with open(marker, "w") as f:
        f.write(str(now))
    print(f"robium: {n} pending learning flag(s) — run a retro/promotion when convenient.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_hook_scripts.py -v`
Expected: 13 PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/session_start.py hooks/scripts/stop_nudge.py tests/engine/test_hook_scripts.py
git commit -m "feat(engine): SessionStart summary + throttled Stop nudge hooks"
```

---

### Task 7: SessionEnd transcript archiver (`session_end.py`)

**Files:**
- Create: `hooks/scripts/session_end.py`
- Test: `tests/engine/test_session_end.py`

**Interfaces:**
- Consumes: Task 1 helpers. Stdin: `{session_id, transcript_path, cwd, reason}`.
- Produces: copies the session transcript to `.robium/transcripts/<project>__<session_id>.jsonl` (overwrite = idempotent; latest wins). Prunes oldest archives when the dir exceeds `MAX_ARCHIVE_MB` (500). This is spec §4.0's retention defense — the highest-value hook of the set.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_session_end.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "hooks" / "scripts"


def run_hook(event):
    return subprocess.run([sys.executable, str(SCRIPTS / "session_end.py")],
                          input=json.dumps(event), capture_output=True, text=True, timeout=10)


def test_archives_transcript(tmp_path):
    src = tmp_path / "fake-transcript.jsonl"
    src.write_text('{"type":"user","message":{"role":"user","content":"hi"}}\n')
    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "abc123",
                  "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"})
    assert r.returncode == 0
    dest = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__abc123.jsonl"
    assert dest.exists() and dest.read_text() == src.read_text()


def test_rearchive_overwrites(tmp_path):
    src = tmp_path / "t.jsonl"
    src.write_text("v1\n")
    ev = {"hook_event_name": "SessionEnd", "session_id": "abc123",
          "cwd": str(tmp_path), "transcript_path": str(src), "reason": "exit"}
    run_hook(ev)
    src.write_text("v1\nv2\n")
    run_hook(ev)
    dest = tmp_path / ".robium" / "transcripts" / f"{tmp_path.name}__abc123.jsonl"
    assert dest.read_text() == "v1\nv2\n"


def test_missing_or_empty_transcript_is_noop(tmp_path):
    r = run_hook({"hook_event_name": "SessionEnd", "session_id": "x",
                  "cwd": str(tmp_path), "transcript_path": str(tmp_path / "nope.jsonl"),
                  "reason": "exit"})
    assert r.returncode == 0
    tdir = tmp_path / ".robium" / "transcripts"
    assert not tdir.exists() or list(tdir.iterdir()) == []


def test_prunes_oldest_over_budget(tmp_path, monkeypatch):
    import session_end
    tdir = tmp_path / ".robium" / "transcripts"
    tdir.mkdir(parents=True)
    old = tdir / "proj__old.jsonl"
    new = tdir / "proj__new.jsonl"
    old.write_bytes(b"x" * 1024)
    new.write_bytes(b"y" * 1024)
    import os, time
    os.utime(old, (time.time() - 9999, time.time() - 9999))
    monkeypatch.setattr(session_end, "MAX_ARCHIVE_MB", 0.0015)  # ~1.5KB budget
    session_end.prune_archive(str(tmp_path))
    assert not old.exists() and new.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_session_end.py -v`
Expected: FAIL (script/module missing)

- [ ] **Step 3: Implement `hooks/scripts/session_end.py`**

```python
#!/usr/bin/env python3
"""SessionEnd hook — archive the session transcript before Claude Code retention
prunes it (spec §4.0: transcripts are Tier −1, the engine's raw record)."""
import os
import shutil
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

MAX_ARCHIVE_MB = 500


def prune_archive(cwd: str) -> None:
    tdir = os.path.join(cwd, ".robium", "transcripts")
    if not os.path.isdir(tdir):
        return
    files = [os.path.join(tdir, f) for f in os.listdir(tdir) if f.endswith(".jsonl")]
    total = sum(os.path.getsize(f) for f in files)
    budget = MAX_ARCHIVE_MB * 1024 * 1024
    for f in sorted(files, key=os.path.getmtime):
        if total <= budget:
            break
        total -= os.path.getsize(f)
        os.remove(f)


def main() -> None:
    from robium_hooks import read_event, robium_dir

    event = read_event()
    cwd = event.get("cwd") or ""
    src = event.get("transcript_path") or ""
    if not (src and os.path.exists(src) and os.path.getsize(src) > 0):
        return
    d = robium_dir(cwd)
    project = os.path.basename(os.path.abspath(cwd or os.getcwd()))
    session = event.get("session_id") or os.path.splitext(os.path.basename(src))[0]
    dest = os.path.join(d, "transcripts", f"{project}__{session}.jsonl")
    shutil.copy2(src, dest)
    prune_archive(cwd)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_session_end.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/session_end.py tests/engine/test_session_end.py
git commit -m "feat(engine): SessionEnd transcript archiver with size-budget pruning"
```

---

### Task 8: Plugin hook registration + live smoke test

**Files:**
- Create: `hooks/hooks.json`

**Interfaces:**
- Consumes: all five entry scripts (Tasks 4–7).
- Produces: hooks active in every session with the robium plugin enabled. Claude Code auto-discovers a plugin's `hooks/hooks.json`; `${CLAUDE_PLUGIN_ROOT}` resolves to the installed plugin dir.

- [ ] **Step 1: Write `hooks/hooks.json`**

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/user_prompt_submit.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/post_tool_use.py\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/stop_nudge.py\"" }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session_start.py\"" }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session_end.py\"" }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Validate the JSON**

Run: `python3 -c "import json; json.load(open('hooks/hooks.json')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Full engine test suite still green**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine -v`
Expected: all PASS

- [ ] **Step 4: Live smoke test (manual — requires a human/agent-driven Claude Code session)**

1. In a Claude Code session: `/plugin marketplace add /Users/robium/repos/robium` (already added → skip) then `/plugin install robium@robium` or `/reload-plugins` if already installed.
2. Start a **new** session in any scratch git repo. Verify `.robium/transcripts/` was created and `.git/info/exclude` contains `.robium/`.
3. Type a correction-shaped prompt: `no, use humble not jazzy for this`. Then check `cat .robium/queue.jsonl` — expect one `user-correction` flag with a scrubbed excerpt.
4. Run a failing command via the agent (e.g. `colcon build` outside a workspace). Expect an `error` flag.
5. End the session (`/exit` or close). Reopen a shell: expect `.robium/transcripts/<project>__<session>.jsonl` to exist.
6. **Acceptance (spec §15 Phase 1 exit):** at least one real friction flag captured + the transcript archived, with zero session breakage or visible latency.

- [ ] **Step 5: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat(engine): register capture hooks in plugin (hooks.json)"
```

---

### Task 9: Validator extensions — anchors + sidecar schemas

**Files:**
- Modify: `skills/skill-author/scripts/validate_skills.py`
- Test: `tests/engine/test_validator_extensions.py`

**Interfaces:**
- Consumes: existing `check_skill(skill_dir) -> list[str]` structure (lines 31–74 of the current script).
- Produces (importable, used by tests and later phases):
  - `check_anchors(name: str, text: str) -> list[str]` — anchor format + per-skill uniqueness; malformed `<!-- id:` comments are errors.
  - `check_sidecars(skill_dir: Path, anchors: set[str]) -> list[str]` — schema-validate `evidence.yaml` and `evals.yaml` when present (missing files are fine).
  - `ANCHOR_RE` regex.
  - Output contract unchanged: `FAIL:` lines + `Checked N skills: PASS|FAIL`.

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_validator_extensions.py`:

```python
from pathlib import Path

import validate_skills as vs


def _mk_skill(tmp_path, body_extra="", evidence=None, evals=None):
    d = tmp_path / "nav2"
    d.mkdir()
    body = "\n".join([
        "## When to use this skill", "x",
        "## Key directives", "- posture. <!-- id: posture -->",
        "## Quick start", "y",
        "## Platform gotchas", "z",
        "## Customization", "c",
        "## References", "r",
        body_extra,
    ])
    (d / "SKILL.md").write_text(
        "---\nname: nav2\nversion: 1.0.0\ndescription: d\n---\n" + body)
    if evidence is not None:
        (d / "evidence.yaml").write_text(evidence)
    if evals is not None:
        (d / "evals.yaml").write_text(evals)
    return d


def test_valid_anchors_pass(tmp_path):
    d = _mk_skill(tmp_path, "- fact one. <!-- id: costmap-inflation -->")
    assert vs.check_skill(d) == []


def test_duplicate_anchor_fails(tmp_path):
    d = _mk_skill(tmp_path, "- a. <!-- id: posture -->")
    errs = vs.check_skill(d)
    assert any("duplicate anchor" in e for e in errs)


def test_malformed_anchor_fails(tmp_path):
    d = _mk_skill(tmp_path, "- a. <!-- id: Bad_Name -->")
    errs = vs.check_skill(d)
    assert any("malformed anchor" in e for e in errs)


def test_evidence_schema_enforced(tmp_path):
    good = "posture:\n  helpful: 2\n  harmful: 0\n  sources: [learnings/2026-07-10.md#lrn-1]\n"
    assert vs.check_skill(_mk_skill(tmp_path, evidence=good)) == []
    bad = "posture:\n  helpful: many\n"
    errs = vs.check_skill(_mk_skill((tmp_path / "b").mkdir() or tmp_path / "b", evidence=bad))
    assert any("evidence.yaml" in e for e in errs)


def test_evidence_unknown_anchor_fails(tmp_path):
    ev = "ghost-anchor:\n  helpful: 1\n  harmful: 0\n  sources: []\n"
    errs = vs.check_skill(_mk_skill(tmp_path, evidence=ev))
    assert any("unknown anchor" in e for e in errs)


def test_evals_schema_enforced(tmp_path):
    good = ("triggers:\n  positive:\n    - phrase: robot hugs walls\n"
            "      source: learnings/2026-07-10.md\n  negative:\n"
            "    - phrase: simulate lidar\n      expect: gazebo\ntasks: []\n")
    assert vs.check_skill(_mk_skill(tmp_path, evals=good)) == []
    errs = vs.check_skill(_mk_skill((tmp_path / "b2").mkdir() or tmp_path / "b2",
                                    evals="triggers: nope\n"))
    assert any("evals.yaml" in e for e in errs)


def test_missing_sidecars_are_fine(tmp_path):
    assert vs.check_skill(_mk_skill(tmp_path)) == []
```

Note: the `_mk_skill` helper for the `bad`/`b2` cases must create the parent dir before calling — if the inline `mkdir() or` idiom trips you up, restructure the helper to take a dirname parameter; the assertions are what matter.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_validator_extensions.py -v`
Expected: FAIL — `check_anchors`/`check_sidecars` don't exist, duplicate-anchor errors not produced.

- [ ] **Step 3: Extend `validate_skills.py`**

Add after `LOCAL_REF_RE` (line 28):

```python
ANCHOR_RE = re.compile(r"<!--\s*id:\s*([a-z0-9][a-z0-9-]*)\s*-->")
ANCHOR_ANY_RE = re.compile(r"<!--\s*id:")


def check_anchors(name: str, text: str) -> tuple[list[str], set[str]]:
    errs: list[str] = []
    anchors = ANCHOR_RE.findall(text)
    if len(ANCHOR_ANY_RE.findall(text)) != len(anchors):
        errs.append(f"{name}: malformed anchor comment (must be '<!-- id: kebab-case -->')")
    seen: set[str] = set()
    for a in anchors:
        if a in seen:
            errs.append(f"{name}: duplicate anchor id '{a}'")
        seen.add(a)
    return errs, seen


def check_sidecars(skill_dir: Path, anchors: set[str]) -> list[str]:
    errs: list[str] = []
    name = skill_dir.name

    ev_path = skill_dir / "evidence.yaml"
    if ev_path.exists():
        try:
            data = yaml.safe_load(ev_path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError("top level must be a mapping of anchor -> entry")
            for key, entry in data.items():
                if key not in anchors:
                    errs.append(f"{name}: evidence.yaml unknown anchor '{key}'")
                if not isinstance(entry, dict):
                    raise ValueError(f"entry '{key}' must be a mapping")
                for fld in ("helpful", "harmful"):
                    if not isinstance(entry.get(fld, 0), int) or entry.get(fld, 0) < 0:
                        raise ValueError(f"entry '{key}.{fld}' must be a non-negative int")
                if not isinstance(entry.get("sources", []), list):
                    raise ValueError(f"entry '{key}.sources' must be a list")
        except Exception as exc:
            errs.append(f"{name}: evidence.yaml invalid: {exc}")

    evals_path = skill_dir / "evals.yaml"
    if evals_path.exists():
        try:
            data = yaml.safe_load(evals_path.read_text(encoding="utf-8")) or {}
            trig = data.get("triggers", {})
            if not isinstance(trig, dict):
                raise ValueError("'triggers' must be a mapping")
            for side in ("positive", "negative"):
                for case in trig.get(side) or []:
                    if not isinstance(case, dict) or not case.get("phrase"):
                        raise ValueError(f"each triggers.{side} case needs a 'phrase'")
            if not isinstance(data.get("tasks", []), list):
                raise ValueError("'tasks' must be a list")
        except Exception as exc:
            errs.append(f"{name}: evals.yaml invalid: {exc}")

    return errs
```

Wire into `check_skill` — after the `LOCAL_REF_RE` loop (line 73), before `return errs`:

```python
    anchor_errs, anchors = check_anchors(skill_dir.name, body)
    errs.extend(anchor_errs)
    for ref_file in skill_dir.glob("references/*.md"):
        ref_errs, ref_anchors = check_anchors(f"{skill_dir.name}/{ref_file.name}",
                                              ref_file.read_text(encoding="utf-8"))
        errs.extend(ref_errs)
        dup = anchors & ref_anchors
        for a in dup:
            errs.append(f"{skill_dir.name}: anchor '{a}' duplicated in {ref_file.name}")
        anchors |= ref_anchors
    errs.extend(check_sidecars(skill_dir, anchors))
```

- [ ] **Step 4: Run tests + full validator to verify**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_validator_extensions.py -v`
Expected: 7 PASS
Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 24 skills: PASS` (no skill has anchors/sidecars yet — extensions must be no-ops on the current catalog)

- [ ] **Step 5: Commit**

```bash
git add skills/skill-author/scripts/validate_skills.py tests/engine/test_validator_extensions.py
git commit -m "feat(validator): anchor id + evidence/evals sidecar schema checks"
```

---

### Task 10: Anchor seeding — tool skills (12)

**Files:**
- Modify: `skills/{ros2,nav2,gazebo,mujoco,lerobot,isaac-sim,isaac-lab,rviz2,foxglove,rerun,huggingface,cloud-run}/SKILL.md`
- Create: `archive/<name>/<old-version>/` snapshot per touched skill

This is a judgment task, not mechanical find-replace. **What gets an anchor** (spec §4.1): discrete, claim-bearing items — gotchas, version facts, exact commands, config rules, decision rules — in `## Key directives`, `## Quick start`, `## Decision guidance`/`## Usage patterns`, `## Platform gotchas`. **What does not:** connective prose, headings, the cross-reference stanzas, `## Changelog`, `## References` link lists. Aim for 8–20 anchors per deep skill, fewer for thin ones. ID style: short kebab noun-phrases naming the claim (`costmap-inflation`, `dds-domain-id`, `humble-jazzy-split`) — stable names, not positional (`kd-01` is forbidden: anchors must survive reordering).

- [ ] **Step 1: Snapshot + bump loop (run once, before editing)**

For each of the 12 skills, read `version:` from frontmatter and snapshot:

```bash
for s in ros2 nav2 gazebo mujoco lerobot isaac-sim isaac-lab rviz2 foxglove rerun huggingface cloud-run; do
  v=$(python3 - "$s" <<'EOF'
import re, sys
text = open(f"skills/{sys.argv[1]}/SKILL.md").read()
print(re.search(r"^version:\s*(\S+)", text, re.M).group(1))
EOF
)
  mkdir -p "archive/$s" && cp -r "skills/$s" "archive/$s/$v"
done
```

- [ ] **Step 2: Anchor each skill + bump build version + changelog line**

Per skill: add anchors per the guidance above; bump `version:` build digit (e.g. `2.1.0` → `2.1.1`); append changelog line:

```markdown
- <new-version> (YYYY-MM-DD): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
```

- [ ] **Step 3: Validate**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 24 skills: PASS`. Fix any duplicate/malformed anchor errors.

- [ ] **Step 4: Spot-check anchor quality**

Run: `grep -c 'id: ' skills/nav2/SKILL.md` (expect ≥8 for deep skills) and `grep -n 'id: .*-[0-9]*[0-9] -->' skills/*/SKILL.md | grep -E 'id: [a-z]+-[0-9]+ -->'` (expect no purely positional IDs).

- [ ] **Step 5: Commit**

```bash
git add skills/ archive/
git commit -m "feat(skills): anchor IDs for the 12 tool skills (learning-engine Phase 1)"
```

---

### Task 11: Anchor seeding — umbrella skills (10)

**Files:**
- Modify: `skills/{architect,integration,environments,data,visualization,simulation,testing,test-assets,live-demo,skill-author}/SKILL.md`
- Create: `archive/<name>/<old-version>/` per touched skill

Same rules and steps as Task 10 (snapshot loop with the 10 umbrella names → anchor → build-bump → changelog → validate → commit). `skill-updater` and `skill-refiner` are deliberately excluded (they retire in Phase 2). Umbrella skills anchor *decision rules* ("when X choose Y") and routing claims, not the catalog-listing prose.

- [ ] **Step 1: Snapshot the 10 skills** (same loop as Task 10 Step 1 with the umbrella name list)
- [ ] **Step 2: Anchor + build-bump + changelog line per skill**
- [ ] **Step 3: Run:** `uv run skills/skill-author/scripts/validate_skills.py` — Expected: `Checked 24 skills: PASS`
- [ ] **Step 4: Commit**

```bash
git add skills/ archive/
git commit -m "feat(skills): anchor IDs for the 10 umbrella skills (learning-engine Phase 1)"
```

---

### Task 12: Eval seeding from the existing learnings backlog

**Files:**
- Create: `skills/<name>/evals.yaml` — only for skills where the backlog yields ≥1 case
- Test: validator run (schema enforcement from Task 9)

**Interfaces:**
- Produces: `evals.yaml` files per spec §4.3 exactly (keys: `triggers.positive[].{phrase,source}`, `triggers.negative[].{phrase,expect}`, `tasks: []`). Consumed by Phase 2's trigger-eval runner.

- [ ] **Step 1: Harvest recorded phrasings**

Run: `grep -rn -iE "(no skill fired|trigger|didn'?t fire|should have fired|phras)" learnings/*.md` and read each hit's full entry. For every entry recording an exact user phrasing where a skill should have fired: add to that skill's `evals.yaml` `triggers.positive` with the learnings file as `source`. For every misfire (wrong skill fired): add to the *misfiring* skill's `triggers.negative` with `expect: <right-skill>`. Use the phrasing **verbatim** — no paraphrase (spec principle 9: evals from real usage, never synthesis). Do not invent cases for skills with no recorded phrasings — empty files are not created.

- [ ] **Step 2: Validate**

Run: `uv run skills/skill-author/scripts/validate_skills.py`
Expected: `Checked 24 skills: PASS` (schema errors here mean a malformed evals.yaml — fix format, not the validator)

- [ ] **Step 3: Record coverage**

Run: `ls skills/*/evals.yaml | wc -l` and note the count + total case count in the commit message body — this is the eval-suite baseline metric (spec §15 loop-health).

- [ ] **Step 4: Commit**

```bash
git add skills/*/evals.yaml
git commit -m "feat(skills): seed trigger evals from recorded learnings phrasings"
```

---

### Task 13: Learnings schema v2 docs

**Files:**
- Modify: `learnings/README.md` (rewrite)
- Modify: `CLAUDE.md` — the "Capture learnings as you work" section (add fields + entry IDs; do NOT touch the STRICT skill-update policy — that rewrite is Phase 2)

- [ ] **Step 1: Rewrite `learnings/README.md`**

```markdown
# learnings/

Dated notes from building with the robium plugin — Tier 1 of the learning engine
(spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md §4.4). Raw
session transcripts (Tier −1) live gitignored in `.robium/transcripts/`; entries
here are **derived views with pointers back** — never the only copy of anything
a transcript holds.

One file per day: `YYYY-MM-DD.md` (`-<app>` suffix if two apps run the same day).

## Entry template (schema v2)

    - [nav2] wrong-guidance (seen 2x) <!-- id: lrn-0710-03 -->
      symptom: `[controller_server]: Costmap layer error` — robot hugged obstacles
      root-cause: Quick-start costmap YAML omits inflation_layer block
      fix: added inflation_layer, cost_scaling_factor 3.0 — check: nav smoke test passed
      dead-ends: tuning robot_radius (no effect — wrong layer)
      anchors: nav2#costmap-inflation
      source: transcript a1b2c3#turn-142..158 (apps/nav-trial, 2026-07-10)

Rules:
- First line: `[skill-name]` or `[none]`, one of the seven signal types
  (wrong-guidance | no-skill-fired | figured-out-from-scratch | better-method |
  noise | verified | user-correction), optional `(seen Nx)`, and a stable entry
  id `<!-- id: lrn-MMDD-NN -->` so ledgers/observations can cite the entry.
- `symptom` / `fix (check: …)` / `dead-ends` are the three-part evidence bar as
  named fields. Missing parts are fine — the entry is `tentative` until complete.
- `anchors:` names the exact skill item implicated (grep the skill for
  `<!-- id:` to find them). `source:` points into the transcript archive when known.
- Only the first line is mandatory. Capture is never blocked on schema — write
  the one-liner mid-session; the consolidation pass (Phase 2) completes fields
  from the archived transcript.
- Absorption marking: entries stay in place; `<!-- absorbed: YYYY-MM-DD -->`
  markers continue until the observations tier (Phase 2) replaces them.
```

- [ ] **Step 2: Update CLAUDE.md capture section**

In the "Capture learnings as you work (mandatory)" section, after the signal-type list, add one paragraph (keep everything else intact):

```markdown
**Schema v2 (learning engine Phase 1):** entries follow the template in
`learnings/README.md` — first line `[skill] signal-type (seen Nx) <!-- id: lrn-MMDD-NN -->`,
then optional `symptom:` / `root-cause:` / `fix: … (check: …)` / `dead-ends:` /
`anchors:` / `source:` fields. Only the first line is mandatory mid-session.
Capture hooks also flag corrections and errors automatically into the gitignored
`.robium/queue.jsonl`; promote flagged items into a dated entry at the next
natural break (the SessionStart summary lists what's pending).
```

- [ ] **Step 3: Verify no policy drift**

Run: `git diff CLAUDE.md` — confirm the diff touches ONLY the capture section; the "Skill update policy (STRICT)" section must be byte-identical.

- [ ] **Step 4: Commit**

```bash
git add learnings/README.md CLAUDE.md
git commit -m "docs: learnings schema v2 — entry IDs, evidence fields, transcript pointers"
```

---

### Task 14: Transcript miner (`mine_transcripts.py`)

**Files:**
- Create: `scripts/engine/mine_transcripts.py`
- Test: `tests/engine/test_miner.py`

**Interfaces:**
- Consumes: `classify.classify_prompt`, `classify.is_error_result`, `classify.error_signature`, `classify.ROBOTICS_KEYWORDS`, `scrub.scrub` (import via `sys.path` append of `hooks/scripts`).
- Produces: CLI `python3 scripts/engine/mine_transcripts.py <files...> --queue <path> --report <path>`; appends flags with `"source": "transcript <basename>#<uuid>"` and `"mined": true`; writes a markdown report grouped by type. Core function `mine_file(path) -> list[dict]` (used by tests and Phase 2's consolidator).
- Flag types emitted: `user-correction` (incl. tool rejections), `error` (with `seen: N` when repeated), `no-skill-fired` (robotics keywords in a user prompt while no robium skill loaded).

- [ ] **Step 1: Write the failing tests**

`tests/engine/test_miner.py`:

```python
import json
from pathlib import Path

import mine_transcripts as mt


def _write_transcript(tmp_path, events):
    p = tmp_path / "proj__sess1.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return p


def _user(text, uuid="u1", sidechain=False):
    return {"type": "user", "uuid": uuid, "isSidechain": sidechain,
            "message": {"role": "user", "content": text}}


def _assistant_tooluse(tool_id, name, cmd, uuid="a1"):
    return {"type": "assistant", "uuid": uuid, "isSidechain": False,
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": tool_id, "name": name,
                 "input": {"command": cmd} if name == "Bash" else {"skill": cmd}}]}}


def _tool_result(tool_id, text, uuid="r1"):
    return {"type": "user", "uuid": uuid, "isSidechain": False,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": text}]}}


def test_mines_rejection_as_user_correction(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "rm -rf build/"),
        _tool_result("t1", "The user doesn't want to proceed with this tool use."),
        _user("don't delete build, just clean the one package", uuid="u9"),
    ])
    flags = mt.mine_file(str(p))
    rej = [f for f in flags if f["type"] == "user-correction"]
    assert rej and "clean the one package" in rej[0]["excerpt"]
    assert rej[0]["source"].startswith("transcript proj__sess1.jsonl#")


def test_mines_repeated_errors_with_count(tmp_path):
    err = "CMake Error at CMakeLists.txt:14"
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "colcon build", uuid="a1"),
        _tool_result("t1", err, uuid="r1"),
        _assistant_tooluse("t2", "Bash", "colcon build", uuid="a2"),
        _tool_result("t2", err, uuid="r2"),
    ])
    flags = mt.mine_file(str(p))
    errors = [f for f in flags if f["type"] == "error"]
    assert len(errors) == 1 and errors[0]["seen"] == 2


def test_single_error_not_flagged(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Bash", "colcon build"),
        _tool_result("t1", "CMake Error at CMakeLists.txt:14"),
    ])
    assert [f for f in mt.mine_file(str(p)) if f["type"] == "error"] == []


def test_no_skill_fired_detection(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("how do I tune the nav2 costmap so the robot stops hugging walls?"),
    ])
    flags = mt.mine_file(str(p))
    ns = [f for f in flags if f["type"] == "no-skill-fired"]
    assert ns and "costmap" in ns[0]["excerpt"]


def test_skill_loaded_suppresses_no_skill_fired(tmp_path):
    p = _write_transcript(tmp_path, [
        _assistant_tooluse("t1", "Skill", "nav2"),
        _tool_result("t1", "Launching skill: nav2"),
        _user("how do I tune the nav2 costmap here?", uuid="u2"),
    ])
    assert [f for f in mt.mine_file(str(p)) if f["type"] == "no-skill-fired"] == []


def test_sidechain_messages_ignored(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("no, that's wrong — use BEST_EFFORT", sidechain=True),
    ])
    assert mt.mine_file(str(p)) == []


def test_cli_writes_queue_and_report(tmp_path):
    p = _write_transcript(tmp_path, [
        _user("no, use the humble image not jazzy"),
    ])
    queue = tmp_path / "queue.jsonl"
    report = tmp_path / "report.md"
    mt.main([str(p), "--queue", str(queue), "--report", str(report)])
    assert len(queue.read_text().splitlines()) == 1
    assert "user-correction" in report.read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_miner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mine_transcripts'`

- [ ] **Step 3: Implement `scripts/engine/mine_transcripts.py`**

```python
#!/usr/bin/env python3
"""Offline transcript miner (spec §5): rejections, repeated errors, no-skill-fired.

Reads archived Claude Code session JSONL (.robium/transcripts/), emits queue
flags with transcript coordinates plus a human-readable report. stdlib only.
Usage: python3 scripts/engine/mine_transcripts.py FILES... [--queue Q] [--report R]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "hooks", "scripts"))

from classify import ROBOTICS_KEYWORDS, classify_prompt, error_signature, is_error_result  # noqa: E402
from scrub import scrub  # noqa: E402

REJECTION_MARKERS = ("doesn't want to proceed", "user rejected", "User rejected")
MIN_ERROR_COUNT = 2


def _iter_events(path):
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            yield json.loads(line)
        except Exception:
            continue


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if isinstance(block.get("content"), str):
                    parts.append(block["content"])
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
        return "\n".join(parts)
    return ""


def mine_file(path):
    base = os.path.basename(path)
    flags = []
    tool_uses = {}          # tool_use_id -> {"name", "input", "uuid"}
    error_counts = {}       # signature -> {"count", "command", "excerpt", "uuid"}
    skill_loaded = False
    pending_rejection = None

    for ev in _iter_events(path):
        if ev.get("isSidechain"):
            continue
        etype = ev.get("type")
        msg = ev.get("message") or {}
        uuid = ev.get("uuid", "")

        if etype == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_uses[block.get("id")] = {"name": block.get("name"),
                                                  "input": block.get("input") or {},
                                                  "uuid": uuid}
                    if block.get("name") == "Skill":
                        skill_loaded = True

        elif etype == "user":
            content = msg.get("content")
            # tool results
            if isinstance(content, list):
                for block in content:
                    if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                        continue
                    text = _text_of(block.get("content"))
                    tu = tool_uses.get(block.get("tool_use_id"), {})
                    if any(m in text for m in REJECTION_MARKERS):
                        pending_rejection = {"tool": tu.get("name", "?"),
                                             "command": (tu.get("input") or {}).get("command", ""),
                                             "uuid": uuid}
                    elif tu.get("name") == "Bash":
                        cmd = (tu.get("input") or {}).get("command", "")
                        if is_error_result(cmd, text):
                            sig = error_signature(cmd, text)
                            rec = error_counts.setdefault(
                                sig, {"count": 0, "command": cmd,
                                      "excerpt": text[-400:], "uuid": uuid})
                            rec["count"] += 1
                continue
            # plain user prompt
            text = content if isinstance(content, str) else _text_of(content)
            if not text:
                continue
            if pending_rejection is not None:
                flags.append({
                    "type": "user-correction", "confidence": 0.9, "mined": True,
                    "excerpt": scrub(text[:400]),
                    "context": scrub(f"rejected {pending_rejection['tool']}: "
                                     f"{pending_rejection['command'][:150]}"),
                    "source": f"transcript {base}#{uuid}",
                })
                pending_rejection = None
                continue
            hit = classify_prompt(text)
            if hit:
                flags.append({"type": hit["type"], "confidence": hit["confidence"],
                              "mined": True, "excerpt": scrub(text[:400]),
                              "source": f"transcript {base}#{uuid}"})
            elif not skill_loaded and any(k in text.lower() for k in ROBOTICS_KEYWORDS):
                flags.append({"type": "no-skill-fired", "confidence": 0.6, "mined": True,
                              "excerpt": scrub(text[:400]),
                              "source": f"transcript {base}#{uuid}"})

    for sig, rec in error_counts.items():
        if rec["count"] >= MIN_ERROR_COUNT:
            flags.append({"type": "error", "seen": rec["count"], "signature": sig,
                          "mined": True, "command": scrub(rec["command"][:200]),
                          "excerpt": scrub(rec["excerpt"]),
                          "source": f"transcript {base}#{rec['uuid']}"})
    return flags


def write_report(flags, path):
    by_type = {}
    for f in flags:
        by_type.setdefault(f["type"], []).append(f)
    lines = ["# Transcript mining report", ""]
    for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {t} ({len(items)})")
        for f in items:
            head = f.get("command") or f.get("excerpt", "")[:100]
            seen = f" (seen {f['seen']}x)" if f.get("seen") else ""
            lines.append(f"- {head}{seen} — {f['source']}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--queue", default=".robium/queue.jsonl")
    ap.add_argument("--report", default=".robium/mining-report.md")
    args = ap.parse_args(argv)

    all_flags = []
    for path in args.files:
        all_flags.extend(mine_file(path))
    os.makedirs(os.path.dirname(os.path.abspath(args.queue)), exist_ok=True)
    with open(args.queue, "a", encoding="utf-8") as q:
        for f in all_flags:
            q.write(json.dumps(f, ensure_ascii=False) + "\n")
    write_report(all_flags, args.report)
    print(f"mined {len(all_flags)} flags from {len(args.files)} transcript(s) "
          f"-> {args.queue}, report: {args.report}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml -m pytest tests/engine/test_miner.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/engine/mine_transcripts.py tests/engine/test_miner.py
git commit -m "feat(engine): offline transcript miner — rejections, repeated errors, no-skill-fired"
```

---

### Task 15: Back-mining run + Phase 1 exit checklist

**Files:**
- Read: `.robium/transcripts/*.jsonl` (21 rescued files)
- Produce: `.robium/queue.jsonl` entries + `.robium/mining-report.md` (both gitignored — deliverables for Phase 2 consolidation, not for git)

- [ ] **Step 1: Run the back-mining pass**

```bash
python3 scripts/engine/mine_transcripts.py .robium/transcripts/*.jsonl \
  --queue .robium/queue.jsonl --report .robium/mining-report.md
```

Expected: `mined N flags from 21 transcript(s)` with N > 0 (these transcripts contain real app-build sessions; zero would indicate a parsing bug — debug `mine_file` against one file before proceeding).

- [ ] **Step 2: Sanity-read the report**

Run: `head -60 .robium/mining-report.md` — verify entries reference real sessions and excerpts are scrubbed (spot-check: `grep -iE "token|secret|password" .robium/queue.jsonl` should return nothing sensitive-looking).

- [ ] **Step 3: Full test suite + validator, final**

```bash
uv run --with pytest --with pyyaml -m pytest tests/engine -v
uv run skills/skill-author/scripts/validate_skills.py
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); json.load(open('hooks/hooks.json')); print('OK')"
```

Expected: all tests PASS · `Checked 24 skills: PASS` · `OK`

- [ ] **Step 4: Phase 1 exit checklist (spec §15)**

- [ ] Hooks flagged ≥1 real session's friction (Task 8 smoke test) with zero session breakage
- [ ] Session transcript archived by SessionEnd hook (Task 8 step 4.5)
- [ ] Validator green with anchors across 22 anchored skills
- [ ] Eval seed baseline recorded (Task 12 count)
- [ ] Back-mining produced a non-empty queue + report from the rescued transcripts

- [ ] **Step 5: Update docs/CHANGELOG.md and commit**

Append under a new dated heading in `docs/CHANGELOG.md`:

```markdown
## 2026-08-XX — Learning engine Phase 1: substrate + capture

Anchor IDs across 22 skills; evidence/evals sidecar formats with validator
enforcement; learnings schema v2; capture hooks shipped in the plugin
(corrections, bash errors, commit nudge, session summary, transcript archiver);
secret scrubber; offline transcript miner; back-mining of 21 rescued session
transcripts. Spec: docs/superpowers/specs/2026-08-01-learning-engine-design.md.
```

```bash
git add docs/CHANGELOG.md
git commit -m "docs: changelog — learning engine Phase 1 (substrate + capture)"
```

---

## Self-review notes (performed at plan-writing time)

- **Spec coverage (Phase 1 row of §15):** anchors → Tasks 10–11; ledger format → validator schema in Task 9 (no `evidence.yaml` files are seeded — spec §4.2: only engine tooling writes them, which arrives with the Phase 2 consolidator); evals sidecars → Tasks 9 + 12; learnings schema v2 → Task 13; hooks incl. SessionEnd archiver → Tasks 4–8; miner → Task 14; scrubber → Task 2; validator extensions → Task 9; `.robium/` convention → Task 1 (+ hook-driven git-exclude); back-mining → Task 15. Transcript rescue of pre-hook sessions was already done during brainstorming (21 files in `.robium/transcripts/`).
- **Known deviation from spec §13:** the miner lives at `scripts/engine/` in Phase 1; the spec places engine scripts under the `learning-loop` skill, which doesn't exist until Phase 2. Phase 2's meta-skill restructure task must either relocate it or (preferred, decide then) leave engine tooling at `scripts/engine/` with `learning-loop` referencing it — record whichever in the Phase 2 plan.
- **Type consistency:** flag dict keys (`type/confidence/session/excerpt/command/signature/seen/source/mined/ts/project`) are consistent across Tasks 1, 4, 5, 14; `check_anchors` returns `(errs, anchors)` and Task 9's wiring uses it that way; test helper `run_hook`/`read_queue` defined once in Task 4's file and reused by Tasks 5–6 (same file).
- **Hook-input field names** (`session_id`, `transcript_path`, `cwd`, `prompt`, `tool_name`, `tool_input`, `tool_response`, `stop_hook_active`, `source`, `reason`) follow the Claude Code hooks contract; the live smoke test in Task 8 is the ground-truth check — if a field name mismatches in practice, fix the entry script, not the tests' intent.
