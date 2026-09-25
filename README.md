<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/robium-lockup-dark.png">
  <img src="assets/brand/robium-lockup.png" alt="robium" width="360">
</picture>

### Physical AI skills for coding agents

Robium gives Claude Code, Codex, Gemini CLI, and Cursor field-tested robotics
skills, troubleshooting guidance, and runnable reference applications. Start
with a working robot, then ask your agent to adapt it.

[![skills](https://github.com/robium-ai/robium/actions/workflows/skills.yml/badge.svg)](https://github.com/robium-ai/robium/actions/workflows/skills.yml)
[![Website](https://img.shields.io/badge/robium.ai-website-4c8bf5)](https://robium.ai)
[![npm](https://img.shields.io/npm/v/robium-ai?label=npm%20robium-ai&color=cb3837)](https://www.npmjs.com/package/robium-ai)
[![License: MIT](https://img.shields.io/badge/license-MIT-3da638)](./LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Robium-5865F2?logo=discord&logoColor=white)](https://robium.ai/join/discord)

</div>

## Install

You need Node.js 18+, Git, and at least one supported coding agent.

```bash
npx robium-ai setup
npx robium-ai doctor
```

Setup detects your agents and asks where to create the workspace. To install
for one agent or choose the location up front:

```bash
npx robium-ai setup --agent codex
npx robium-ai setup --dir ~/projects/my-robotics
```

This is an **editable install**, not a hidden package snapshot. Setup creates
ordinary Git checkouts and connects your agent to them:

```text
~/robium-workspace/       # default; location and name are your choice
├── robium/               # editable skills and plugin source
└── robium-apps/          # runnable reference applications
```

Run `npx robium-ai workspace` anytime to find them. After editing or manually
updating Robium, run `npx robium-ai setup` again and restart your agent so its
integration refreshes.

## Try a working robot

Restart your agent after setup, open it in a folder where it may work, and paste
one of these prompts. Robium will inspect the matching reference app, check the
prerequisites, and aim for a visible result before suggesting custom work.

### Map and navigate a simulated home

<a href="https://github.com/robium-ai/robium-apps/tree/main/robot-navigation"><img src="https://raw.githubusercontent.com/robium-ai/robium-apps/main/robot-navigation/assets/stills/readme-navigation.png" alt="A simulated TurtleBot mapping and navigating a home" width="700"></a>

> Help me map a simulated environment, localize a mobile robot, and navigate to a goal.

This uses the stable `robot-navigation` example with ROS 2, Nav2, Gazebo, and a
bundled browser viewer. Docker with Compose v2 is required. A successful first
run creates and saves a map, localizes the robot on it, and reaches a navigation
goal.

To run the example directly instead:

```bash
npx robium-ai app doctor robot-navigation
npx robium-ai app run robot-navigation
```

### Run a pretrained two-arm policy

> Help me run a pretrained policy that transfers a cube between two simulated robot arms.

This uses the official ACT checkpoint in `act-aloha-cube-transfer`. There is no
training step and no dedicated GPU is required. The first run prepares the
locked environment and downloads the pinned model; success means the viewer
opens, real inference runs, and the default cube-transfer result is reported.

```bash
npx robium-ai app doctor act-aloha-cube-transfer
npx robium-ai app run act-aloha-cube-transfer
```

The native path is tested on Apple Silicon. Ask your agent to check the app
README before using another platform.

### Build a robot assistant

> Help me build a simulated robot assistant that understands what it sees and follows natural-language instructions.

This starts from `silly-turtlebot`: a camera-equipped TurtleBot simulation with
guarded navigation tools. It requires Docker and your own authorized Gemini
Robotics access. Live model calls may cost money, so Robium checks access before
starting and will not present a mock run as a live result.

More applications and hosted demos are at [robium.ai](https://robium.ai) and in
[robium-apps](https://github.com/robium-ai/robium-apps).

## Make it yours

Keep the shipped examples clean and create an editable derivative in your own
`my-apps/` directory:

```bash
npx robium-ai app new my-navigation --from robot-navigation
```

Then open that new app with your coding agent and describe one change. Robium
will reuse the proven environment and test shape instead of rebuilding the
whole stack from scratch.

Useful commands:

```bash
npx robium-ai app list              # browse every reference app
npx robium-ai skills nav            # search the skill catalog
npx robium-ai update --check        # check upstream without changing files
npx robium-ai update                # update clean main branches safely
```

## What is included

- Skills for ROS 2, Nav2, Gazebo, MuJoCo, Isaac Sim/Lab, LeRobot, robot data,
  visualization, testing, and deployment.
- An architect that selects a compatible reference app and proves the smallest
  useful robot behavior first.
- Capture and learning tools that turn verified build findings into better
  guidance without requiring raw agent transcripts.
- A zero-dependency CLI for setup, diagnosis, updates, skills, and application
  lifecycle commands.

See the [CLI guide](cli/README.md) for host-specific setup and update behavior,
or [CONTRIBUTING.md](CONTRIBUTING.md) to improve a skill. Questions are welcome
on [Discord](https://robium.ai/join/discord) and in
[GitHub Discussions](https://github.com/robium-ai/robium/discussions).

## License

[MIT](LICENSE)
