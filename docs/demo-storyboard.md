# robium demo video — production storyboard (issue #37)

A 60–90s demo that takes a viewer from "my coding agent is lost in robotics" to
"a robot navigating in simulation," with the real `robium-ai` install in the
middle. This doc is the human's filming guide. It has two parts:

1. **Terminal capture** — already scripted; render it with `vhs` (no filming).
2. **Sim payoff footage** — a screen recording a human still needs to do.

Status of #37: **OPEN.** The terminal GIF is reproducible from a committed tape;
the full sim video still needs a human screen-recording per this plan.

---

## Part 1 — terminal GIF (no camera, fully scripted)

The install/CLI half of the demo is captured honestly by
[`assets/demo-terminal.tape`](../assets/demo-terminal.tape) using
[charmbracelet/vhs](https://github.com/charmbracelet/vhs). It records the REAL
`robium-ai` CLI (`install`, `doctor`, `skills`) and shows the manual `/plugin`
lines + the natural-language prompt as typed-then-cleared text (never fabricated
output).

Render it:

```bash
brew install vhs                     # macOS; or see the vhs README for Linux
vhs assets/demo-terminal.tape        # writes assets/demo-terminal.gif
```

Record on a machine with Node ≥18 on PATH and network access. Install Claude
Code first (`https://claude.com/claude-code`) so `install` and `doctor` print
their real success lines instead of the "not found" branch. The tape is
idempotent — re-running `install` prints "already installed," which is fine to
capture.

This GIF can ship to the README top on its own (see the snippet the parent
session will wire into the README `<!-- TODO(#39/demo-gif) -->` slot). The full
video below embeds the same terminal beat as its middle act.

---

## Part 2 — the full 60–90s video (human screen-recording)

### Which app to film for the payoff: **nav-trial** (recommended)

Film **`apps/nav-trial/`** — TurtleBot 3 Burger navigating in Gazebo with Nav2,
viewed in browser Foxglove. Two reasons, and they both matter:

1. **Most legible payoff.** "A robot drives around obstacles to a goal" reads
   instantly to a non-robotics audience — a moving robot + a planned path on a
   map is self-explanatory. An arm is less obvious on a small social thumbnail.
2. **It actually works, end to end.** `make smoke` is a green pass bar
   (verified 2026-07-11, REGISTRY.md). By contrast, **do not film vla-trial for
   the payoff**: per `apps/vla-trial/README.md` the pipeline is validated but
   **no policy has been trained** — the only checkpoint is a 100-step pipe-test
   that scores ~0%. Filming "language → arm" today would show an arm that does
   **not** follow the instruction. That's a great demo *later* (it's the higher
   "wow" ceiling once `make train-full` runs), but it's not honest footage now.

Keep vla-trial as the sequel demo; ship the nav-trial video first.

### Exact bring-up to reach the visible payoff (from `apps/nav-trial/README.md`)

All commands run from `apps/nav-trial/`. It's Docker-only (arm64), headless,
Foxglove in the browser. There is no on-host RViz window — **the visible payoff
is the Foxglove browser view**, so that's what you screen-record.

```bash
cd apps/nav-trial

# 0. One-time: build the image (bakes in the saved map).
make build

# 1. Bring up navigation on the saved map. Foreground; Ctrl-C to stop.
make nav
#    'make nav' runs the Nav2 stack and waits for goals from send_goals.py
#    or from Foxglove. It publishes /scan, /tf, /map, /plan, and costmaps
#    on the Foxglove bridge at ws://localhost:8765.
```

Then, in a browser (**use Chrome** — Safari blocks `ws://localhost` from the
https app):

1. Open `https://app.foxglove.dev` → **Open connection** → `ws://localhost:8765`.
2. Import the preconfigured layout once:
   **Layout menu → Import from file…** → `apps/nav-trial/foxglove/nav-trial-layout.json`.
   It sets display frame `map` and shows /map, /scan, /plan and the global
   costmap, with the Publish tool pointed at Nav2's `/goal_pose`.
3. Drop a goal: use the Foxglove **Publish** (goal) tool to set a pose, or run
   the scripted goal client in a second terminal:

   ```bash
   # second terminal, from apps/nav-trial/
   make nav        # (already running) — send goals via the helper the smoke path uses:
   # the smoke scenario drives send_goals.py automatically; for a hands-free
   # take, record `make smoke` instead (see below).
   ```

**Recommended hands-free take:** record `make smoke`. It rebuilds via `--build`,
runs the nav scenario **plus the goal client**, and exits 0 on success — so the
robot drives the route on its own while you capture Foxglove, no manual goal
clicks. Bound the run with `SMOKE_TIMEOUT` (default 180s) if needed. This is the
same green pass bar in REGISTRY.md, so the footage is guaranteed-reproducible.

Reset / teardown between takes: `make down` (tears down all profiles).

Map-frame gotcha for framing goals: the SLAM map origin is the robot's start
pose, so world `(-2.0, -0.5)` = map `(0, 0)` (README "Visualization" note).

