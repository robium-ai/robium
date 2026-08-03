# vla-trial demo page (v1, local-only) — design

**Date:** 2026-07-15
**App:** `apps/vla-trial` (backend) + `robium-website` (page, orchestrator entry)
**Status:** approved in conversation, this document records it
**Builds on:** `2026-07-13-vla-trial-design.md` §3 (demo architecture — M4/M5, which
were designed but never implemented). This spec is the v1 cut of those milestones.

## 1. What ships

An interactive demo page at `/demos/vla-trial/`: the visitor types an instruction,
picks a controller, hits Run, and watches the SO-101 arm act in MuJoCo on an
embedded Rerun timeline (wrist camera, scene camera, joint state, action, task).

**v1 is local-only.** It works when the website runs on localhost (`npm run dev`)
with Docker up. The deployed site shows the card and page, but Start is replaced
by an honest "cloud version not yet supported — run it locally" notice. Cloud Run
deployment (CPU inference tuning, checkpoint baking economics, egress) is a
deliberate later phase.

### Honesty constraints (load-bearing)

- The trained checkpoint is the 100-step pipe-test artifact
  (`robium-ai/train_2026-07-15_08-09-36`); it scores 0/10 by design (the paid
  20k-step `make train-full` hasn't run). The UI labels it "fine-tune in
  progress — currently flails" or equivalent; no success theater.
- The **oracle** controller (scripted, ground-truth-fed, 10/10) is offered so a
  visitor can watch the task actually completed — labeled as scripted and blind
  to the instruction text.
- Instruction box is prefilled with the training task string; free text is
  allowed with a visible hint that off-distribution asks produce flailing.

## 2. Architecture (approach A — Gradio is the gateway)

One Python process, one port (8765), per the vla-trial design §3.1:

- **FastAPI** app implementing nav-trial's session contract so the website's
  Controls/demoClient/orchestrator reuse unchanged:
  - `POST /start?session=U` — claim (idle claims takeable, busy foreign → 503)
  - `GET /status?session=U` — same JSON shape as nav-trial (`claimed`, `ready`,
    `rtf: null`, `nodes: 0`, `uptime_s`, `remaining_s`, `fleet`, `log[]`);
    foreign session → 409
  - `POST /shutdown?session=U` — foreign → 403; own → exit the process
    (container dies; orchestrator AutoRemove reaps it)
  - CORS: exact-origin reflect for `https://robium.ai` + `http://localhost:*`,
    credentials allowed
- **Gradio 6** app mounted at `/ui` via `gr.mount_gradio_app`, containing:
  - instruction Textbox (prefilled `TASK`), controller Radio (`oracle` |
    `trained`), Run button, status line, and the **`gradio_rerun` 0.34.1**
    viewer component streaming the episode as it computes
  - one episode per Run; a run lock so concurrent Runs queue/reject
- "Ready" = checkpoint loaded + env constructed + warm-up render done, then the
  gateway prints **`DEMO READY`** (the orchestrator's `readyLog`).
- New code lives in `src/vla_trial/demo/` (`gateway.py`, `ui.py`,
  `episode_runner.py`) — thin wrappers over the existing, proven
  `SO101PickEnv`, `oracle.scripted_pick.rollout`, and `policy/evaluate.py`
  inference path (extracted into a reusable single-episode runner rather than
  duplicated).

## 3. Two run modes

| Mode | Start | Inference | Who owns lifecycle |
| --- | --- | --- | --- |
| **Orchestrator** (default) | page's Start button → orchestrator spawns `vla-trial:latest` | CPU (~9 s/pass; Docker on macOS has no MPS) | orchestrator (stop/reap/budget) |
| **Direct / native MPS** | `make demo` in `apps/vla-trial` (uv, host Python) | **MPS** (~0.55 s/pass) | the user's terminal |

The page's dev-only backend dropdown (same pattern as nav-trial's
`Workspace.tsx`) selects between them; `?host=localhost:8765` forces direct.
The gateway therefore avoids container-only assumptions: shutdown targets its
own process (not PID 1 blindly), paths resolve from the repo, device is
`config.INFERENCE_DEVICE` (auto: mps native, cpu container).

## 4. Backend deliverables (`apps/vla-trial`)

- `src/vla_trial/demo/` as above; `DEMO_CHECKPOINT` constant in `config.py`
  (today: the pipe-test artifact; flips to the real fine-tune later — one line).
- `docker/demo.Dockerfile` — python:3.12-slim + GL libs (spike.Dockerfile
  base), deps via uv, assets fetched, **checkpoint baked at build** (HF token
  via build secret; the repos are private), `MUJOCO_GL=egl`, `VLA_DEVICE=cpu`,
  CMD runs the gateway on 8765.
- Makefile: `demo` (native/MPS), `demo-image` (build `vla-trial:latest`),
  `demo-smoke` (the live-demo skill's bar: boots, `/status` reaches ready,
  foreign session 409/403, one **oracle** episode succeeds through the Gradio
  API, `/shutdown` exits). Oracle, not trained, is the smoke's success
  assertion — it's the controller with a truthful pass bar.

## 5. Website deliverables (`robium-website`)

- `demo-orchestrator/src/demos.json`: `vla-trial` entry — image
  `vla-trial:latest`, `gatewayPort` 8765, `readyLog` `DEMO READY`,
  `maxInstances` **1** (CPU inference eats cores), `sessionSeconds` 1800.
  (`ROS_DOMAIN_ID` injection is harmless for a non-ROS demo.)
- `src/pages/demos/vla-trial.astro` + a minimal `VlaWorkspace.tsx`: topbar
  (with the dev backend dropdown), Controls pane (reused), and a single
  **Robot** pane = iframe to `http://<host>/ui` once ready. No Terminal /
  Editor / Files in v1 (deliberate; they return later).
- On a non-localhost origin the page renders the "run it locally" notice
  instead of Start (cloud unsupported for now).
- `Apps.astro`: vla-trial card (real stack line + description) with
  "Try the live demo →" button; `tests/smoke.sh` assertions updated.

## 6. Testing

- `make demo-smoke` (backend, native mode) is the app-side gate.
- Website `make smoke` keeps asserting the landing page's literal strings,
  now including the vla-trial card.
- E2E by hand for v1: orchestrator mode (container) and direct mode (MPS)
  each drive one oracle and one trained episode.

## 7. Explicitly out of scope (deferred)

- Cloud Run deployment; anything about egress/service accounts.
- The `base` third controller and the "watch it learn" checkpoint story
  (needs the paid fine-tune to be meaningful).
- Terminal / Editor / FileTree panes; planner (Claude) chat mode.
- Embedded true-3D MuJoCo mesh logging (rendered cameras ship first, per the
  vla-trial design's de-risk note).
