# Secrets & env vars

> **You do NOT need any secrets to develop robium.** Authoring skills, running the
> validator, and building the apps/site locally require none. Secrets are
> **maintainer/operator-only** — publishing the `robium-ai` CLI, deploying the
> site, and RunPod/NGC/GCP work. Contributors: just `git clone` +
> `./scripts/bootstrap.sh` (it skips secrets) and ignore the rest of this doc.

Maintainer secrets are managed centrally in **Doppler** — never committed to git,
never copy-pasted between machines. Project `robium`, config `dev` (per-project
namespace; add more projects like `dervish`/`personal` later).

`doppler.yaml` at the repo root pins the project/config; `.env.template` lists
the expected variable **names** (no values).

## Using secrets

Two supported sources — use whichever a machine has:

- **Doppler** (recommended, central, cross-machine) — `doppler run -- <command>`.
- **Local `.env`** (simple, single-machine) — a gitignored file at the repo root.

To avoid hard-coding either, `scripts/run.sh` **auto-detects** the source
(Doppler if configured, else `.env`, else nothing) and injects secrets:

```bash
./scripts/run.sh <command>
./scripts/run.sh npm --prefix cli publish
./scripts/run.sh make -C website deploy
```

Direct forms also work if you prefer:

```bash
# Doppler
cd cli && doppler run -- npm publish
# .env (gitignored) — for a machine without Doppler
set -a && . ./.env && set +a && cd cli && npm publish
```

