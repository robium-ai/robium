# robium CLI (npx package) — design

Date: 2026-07-18. Approved in-session (brainstormed in robium-plugin, built here).

## Purpose

Claim the `robium` npm name and give the website a one-command onboarding path
that works from a plain shell, plus the first genuinely robotics-flavored
utility (`doctor`). Fills the "A robium CLI" backlog item (robium-plugin
`docs/BACKLOG.md`, Later) at Claude-first scope.

## Decisions

- **Package**: npm name `robium-ai`, bin `robium`, v0.1.0. New sibling repo
  `robium-ai/robium-cli` — keeps the plugin repo JS-free. The bare name
  `robium` was unregistered but npm's similarity policy rejected it at publish
  time ("too similar to existing package radium"); `robium-cli` was ruled out
  for the same reason (`radium-cli` exists). `robium-ai` matches the domain
  and GitHub org; fallback if ever needed: `@robium/cli` (the npm account is
  `robium`, so the scope is owned).
- **Stack**: plain ESM JavaScript, Node ≥18, zero runtime dependencies, no
  build step. `node:test` for tests.
- **v1 scope**: Claude-first. `install` fully automates the Claude Code path
  via the documented non-interactive CLI (`claude plugin marketplace add`,
  `claude plugin install --scope user`, verified with
  `claude plugin list --json`). `--agent cursor|gemini` prints an honest
  coming-soon, mirroring the website tabs. Cursor/Gemini manifest generation
  stays in the robium-plugin backlog ("public release machinery").
- **Commands**:
  - `install [--agent claude|cursor|gemini]` — detect `claude --version`;
    add marketplace `robium-ai/robium-plugin` (fall back to
    `marketplace update robium` if it already exists); install
    `robium@robium`; verify; print a "try this" next step.
  - `doctor [--json]` — fast read-only checks, statuses
    pass/warn/fail/info/skip, exit 1 only on fail: platform (Apple
    Silicon/MPS, Linux DISPLAY), Claude Code, robium plugin, Docker CLI +
    daemon, disk space (warn <20 GB), GPU (nvidia-smi / MPS), python3 + uv,
    native ros2 (informational only). `--json` is the future hook for skills
    to consume — wiring that into skills is a separate, user-gated change.
  - `skills [query]` — list name/version/first-sentence from
    `src/catalog.json`.
- **Catalog**: `src/catalog.json` generated at publish time by
  `scripts/build-catalog.mjs` from the sibling robium-plugin checkout
  (frontmatter parser handles plain + folded scalars). Committed; no runtime
  network calls. Drift window = publish-to-publish, acceptable for a listing.
- **Testing**: unit tests for the frontmatter/catalog builder (fixtures),
  doctor and install logic (injected fake exec), CLI dispatch smoke tests
  (spawned subprocess).

## Out of scope (follow-ups)

Cursor/Gemini generation; app scaffolder (`create`); demo launcher; website
AgentTabs update to advertise `npx robium install` (robium-website edit after
the package is live); any skill-file mention of `robium doctor` (gated by the
skill-update policy).
