# AGENTS.md

Canonical guidance for Codex, Claude Code, and other coding agents working in
this repository.

## Repository purpose

**robium** ships a native robotics-skills plugin plus its CLI and learning
engine. The plugin is knowledge and real reusable examples, not an application
framework or invented DSL.

- `skills/`, `hooks/`, `agents/`, `.codex-plugin/`, `.claude-plugin/`: plugin.
- `cli/`: the `robium-ai` npm package.
- `learnings/`, `scripts/engine/`: evidence capture and skill hardening.
- `docs/`: current client/operator guidance and the shipped-work changelog.

Applications live in the sibling `robium-ai/robium-apps` repository. The site
and live-demo orchestrator live in `robium-ai/robium-website`. Make changes in
the repository that owns the output; cross-reference rather than duplicate.

These are cloned as siblings inside a `robium-ai/robium-workspace` parent,
beside a user-owned `my-apps/` for applications that are not contributed
upstream. All are independent checkouts, never submodules.

A local `website/` or `apps/` directory here is an untracked leftover from the
old monorepo holding stale build output. Neither is a source of truth; use the
sibling `robium-website/` and `robium-apps/` checkouts instead.

## Maintainer collaboration

- An explicit, bounded change request authorizes implementation after reading
  the affected code. Give a short work update, then proceed; do not announce a
  process classification or ask for the same approval twice.
- For a new application or material architecture change, present one rough
  direction with meaningful alternatives. Once approved, implement and verify
  without further conversational gates.
- Pause only when a missing choice materially changes the result, scope must
  expand, or safety/external authority requires confirmation.
- Prefer the cheapest risk-reducing probe and the first user-visible working
  slice before polishing infrastructure or optimizing scale.

## Modes and ownership

- **User workspaces and updates:** setup remembers a configurable parent
  containing `robium/` and `robium-apps/`. Use `npx robium-ai workspace --json`
  to discover it; do not hardcode paths or treat a plugin cache as editable
  source. Follow [workspace update guidance](skills/architect/references/workspace-updates.md)
  when asked about freshness or updating. Check and apply are separate;
  personal branches and local changes must remain intact. Quiet checks belong
  at new-example boundaries, not on every prompt or during maintenance.

- **Skill authoring:** follow `skills/AGENTS.md` and load `skill-author`.
- **Learning engine:** follow `learnings/AGENTS.md` and load `learning-loop`.
- **Application build/QA:** work in `robium-apps`; hooks capture evidence
  silently here. Do not interrupt the build to edit skills.
- **CLI:** work under `cli/`; publish only from that directory and only with
  explicit authorization.
- **Website/demo infrastructure:** work in `robium-website` under its guidance.

## Common checks

Choose checks for the affected behavior; this is a toolbox, not a mandatory
suite for every task. Batch coherent edits before the smallest relevant check.
Do not add tests or repeat passing suites without risk, uncertainty, or a user
request that justifies them. Use browser/computer-use checks only for relevant
visual/interaction uncertainty or when requested. Low-risk manual acceptance
may be handed to the user with exact steps and an explicit unverified status;
never defer evidence needed before safety-critical, destructive, or paid actions.

```bash
./scripts/bootstrap.sh
./scripts/check.sh
uv run --with pyyaml --with pytest python -m pytest tests/engine
```

Maintainer credentials live in Doppler (`robium/dev`) and never in git. Use
`doppler run -- <command>` only for an explicitly authorized privileged task.

## Git and external actions

- External contributors, unattended automation, and unrequested learning
  absorption use a branch/PR and human merge for `skills/**`.
- The maintainer may explicitly authorize direct-to-`main` work in the current
  conversation. That exception permits the local commit, not an inferred push,
  deploy, publish, paid job, or destructive cloud action.
- Live skills are intentionally versionless and changelog-free; Git history is
  their change record. Regenerate the catalog when names or descriptions
  change, and run the lightweight skill validator after skill edits.
- Preserve unrelated working-tree changes. Never rewrite history or use a
  destructive reset unless the maintainer explicitly asks.

## Tracker

GitHub Issues owns forward work: `robium-ai/robium` for plugin/CLI/learning
work, `robium-ai/robium-apps` for applications, and `robium-ai/robium-website`
for site/orchestrator work. Do not create checked-in TODO lists.
