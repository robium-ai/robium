<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/robium-lockup-dark.png">
  <img src="assets/brand/robium-lockup.png" alt="robium" width="360">
</picture>

### Physical AI skills for your agents

An open-source, continuously evolving collection of field-tested robotics<br>
expertise — install robium as a plugin to empower your favorite AI coding<br>
agent with the robotics skills it needs.

[![skills](https://github.com/robium-ai/robium/actions/workflows/skills.yml/badge.svg)](https://github.com/robium-ai/robium/actions/workflows/skills.yml)
[![Website](https://img.shields.io/badge/robium.ai-website-4c8bf5)](https://robium.ai)
[![npm](https://img.shields.io/npm/v/robium-ai?label=npm%20robium-ai&color=cb3837)](https://www.npmjs.com/package/robium-ai)
[![License: MIT](https://img.shields.io/badge/license-MIT-3da638)](./LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Robium-5865F2?logo=discord&logoColor=white)](https://robium.ai/join/discord)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97-robium-FFD21E)](https://huggingface.co/robium)

</div>

Ask a coding agent to build a warehouse robot and it may guess at ROS 2,
invent Gazebo syntax, or pick the wrong simulator.

robium gives it versioned robotics skills for choosing the stack, building the
system, and testing the result.

## Install

**Quick** — clone the repository and install the skills for every supported
agent detected on your machine:

```bash
npx robium-ai setup                  # auto-detects your agents
npx robium-ai setup --agent codex    # or target one
```

The default clone lives at `~/robium`. Target one agent with `--agent`.

**Native install** — clone the repository, then use your agent's own package
flow where one is available:

```bash
git clone https://github.com/robium-ai/robium ~/robium

# Claude Code — plugin with skills, architect agent, and capture hooks
claude plugin marketplace add ~/robium && claude plugin install robium@robium

# Codex — native plugin
codex plugin marketplace add ~/robium && codex plugin add robium@robium

# Gemini CLI — extension with automatic updates
gemini extensions install https://github.com/robium-ai/robium --auto-update

# Cursor — versioned skills
mkdir -p ~/.cursor/skills && ln -s ~/robium/skills/* ~/.cursor/skills/
```

The repository remains the source of truth. Pull it to update local plugin and
symlink-based installs.

Your application stays in its own repository; Robium lives beside it. Use the
reference apps as starting points and contribute reusable fixes back.

## Your first robot sim — on a plain laptop

No GPU, no robot, no cloud. After installing, ask for what you want in plain
language:

> *"Set up a MuJoCo manipulation sim I can run headless on my laptop."*

The `architect` skill selects a stack and routes the agent through environment
setup, simulation, and a smoke test. This MuJoCo path runs offscreen without a
GPU, including on macOS.

> *"Now build me a mobile robot that navigates a warehouse in simulation."*

## How it fits

Robium provides robotics expertise. Your project provides the context. Your AI
coding agent handles architecture, implementation, simulation, testing, and
deployment.

Captured build learnings can improve future skill versions. See the workflow
at [robium.ai](https://robium.ai/#how-it-fits).

## What's inside

```
robium/
├── skills/          the catalog — versioned, hand-crafted, validator-enforced
├── agents/          robium-architect: researches the stack, writes your brief
├── .claude-plugin/  Claude Code package
├── .codex-plugin/   Codex package and marketplace
├── gemini-extension.json  Gemini CLI extension
├── learnings/       field evidence from real builds — input to the learning loop
└── cli/             npx robium-ai — setup, doctor, skill search
```

The reference applications live in
[robium-ai/robium-apps](https://github.com/robium-ai/robium-apps) and the
robium.ai site + live-demo infrastructure in
[robium-ai/robium-website](https://github.com/robium-ai/robium-website).

The catalog in one view — every skill is one folder under
[`skills/`](./skills), browsable on [robium.ai](https://robium.ai):

| Pillar | Skills |
| --- | --- |
| Architecture & proof | `architect` · `testing` · `test-assets` · `live-demo` · `cloud-run` |
| Simulation | `simulation` · `gazebo` · `mujoco` · `isaac-sim` · `isaac-lab` |
| Data & learning | `data` · `lerobot` · `huggingface` |
| Visualization | `visualization` · `foxglove` · `rerun` · `rviz2` |
| Robotics integration | `ros2` · `nav2` · `integration` · `environments` |
| Catalog upkeep | `skill-author` · `learning-loop` · `mining` |

**Umbrella skills** own decisions (which simulator, where data comes from, how
to test); **tool skills** own the mechanics of one library. `architect` is the
entry point and routes to everything else.

## A catalog that maintains itself

Robotics guidance rots fast — APIs move, versions pair differently, commands
change shape. robium is built to notice:

- **Capture** — hooks record what broke and what fixed it during real build
  sessions; [`learnings/`](./learnings) holds the evidence.
- **Mine** — the ecosystem's proven patterns are read out of real repos, with
  citations that must still hold at the pinned commit.
- **Absorb** — evidence-gated pull requests fold both back into the versioned
  skills. Agents draft; a human merges every change.
- **Verify** — version facts are checked against live upstream docs at
  authoring time, and each claim states how it was verified. Prior skill
  versions stay browsable under [`archive/`](./archive).

## Reference apps

Reference applications exercise the catalog against real robotics workflows.
They live in [robium-ai/robium-apps](https://github.com/robium-ai/robium-apps)
(start at its REGISTRY.md); demos and recorded results are available at
[robium.ai](https://robium.ai).

- **nav-trial** — TurtleBot 3 navigating in Gazebo with Nav2, headless in Docker.
- **manip-trial** — LeRobot manipulation: train, evaluate, and demo a policy on a GPU-less laptop.
- **vla-trial** — language-conditioned VLA arm: instruction → SmolVLA → SO-101 in MuJoCo.
- **go2-locomotion** — Unitree Go2 quadruped learning to walk via RL (Isaac Lab) on a cloud GPU.
- **tb4-teleop** — drive a real TurtleBot 4 from the browser (hardware-in-the-loop).

## Contributing

The contribution unit is small on purpose: **one skill, no build system**.
Pick a robotics tool you know, copy the template, pass the validator:

```bash
uv run skills/skill-author/scripts/validate_skills.py
```

[CONTRIBUTING.md](./CONTRIBUTING.md) has the five-step walkthrough;
[`good-first-skill`](https://github.com/robium-ai/robium/labels/good-first-skill)
issues are the on-ramp. Questions:
[Discord](https://robium.ai/join/discord) or
[Discussions](https://github.com/robium-ai/robium/discussions).

## License

[MIT](./LICENSE). See [CONTRIBUTING.md](./CONTRIBUTING.md) for the skill format,
quality bar, and development workflow.
