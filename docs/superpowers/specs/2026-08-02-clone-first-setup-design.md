# Clone-first setup + multi-agent distribution — design

Date: 2026-08-02. Status: approved direction, pending final user review.
Supersedes the v0.3.0 payload-copy behavior (shipped this session) as the
default path; payload-copy remains the fallback.

## Goal

Every developer lands in the robium repo: `npx robium-ai setup` clones it,
wires it into every coding agent on the machine, and keeps everything fresh
via `git pull`. Developing inside the clone needs zero setup. The repo is the
single source of truth for skills across all agents, and the natural surface
for contribution.

## Decisions (user-approved in brainstorm)

1. **Clone-only.** `setup` clones `robium-ai/robium` (tracked content packs
   to ~372 KiB — clones in seconds). The clone is the ONLY source of skills:
   the npm package ships no skill content (drop the v0.3 bundling +
   prepublishOnly step), so npm republish is needed only for CLI code
   changes — skill updates reach users via `git pull` the moment they merge.
   No git on machine -> clear error with the manual-clone instructions
   (no stale-bundle fallback). Git stays a system prerequisite (decided over
   bundling isomorphic-git); all git ops go through the injected-exec seam,
   so a pure-JS git fallback remains a contained swap if ever needed.
2. **One prompt only**: "Where should the robium repo live? [~/robium]" —
   TTY only; `--dir <path>` and `-y` skip it; non-TTY takes the default.
   No agent-picker prompt: auto-detect + `--agent` flag covers it.
3. **Symlinks, not copies**, for the shared install:
   `~/.agents/skills/<name>` -> `<clone>/skills/<name>`. Codex, Gemini CLI,
   Cursor, and OpenCode all read `~/.agents/skills` natively (verified against
   official docs and loader sources). `git pull` and local edits are live
   immediately in all four.
