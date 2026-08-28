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
- `archive/`: immutable snapshots of prior skill versions.
- `docs/`: history, architecture notes, and changelog.

Applications live in the sibling `robium-ai/robium-apps` repository. The site
and live-demo orchestrator live in `robium-ai/robium-website`. Make changes in
the repository that owns the output; cross-reference rather than duplicate.

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

- **Skill authoring:** follow `skills/AGENTS.md` and load `skill-author`.
- **Learning engine:** follow `learnings/AGENTS.md` and load `learning-loop`.
- **Application build/QA:** work in `robium-apps`; hooks capture evidence
  silently here. Do not interrupt the build to edit skills.
- **CLI:** work under `cli/`; publish only from that directory and only with
  explicit authorization.
- **Website/demo infrastructure:** work in `robium-website` under its guidance.

## Common checks

```bash
./scripts/bootstrap.sh
uv run skills/skill-author/scripts/validate_skills.py
uv run --with pyyaml --with pytest python -m pytest tests/engine
python3 -c "import json; [json.load(open(p)) for p in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json', 'hooks/hooks.json')]; print('OK')"
```

Maintainer credentials live in Doppler (`robium/dev`) and never in git. Use
`doppler run -- <command>` only for an explicitly authorized privileged task.

## Git and external actions

- External contributors, unattended automation, and unrequested learning
  absorption use a branch/PR and human merge for `skills/**`.
- The maintainer may explicitly authorize direct-to-`main` work in the current
  conversation. That exception permits the local commit, not an inferred push,
  deploy, publish, paid job, or destructive cloud action.
- Every skill edit still requires its archive snapshot, version bump,
  changelog, catalog regeneration, and validation.
- Preserve unrelated working-tree changes. Never rewrite history or use a
  destructive reset unless the maintainer explicitly asks.

## Tracker

GitHub Issues owns forward work: `robium-ai/robium` for plugin/CLI/learning
work, `robium-ai/robium-apps` for applications, and `robium-ai/robium-website`
for site/orchestrator work. Do not create checked-in TODO lists.
