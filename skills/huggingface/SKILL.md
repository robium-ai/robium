---
name: huggingface
version: 2.0.0
description: >
  Hugging Face Hub operations for robotics projects: inspect, download, create,
  upload, authenticate safely, explore Dataset Viewer data, run and diagnose
  Jobs, and inspect Spaces. Use when: "Hugging Face", "HF Hub", "hf download",
  "hf upload", "Hub dataset", "Hub model", "Dataset Viewer", "HF Jobs", or
  "Space logs" in a robotics workflow. Self-contained for the common path;
  checks live `hf --help` and official docs for volatile flags. Pairs with
  `lerobot` for LeRobot-specific formats and training, and `data` for sourcing.
---

# huggingface

The lean, self-contained Hub layer for Robium. Use the installed CLI as the
executable source of truth, keep robotics-specific artifact checks visible,
and pause before publishing, paid compute, destructive operations, or handling
credentials beyond the user's explicit authority.

## When to use this skill

- Inspecting, downloading, creating, or uploading a robotics dataset or model
  repository on the Hugging Face Hub.
- Exploring a dataset before downloading it, including its subsets, rows,
  Parquet exports, size, or statistics through Dataset Viewer.
- Listing available Hub Jobs hardware or, after explicit authority, running,
  monitoring, inspecting, or cancelling a Job.
- Inspecting a Space's metadata, runtime, build logs, or run logs.
- Route LeRobotDataset structure, recording, policy training, checkpoint
  semantics, and evaluation to `lerobot`; route source-selection strategy to
  `data`; route whole-application choices to `architect`.

## Key directives

- **Delegation posture: embed + links.** Embed the stable common path below;
  consult live `hf <group> --help` and official documentation for flags and
  uncommon operations. The external Hugging Face skill catalog is optional,
  not a dependency.
- **Inspect before transfer.** Check the repo card, file tree, revision,
  license, access status, and robotics embodiment/schema before downloading a
  large artifact or planning around it.
- **Keep secrets out of prompts, commands, logs, and commits.** Prefer the
  browser/device flow from `hf auth login` or an already configured `HF_TOKEN`.
  Never echo a token, place it directly on a command line, or print it through
  `hf auth token` during an agent session.
- **External mutations need authority.** Creating a repo, uploading or changing
  visibility, starting paid compute, restarting a Space, cancelling another
  process, or deleting/moving content requires explicit user authorization for
  the concrete action. Inspection and public downloads are read-only.
- **Do not copy a generated CLI inventory into Robium.** Run `hf --help` and
  the relevant subgroup's help immediately before using a version-sensitive
  flag. The installed CLI and current official docs outrank examples here.
- **Never infer dataset/model facts from memory.** Verify current contents,
  licensing, access, file sizes, and task/robot compatibility against the Hub.

## Quick start

### 1. Inspect the local CLI

```bash
hf version
hf --help
hf auth whoami
```

If `hf` is unavailable, use an isolated current CLI with `uvx hf ...` or install
the project-compatible `huggingface_hub` package. Do not upgrade a locked
environment merely to obtain a newer CLI without checking compatibility.

### 2. Inspect before downloading

```bash
hf models info ORG/MODEL
hf models ls --search QUERY --limit 10
hf datasets info ORG/DATASET
hf datasets ls --search QUERY --limit 10
hf download ORG/MODEL config.json
hf download ORG/DATASET --repo-type dataset --include 'meta/**'
```

Use `hf models info --help`, `hf datasets info --help`, and
`hf download --help` if the installed CLI rejects an option. Pin `--revision`
when reproducibility matters and record that immutable revision.

### 3. Authenticate only when necessary

```bash
hf auth login
hf auth whoami
```

Use the least-privileged token that can perform the authorized operation. A
public inspection or download should not be made dependent on a private token.

### 4. Create or upload only after explicit authorization

```bash
hf repos create ORG/NAME --repo-type dataset --private --exist-ok
hf upload ORG/NAME ./data . --repo-type dataset
hf upload ORG/MODEL ./checkpoint .
```

Before running either command, present the destination repo ID, type,
visibility, local source, and expected changed content. Use a PR revision when
review is appropriate. Do not add delete/sync flags unless deletion was
specifically authorized.

## Usage patterns

### Explore a dataset without pulling it

Use the Hub page and Dataset Viewer first. Its REST API can enumerate subsets
and splits, preview initial rows, fetch row slices, expose Parquet files, report
size, and return statistics. The `/rows` endpoint limits a request to 100 rows;
gated datasets require an authorization header. See `references/hub-operations.md`
for the endpoint checklist.

For robotics data, verify at least:

- robot/embodiment and task;
- observation, action, camera, state, and timing features;
- episode/split structure and format version;
- license, gating, and provenance;
- expected transfer size before downloading media or checkpoints.

The `LeRobot` dataset tag is a useful discovery filter, not proof that an
artifact matches the target robot. Route format-level checks to `lerobot`.