> Note: this app is macOS/arm64 Docker-headless. If you have a Linux + display
> box, an on-host RViz2 window is an alternative capture surface, but the
> committed, verified path here is Foxglove-in-browser — film that.

### Shot list (sums to ~75s; trim sleeps to hit 60s, extend payoff to reach 90s)

| # | Time | Shot | On-screen text (no voiceover) |
|---|------|------|-------------------------------|
| 1 | 0:00–0:07 | **Hook.** Black card → the README line, big. | "Your coding agent is great at web apps — and lost in robotics." |
| 2 | 0:07–0:12 | Cut to a code editor / agent chat guessing wrong at ROS 2 (optional B-roll; or skip straight to 3). | "It guesses at ROS 2. Invents Gazebo syntax. Picks the wrong simulator." |
| 3 | 0:12–0:20 | **Install.** The terminal GIF beat: `npx robium-ai install` running for real. | "One command." · `npx robium-ai install` |
| 4 | 0:20–0:27 | `npx robium-ai doctor` scrolling its real checks. | "Checks your machine for robotics work." |
| 5 | 0:27–0:34 | **The prompt.** Type the natural-language ask into the agent. Hold on the typed line. | `> build me a mobile robot that navigates a warehouse in simulation` |
| 6 | 0:34–1:05 | **The payoff.** Foxglove: TurtleBot 3 driving the route on the map — /scan sweeping, the green /plan path, the robot following it around obstacles to the goal. This is the emotional beat; give it the most time. | "…and the skills route the agent from stack choice → build → sim → test." (fade) then "TurtleBot 3 · Nav2 · Gazebo · all in sim, on a laptop." |
| 7 | 1:05–1:15 | **Closing card.** Logo + calls to action. | "robium.ai" · `npx robium-ai install` · "23 hand-crafted robotics skills for your coding agent." |

If you must hit a hard 60s: compress shots 3–4 (reuse the terminal GIF at
1.25×) and keep shot 6 at ≥25s — the navigation is what people share.

### Capture settings

- **Payoff screen-recording:** record the Foxglove browser view at **1920×1080,
  60 fps** (or your display's native), then crop to the map viewport. Record
  clean (hide bookmarks bar, use a neutral browser theme). ScreenFlow / OBS /
  QuickTime all fine.
- **Master edit / hero + site:** export **1920×1080 (16:9) MP4/H.264** and a
  **WebM/VP9** sibling. Use `<video autoplay muted loop playsinline>` for the
  site hero and any README-embeddable host — far smaller than a GIF at this
  length. Target **< 8 MB** for the WebM loop, **< 12 MB** for the MP4.
- **Social (X / Reddit / HN):** those platforms want **MP4/H.264, ≤ 1080p**.
  Also cut a **square 1080×1080** and a **vertical 1080×1350** variant for the
  feed — the payoff (shots 5–7) alone makes a strong 15–20s standalone clip.
- **GIF fallback (only where video won't embed, e.g. some markdown):** 1000–1200
  px wide, ≤ 15 fps, **target < 8 MB** (GitHub caps inline at ~10 MB; a 75s full
  GIF will blow past that, so the GIF is the *terminal beat only* — the
  `assets/demo-terminal.gif` from Part 1 — while the full demo ships as video).
- **Where the final assets live:** commit under [`assets/`](../assets/):
  - `assets/demo-terminal.gif` — terminal beat (from the tape; README-top).
  - `assets/demo.mp4` + `assets/demo.webm` — the full 60–90s video (site hero,
    social master).
  - `assets/demo-square.mp4`, `assets/demo-vertical.mp4` — social cuts (optional).

  Large binaries: if the repo uses Git LFS, add these paths; otherwise host the
  heavy MP4/WebM on the site/CDN and keep only the lightweight terminal GIF in
  git. Confirm the host policy before committing multi-MB files.

### Caption / on-screen-text bank (pick per platform)

- "Your coding agent is lost in robotics. robium fixes that."
- "One command: `npx robium-ai install`."
- "Ask in plain language. Get a robot navigating in sim."
- "23 versioned robotics skills — ROS 2, Nav2, Gazebo, LeRobot, Isaac, MuJoCo."
- "Tested against real builds, not vibes."
- Closing: "robium.ai · `npx robium-ai install`"

---

## Reproducibility checklist (before you hit record)

- [ ] `node --version` ≥ 18 and network access (for the `npx` beat).
- [ ] Claude Code installed (`claude --version`) so `install`/`doctor` show real success lines.
- [ ] `vhs --version` present (`brew install vhs`) to render the terminal GIF.
- [ ] `cd apps/nav-trial && make build` succeeds (Docker running, arm64).
- [ ] `make smoke` exits 0 (this is the exact motion you'll film).
- [ ] Chrome open on `https://app.foxglove.dev`, layout `nav-trial-layout.json` imported, connected to `ws://localhost:8765`.
