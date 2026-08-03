# Robium v2 — Implementation Plan

**Status:** Ready to execute
**Date:** 2026-07-09
**Implements:** `docs/superpowers/specs/2026-07-09-robium-v2-design.md`
**Amends:** that spec's §3 (targets), §4 (vendoring), §6 (scaffolding), and the Build Order

This plan was written after verifying the design spec's external assumptions against
upstream sources, then reviewed adversarially against itself. Four upstream assumptions
did not survive contact (Part I). The review then found that the *consequences* of those
amendments had not been propagated — the risk ordering, the gate, and the effort
estimates were all inherited from the spec unexamined (Part II).

Where this document and the design spec disagree, this document wins.

**Headline: the spec's "1–2 weeks" is not real. This plan is ~3 weeks.** The compression
came from estimating the CLI at one day and from front-loading a hard gate on the wrong
risk. Both are corrected below.

---

## Part I — Amendments to the Design Spec (upstream reality)

### A1. Remote Docker contexts are cut from the MVP (amends §3)

**Finding.** A remote Docker context resolves bind-mount source paths on the *client*
and executes them on the *remote daemon*. `./config:/config` becomes an absolute local
path string, shipped to a remote host where it does not exist — and Docker's bind-mount
semantics then **silently create it as an empty directory**. The container boots, the
mount is empty, no error is raised. `build: .` behaves differently: it *does* package
and upload its context over SSH. So one compose file resolves half against the local
filesystem and half against the remote one.

