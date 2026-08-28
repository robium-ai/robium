# Gemini CLI integration

Robium is a native Gemini CLI extension. Gemini discovers the versioned skills
under `skills/`, the `robium-architect` subagent under `agents/`, and lifecycle
hooks under `hooks/hooks.json` from one installation.
Gemini currently documents custom subagents as a preview feature.

## Install from a checkout

The recommended setup keeps a normal Robium checkout as the live extension
source:

```bash
npx robium-ai setup --agent gemini
gemini extensions list --output-format json
```

The first command runs Gemini CLI's documented local-development flow,
`gemini extensions link <checkout> --consent`. `--consent` acknowledges that
extensions may execute local code. Review `hooks/hooks.json` and
`hooks/scripts/gemini_hook.mjs` before installation if the checkout is not
trusted. Restart Gemini CLI after installing or changing an extension.

To install a copied release instead of a linked checkout:

```bash
gemini extensions install https://github.com/robium-ai/robium --auto-update
```

## Update and remove

For the linked setup, pull and re-run setup so the CLI verifies the extension
and migrates any old Robium-managed skill links:

```bash
npx robium-ai update --agent gemini
npx robium-ai doctor
```

For a copied Gemini installation, use Gemini's native update command:

```bash
gemini extensions update robium
```

Remove Robium without deleting its checkout:

```bash
npx robium-ai remove --agent gemini
# native equivalent for the extension only:
gemini extensions uninstall robium
```

The Robium removal command also removes legacy symlinks or copied skills that
carry Robium's management marker. It does not delete foreign Gemini skills.

## Hooks, permissions, and privacy

Gemini runs extension hooks with the user's local permissions and a sanitized
environment. Robium uses Gemini's `BeforeAgent`, `AfterTool` (matched only to
`run_shell_command`), `SessionStart`, and `SessionEnd` events. Commands resolve
files with Gemini's `${extensionPath}` and `${/}` variables. The adapter uses
Node.js, which Gemini CLI already requires, and invokes `python3`, `python`, or
the Windows `py -3` launcher for the existing standard-library capture logic.

Capture is local, deterministic, and capture-only: it may append scrubbed
signals under the current project's gitignored `.robium/` directory and archive
the transcript path supplied by Gemini. It does not inject memories or call a
model. Session-end is best effort because Gemini does not wait for shutdown
hooks.

Every adapter invocation prints a valid empty JSON object and exits zero. Bad
input, a missing Python interpreter, an unavailable transcript, or a capture
error therefore leaves Gemini's turn and shutdown flow unblocked. Disable the
hooks with Gemini's `/hooks` controls if capture is not desired.

Current contract reference: [Gemini CLI extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md)
and [hooks reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md).
