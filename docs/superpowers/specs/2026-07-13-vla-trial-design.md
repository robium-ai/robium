# vla-trial — design

**Date:** 2026-07-13
**App:** `apps/vla-trial`
**Status:** approved design, not yet implemented
**Supersedes:** the backlog's "demo 1 — classical arm pick-and-place (MoveIt 2 + ros2_control)"

## 1. What it is

You type *"put the red cube in the box"* into a chat window. A language-conditioned
vision-language-action model (VLA) drives a simulated SO-101 arm to do it. You watch the
robot's camera, its 3D motion, its joint states, the instruction it was given, and the
action chunk it decided on — all on one scrubable Rerun timeline. The repo underneath
holds the loop that *taught* it: collect episodes → fine-tune on a GPU → eval → redeploy.

### The three-way narrative (the demo's actual point)

The demo page can switch between three controllers live, from the Controls panel:

| Controller | What it does | Why it's there |
| --- | --- | --- |
| **Oracle** | Completes the task flawlessly | ...but it is scripted and *blind* — it works only because it was handed the cube's ground-truth pose from the MJCF. Not a policy. |
| **Base SmolVLA** | Flails | The pretrained checkpoint has never seen this scene. Same instruction, no useful behavior. |
| **Fine-tuned SmolVLA** | Completes the task | Trained on 75 oracle episodes. Acts from **pixels and language alone** — no ground truth. |

That progression is the lesson. It is the honest version of "it learns what I want," and it
lands harder than a model that quietly works. It also means the demo page never needs a GPU
to *train* anything — the "learning" is shown as a switch between pre-trained checkpoints.

### Why not a live fine-tune on the demo page

A real fine-tune is GPU-hours. A visitor has ~60 seconds. Live training on the page was
explicitly rejected; the page demonstrates the *result*, the repo demonstrates the *method*.

## 2. Stack

Every choice below was verified against current sources on 2026-07-13 (see §8 for what
could **not** be verified).

| Layer | Choice | Why |
| --- | --- | --- |
| Simulator | **MuJoCo 3.10** | Only viable option on Apple Silicon. Native arm64 wheels; headless offscreen rendering via `MUJOCO_GL=cgl`. ManiSkill3/SAPIEN is CPU-only + experimental on macOS (GPU sim explicitly unsupported); Isaac is NVIDIA-only. |
| Robot | **SO-101**, `mujoco_menagerie` → `robotstudio_so101/` | Menagerie-grade asset with **manipulation-tuned collision geometry**, a **camera mount**, and a ready `scene_box.xml` pick-and-place scene. Do **not** use the upstream `TheRobotStudio/SO-ARM100` MJCF — its own README admits the gripper joint mapping "is not yet reflected in the current URDF and MuJoCo files." |
| Env | **Hand-built Gymnasium env** (`so101_pick`) | No SO-101 gym env exists. This is the single biggest build item. Shaped like `gym-hil` but **not depending on it** (see §8, risk 6). |
| Policy | **SmolVLA** — `lerobot/smolvla_base`, 450M | The only VLA in the "runs without a GPU" class. Its entire pretraining corpus is SO-100 data (487 community datasets, ~10M frames), so fine-tuning on SO-101 is **in-embodiment** — the cheapest possible adaptation. |
| Training | **HF Jobs**, `lerobot-train --job.target=a10g-small` | One flag: pushes the dataset to the Hub if needed, submits the job, streams logs back. No infra to build. ~4–10 GPU-h, ~$5–15 per fine-tune. |
| Inference | **LeRobot async inference** (policy server + robot client) | Same code path whether the policy runs in-process locally or on a remote GPU — makes the location a deployment flag, not a rewrite. Computes chunk N+1 while the arm executes chunk N. |
| Viz | **Rerun 0.34.1** | Multi-view on a shared timeline: camera + 3D scene + scalars + instruction + action chunk. A plain video stream would throw all but the first away. Version matches robium's `rerun` skill pin exactly. |
| UI | **Gradio 6** + **`gradio_rerun` 0.34.1** | The Rerun viewer is an official Gradio *component* (`rerun-io/gradio-rerun-viewer`), not a competing embed. Gradio is self-hosted in our own container — **it has no HuggingFace dependency**; HF Spaces is merely one deployment target for it, and we are not using it. |
| Python | **3.12** | Hard requirement of LeRobot 0.6.0. |
| Env mgmt | `uv` for local dev, **Docker** for the demo + deploy | Follows `environments`: local and remote must reproduce identically. See the MPS/Docker tension in §8, risk 1. |
| Deploy | **Cloud Run**, per-visitor containers | Same pattern nav-trial already proved. |

