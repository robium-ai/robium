# Standard App Lifecycle Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose help, doctor, build, run, status, logs, and stop consistently through Make and the generic Robium app CLI.

**Architecture:** Indoor navigation owns the actual lifecycle operations in its Makefile. Its `robium-app.yaml` describes those operations, while the zero-dependency Node CLI normalizes string or object verb declarations, displays command help, and dispatches the selected Make command.

**Tech Stack:** GNU Make, Docker Compose v2, zero-dependency Node.js ESM, `robium-app.yaml`

## Global Constraints

- The exact standard verbs are `help`, `doctor`, `build`, `run`, `status`, `logs`, and `stop`.
- Remove indoor-navigation's `mapping`, `down`, and `check` Make targets without aliases.
- Keep app-specific runtime behavior in Make; the CLI only resolves metadata and executes commands.
- Preserve string-valued verbs for manifests that have not migrated.
- Do not add, update, or run automated tests.

---

### Task 1: Standardize indoor-navigation's Make interface

**Files:**
- Modify: `/Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation-control-panel/indoor-navigation/Makefile`
- Modify: `/Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation-control-panel/indoor-navigation/README.md`

**Interfaces:**
- Produces: `make help|doctor|build|run|status|logs|stop`.
- Preserves: advanced `sim`, `demo`, and other development/deployment targets.

- [ ] Rename the current preflight target to `doctor`, dashboard target to `run`, and teardown target to `stop`; remove the old names.
- [ ] Add `help`, `status`, and `logs` wrappers with concise output and dashboard endpoints.
- [ ] Replace active README references to the removed commands and document the standard lifecycle table.

### Task 2: Describe rich lifecycle verbs in the app manifest

**Files:**
- Modify: `/Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation-control-panel/indoor-navigation/robium-app.yaml`

**Interfaces:**
- Produces: verb objects containing `command` and `summary`.
- Consumes: the seven Make targets from Task 1.

- [ ] Set `runtime.entrypoint` to `make run`.
- [ ] Declare the seven standard verbs with their Make command and user-facing summary.
- [ ] Declare `demo` as an explicit advanced scenario and keep `sim`, `slam`, and `nav` scenarios available.

### Task 3: Extend the generic Robium CLI dispatcher

**Files:**
- Create: `/Users/mdemirst/repos/robium/cli/src/appVerbs.js`
- Modify: `/Users/mdemirst/repos/robium/cli/src/apps.js`
- Modify: `/Users/mdemirst/repos/robium/cli/src/appValidate.js`
- Modify: `/Users/mdemirst/repos/robium/cli/bin/robium.js`
- Modify: `/Users/mdemirst/repos/robium/cli/README.md`

**Interfaces:**
- Produces: `robium app help|doctor|build|run|status|logs|stop <id>`.
- Consumes: string verbs and `{ command, summary }` verb objects.

- [ ] Add one verb normalizer used by command resolution, validation, and help rendering.
- [ ] Generate per-app help with CLI spelling, equivalent Make command, and summary.
- [ ] Dispatch `build`, `run`, `status`, `logs`, and `stop` through manifest verbs; keep `doctor` as environment facts followed by the app's doctor verb.
- [ ] Update CLI usage and README examples to the standard lifecycle vocabulary.

### Task 4: Review and publish both repositories

**Files:**
- Review only the files named in Tasks 1–3.

**Interfaces:**
- Produces: one app commit on `promote/indoor-navigation-control-panel` and one CLI commit in the robium repository.

- [ ] Review source diffs without running automated tests.
- [ ] Commit and push the app branch while excluding saved map directories.
- [ ] Commit the CLI changes without modifying skill content.
