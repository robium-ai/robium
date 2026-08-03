# Project notes

Durable robium facts that aren't obvious from the code — accounts, publishing,
and project lineage. (Consolidated 2026-07-31 from scattered assistant-memory
notes into the repo, corrected for the monorepo.)

## Community accounts

- **Hugging Face org:** `robium` → https://huggingface.co/robium (verified live 2026-07-18).
- **Discord:** "Robium" — invite https://discord.gg/cyd8xC6W6 (verified via Discord API 2026-07-20).
  - ⚠️ **This invite expires 2026-08-19** (not created "Never expire"). Get a permanent
    invite before launch and swap it in `website/src/components/Nav.astro` +
    `website/src/components/Footer.astro` and here.
  - The `discord.gg/robium` vanity is invalid until the server reaches boost level 3.
- Both appear in the site footer (HF 2026-07-18, Discord 2026-07-20; Discord also a Nav icon).

## CLI / npm publishing (`cli/`)

- Published to npm as **`robium-ai`** (bin name `robium`); first release 0.1.0 on 2026-07-18.
  Commands: `install` (Claude-first, drives the non-interactive `claude plugin` CLI),
  `doctor [--json]`, `skills [query]`.
- npm's similarity policy **permanently blocks the bare name `robium`** ("too similar to
  radium"); `robium-cli` / `create-robium` are equally at risk (`radium-cli` / `create-radium`
  exist). The `@robium/*` scope is owned as a fallback (npm account `robium`).
- `cli/src/catalog.json` is generated from the plugin at the **monorepo root** by
  `cli/scripts/build-catalog.mjs` — regenerate before every publish (see `cli/README.md`).
- Publishing needs **2FA**: interactive `npm publish` (browser flow) or a granular token with
  "Bypass 2FA" + read-write. The token lives in **Doppler** as `NPM_TOKEN` — see
  `docs/secrets.md` (`cd cli && doppler run -- npm publish`).
- **Git pushes to the `robium-ai` org must use SSH remotes.** The HTTPS keychain credential
  on this machine is a different account (`robiumhub`) without org access.

## Git & GitHub accounts

- **Commit as `robium-admin`.** This repo's git identity is set to
  `robium-admin <306426232+robium-admin@users.noreply.github.com>`. Author
  everything as `robium-admin`.
- **Issue tooling** uses the `robium-admin` fine-grained PAT in Doppler
  (`GITHUB_TOKEN`). It needs **Issues: Read and write** (plus Contents) — and
  use the **REST** API (`gh api`), not `gh issue`'s GraphQL path, which this
  fine-grained token doesn't resolve.

## Project lineage

- **robium** is a restart (July 2026) of an earlier robotics dev platform built ~2024–2025.
  Full legacy knowledge base is in `docs/legacy-memory/` (history, original vision, final
  state, architecture, robotics domain model, lessons) — read there before answering
  questions about the old project.
- **V2 direction** (decided 2026-07-08) is in `docs/V2_VISION.md`: an AI-agent-first robotics
  dev toolchain — curation/glue over the open-source robotics ecosystem is the moat, no
  algorithm development. The plugin + reference apps in this monorepo are that toolchain.