Populate a `.env` (only if you're not using Doppler interactively):

```bash
doppler secrets download --no-file --format env > .env   # from Doppler, or
cp .env.template .env                                    # then fill in by hand
```

> Note: `GCP_SA_KEY` is multi-line JSON — it lives cleanly in Doppler but is
> awkward in a hand-edited `.env`. If you go the `.env` route and need GCP, keep
> that one in Doppler (or store it base64-encoded on a single line).

## Onboarding a new machine (maintainer, with secrets)

Clone the repo, then run bootstrap. It's **secret-free by default** (see the
Development note at the top — that's all contributors need). To also wire the
maintainer secrets, opt in with `--secrets`, or set `DOPPLER_TOKEN` (which
auto-enables it):

**Laptop** (browser):
```bash
git clone git@github.com:robium-ai/robium.git && cd robium
doppler login                 # once
./scripts/bootstrap.sh --secrets
```

**Server / CI** (no browser — the token auto-enables secrets):
```bash
export DOPPLER_TOKEN=dp.st.dev.xxxxx
git clone https://github.com/robium-ai/robium.git && cd robium
./scripts/bootstrap.sh
```

Bootstrap installs uv + npm deps and, when secrets are enabled, installs the
Doppler CLI, binds `robium/dev`, and verifies secrets are reachable. Then run
privileged tasks with `doppler run -- <command>`.

**Manual equivalent** of the secrets part: install the Doppler CLI
(`brew install dopplerhq/cli/doppler` or `curl -Ls https://cli.doppler.com/install.sh | sh`),
authenticate as above, `doppler setup` (reads `doppler.yaml`), then `doppler run --`.

### Headless server / CI — no interactive login

There's no browser on a server, so instead of `doppler login` use a **service
token** as the single seed secret. It's scoped to `robium/dev`, so `doppler run`
works directly — no `login`, no `setup`.

1. **Create the token** in the dashboard (so it never lands in a shell history):
   dashboard.doppler.com → `robium` → `dev` → **Access → Service Tokens →
   Generate**, read-only. Copy the `dp.st.dev.…` value.
   (CLI equivalent: `doppler configs tokens create ci --project robium --config dev --plain`.)
2. **Give it to the server as `DOPPLER_TOKEN`** via your platform's env/secret:
   - systemd: `Environment=DOPPLER_TOKEN=dp.st.dev.…` (or `EnvironmentFile=`)
   - Docker: `docker run -e DOPPLER_TOKEN=dp.st.dev.… …`
   - Cloud Run: `--set-env-vars DOPPLER_TOKEN=…` (or a mounted secret)
   - GitHub Actions: repo secret → `env: DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}`
3. **Everything else flows from it** — even a private clone uses the GitHub token
   stored in Doppler, so `DOPPLER_TOKEN` stays the *only* thing you provision:

   ```bash
   export DOPPLER_TOKEN=dp.st.dev.xxxxx            # the one seed (from your host's secret store)
   curl -Ls https://cli.doppler.com/install.sh | sh
   doppler run -- git clone https://x-access-token:$GITHUB_TOKEN@github.com/robium-ai/robium.git
   cd robium && ./scripts/bootstrap.sh             # detects DOPPLER_TOKEN, skips interactive login
   doppler run -- <do work>                        # all keys present, fully non-interactive
   ```

Rotate or revoke a service token anytime in the dashboard — it's independent of
your personal login, so a compromised server token never touches your account.

## Adding / rotating a secret

```bash
doppler secrets set RUNPOD_API_KEY   # prompts (value not echoed), or:
doppler secrets set RUNPOD_API_KEY="$(pbpaste)"
```

Then add its name to `.env.template` so the expected set stays documented.

## npm publishing

`cli/.npmrc` (committed, no secret) authenticates via `${NPM_TOKEN}`, so publish
under Doppler:

```bash
cd cli && doppler run -- npm publish
```

The plaintext token was removed from `~/.npmrc` — publishing now only works under
`doppler run`. (`npm whoami` returns 401 with this granular publish token; that's
expected and doesn't affect publishing.) HuggingFace tools pick up `HF_TOKEN` from
the Doppler-injected env automatically (the `~/.cache/huggingface/token` file was
removed too) — run HF commands under `doppler run --`.

## Per-service usage

All of these run under `doppler run --`, so a fresh machine needs only the
Doppler CLI + `doppler login` (or a service token) — no per-tool login.

- **HuggingFace** (`HF_TOKEN`) — `huggingface_hub` reads it from the env
  automatically: `doppler run -- <hf command>`.
- **RunPod** (`RUNPOD_API_KEY`) — read from the env by your provisioning
  scripts: `doppler run -- <runpod script>`.
- **NGC / nvcr.io** (`NGC_API_KEY`) — docker login uses the literal user
  `$oauthtoken` + this key:
  `doppler run -- sh -c 'echo "$NGC_API_KEY" | docker login nvcr.io -u \$oauthtoken --password-stdin'`
  (for RunPod pods the key goes into the pod's `containerRegistryAuth` — see the
  isaac-lab skill).
- **GitHub** (`GITHUB_TOKEN`, fine-grained PAT, robium-ai org) — for git/gh over
  HTTPS on any machine without SSH keys:
  `doppler run -- gh auth login --with-token <<< "$GITHUB_TOKEN"`, or for a git
  push: `doppler run -- sh -c 'git push https://x-access-token:$GITHUB_TOKEN@github.com/robium-ai/robium.git'`.
- **GCP** (`GCP_SA_KEY`, service account `robium-deployer@robium-prod`) — the key
  is JSON in one env var; materialize it to a temp file and point
  `GOOGLE_APPLICATION_CREDENTIALS` at it. To deploy the site with **zero
  `gcloud login`**:

  ```bash
  cd website
  doppler run -- bash -lc '
    f="$(mktemp)"; printf "%s" "$GCP_SA_KEY" > "$f"
    gcloud auth activate-service-account --key-file="$f" --quiet
    export GOOGLE_APPLICATION_CREDENTIALS="$f"
    make deploy
    rm -f "$f"
  '
  ```

  The SA is deploy-scoped (Cloud Run, Cloud Build, Artifact Registry, Storage,
  Service Account User). It's a long-lived key — rotate it periodically in
  Cloud Console and re-run `doppler secrets set GCP_SA_KEY=...`.
