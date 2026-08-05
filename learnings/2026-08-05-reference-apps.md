# 2026-08-05 - reference-apps roadmap build (all apps + CLI + website)

- [none] figured-out-from-scratch <!-- id: lrn-0805-01 -->
  symptom: the shared demo-gateway contract test 404'd every static file on macOS even though the same code served fine inside the container.
  root-cause: the traversal guard compares `os.path.realpath(joined)` against the configured STATIC_ROOT string; macOS tmpdirs live under the `/var -> /private/var` symlink, so the canonicalized child never string-prefixes the un-canonicalized root. Containers hid the bug because /opt/lichtblick has no symlinks.
  fix: canonicalize the root once at startup, `STATIC_ROOT = os.path.realpath(env)` (check: `python3 shared/demo-gateway/test_gateway.py` prints GATEWAY CONTRACT TEST PASS).
  dead-ends: not a permissions or PORT issue; /status worked throughout, which localized it to the static path guard.
  anchors: robium-internal-apps shared/demo-gateway/demo_gateway.py STATIC_ROOT constant.
  source: extracting the gateway package, spec v1.2.

- [none] figured-out-from-scratch <!-- id: lrn-0805-02 -->
  symptom: the website's vendored robium-app.yaml parser returned `demo.orchestrator = null` and leaked orchestrator child keys into the parent map, while the CLI's identical-looking parser parsed the same file correctly.
  root-cause: the parser was vendored by retyping, not copying, and dropped one branch: a section-opening line with a trailing comment (`orchestrator:  # ...`) must be treated as a nested-map opener (`rest` is comment-only), not a scalar.
  fix: vendor byte-for-byte; the missing clause is `rest.trim() === '' || /^\s+#/.test(rest)` (check: fetch-apps.mjs emits demo_id manip-trial/nav-trial/vla-trial, not null).
  anchors: robium-website scripts/fetch-apps.mjs parseAppYaml; robium cli/src/apps.js is the source copy.
  source: website ingestion, spec v1.1.

- [none] worked-as-documented ✓ <!-- id: lrn-0805-03 -->
  The derived orchestrator configs came out byte-identical to the three
  hand-written demo-orchestrator jsons (nav/vla exact; manip differed only in
  JSON unicode escaping of an em dash), which is strong evidence the
  demo.orchestrator schema captured the real contract on the first pass.
  sync-demos.mjs --check now guards drift in site smoke.

- [none] figured-out-from-scratch <!-- id: lrn-0805-04 -->
  symptom: a file committed to the robium repo minutes earlier was absent from a freshly created Claude Code worktree.
  root-cause: EnterWorktree's default baseRef is `fresh` = origin/<default-branch>; local main was ahead of origin (unpushed docs commits), so the worktree silently lacked them.
  fix: push main first (or reset the worktree branch to local main) before building on same-day main commits (check: the spec file exists inside the worktree).
  source: CLI worktree setup for the reference-apps build.

## End-of-block retro (2026-08-05, reference-apps roadmap)

No robium skills loaded during this block either (plugin skills still absent
from the session's skill list; only the robium:robium-architect agent was
registered) - fired/quiet scoring not applicable, same finding as the
2026-08-03 block. The work was contract/CLI/web plumbing; the one robotics
touchpoint (gateway contract) is captured above and in the shared package's
README rather than as skill deltas.
