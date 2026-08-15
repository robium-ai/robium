# robium CLI

CLI for [robium](https://robium.ai), the robotics skill pack for coding agents:
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

# Work with reference applications (robium-app.yaml contract)
npx robium-ai app list                        # catalog of apps in the apps repo
npx robium-ai app describe indoor-navigation  # one app's metadata (JSON)
npx robium-ai app help indoor-navigation      # commands + equivalent Make targets
npx robium-ai app doctor indoor-navigation    # environment + app diagnosis
npx robium-ai app build indoor-navigation     # build application artifacts
npx robium-ai app run indoor-navigation       # primary local experience
npx robium-ai app status indoor-navigation    # running state and endpoints
npx robium-ai app logs indoor-navigation      # follow process logs
npx robium-ai app stop indoor-navigation      # stop application services
npx robium-ai app run indoor-navigation --scenario demo
npx robium-ai app validate --json               # schema-check every app (CI)
npx robium-ai app new my-app --from indoor-navigation   # scaffold by copy
```

`app` commands find the apps repo via `--dir <path>`, else `$ROBIUM_APPS_DIR`,
else by walking up from the current directory to the first repo containing
`REGISTRY.md` plus `robium-app.yaml` files. They exec each app's declared
commands (usually Make targets); nothing app-specific is reimplemented in the
CLI. A verb may be a command string or a `command`/`summary` object; the latter
lets `app help` display both the CLI spelling and Make equivalent. See the
reference-apps spec: `docs/superpowers/specs/2026-08-05-reference-applications-design.md`.

## How setup works

**The repo is the source of truth.** `setup` clones
`github.com/robium-ai/robium` (default `~/robium`; one prompt, Enter accepts),
or uses the checkout you're already inside, then wires it in per agent:

- **Claude Code**: the full plugin (skills + the robium-architect agent +
  capture hooks) via `claude plugin marketplace add <clone>` +
  `claude plugin install robium@robium`. Served from the clone.
- **Codex**: the native plugin (skills + capture hooks) via
  `codex plugin marketplace add <clone>` + `codex plugin add robium@robium`.
  Review and trust the bundled hooks with `/hooks` before expecting capture.
- **Gemini CLI and Cursor**: each skill is symlinked from the clone into the
  agent's native user skill directory (`~/.gemini/skills` or
  `~/.cursor/skills`).

`git pull` updates symlink-based installs immediately. Native plugin hosts use
an installed cache, so re-run `setup` after pulling and start a new session.
The npm package carries no skill content, so skill releases never wait on an
npm publish. Re-running `setup` refreshes the clone, reinstalls native plugins,
and repairs links; it never overwrites a
same-named skill it doesn't own. Run `setup` before working inside a clone so
Codex uses the plugin as the single source of Robium skills and hooks; keeping a
second repo-scoped `.agents/skills/` copy would register every skill twice.

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
