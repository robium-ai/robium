# Standard App Lifecycle Commands Design

## Goal

Give every Robium reference app one predictable human-facing lifecycle
vocabulary through both Make and the `robium app` CLI:

```text
help doctor build run status logs stop
```

Indoor navigation is the first app migrated to the contract.

## Command semantics

| Verb | Behavior |
|---|---|
| `help` | Show available lifecycle commands, descriptions, examples, and the equivalent Make/CLI spelling. |
| `doctor` | Diagnose prerequisites, runtime availability, port conflicts, and build readiness without changing app state. |
| `build` | Build the app's local runtime artifacts. |
| `run` | Run the app's primary local experience in the foreground. |
| `status` | Report whether app services are running and print useful endpoints. |
| `logs` | Follow runtime/process logs until interrupted without stopping the app. |
| `stop` | Stop all runtime services owned by the app. |

For indoor navigation, `run` means the current interactive dashboard flow:
Gazebo, TurtleBot3, foxglove_bridge, Lichtblick, and Robot Control start with
the navigation session in IDLE. Mapping or localization begins from the panel.

## Architecture

Make remains the app-local execution layer and owns Docker Compose and ROS 2
commands. `robium-app.yaml` maps standard verbs to Make commands and supplies a
short summary. The generic CLI reads this metadata, prints help, and executes
the declared command in the app directory. It must not duplicate app-specific
Docker or ROS logic.

Verb metadata accepts either the existing command string or a richer object:

```yaml
verbs:
  run:
    command: make run
    summary: Start the simulator and interactive control panel
```

Supporting strings preserves compatibility with apps that have not migrated.
Indoor navigation uses objects for all standard verbs so its CLI help can show
descriptions and exact Make equivalents.

## Naming and compatibility

Indoor navigation removes `make mapping`, `make down`, and `make check`. There
are no aliases for the old names. The replacements are `make run`, `make stop`,
and `make doctor`.

Mode-specific commands such as `sim` and `demo` remain available as advanced
modes. The CLI runs them through `robium app run indoor-navigation --mode
<name>`.

## Help output

`make help` and `robium app help indoor-navigation` show the same seven verbs.
CLI help includes both spellings so users can move between interfaces without
learning a second vocabulary.

## Verification constraint

Do not add, update, or run automated tests for this prototype work. Review the
changed command mappings and source diffs only, following the user's explicit
development preference.
