# robium CLI

CLI for [robium](https://robium.ai) — the robotics skill pack for coding agents:
ROS 2, Nav2, Gazebo, LeRobot, Isaac Sim/Lab, visualization, data, and testing
skills for Claude Code, Codex, Gemini CLI, and Cursor.

## Usage

```bash
# Clone the robium repo and wire it into every coding agent on your machine
npx robium-ai setup

# Target one agent / control the clone location / no prompts
npx robium-ai setup --agent codex      # claude | codex | gemini | cursor
npx robium-ai setup --dir ~/src/robium
npx robium-ai setup -y                 # accept defaults (CI / agent-driven)
npx robium-ai setup --copy             # copy skills from the repo instead of symlinking

# `install` is an alias for `setup`
npx robium-ai install

# Check your machine for robotics work (Docker, GPU, disk, Python/uv, …)
npx robium-ai doctor          # human-readable
npx robium-ai doctor --json   # machine-readable (for agents/scripts)

# Browse the skill catalog
npx robium-ai skills          # all skills
npx robium-ai skills nav      # filter
```

## How setup works

**The repo is the source of truth.** `setup` clones
`github.com/robium-ai/robium` (default `~/robium`; one prompt, Enter accepts)
— or uses the checkout you're already inside — then wires it in per agent:

- **Claude Code** — the full plugin (skills + the robium-architect agent +
  capture hooks) via `claude plugin marketplace add <clone>` +
  `claude plugin install robium@robium`. Served from the clone.
- **Codex, Gemini CLI, and Cursor** — each skill is **symlinked** into
  the shared [Agent Skills](https://agentskills.io) directory
  `~/.agents/skills/`, which all three discover automatically. No registration.

`git pull` in the clone updates every agent at once — the npm package carries
no skill content, so skill releases never wait on an npm publish. Re-running
`setup` refreshes the clone and repairs links; it never overwrites a
same-named skill it doesn't own. Working *inside* the clone needs no setup at
all for Codex/Gemini/Cursor — the repo ships a committed
`.agents/skills/` farm they discover at workspace scope.

Requires `git` (setup prints the manual recipe if missing).

## Development

Plain ESM Node (≥18), zero runtime dependencies, no build step.

This package lives in the [robium](https://github.com/robium-ai/robium)
monorepo under `cli/`. Run these from the `cli/` directory:

```bash
npm test                 # node:test suite
npm run build:catalog    # regenerate src/catalog.json from the repo root (the plugin)
```

`src/catalog.json` is generated from the robium plugin at the monorepo root
and committed; `prepublishOnly` regenerates it.

## Release checklist

Run from the `cli/` directory:

1. `npm test`
2. Bump `version` in package.json, commit, tag `cli-vX.Y.Z`
3. `npm publish`

## License

MIT