4. **Committed `.agents/skills/` symlink farm in the repo** (relative links
   `../../skills/<name>`). Anyone developing inside the clone gets all skills
   auto-discovered by Codex/Gemini/Cursor/OpenCode/Antigravity at workspace
   scope — zero setup. Deliberately NOT `.claude/skills/` (would duplicate
   the plugin's namespaced skills in Claude Code — `robium:ros2` + `ros2`).
5. **Claude Code**: plugin from the clone — `claude plugin marketplace add
   <clone-path>` + `plugin install robium@robium`. Existing robium
   marketplace (e.g. GitHub-based) is kept, not replaced.
6. **Precedence model** (native to every agent): workspace skills beat user
   skills. Inside the clone the committed farm wins; in a user's own repo the
   user-level symlinks apply; a team repo can override any skill per-project
   with its own `.agents/skills/<name>`.

## CLI v0.4.0 (`cli/`)

Flow of `npx robium-ai setup`:

1. Resolve repo: inside a robium checkout (`.claude-plugin/plugin.json` +
   `skills/`) -> use it. Else `--dir` / prompt / default `~/robium`:
   existing robium clone -> `git pull --ff-only` (skip with warning if dirty
   or diverged); missing -> `git clone`. No git -> exit 1 with the
   manual-clone recipe (no bundled fallback).
2. Detect agents (context7 pattern: cheap existence checks; we keep binary
   probes + `~/.cursor` dir). `--agent <name>` overrides; explicit but
   undetected -> proceed with note.
3. Per-agent install, per-item status strings, one failure never aborts the
   rest (context7's `setupAgent` pattern):
   - claude -> plugin flow from the clone.
   - codex/gemini/cursor/opencode -> ensure `~/.agents/skills/<name>` symlink
     per skill. Ownership rule: replace if it's already a symlink into any
     robium clone or a dir with our `.robium-managed` marker (v0.3 copies);
     skip foreign dirs with a warning. Symlink failure (e.g. Windows without
     symlink rights) -> fall back to copy-from-clone + marker for that skill.
     `--copy` forces copy-from-clone for all skills (still clone-sourced;
     re-run refreshes copies after git pull).
4. Report: repo location, agents configured, "git pull updates everything",
   contribution pointer.

Flags: `--dir <path>`, `--copy`, `--agent <name>`, `-y`. `install` remains an
alias. Structure adopts context7's declarative adapter registry (one config
object per agent; no per-agent modules) and its temp-dir integration-test
style. Zero new runtime deps: `node:readline` for the single prompt.

Out of scope for v0.4 (tracked as GitHub issues, per repo policy):
`robium-ai remove` (mirror of setup, artifact-based detection), rule/pointer
files ("load architect first" hint for non-Claude agents, context7-style),
self-update notice.

## Repo changes

- `.agents/skills/` committed symlink farm (24 relative symlinks). Excluded:
  `_TEMPLATE`. A standalone `scripts/check_agents_farm.py` (repo root — NOT
  under skills/, which is policy-gated) verifies farm == skills/ dirs; wired
  into bootstrap and CI alongside the skill validator; drift = failure.
- Windows note in README (core.symlinks; setup repairs by copying).

## Native per-agent packaging (roadmap, not v0.4)

Research verdict: the plugin concept has spread — these are all real today
and context7 ships all of them from one repo alongside its CLI:

| Target | Vehicle | Carries | Install |
|---|---|---|---|
| Gemini CLI | `gemini-extension.json` at repo root | skills + subagents + hooks + commands | `gemini extensions install <github-url>` (+gallery, auto-update) |
| Codex | `.codex-plugin/plugin.json` | skills + hooks + MCP (no agent defs) | `codex marketplace add robium-ai/robium` + `codex plugin install` |
| Cursor | `.cursor-plugin/plugin.json` | skills + agents + hooks + commands + mcp | reviewed marketplace |
| OpenCode | none needed | reads `.agents/skills` + `.claude/skills` natively | — |

Staging: Gemini extension first (one manifest wrapping existing `skills/`;
only route to deliver robium-architect + capture hooks to Gemini), then Codex
plugin, then Cursor marketplace submission. Each is its own issue; subagent
and hook ports need per-agent format translation and are not blockers for
skills distribution. An MCP server is explicitly NOT planned unless robium
grows a dynamic query surface (context7's lesson: they added skills+CLI mode
because static knowledge triggers better as skills).

## Development workspace & the external learning loop

- **Architect asks the workspace question** at kickoff: "Where should this
  app live — your own repo, or the robium clone's apps/?" Own repo is the
  default (their IP/CI; skills follow via the user-level install); apps/ is
  the contributor path (two-hats rules apply; end-state is a PR). This is an
  architect-skill edit → ships via the skill-update pipeline (archive +
  version bump), NOT part of the v0.4 CLI build.
- **External loop** (users working outside the repo):
  1. Capture hooks ship with the user-scoped plugin → fire in any project;
     learnings land project-local.
  2. First beneficiary: their own/team skills (skill-author → project
     `.agents/skills/`, which override robium's per-project).
  3. Upstream: the guaranteed `~/robium` clone makes "contribute back"
     concrete — sanitized, robium-relevant learnings flow into the clone's
     learnings/, then the normal consolidate→absorb pipeline → PR from their
     fork. Human merge gate unchanged.
- Learning-loop skill guidance for step 3 is a follow-on skill edit (same
  pipeline); v0.4 only documents the path (README + site copy).

## Website (`website/`) + README

- **Get started section placement: directly after ValueProps (Why robium).**
- **Two setup paths, both visible, short and neat:**
  - Path A — "Quick": `npx robium-ai setup` (one command, auto-detects).
  - Path B — "Clone + manual": `git clone` then the per-agent manual step.
- **Per-agent card click shows BOTH paths for that agent** (compact, 2 lines
  each): e.g. claude → A: `npx robium-ai setup --agent claude`; B:
  `git clone … && claude plugin marketplace add ~/robium && claude plugin
  install robium@robium`. codex/gemini/cursor/opencode → A: `--agent <x>`;
  B: clone + `ln -s ~/robium/skills/* ~/.agents/skills/` (plus the "or just
  work inside the clone — auto-discovered" note).
- **Hero install button** (`npx robium-ai setup` primary button) becomes an
  in-page anchor to #install instead of linking to GitHub.
- Root README gets the same two-path structure ("Manual install (no npm)")
  plus the workspace guidance one-liner: "your app lives in your repo —
  robium lives beside it."
- Deploy gate unchanged: publish CLI v0.4.0 to npm before deploying copy
  that describes clone behavior.

## Testing

- CLI: temp-dir integration tests per scenario — fresh clone (mock git via
  injected exec), existing clone pull, dirty clone skip, in-repo detection,
  symlink install, foreign-dir skip, v0.3 copy upgrade to symlink, no-git
  fallback, `--copy`, non-TTY defaults. Target: keep 100% pass in `node --test`.
- Repo: farm-sync check wired into the skill validator run.
- Site: `make smoke` assertions updated with the section move + new copy.
