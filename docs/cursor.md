# Cursor client

Robium is a native Cursor Plugin. Cursor loads the complete skill catalog, the
`robium-architect` custom agent, and fail-open learning-capture hooks from one
`.cursor-plugin/plugin.json` manifest.

## Local install

From a Robium checkout, run:

```bash
npx robium-ai setup --agent cursor
```

Setup follows Cursor's documented local-development layout by linking the
checkout to `~/.cursor/plugins/local/robium`. Reload Cursor with
**Developer: Reload Window**, open **Customize**, and confirm that Robium's
skills, agent, and hooks are listed. Cursor does not currently expose a
supported command-line API for checking local-plugin activation, so
`npx robium-ai doctor` verifies the manifest and version on disk and reports
activation as unavailable rather than claiming it is active.

Use `--copy` when symlinks are undesirable. That mode copies only the files the
plugin needs and marks the copy as Robium-managed. `npx robium-ai update
--agent cursor` refreshes either form. Setup also removes legacy Robium-managed
entries from `~/.cursor/skills`; it preserves foreign skills and any foreign
plugin occupying the local `robium` path.

Remove the integration without deleting the checkout:

```bash
npx robium-ai remove --agent cursor
```

## Hook behavior and permissions

Cursor plugins and OpenAI Codex plugins use a similar component model, but
their hook contracts are not interchangeable. Robium therefore selects
`hooks/cursor-hooks.json` explicitly instead of letting Cursor discover the
multi-host `hooks/hooks.json` file.

| Cursor event | Robium capture behavior |
| --- | --- |
| `beforeSubmitPrompt` | Detect short correction signals; always returns `{"continue": true}` |
| `afterShellExecution` | Capture error-bearing shell commands |
| `sessionStart` | Initialize the project-local `.robium/` evidence directory |
| `sessionEnd` | Archive an available Cursor transcript and clean session deduplication state |

Hooks receive prompt text, command output, workspace paths, and—when Cursor
provides it—a transcript path. They write only to `.robium/` in the open
project, scrub likely secrets before queueing excerpts, emit no recalled
context, and fail open if Node, Python, or transcript data is unavailable.
Cursor asks users to trust a workspace before project automation runs; local
plugin imports may also be disabled by team policy. On Enterprise, **Allow
Local Plugin Imports** is off by default. `sessionStart` and `sessionEnd` do not
run in Cursor Cloud Agents; Cursor lists the prompt and shell hook types as
Cloud Agent-compatible.

## Marketplace readiness

This repository is a single Cursor plugin, so it intentionally uses only the
root `.cursor-plugin/plugin.json`; Cursor's official template says a
single-plugin repository should not retain a multi-plugin
`.cursor-plugin/marketplace.json`. The manifest has marketplace metadata,
explicit relative component paths, valid skill/agent frontmatter, and a
repository-owned logo.

Marketplace publication is a separate maintainer action. Cursor requires the
repository to be public, manually reviews plugins and every update, and accepts
submissions at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).
Until approval, the local install above is the supported test path. A
Marketplace installation with the same plugin name takes precedence over a
local copy.

Official references: [plugins guide](https://cursor.com/docs/plugins),
[plugin format](https://cursor.com/docs/reference/plugins), and
[hooks contract](https://cursor.com/docs/hooks).