### Rejected: MolmoAct2

`allenai/MolmoAct2-SO100_101` advertises **zero-shot** SO-100/101 support and was seriously
considered as a no-training-required path. It was rejected on two independent grounds, both
verified from the model card:

1. **It is a 5.5B GPU model.** Every documented code path is `.to("cuda")` with
   `enable_cuda_graph=True` by default. Stated memory: **~26 GB in float32, "under 16 GB" in
   bfloat16**. It is 12× SmolVLA and runs a 10-step flow solver per action chunk. Not a
   laptop model, and not a cheap Cloud Run model.
2. **Its "zero-shot" claim is about *real* robots.** The checkpoint is fine-tuned on the
   SO-100/101 mixture — RealSense images of real scenes (its own sample inputs are
   `sample_realsense_*_rgb.png`). We would be feeding it **MuJoCo renders**. That is a domain
   gap in the unfavorable direction, and a VLA's vision encoder is exactly what's sensitive
   to it. Expect flailing.

It remains a legitimate backlog item as a rented-GPU side-spike ("what does a 12×-larger
model do?"), but the demo does not depend on it.

## 3. Architecture

### 3.1 Where logic lives: the gateway, not the UI

The demo container already runs a gateway process (this is how nav-trial serves its terminal,
`/status`, and file tree). We **extend that same process** rather than adding services:

- `POST /instruct` — set the language instruction the policy conditions on
- `POST /checkpoint` — switch controller (`oracle` | `base` | `finetuned`)
- `GET  /metrics` — eval metrics / current episode state
- `/ui` — the Gradio app, mounted via `gr.mount_gradio_app(app, io, path="/ui")`
- (inherited from nav-trial) `/start`, `/status`, `/shutdown`, `/fs/*`, PTY-over-WebSocket

**One process, one port (8765), one container.** Both the Gradio app and any future native
React panel are thin clients over this contract, so there is no behavior to keep in sync.

### 3.2 Demo page layout

```
┌──────────────┬────────────────────────────────────┬──────────────┐
│  Controls    │  [ Robot ] [ Terminal ] [ Editor ] │  Files       │
│              │                                    │              │
│  Start/Stop  │   ┌── Gradio app (embedded) ──┐    │  src/        │
│  session     │   │  ┌──────────────────────┐ │    │   so101_env/ │
│  ready ●     │   │  │ Rerun viewer         │ │    │   oracle/    │
│              │   │  │  • 3D arm scene      │ │    │   policy/    │
│  controller: │   │  │  • wrist camera      │ │    │  configs/    │
│  ( ) oracle  │   │  │  • joint scalars     │ │    │  Makefile    │
│  ( ) base    │   │  │  • instruction       │ │    │              │
│  (•) tuned   │   │  │  • action chunk      │ │    │              │
│              │   │  └──────────────────────┘ │    │              │
│              │   │  chat ▸ "put the cube…"   │    │              │
│              │   │  [ direct ⟷ planner ]     │    │              │
│              │   └───────────────────────────┘    │              │
└──────────────┴────────────────────────────────────┴──────────────┘
```

Controls (left) and Files (right) are nav-trial's existing components, reused. The middle is
its existing `WorkTabs`, with a new default **Robot** tab. Terminal and Editor remain siblings
so the "you are driving a real repo" story — robium's actual pitch — survives.

`Workspace.tsx` already takes the demo name as a parameter (`createInstance('nav-trial', s)`),
and the orchestrator is driver-agnostic, so this is a registry entry plus panels, not a rebuild.

### 3.3 The chat: direct + planner toggle

- **Direct (default).** Your text *is* the policy's language condition, verbatim. Zero extra
  moving parts; honestly demonstrates the VLA. A visible **known-instructions hint list** sits
  beside the chat, because off-distribution asks produce flailing and we surface that rather
  than hide it.
- **Planner (toggle).** Claude sits in front: decomposes multi-step asks ("tidy the table" →
  three pick-and-places), and **declines** what the policy demonstrably cannot do. This makes
  the model's boundary *legible* instead of embarrassing.

The toggle is visible so a visitor always knows which brain is driving.

### 3.4 One control cycle

1. Sim emits an observation: wrist-camera RGB + joint state.
2. Policy client sends it — in-process locally, or over gRPC to a policy server (decided by
   the §7 spike; async inference makes this a flag, not a rewrite).
3. Policy returns a **chunk of ~50 actions**.
4. Chunk executes open-loop in MuJoCo while chunk N+1 is already being computed.
5. Everything is logged to Rerun on a shared timeline: image, 3D scene, joint scalars,
   instruction text, predicted chunk.

**Action chunking is why a laptop is plausible at all.** The model does not run per control
step. At 30 FPS a 50-action chunk is ~1.7 s of robot motion, so the requirement is roughly
*one forward pass per second or two*, not 30 Hz.

## 4. Repo layout

```
apps/vla-trial/
  docker/          Dockerfile · compose.yaml (profiles = scenarios) · entrypoint.sh
  src/vla_trial/
    env/           so101_env.py · scene.xml (from menagerie)
    oracle/        scripted_pick.py (IK approach→grasp→lift→place)
    data/          record_episodes.py → LeRobotDataset v3
    policy/        client.py (async inference) · server.py
    ui/            app.py (Gradio + gradio_rerun)
    gateway/       app.py (extends nav-trial's demo_gateway.py)
  configs/         config.py — single source of run params, shared by Makefile and pytest
  tests/           test_env.py · test_oracle.py · test_dataset.py · smoke_vla.py
  docs/            architecture-brief.md
  outputs/         train/ · eval/ · viz/
  Makefile · pyproject.toml · uv.lock · README.md
```

`configs/config.py` as the single source of run params shared by Makefile and pytest is
lifted directly from manip-trial, whose registry card names it as a bootstrap pattern.

### Makefile targets

`spike` · `oracle` · `record` · `train` (HF Jobs) · `eval` · `ui` · `demo` · `demo-deploy` ·
`smoke` · `down`

## 5. Data

**Collection: a scripted IK oracle**, not teleop. We control the MJCF, so the cube's
ground-truth pose is known; the oracle runs approach → grasp → lift → place with randomized
spawn and mild waypoint noise. It generates 75 episodes **unattended in minutes**, it is
regenerable after any scene tweak, and it is the *only* option that scales for free. Teleop
(`gym-hil` + `gym_manipulator` records straight to LeRobotDataset) stays available as a
fallback for a handful of human-flavored episodes, but 50 episodes of teleop is an hour or
two of tedium with variable quality. HIL-RL is the wrong tool entirely — it learns a policy
via interventions, it does not produce an imitation dataset.

**Format:** LeRobotDataset v3.0 (sharded parquet + mp4), `single_task="put the red cube in
the box"`, pushed to the Hub.

**Episode count and workspace size — a hard design constraint.** The only real data points
available:

- 25 episodes → "bad performance"
- **50 episodes over a 30 cm workspace → FAILED.** The policy learned the general motion but
  could not pin down grasp locations.
- **75 episodes over a ~10 cm workspace → 80% success on first eval.**

**The lesson is density, not count.** A wide workspace at 50 episodes produces a demo that
grasps at air. Therefore: **tight cube spawn region (~10 cm), 75 episodes, not 50.**

## 6. Testing

Per the robium `testing` skill's pyramid:

| Level | Test | Asserts |
| --- | --- | --- |
| Unit | `test_env.py` | reset/step shapes, action bounds, task string plumbed to obs |
| Unit | `test_oracle.py` | oracle reaches grasp pose within tolerance |
| **Integration (day-1 canary)** | seeded oracle rollout | **10/10 episodes succeed, deterministically** |
| Data | `test_dataset.py` | recorded episodes load as LeRobotDataset v3; correct fps, shapes, `single_task` |
| Train | training-loop smoke | ~5 steps — proves the loop *starts*. Explicitly **not** training. |
| **Pass bar** | **`make smoke`** | seeded 10-episode eval of the fine-tuned policy: **success rate ≥ 60%**, metrics JSON written, exit-code chain through make |
| Demo | `make demo-smoke` | gateway ready, `/instruct` accepted, Rerun stream alive, session guards (409/403), `/shutdown` kills the container |

**Why ≥60%:** the one real reference point (75 episodes / ~10 cm workspace) produced 60–80%.
Setting the bar at the bottom of that band keeps the regression suite honest without making
it flaky.

## 7. Milestones

| # | Milestone | Exit criterion |
| --- | --- | --- |
| **M0** | **Spike** (day 1) | Four numbers measured (§8 risks 1–2). Architecture decided, not guessed. |
| M1 | Env + oracle + Rerun | Arm moving on screen; seeded oracle test 10/10 green |
| M2 | Dataset | 75 episodes, LeRobotDataset v3, on the Hub, `test_dataset.py` green |
| M3 | Fine-tune + eval | HF Jobs run completes; `make smoke` passes at ≥60% |
| M4 | Gradio UI | Chat (direct + planner toggle), Rerun viewer, checkpoint switcher |
| M5 | Demo page | Orchestrator registry entry, Cloud Run deploy, `make demo-smoke` green |
| M6 | Close-out | Registry card, architecture brief, learnings absorbed-or-offered |

**M1 is deliberately before M3.** The oracle puts a moving arm on screen on day one with zero
model inference, so the UI, the Rerun wiring, and the demo page are all built against
something real rather than against a promise.

## 8. Risks and unknowns

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| 1 | **SmolVLA inference latency is unbenchmarked on Apple Silicon.** HF's "runs on a MacBook" is a marketing claim, not a measurement. **Compounding it: Docker on macOS cannot see MPS** — manip-trial uses `uv` instead of Docker for exactly this reason. So the number that actually decides the architecture is **CPU**, not MPS: the demo container is CPU on your Mac *and* CPU on Cloud Run. | **HIGH** | **M0 spike measures three numbers:** forward-pass latency on MPS native, CPU native, and CPU inside the linux/arm64 container. If CPU clears ~1 pass/sec, everything runs everywhere with no GPU in the demo path. If not → policy-server split, and the deployed demo needs a GPU (materially more expensive per visitor). |
| 2 | **MuJoCo CGL offscreen render throughput on M-series is unmeasured.** If slow, every training render and eval rollout is bottlenecked. There is an open upstream discussion titled "Offscreen rendering with mjr_render is extremely slow." | **HIGH** | **M0 spike:** time 1000 offscreen 256×256 renders before committing. |
| 3 | **No SO-101 gym env exists — we build it.** Biggest single line item. | **HIGH** | Bootstrap structure from `gym-hil`; menagerie's `scene_box.xml` supplies the scene free. Community priors exist (`gym-so100`, `lachlanhurst/so100-mujoco-sim`) to crib from. |
| 4 | **75-episode / 10 cm constraint** (see §5). A wide workspace at 50 episodes is a known failure. | **HIGH** | Constrain the spawn region hard. Budget 75 episodes. |
| 5 | LeRobot 0.6.0 requires **Python ≥3.12**; silently breaks 3.10/3.11 envs. | MEDIUM | Pin `requires-python = ">=3.12"` in the uv project from the start. |
| 6 | **MuJoCo version conflict.** `gym-hil`/`gym-aloha` pin `mujoco<3.9`; `gym-xarm` pins `<3.0`. Menagerie's SO-101 needs **≥3.1.3**, and current is 3.10. Taking a hard dep on `gym-hil` would *downgrade* MuJoCo. | MEDIUM | **Do not depend on `gym-hil` — copy its patterns.** Verify the SO-101 MJCF loads under the resolved MuJoCo version. |
| 7 | **`mjpython` required for MuJoCo's interactive viewer on macOS** (plain `python` fails; also a known bug under `uv`). | MEDIUM | Headless path avoids it. Document it for anyone eyeballing the sim. |
| 8 | Off-distribution chat instructions produce flailing. | MEDIUM | Known-instructions hint list in the UI; planner mode can decline. Treated as an honesty feature, not a bug to hide. |

### Explicitly unverified (do not plan around these)

- SmolVLA inference latency on Apple Silicon (MPS **or** CPU) — **no published benchmark exists anywhere.** This is the demo's core assumption and it is measured on day 1, not assumed.
- MuJoCo CGL offscreen render throughput on M-series.
- MuJoCo → Rerun **true 3D** logging (meshes + per-body transforms) end-to-end. Ship the rendered scene-camera image first (certain to work); upgrade to interactive 3D as a follow-on.
- Genesis simulator's current macOS arm64 status.

## 9. What this hardens (the two-hats purpose)

**Gets a hardening vehicle:** `mujoco` (backlog skill #3 — this *is* its vehicle), `lerobot`,
`huggingface`, `data`, `rerun`, `environments`, `integration`, `testing`, `live-demo`.

**Gets nothing here:** `moveit`, `ros2_control`, `rviz2`. These were demo 1's original purpose;
they now wait for the classical pick-and-place demo, which slides down the backlog but stays
alive. The classical-manipulation gap in the registry remains open — accepted, not forgotten.

## 10. Open questions

None blocking. The two architecture-deciding unknowns (risks 1 and 2) are answered by the M0
spike before any dependent code is written; that sequencing *is* the answer.
