# App Mode Naming Design

## Goal

Use **mode** consistently for named ways an app can run. Remove **scenario**
from the public Robium CLI and `robium-app.yaml` contract before the new app
commands are published.

## Interface

The CLI accepts only `--mode`:

```bash
robium app run indoor-navigation --mode sim
robium app run indoor-navigation --mode slam
robium app run indoor-navigation --mode nav
robium app run indoor-navigation --mode demo
```

There is no `--scenario` alias. Unknown modes report the valid modes declared
by that app. Flags named `--mode` are valid only with `app run`.

## Manifest contract

Every app manifest renames `scenarios:` to `modes:`. Hosted-demo metadata
renames `default_scenario:` to `default_mode:`. Each mode retains its existing
`command` and `summary`; no underlying Make target or runtime behavior changes.

The validator accepts only the new keys and reports errors using mode
terminology. Scaffolding guidance tells authors to rewrite modes as a new app
diverges.

## Help and documentation

Per-app help labels the section **Modes** and prints `--mode`. CLI README
examples use the new flag. Historical engineering prose may continue to use
the ordinary English word “scenario”; this change targets the command and
manifest vocabulary only.

## Verification constraint

Do not add, update, or run automated tests. Review the changed CLI, manifest,
and documentation diffs only, following the user's prototype-development
preference.