Evidence: [docker/compose#9075](https://github.com/docker/compose/issues/9075),
[#8484](https://github.com/docker/compose/issues/8484), open since 2021.
[#11867](https://github.com/docker/compose/issues/11867) requests remote file copying —
still unimplemented, confirming the gap.

**Consequence.** The spec's §3 premise — "this reuses a mechanism Docker already ships
rather than building bespoke orchestration" — is false. Docker ships a mechanism that
*looks* like it works and fails silently. Making it work requires robium to own a file
sync subsystem, which is precisely the speculative machinery
`legacy-memory/06-analysis-and-lessons.md` warns against.

**Amendment.**

- A *target* is the local Docker daemon. **`robium target` is cut from the MVP CLI
  entirely** — a `set` verb that can only ever fail is cargo cult, and `doctor` already
  reports local capability. The noun returns when the feature does.
- `robium doctor` still probes GPU availability, and skills still declare `requires_gpu`.
  Both remain meaningful locally.
- Remote targets move to Non-Goals, with the bind-mount trap recorded as the reason.

**This is not a clean deferral, and the plan will not pretend otherwise.** The spec sold
Docker-context targeting as *the* execution answer for its most-emphasized fragmentation
axis — NVIDIA's GPU-heavy physical-AI stack (Isaac, GR00T), where "the user brings their
own GPU box" was the whole story. That answer is broken. **Robium's post-MVP path to the
GPU-heavy vertical currently has no execution-target story at all.** That is a
thesis-level open problem, not a scheduling item. The MVP thesis survives intact — pain
#1, "mixing ecosystems," needs no remote host, and Isaac/GR00T were already Non-Goals —
but nobody should read A1 as "we'll get to it."

### A2. The Phase gate was testing the wrong thing (amends Build Order)

**Finding.** `lerobot-eval` takes `--policy.device={cuda|cpu|mps}`. PushT is 2D pymunk
physics at 96×96; Diffusion Policy is plain PyTorch. **No GPU is required.** The spec
made "LeRobot, `rerun`, and GPU target switching" the largest unknown and gated the
project on it booting *"on both a local target and a remote GPU context."*

Two of those three are now moot: remote contexts are cut (A1), and GPU is optional.

**But a real unknown surfaced in their place.** The spec asserts `manip-lerobot` is
*"visualized with `rerun`."* Rerun is verified as LeRobot's live-visualization backend
for `lerobot-record` / `lerobot-teleoperate` via `--display_data=true`. It is **not
verified that `lerobot-eval` emits rerun output at all** — eval's documented artifact is
an MP4 video and a JSON metrics blob. If eval does not log to rerun, the "proof of life"
for the ML vertical does not exist as specified and must be hand-written.

**Amendment.** GPU is removed from every gate. The rerun question becomes **Spike S1**,
resolved before any Dockerfile is written. See Part II for the re-derived risk ordering —
because once GPU and remote are gone, `manip-lerobot` is no longer the riskiest thing in
the project.

### A3. Foxglove means the bridge, not the viewer (amends §3 visualization)

**Finding.** `ros-jazzy-foxglove-bridge` is maintained and actively released (3.3.0,
Sep 2025, now on the Foxglove SDK). But open-source **Foxglove Studio froze at v1.87.0
(Feb 2024)**; the product is now account-gated commercial SaaS. There is no free
self-hostable Foxglove viewer.

**Amendment.** `nav-sim` ships `foxglove_bridge` on `ws://localhost:8765`. The skill body
names **[Lichtblick](https://github.com/lichtblick-suite/lichtblick)** (BMW's MPL-2.0
fork, same protocol) as the OSS viewer, and mentions Foxglove's hosted app as a
free-for-single-user alternative. Robium ships neither; both connect to the same bridge.
This keeps the bridge generic, as `V2_VISION.md` originally intended.

### A4. Vendor upstream docs — but not the stale ones (amends §4)

**Finding.** LeRobot's `AGENT_GUIDE.md` exists at repo root and is real, current, and
rich (Docker section §8.2b, hyphenated CLI). **But `lerobot/diffusion_pusht`'s Hub model
card is stale** — it still documents `python lerobot/scripts/eval.py` and `--device=cuda`,
neither of which matches the current `src/` layout or CLI.

Also changed since the spec was written: LeRobot requires **Python ≥3.12**; console
scripts are hyphenated (`lerobot-eval`, not `python -m lerobot.scripts.eval`); extras are
`lerobot[pusht,diffusion]`.

**Amendment.** §4's vendoring rule stands, with a qualifier: **vendor the upstream
document, verify the commands, and record `source_url` + `source_commit`.** Where an
upstream doc is verifiably stale, the skill body carries the corrected command inline and
a note saying why it diverges. Vendoring is not a licence to ship commands nobody ran.
Vendored Apache-2.0 content requires a `NOTICE` file — neither document mentioned this.

### A5. Scaffolding: never-overwrite, not hash reconciliation (amends §6)

The spec's `.robium/manifest.json` with a SHA-256 per generated file, recomputed on
re-`create` to distinguish "unmodified, safe to regenerate" from "user-edited, must
skip," is real engineering for a real problem — **at scale**. At two skills and zero
users it is the over-building the retrospective blames for stalling robium-old.

**Amendment.** MVP rule: **`create` never overwrites an existing file, and reports every
path it skipped.** No manifest, no hashing. It writes `.robium/source.json` recording
only `{skill, version, created_at}` — enough to reconstruct provenance later. Hash
reconciliation earns its keep the first time a user asks to re-sync a scaffold with an
updated catalog. Until then it is a subsystem serving a hypothetical.

The day this buys back goes to `robium-architect` (Phase 5), which the spec calls the
moat and then budgeted a shared afternoon.

### A6. Two smaller notes (no design change)

- **ROS distro.** ROS 2 **Lyrical Luth** (May 2026) is now an LTS through 2031;
  **Kilted** is EOL Nov 2026. Robium stays on **Jazzy** (EOL May 2029) — TurtleBot3,
  Nav2 (`nav2_simple_commander` 1.3.11), `foxglove_bridge`, and Gazebo Harmonic all have
  verified Jazzy debs today; Lyrical's pairing is unverified. Revisit before 1.0.
- **Apple Silicon.** `ros:jazzy` is multi-arch (arm64 ✓). Gazebo Harmonic headless
  *physics* runs on arm64, but there is no GPU passthrough to Linux containers on macOS —
  rendered sensors fall back to llvmpipe software rendering. `nav-sim` must therefore use
  **no camera or depth sensors** in its MVP world. Lidar-only + Nav2 stays fast.
  Likewise, `mps` is unavailable *inside* a container; Docker-on-Mac means CPU torch.

### A7. `metadata:` values are strings

The Agent Skills spec defines `metadata` as "a map from string keys to **string**
values." Claude Code is lenient, but for portability write `requires_gpu: "false"`, not
`requires_gpu: false`. The string→bool coercion is defined **once**, in
`catalog.py::parse_bool` (`"true"`/`"false"`, case-insensitive, anything else is a
validation error), and every consumer calls it. A parsing convention defined in two
places is the invented syntax §4 forbids.

---

## Part II — Re-derived Risk Ordering

The spec ordered risk-first and put `manip-lerobot` at the front. After A1 and A2, that
ordering is stale. What actually remains open, ranked:

| Rank | Unknown | Why it's open | Tail |
| --- | --- | --- | --- |
| **1** | **Claude Code plugin install path** | The *entire distribution thesis*. Never tested. Scheduled last in the original plan. | Unbounded — if the install path doesn't work, robium has no product surface. |
| **2** | **TurtleBot3 on Gazebo Harmonic / Jazzy** | Gazebo Classic is EOL; the `ros_gz` migration is officially available but rough. Open issue ROBOTIS-GIT/turtlebot3#1079. Multiple community forks exist *precisely to smooth this*. | Open-ended. A working commit may not exist. |
| **3** | Does `lerobot-eval` emit rerun output? | The spec asserts it; nothing verifies it. | **Bounded.** Half-day spike, half-day known fallback (hand-write the rollout script). |

The spec's "largest unknown" is now the *smallest-tailed* of the three, because it has a
cheap, known mitigation. A bounded risk does not deserve a project-halting gate while two
open-tailed ones go untested until the buffer.

**Therefore: all three are spiked in the first two days, before any production code.**
Risk-first, honestly applied, means front-loading the risks that can't be bounded.

---

## Part III — Build Order

Seven phases. ~3 weeks. Phase 1 is the only hard gate.

### Phase 0 — Skeleton, skill contract, distribution smoke test (Day 1)

No robium logic. Three deliverables, one of which the original plan omitted entirely.

| Task | Deliverable |
| --- | --- |
| 0.1 | `LICENSE` (Apache-2.0), `NOTICE` (for vendored upstream docs, per A4), `.gitignore`, `README.md` stub |
| 0.2 | `pyproject.toml` — package `robium`, **`requires-python = ">=3.12"`** (matches LeRobot; avoids a spike venv that can't install it), script `robium = "robium.cli:main"`. Declare CLI deps now: `typer`, `pyyaml`. Compose is invoked as a subprocess, not a library. |
| **0.3** | **`docs/SKILL_CONTRACT.md`** — the shared contract Phases 1 and 2 must both satisfy. Without it, "parallelizable" is a scheduling illusion and Phase 4 inherits an unbudgeted reconciliation. Specifies: compose file naming (`docker-compose.yml`, `compose.<variant>.yml`), the exact `metadata` key set and value types, the `out/` volume convention, and **`test.sh`'s I/O contract** (exit 0 = pass, writes a machine-readable result to stdout, takes no arguments, needs no display). |

**Verify:** `pip install -e .` succeeds; `robium` resolves (may exit non-zero).

---

### Phase 1 — Three parallel spikes (Days 2–3) · **GO/NO-GO GATE**

Throwaway code. Nothing here ships. Each spike answers one question in writing.

**S1 — Does `lerobot-eval` emit rerun output?**
In a Python 3.12 venv: `pip install 'lerobot[pusht,diffusion]' rerun-sdk`, then
`lerobot-eval --policy.path=lerobot/diffusion_pusht --env.type=pusht --eval.n_episodes=1
--eval.batch_size=1 --policy.device=cpu`. Inspect every artifact written.

Run it with `SDL_VIDEODRIVER=dummy MUJOCO_GL=osmesa` and **no `DISPLAY`**. A venv on a
desktop has GL and a display; the container will have neither. Without those env vars the
spike proves nothing about headless boot — and even with them, **headless-in-container
remains unproven until Phase 2 builds the image.** The spike answers the *software*
question, not the *packaging* one. Do not let a green S1 create false confidence.

*If eval emits no rerun output* → write `scripts/rollout_rerun.py`: load the policy via
LeRobot's Python API, step `gym_pusht/PushT-v0`, log frames and actions to rerun,
`rr.save("/out/rollout.rrd")`. Budget: half a day.

**S2 — Does TurtleBot3 work on Gazebo Harmonic under Jazzy?**
Boot `ros:jazzy` + `ros-jazzy-turtlebot3*` + `ros-jazzy-ros-gz` + Gazebo Harmonic
headless. Assert `/scan` publishes. Try the official `turtlebot3_simulations` Jazzy
branch first. If it fights back, evaluate the community forks (westpoint-robotics,
MOGI-ROS). **Output: a pinned, known-good commit or fork, and a written note on why.**

**S3 — Does the plugin install path work?**
A repo with `.claude-plugin/plugin.json`, a `marketplace.json` with one trivial
`hello-robium` skill, and nothing else. Push it. Run
`/plugin marketplace add <repo>` → `/plugin install hello-robium@robium` in Claude Code.
Confirm the skill activates. **This is the distribution thesis, tested on day 2 with
twenty lines of YAML instead of on day 20 with the whole product resting on it.**

**GATE — all three answered in writing:**

1. S1: a documented path to a `.rrd` from a CPU rollout, whether via `lerobot-eval` or
   the fallback script.
2. S2: a pinned commit where `/scan` publishes from a headless Harmonic TurtleBot3.
3. S3: a skill installed from a marketplace repo and activating in Claude Code.

**If S3 fails:** stop everything. The catalog has no delivery mechanism.
**If S2 fails:** `nav-sim` needs a different robot or a different simulator. Rethink the
classical vertical before building it.
**If S1 fails:** proceed — the fallback is known and bounded.

---

### Phase 2 — `manip-lerobot` (Days 4–6)

Zero robium code. Plain `docker compose`. Conforms to `SKILL_CONTRACT.md`.

| Task | Detail |
| --- | --- |
| 2.1 | `docker-compose.yml`. Base `python:3.12-slim`. Install `lerobot[pusht,diffusion]` + a **pinned** `rerun-sdk` (the `.rrd` format is version-coupled to the viewer; an unpinned SDK produces recordings a mismatched viewer refuses). Torch **CPU wheels** by default (`--index-url .../cpu`). Env: `SDL_VIDEODRIVER=dummy`, `MUJOCO_GL=osmesa`, `HF_HOME=/cache`. `python:3.12-slim` lacks GL libs — expect to `apt-get install` them; this is the packaging risk S1 could not cover. |
| 2.2 | Mount `./out`; named volume `hf-cache`. Confirm the Hub fetch of `lerobot/diffusion_pusht` on first boot and that the cache makes the second boot offline. **Record the on-disk cache size** — Phase 7 CI needs it. |
| 2.3 | A `healthcheck:` on the service. `lifecycle.status` (Phase 4) has no definition of "up" without one, and neither the spec nor the first draft of this plan mentioned it. |
| 2.4 | `compose.gpu.yml` overlay: cu128 torch wheels, `deploy.resources.reservations.devices` with `capabilities: [gpu]`. Use the `deploy` form, **not** the `gpus:` shorthand — that needs Compose ≥2.30. An overlay **replaces** `command` wholesale; it does not append. |
| 2.5 | `test.sh` per the contract. CPU, 1 episode, exit 0. Asserts the metrics JSON parses and contains a success-rate key. **Asserts the `.rrd` loads programmatically** — read it back through rerun's data API and assert ≥N rows on the expected entity paths. "File exists and is non-zero" passes on a truncated recording; it is not a test. |
| 2.6 | `SKILL.md`. `metadata: {kind: stack, framework: lerobot, simulator: gym-pusht, requires_gpu: "false", use_case: manipulation}`. Body ≤500 lines, inline compose snippets, **corrected** CLI per A4. |
| 2.7 | `references/AGENT_GUIDE.md`, vendored from `huggingface/lerobot@<commit>`, `source_url` + `source_commit` in metadata, attributed in `NOTICE`. Do **not** vendor the diffusion_pusht model card (A4). |

**Performance budget — stated as two numbers, not one.** The original "15 minutes on 4
cores" was invented, and it folded image build, Hub download, and eval into one figure
while CI runs on 2-vCPU standard runners. Instead:

- **Build time** (image + pip install): measured, then cached. CI caches Docker layers.
- **Run time** (1 episode, warm HF cache, 2 vCPU): measured on the *actual runner spec*
  and recorded as the CI ceiling. CI caches the HF model by key.

Derive both from a real measurement in Task 2.2. Do not assert a number in advance.

**The GPU overlay ships unverified unless a GPU environment is committed.** Either stand
up a self-hosted GPU runner, or mark `compose.gpu.yml` **"unverified — community
tested"** in the skill body. Shipping an untested GPU path inside the flagship ML skill,
while calling GPU support a pillar, is worse than shipping no GPU path.

---

### Phase 3 — `nav-sim` (Days 7–8)

De-risked by S2. Independent of Phase 2. Conforms to the same contract.

| Task | Detail |
| --- | --- |
| 3.1 | `docker-compose.yml` on `ros:jazzy` at S2's pinned commit. `ros-jazzy-navigation2`, `-nav2-bringup`, `-turtlebot3*`, `-foxglove-bridge`, `-ros-gz`. |
| 3.2 | Gazebo Harmonic headless (`gz sim -s`). **Lidar only — no cameras, no depth** (A6). Expose `8765`. Add a `healthcheck:`. |
| 3.3 | `scripts/goto.py` via `nav2_simple_commander`'s `goToPose`. This is the agent's extension point — the thing the demo edits. |
| 3.4 | `test.sh` per the contract: boot, wait for `/scan` and `/amcl_pose`, assert `goto.py` reaches a pose within tolerance, exit 0. No GUI, no viewer. |
| 3.5 | `SKILL.md`. `metadata: {kind: stack, framework: ros2, robot: turtlebot3, simulator: gazebo-harmonic, requires_gpu: "false", use_case: navigation}`. Body names **Lichtblick** as the OSS viewer (A3). |

**Verify:** `test.sh` green on x86-64 Linux **and** Apple Silicon. Record wall-clock on
both. If arm64 exceeds ~2× amd64, say so in the skill body rather than optimizing.

---

### Phase 4 — The CLI (Days 9–11)

**Three days, not one.** The spec said Day 5 and the first draft of this plan copied it
without challenge. `scaffold.py`'s non-clobber reporting is a day. `doctor.py` probes a
daemon, a compose version, disk, arch, and spins a throwaway GPU container. `lifecycle`
needs non-blocking `start` and a real definition of "up." Plus unit and integration
tests. The spec's "days 7–10 buffer" was never buffer; it was this phase's overflow.

Blocked by Phases 2 and 3 — the CLI's shape is dictated by what the two real stacks need.

| Module | Surface |
| --- | --- |
| `cli.py` | typer entry point |
| `doctor.py` | Docker daemon reachable; compose ≥2.20; disk; arch; GPU probe by running a throwaway `--gpus all` container (`docker info` runtimes are unreliable under CDI). **No port checks** — port 8765 is `nav-sim`'s concern, and belongs in its preflight, not in a generic capability probe. |
| `catalog.py` | Walk `skills/`, parse frontmatter, filter on `--kind` / `--framework` / `--requires-gpu`. Owns `parse_bool` (A7) — the single definition of the string→bool rule. |
| `scaffold.py` | `create <skill> <dir>` — copy, **never overwrite**, report every skipped path, write `.robium/source.json`, git init (A5) |
| `lifecycle.py` | `start` / `stop` / `status` / `logs`, `kind: stack` only. `start` non-blocking; `status` reads the compose `healthcheck` (Tasks 2.3, 3.2). |

`robium target` is **not** in this list (A1).

**`requires_gpu` reconciliation:** `create` warns; `start` refuses and exits non-zero
naming the unmet requirement, before any image pull.

**Verify:** unit tests for non-clobber (edit a scaffolded file, re-create, assert
untouched *and reported*), for catalog filtering, and for `parse_bool`. Integration:
`robium create manip-lerobot /tmp/x && cd /tmp/x && robium start && robium status &&
robium stop`.

---

### Phase 5 — Meta-skills and generators (Days 12–13)

Written *from* what Phases 2–3 taught. `robium-architect` gets real time here — the spec
calls the catalog the moat, then gave its authoring skill a shared afternoon.

| Task | Detail |
| --- | --- |
| 5.1 | `skills/docker-patterns/` (`kind: module`) — annotated, copy-adaptable snippets extracted from the two real stacks: ROS 2 Jazzy base, headless Gazebo, GPU overlay, foxglove_bridge, rerun wiring, HF cache volume, healthchecks. No `FROM` coupling; authors copy, never inherit. **This phase depends on `SKILL_CONTRACT.md` (0.3) having actually been followed** — snippets are only extractable if the two stacks share idioms. |
| 5.2 | `skills/robium-architect/` (`kind: meta`) — how to author a robium skill. Robium's analogue of huggingface/skills' `hf-cli` skill: the first thing installed. |
| 5.3 | `scripts/validate_skills.py` — hard gates: `name` == dirname; matches `^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars; `description` non-empty, ≤1024 chars; frontmatter parses as a YAML mapping; `metadata` values are strings (A7); `kind: stack` ⇒ `docker-compose.yml` + `test.sh` exist. **No bind-mount lint** — with remote targets cut, it would fire on both flagship skills and train authors to ignore warnings. It returns with remote targets. |
| 5.4 | `scripts/generate_marketplace.py` → `.claude-plugin/marketplace.json` + `AGENTS.md`. Schema per Claude Code: top-level `name`, `owner{name}`, `plugins[]`; each entry `{name, source: "./skills/<name>", skills: "./"}`. Mirror huggingface/skills, whose structure S3 already validated. |
| 5.5 | `scripts/publish.sh --check` — regenerate into a temp dir, diff, exit non-zero on drift. |

**Verify:** `validate_skills.py` green on all four skills; corrupt a frontmatter field and
confirm it fails. `publish.sh --check` clean; hand-edit a `description` and confirm it
fails.

---

### Phase 6 — CI, packaging, demo (Days 14–16)

| Task | Detail |
| --- | --- |
| 6.1 | Real install path, now with the real skills. S3 proved the mechanism; this proves the content. |
| 6.2 | CI: `validate_skills.py` + `publish.sh --check` on every push. `nav-sim` `test.sh` on a standard runner. `manip-lerobot` `test.sh` **on CPU**, standard runner — possible only because of A2. **Cache Docker layers and the HF model by key**, or every run re-pays the build and the download (Task 2.2 measured both). GPU overlay on a GPU runner if one was committed; otherwise it is marked unverified, not silently skipped. |
| 6.3 | Offline-first assertion: `doctor`, `list`, `create` all succeed with networking disabled. Document that `start` still pulls images and `manip-lerobot` fetches from the Hub on first boot. |
| 6.4 | Record the demo. `nav-sim` is the better demo (a robot moves); `manip-lerobot` is the better *proof* (it crosses ecosystems). Lead with nav-sim. |

---

## Part IV — Risk Register

| # | Risk | Detected by | Mitigation |
| --- | --- | --- | --- |
| R1 | Plugin install path doesn't work | **S3, day 2** | Project-halting. Found on day 2 for the cost of a trivial skill. |
| R2 | No working TurtleBot3 + Harmonic + Jazzy combination exists | **S2, day 2** | Pin a community fork, or change robot/simulator. Open-tailed — hence day 2. |
| R3 | `lerobot-eval` emits no rerun output | S1, day 2 | Hand-write `rollout_rerun.py`. Bounded: half a day. |
| R4 | Headless-in-container fails where the S1 venv succeeded (missing GL in `python:3.12-slim`) | Task 2.1 | S1 explicitly does **not** cover this. Budget apt-installed GL libs. |
| R5 | CPU eval too slow for a credible demo | Task 2.2 measurement | 1 episode; GPU is the *demo* path, CPU the *CI* path. |
| R6 | `.rrd` version skew between SDK and viewer | Task 2.5 | Pin `rerun-sdk`; assert programmatic load, not file size. |
| R7 | Phases 2 and 3 diverge despite being "parallel" | `SKILL_CONTRACT.md` (0.3) | The contract is a Phase 0 gate on both. |
| R8 | GPU overlay ships untested | Phase 2 decision | Commit a GPU runner, or label it unverified. No third option. |
| R9 | Scope creep back toward remote targets | Review | A1 is binding. Remote targets need a *design*, not an implementation. |

---

## Part V — Definition of Done

- Both flagship skills' `test.sh` pass in CI, headless, from a clean clone.
- `manip-lerobot`'s `.rrd` is asserted by programmatic load, not file size.
- `validate_skills.py` and `publish.sh --check` green on all four skills.
- `robium doctor && robium list && robium create nav-sim ./demo` works with the network off.
- A user can `/plugin marketplace add` the repo and install a skill in Claude Code.
- Re-running `create` over a hand-edited file leaves it untouched **and says so**.
- `compose.gpu.yml` is either CI-verified or explicitly labelled unverified.
- The demo recording exists.

## Part VI — Open Questions

**Thesis-level, unresolved:**

- **What is robium's execution-target story for the GPU-heavy vertical?** A1 shows Docker
  contexts don't answer it. Isaac/GR00T skills cannot be built until something does. This
  blocks a stated pillar of the thesis, and no candidate answer (sync step, bind-mount
  ban, named-volumes-only, ship-a-remote-agent) has been designed. Do not start Isaac work
  before answering this.

**Deferred, cheap to defer:**

- Formalize the `metadata` facet schema as JSON Schema, or leave informal? Still
  deferring; `validate_skills.py` can add facet validation later without touching any
  `SKILL.md`. (From the design spec, unchanged.)
- Revisit ROS 2 Lyrical Luth before 1.0 (A6).
- Hash-based scaffold reconciliation returns when a user asks to re-sync (A5).

**Unscoped, needs a decision before 1.0:**

- **Windows / WSL2.** Neither document says whether it is supported or excluded. It is a
  large slice of robotics developers. Pick one and write it down.
- **Teardown.** There is no `robium destroy`. `hf-cache` and `out/` accumulate forever.