### Download reproducibly

Inspect first, choose the smallest necessary include set, and pin a commit SHA
or immutable revision for application fixtures and training inputs. Prefer the
Hub cache for reusable artifacts and `--local-dir` when the application needs a
clear project-local copy. Record repo ID, revision, and relevant include/exclude
rules in the app's decision record or data manifest.

### Publish a dataset or policy

Treat publication as an external side effect. Confirm the repository owner,
name, type, visibility, license/card content, and exact local tree. For a
LeRobot artifact, also validate its repo ID, metadata/version, processor and
checkpoint files, and discoverability fields with `lerobot` before upload.

### Run and diagnose Hub Jobs

Jobs are paid remote compute. Inspection is safe:

```bash
hf jobs hardware
hf jobs list
hf jobs inspect JOB_ID
hf jobs logs JOB_ID
```

After explicit approval of the hardware, namespace, image or UV command,
timeout, and expected cost exposure, use the live help before starting:

```bash
hf jobs run --help
hf jobs uv run --help
```

Monitor with `hf jobs logs`, `hf jobs inspect`, `hf jobs stats`, or
`hf jobs wait`. Cancelling is mutating; confirm the exact job ID and namespace,
then use `hf jobs cancel`. Debug the same command locally with Docker or uv when
possible before paying for another run.

### Diagnose a Space

Start with read-only state and logs:

```bash
hf spaces info ORG/SPACE
hf spaces logs ORG/SPACE --build
hf spaces logs ORG/SPACE --tail 100
```

Check the runtime state, SDK, repository files, build logs, and run logs before
changing anything. Restart, factory reboot, pause, hardware changes, and uploads
are external mutations and need explicit authorization.

### Self-host a Gradio demo

Gradio does not require Spaces. It can run as a Python service, mount into an
existing FastAPI process with `gr.mount_gradio_app`, sit behind a reverse proxy,
or be embedded by iframe/web component. Verify the current Gradio API and proxy
requirements before hardcoding signatures or headers.

## Platform gotchas

- `hf` command names and flags evolve. This skill was checked against official
  CLI documentation and local `hf` 1.24.0 help on 2026-08-27; run live help in
  the target environment before execution.
- Authentication stored by the CLI may silently select a personal or org
  identity. Always run `hf auth whoami` before an authorized mutation.
- Dataset Viewer supports inspection, not every storage format or gated dataset
  without credentials. A viewer failure does not prove the repo is invalid.
- Uploading a folder may create a missing repository. Do not use that convenience
  to bypass the explicit destination and visibility check.
- Spaces logs distinguish build and runtime failures. Inspect both before a
  restart; a restart can repeat the same broken build and consume resources.

## Customization

- **Private/org artifacts:** confirm namespace membership and least-privileged
  access without exposing credentials. Keep private repo IDs out of public
  fixtures and examples when confidentiality matters.
- **Large datasets:** inspect metadata and Parquet/size endpoints, download a
  small representative slice, then authorize the full transfer separately.
- **CI or unattended work:** inject a scoped secret through the CI secret store,
  avoid interactive login, pin revisions and CLI/package versions, and default
  mutations to a reviewed branch or pull request.
- **Alternative deployment:** self-host Gradio or the model service when Spaces
  is not required; `integration` owns service boundaries and containers.

## References

- `references/hub-operations.md` - compact Dataset Viewer and CLI checklist.
- [Hugging Face CLI guide](https://huggingface.co/docs/huggingface_hub/en/guides/cli)
  and [CLI reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/cli),
  checked directly on 2026-08-27.
- [Dataset Viewer quickstart](https://huggingface.co/docs/dataset-viewer/en/quick_start),
  checked directly on 2026-08-27.
- [Jobs overview](https://huggingface.co/docs/hub/jobs-overview) and
  [Jobs management](https://huggingface.co/docs/hub/jobs-manage), checked
  directly on 2026-08-27.
- Content strategy was informed by the
  [huggingface/skills](https://github.com/huggingface/skills) project
  (Apache-2.0); Robium embeds only a lean common path and remains independently
  usable.
- Siblings: `lerobot`, `data`, `architect`, and `integration`.

## Changelog

- 2.0.0 (2026-08-27): make the robotics Hub skill self-contained; add lean CLI,
  authentication, inspection, transfer, Dataset Viewer, Jobs, and Spaces paths;
  retain explicit gates for publication, paid compute, destructive actions, and
  credentials; replace the mandatory external skill-catalog dependency with
  live CLI help and official documentation.
- 1.1.2 (2026-08-03): style pass; removed em dashes throughout (no content changes).
- 1.1.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.1.0 (2026-07-15): add Gradio self-hosting mechanics and correct the assumption that a Gradio demo requires Hugging Face Spaces.
- 1.0.1 (2026-07-12): date-stamp provenance claims during the first refinement pass.
