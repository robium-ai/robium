# Editable workspace and updates

Setup creates a user-chosen parent directory containing two ordinary Git
checkouts: `robium/` (skills/plugin source) and `robium-apps/` (reference apps).
The parent is not a Git repository. Do not assume its name or location.

## Find the existing source

Run `npx robium-ai workspace --json` to obtain `root`, `repo`, and `apps`.
Resolution is an explicit `--dir <workspace>`, an enclosing two-repository
workspace, then the root remembered in `~/.config/robium/workspace.json`.
`setup --dir <workspace>` selects and remembers a location; subsequent setup
reuses the checkouts without pulling them. A missing or invalid saved location
is a reason to ask where the user moved it, not to clone over it or guess.

Use `<apps>/REGISTRY.md` and the owning app's README for reference selection.
`npx robium-ai app list --json` discovers the local apps from outside the
workspace too. An explicit `app --dir` targets the apps repository itself;
setup/update `--dir` targets its parent. Honor an explicitly selected app
checkout or `ROBIUM_APPS_DIR` instead of silently using another workspace.

## Check quietly; update intentionally

Before starting a new reference example, optionally run
`npx robium-ai update --check --quiet`. Do not do this on every prompt, during
a running experiment, or as a prerequisite to unrelated maintenance. The CLI
limits these network checks to once per 24 hours per workspace, stays silent
when current/offline, and offers one combined notice no more than weekly and
never repeats the same known revisions. `ROBIUM_UPDATE_CHECKS=0` disables quiet
checks. There is no background daemon or required scheduling.

If the check prints nothing, continue without mentioning it. If it reports an
update, give at most one short non-blocking note at a natural stopping point;
do not pause the task or repeatedly ask. Follow a user's preference not to hear
about updates. A newer commit alone is not evidence of a relevant fix or a
security issue. Do not check unrelated third-party skill repositories.

When asked whether Robium is current, use `npx robium-ai update --check --json`
for a fresh comparison with both official `main` branches. Report `unknown`
honestly on network/repository errors. A check fetches a comparison ref; it
does not modify working files, the current branch, or dependencies.

When the user asks to update, run `npx robium-ai update`. Only clean `main`
branches with no local-only commits are fast-forwarded from official Robium
upstream, even if `origin` is the user's fork. Personal branches, dirty files,
detached HEADs, and divergent history are left alone with a reason. Do not
stash, reset, switch branches, rebase, or merge a personal branch without
separate direction. A partial update is not success for both repos.

Users can also fetch/pull manually after reviewing branch and remote state.
After a manual source update or personal edit, `npx robium-ai setup` reconnects
host integrations without pulling the repos. Follow its host-specific restart
instructions. Cached plugin activation is distinct from Git freshness; do not
claim an agent has loaded edited skills based only on an unchanged version
number. Never edit the installed cache as the user's source of truth.

Develop on a branch in either checkout, test there, and optionally fork and
open a PR later. Contribution is opt-in; never push local work automatically.
