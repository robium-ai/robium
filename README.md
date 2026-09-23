<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/robium-lockup-dark.png">
  <img src="assets/brand/robium-lockup.png" alt="robium" width="360">
</picture>

### Physical AI skills for your agents

An open-source, continuously evolving collection of field-tested robotics<br>
expertise. Install robium as a plugin to empower your favorite AI coding<br>
agent with the robotics skills it needs.<br>
Covers ROS 2, Nav2, Gazebo, MuJoCo, NVIDIA Isaac Sim, Isaac Lab, and LeRobot,<br>
for Claude Code, Codex, Gemini CLI, and Cursor.

[![skills](https://github.com/robium-ai/robium/actions/workflows/skills.yml/badge.svg)](https://github.com/robium-ai/robium/actions/workflows/skills.yml)
[![Website](https://img.shields.io/badge/robium.ai-website-4c8bf5)](https://robium.ai)
[![npm](https://img.shields.io/npm/v/robium-ai?label=npm%20robium-ai&color=cb3837)](https://www.npmjs.com/package/robium-ai)
[![License: MIT](https://img.shields.io/badge/license-MIT-3da638)](./LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Robium-5865F2?logo=discord&logoColor=white)](https://robium.ai/join/discord)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97-robium-FFD21E)](https://huggingface.co/robium)

</div>

## Install

**Quick**: clone the skills and reference-app repositories and install Robium for every supported
agent detected on your machine:

```bash
npx robium-ai setup                  # auto-detects your agents
npx robium-ai setup --agent codex    # or target one
npx robium-ai workspace              # show your remembered directories
npx robium-ai update --check          # check official main without applying
npx robium-ai update                 # fast-forward clean main in both repos
npx robium-ai remove                 # remove integrations; keep the checkout
npx robium-ai doctor                 # verify activation and installed versions
```

Choose the workspace parent and its name during setup, or pass
`npx robium-ai setup --dir ~/projects/my-robotics`. The default is:

```text
~/robium/                 # workspace parent, not a repository
├── robium/               # editable skills and plugin source
└── robium-apps/          # runnable reference examples
```

The CLI remembers it in `~/.config/robium/workspace.json`; agents can discover
both paths with `npx robium-ai workspace --json`. Apps are cloned by default,
but environments and model assets are only set up when an app needs them.

| Agent | Full Robium integration | Live skill source |
| --- | --- | --- |
| Claude Code | Native Claude plugin | Robium checkout; Claude caches released plugins |
| Codex | Native OpenAI plugin | Robium checkout; Codex caches installed plugins |
| Gemini CLI | Native extension: skills, architect subagent, capture hooks | Linked Robium checkout |
| Cursor | Native Cursor plugin: skills, architect agent, capture hooks | Linked Robium checkout |

Codex Desktop is detected on macOS even when its bundled `codex` executable
is not on your shell `PATH`.

To install only one portable skill instead of the full Robium integration:

```bash
npx skills add robium-ai/robium -g --skill navigation --agent codex
npx skills update -g
```

**Native install**: clone the repository, then use your agent's own package
flow where one is available:

```bash
mkdir -p ~/robium
git clone https://github.com/robium-ai/robium ~/robium/robium
git clone https://github.com/robium-ai/robium-apps ~/robium/robium-apps

# Claude Code: plugin with skills, architect agent, and capture hooks
claude plugin marketplace add ~/robium/robium && claude plugin install robium@robium

# Codex: native plugin
codex plugin marketplace add ~/robium/robium && codex plugin add robium@robium

# Gemini CLI: editable local extension
gemini extensions link ~/robium/robium --consent

# Cursor: local native plugin linked from the checkout
npx robium-ai setup --agent cursor --dir ~/robium
```

Run `npx robium-ai setup --dir ~/robium` to remember a manually cloned workspace.
Updates are on demand: clean `main` branches fast-forward from official
upstream; personal branches, dirty files, and divergent histories are skipped
without switching, stashing, or resetting. Work on a branch in either repo and
optionally contribute later.

Quiet checks during example discovery run at most daily and notify at most
weekly, without repeating the same revisions. Disable them with
`ROBIUM_UPDATE_CHECKS=0`; explicit checks remain available. After manual Git
updates or edits, re-run `setup` to refresh integrations without pulling.
Restart the host as instructed; cached skill activation is distinct from source
freshness. See [CLI setup and updates](cli/README.md).

Host-specific install, update, removal, permission, and fail-open details are
in [docs/gemini-cli.md](./docs/gemini-cli.md) and
[docs/cursor.md](./docs/cursor.md).

Your application stays in its own repository; Robium lives beside it. Use the
reference apps as starting points and contribute reusable fixes back.

## How it fits

Robium provides robotics expertise. Your project provides the context. Your AI
coding agent handles architecture, implementation, simulation, testing, and
deployment.

Captured build learnings can improve future skill guidance. See the workflow
at [robium.ai](https://robium.ai/#how-it-fits). External users can contribute a
[sanitized build finding](./CONTRIBUTING.md#contributing-a-sanitized-build-finding)
without sharing a raw agent transcript.

## What's inside

```
robium/
├── skills/          the catalog: lean, hand-crafted, validator-checked
├── agents/          robium-architect: researches the stack, writes your brief
├── .claude-plugin/  Claude Code package
├── .codex-plugin/   Codex package manifest
├── .cursor-plugin/  Cursor-native package manifest
├── .agents/plugins/ Codex-native repository marketplace
├── hooks/           shared hooks plus Gemini and Cursor event adapters
├── AGENTS.md        canonical Codex-native maintainer guidance
├── gemini-extension.json  Gemini CLI extension
├── learnings/       field evidence from real builds, input to the learning loop
└── cli/             npx robium-ai: setup, doctor, skill search
```

The reference applications live in
[robium-ai/robium-apps](https://github.com/robium-ai/robium-apps) and the
robium.ai site + live-demo infrastructure in
[robium-ai/robium-website](https://github.com/robium-ai/robium-website).

The catalog in one view: every skill is one folder under
[`skills/`](./skills), browsable on [robium.ai](https://robium.ai):

| Pillar | Skills |
| --- | --- |
| Architecture & proof | `architect` · `testing` · `test-assets` · `live-demo` · `cloud-run` · `runpod` |
| Simulation | `simulation` · `gazebo` · `mujoco` · `isaac-sim` · `isaac-lab` |
| Data & learning | `data` · `lerobot` · `huggingface` |
| Visualization | `visualization` · `foxglove` · `rerun` · `rviz2` |
| Robotics integration | `ros2` · `navigation` · `integration` · `environments` |
| Catalog upkeep | `skill-author` · `learning-loop` · `mining` |

**Umbrella skills** own decisions (which simulator, where data comes from, how
to test); **tool skills** own the mechanics of one library. `architect` is the
entry point and routes to everything else.

## A catalog that maintains itself

Robotics guidance rots fast: APIs move, versions pair differently, commands
change shape. robium is built to notice:

- **Capture**: hooks record what broke and what fixed it during real build
  sessions into local staging. A once-daily session-start reminder appears only
  when substantial signals are waiting.
- **Mine**: the ecosystem's proven patterns are read out of real repos, with
  citations that must still hold at the pinned commit.
- **Absorb**: approved background learning runs fold ready evidence into the
  skills. Observations are local working notes and are deleted after absorption;
  durable citations and details live with the skill.
- **Verify**: volatile facts are checked against current upstream docs, and
  observed values retain the conditions that produced them.

## Contributing

The contribution unit is small on purpose: **one skill, no build system**.
If you installed Robium with `npx robium-ai setup`, reuse its checkout—do not
clone it again:

```bash
cd ~/robium/robium                # or the repo path from robium workspace
./scripts/bootstrap.sh
git switch -c my-skill-fix
```

Pick a robotics tool you know, edit its skill, and run the repository check:

```bash
./scripts/check.sh
```

[CONTRIBUTING.md](./CONTRIBUTING.md) has the five-step walkthrough;
[`good-first-skill`](https://github.com/robium-ai/robium/labels/good-first-skill)
issues are the on-ramp. Questions:
[Discord](https://robium.ai/join/discord) or
[Discussions](https://github.com/robium-ai/robium/discussions).

## License

[MIT](./LICENSE). See [CONTRIBUTING.md](./CONTRIBUTING.md) for the skill format,
quality bar, and development workflow.
