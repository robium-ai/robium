# App Mode Naming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace scenario-named CLI and manifest fields with mode terminology across every Robium app.

**Architecture:** The generic CLI reads `modes` from `robium-app.yaml`, selects one through `--mode`, and dispatches its existing command. All app manifests migrate together so the schema has one name and requires no compatibility alias.

**Tech Stack:** zero-dependency Node.js ESM, `robium-app.yaml`

## Global Constraints

- Use only `--mode`, `modes`, and `default_mode` in the CLI/application contract.
- Do not retain `--scenario`, `scenarios`, or `default_scenario` aliases.
- Do not rename underlying Make targets or change runtime behavior.
- Do not add, update, or run automated tests.

---

### Task 1: Rename the generic CLI contract

**Files:**
- Modify: `/Users/mdemirst/repos/robium/cli/bin/robium.js`
- Modify: `/Users/mdemirst/repos/robium/cli/src/apps.js`
- Modify: `/Users/mdemirst/repos/robium/cli/src/appValidate.js`
- Modify: `/Users/mdemirst/repos/robium/cli/src/appNew.js`
- Modify: `/Users/mdemirst/repos/robium/cli/README.md`

**Interfaces:**
- Consumes: `flags.mode` and `app.modes`.
- Produces: mode resolution, mode errors, and Mode help output.

- [ ] Parse `--mode` and remove `--scenario` parsing.
- [ ] Resolve `app.modes[mode]`, render a `Modes` help section, and reject `--mode` outside `app run`.
- [ ] Validate `modes` plus `demo.default_mode` and update scaffold guidance and examples.

### Task 2: Migrate every app manifest

**Files:**
- Modify: `/Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation-control-panel/*/robium-app.yaml`
- Modify: active README/help references to the CLI flag or manifest field.

**Interfaces:**
- Produces: `modes` maps and `default_mode` metadata for every reference app.
- Preserves: every existing mode command and summary.

- [ ] Rename the manifest keys without changing their values.
- [ ] Rename active documentation references to the manifest/CLI contract.

### Task 3: Review and publish

**Files:**
- Review only the files named above and these spec/plan documents.

**Interfaces:**
- Produces: commits on the existing app and CLI branches.

- [ ] Review diffs without running automated tests.
- [ ] Commit and push the app branch while excluding saved maps.
- [ ] Commit and push `codex/standard-app-lifecycle-cli`.
