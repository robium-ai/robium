# robium CLI

CLI for [robium](https://robium.ai), the robotics skill pack for coding agents:
ROS 2, Nav2, Gazebo, LeRobot, Isaac Sim/Lab, visualization, data, and testing
skills for Claude Code, Codex, Gemini CLI, and Cursor.

## Usage

```bash
# Clone both repositories and connect the plugin to your detected agents
npx robium-ai setup

# Target one agent / choose the workspace parent / no prompts
npx robium-ai setup --agent codex      # claude | codex | gemini | cursor
npx robium-ai setup --dir ~/src/robium
npx robium-ai setup -y                 # accept defaults (CI / agent-driven)
npx robium-ai setup --copy             # copy integration files instead of symlinking

# Discover paths, check upstream, or apply safe updates to both repositories
npx robium-ai workspace --json
npx robium-ai update --check
npx robium-ai update

# `install` is an alias for `setup`
npx robium-ai install

# Remove managed integrations but preserve the Robium checkout
npx robium-ai remove
npx robium-ai remove --agent cursor

# Check your machine and Robium integration state
npx robium-ai doctor          # human-readable
npx robium-ai doctor --json   # machine-readable (for agents/scripts)

# Browse the skill catalog
npx robium-ai skills          # all skills
npx robium-ai skills nav      # filter

# Work with reference applications (robium-app.yaml contract)
npx robium-ai app list                        # catalog of apps in the apps repo
npx robium-ai app describe robot-navigation  # one app's metadata (JSON)
npx robium-ai app help robot-navigation      # commands + equivalent local commands
npx robium-ai app doctor robot-navigation    # environment + app diagnosis
npx robium-ai app build robot-navigation     # build application artifacts
npx robium-ai app run robot-navigation       # primary local experience
npx robium-ai app status robot-navigation    # running state and endpoints
npx robium-ai app logs robot-navigation      # follow process logs
npx robium-ai app stop robot-navigation      # stop application services
npx robium-ai app run robot-navigation --mode demo
npx robium-ai app validate --json               # schema-check every app (CI)
npx robium-ai app new my-app --from robot-navigation   # scaffold by copy
```

`app` commands find the apps repo via `--dir <path>`, else `$ROBIUM_APPS_DIR`,
else by walking up from the current directory to the first repo containing
`REGISTRY.md` plus `robium-app.yaml` files, then `robium-apps/` in the current
or remembered workspace. They exec each app's declared
commands (usually Make targets); nothing app-specific is reimplemented in the
CLI. A verb may be a command string or a `command`/`summary` object; the latter
lets `app help` display both the CLI spelling and Make equivalent. See the
reference-apps spec: `docs/superpowers/specs/2026-08-05-reference-applications-design.md`.

## How setup works

**Git is the source of truth.** Setup asks for a workspace parent (default
`~/robium`; Enter accepts). Choose any name/location with
`npx robium-ai setup --dir ~/projects/my-robotics`. It clones both official
repositories on `main`, without building apps or downloading model assets:

```text
~/projects/my-robotics/   # not a Git repository
├── robium/              # editable skills, plugin, CLI source
└── robium-apps/         # runnable reference examples
```

The root is remembered in `~/.config/robium/workspace.json`. Run
`npx robium-ai workspace --json` to discover the paths. Explicit `--dir` wins,
then an enclosing workspace, then the saved default. For setup and update,
`--dir` means the parent; for app commands it means the apps repository.
Setup reuses existing checkouts unchanged and wires `robium/` in per agent:

- **Claude Code**: the full plugin (skills + the robium-architect agent +
  capture hooks) via `claude plugin marketplace add <clone>` +
  `claude plugin install robium@robium`. Served from the clone.
- **Codex**: the native plugin (skills + capture hooks) via
  `codex plugin marketplace add <clone>` + `codex plugin add robium@robium`.
  Review and trust the bundled hooks with `/hooks` before expecting capture.
- **Gemini CLI**: the checkout is linked as a native extension with
  `gemini extensions link <clone> --consent`. Gemini auto-loads the skills,
  architect subagent, and capture hooks from the extension. Setup removes only
  legacy Robium-managed skill links; foreign skills are preserved.
- **Cursor**: the checkout is linked as a native Cursor Plugin at
  `~/.cursor/plugins/local/robium`. Cursor auto-loads the complete skill
  catalog, architect agent, and Cursor-native capture hooks. Setup removes only
  legacy Robium-managed skill links; foreign skills and plugins are preserved.

### Check and update on demand

```bash
npx robium-ai workspace                  # where both repositories live
npx robium-ai update --check             # fresh check, no working-file changes
npx robium-ai update --check --json      # paths, revisions, branches, status
npx robium-ai update                     # safe updates, then refresh integrations
```

Update fetches **official Robium main**, not a personal fork's main. Only clean
`main` branches without local-only commits are fast-forwarded. Dirty files,
personal branches, detached HEADs, and divergent history are left untouched
with a reason; partial updates return a nonzero exit status. Forks should retain
the official repo as an `upstream` remote. Nothing is pushed, reset, stashed,
automatically rebased, or installed into the apps' environments.

Human-readable `app list` may check quietly before listing. Agents may also use
`update --check --quiet` before a new example: at most daily network checks,
at most weekly combined notices, no repeat notice for the same revisions.
Current/offline results stay silent and do not prevent app listing. Set
`ROBIUM_UPDATE_CHECKS=0` to disable opportunistic checks. Explicit checks still
work and report network errors as unknown, not current. There is no daemon,
background scheduler, or automatic source update.

Manual Git updates are supported. After pulling or editing source, re-run
`setup` to refresh integrations **without pulling either checkout**. Restart
the host as instructed. Source freshness and cached-plugin activation are
separate: a matching version alone does not prove a local skill edit is active.
Edit the source, never the installed cache or installer-managed copies.

The npm package carries no skill content. Run `setup` before working inside a clone so
Codex uses the plugin as the single source of Robium skills and hooks; keeping a
second repo-scoped `.agents/skills/` copy would register every skill twice.

Requires `git` (setup prints the manual recipe if missing).

Codex Desktop on macOS is supported even when its bundled CLI is not on shell
`PATH`; setup and doctor probe the application bundle directly.

After setup, Robium asks each host whether the integration is active when the
host exposes a supported status command. Claude Code and Codex report native
plugin state and installed version; Gemini reports native extension state.
Cursor currently exposes no local-plugin activation-status API, so setup
reports the limitation and asks for a window reload and Customize check instead
of claiming the plugin is active. `doctor` uses the same local probes to
distinguish missing, inactive, active, obviously outdated, and
activation-unknown installations. Its refresh guidance names the session or
task that must be restarted.

`npx robium-ai remove` reverses setup without deleting the repository checkout.
Claude Code and Codex use their native plugin and marketplace removal commands.
Gemini CLI uses `gemini extensions uninstall robium` and also cleans up legacy
Robium-managed skill links. Cursor removes only the Robium-managed local plugin
link or marked copy plus legacy managed skill links. Unrelated plugins, skills,
and files are preserved. Repeated removal is a successful no-op.

### Install one skill

The full setup is optional. Agent Skills users can install and update one
skill through the cross-agent Skills CLI:

```bash
npx skills add robium-ai/robium -g --skill navigation --agent codex
npx skills update -g
```

That is an installed skill snapshot. `npx robium-ai setup`, by contrast,
keeps a real Git checkout that can be used directly for contributions.

## Development

Plain ESM Node (≥18), zero runtime dependencies, no build step.

When `setup` created `~/robium`, contributors can work in its checkout rather
than cloning again:

```bash
cd ~/robium/robium               # or the repo path from robium workspace
./scripts/bootstrap.sh
git switch -c my-skill-fix
# edit, then verify
./scripts/check.sh
```

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
