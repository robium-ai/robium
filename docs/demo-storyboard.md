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

### Which app to film for the payoff: **Robot Navigation** (recommended)

Film **`robot-navigation/`** in the sibling
[`robium-apps`](https://github.com/robium-ai/robium-apps) checkout: TurtleBot 3
Waffle Pi navigating in Gazebo with Nav2, viewed in the bundled browser
dashboard. Two reasons, and they both matter:

1. **Most legible payoff.** "A robot drives around obstacles to a goal" reads
   instantly to a non-robotics audience — a moving robot + a planned path on a
   map is self-explanatory. An arm is less obvious on a small social thumbnail.
2. **It works end to end without special hardware.** The current registry
   records local and Cloud Run runtime validation, and the app needs no GPU,
   physical robot, or local ROS installation.

The VLA and manipulation apps are strong sequel demos, but Robot Navigation
remains the clearest general-audience introduction.

### Exact bring-up to reach the visible payoff

All commands run from the sibling app checkout. The Docker path includes
Gazebo, ROS 2, Nav2, Lichtblick, and the Robium Dashboard; no on-host RViz
window is required.

```bash
git clone https://github.com/robium-ai/robium-apps ../robium-apps  # once
cd ../robium-apps/robot-navigation
./app doctor
./app run
```

Open `http://localhost:8080`, load a saved map, choose **Load & localize**, and
send a goal from the 3D view. The global plan is cyan and the local controller
plan is orange. For an autonomous take, use `./app demo`; use `./app stop`
between takes. Consult the app's current README and `./app help` before filming
because the application owns its launch interface.

### Shot list (sums to ~75s; trim sleeps to hit 60s, extend payoff to reach 90s)

| # | Time | Shot | On-screen text (no voiceover) |
|---|------|------|-------------------------------|
| 1 | 0:00–0:07 | **Hook.** Black card → the README line, big. | "Your coding agent is great at web apps — and lost in robotics." |
| 2 | 0:07–0:12 | Cut to a code editor / agent chat guessing wrong at ROS 2 (optional B-roll; or skip straight to 3). | "It guesses at ROS 2. Invents Gazebo syntax. Picks the wrong simulator." |
| 3 | 0:12–0:20 | **Install.** The terminal GIF beat: `npx robium-ai install` running for real. | "One command." · `npx robium-ai install` |
| 4 | 0:20–0:27 | `npx robium-ai doctor` scrolling its real checks. | "Checks your machine for robotics work." |
| 5 | 0:27–0:34 | **The prompt.** Type the natural-language ask into the agent. Hold on the typed line. | `> build me a mobile robot that navigates a warehouse in simulation` |
| 6 | 0:34–1:05 | **The payoff.** Lichtblick: TurtleBot 3 driving the route on the map, lidar sweeping, planned paths visible, and the robot following the route around obstacles. This is the emotional beat; give it the most time. | "…and the skills route the agent from stack choice → build → sim → test." (fade) then "TurtleBot 3 · Nav2 · Gazebo · all in sim, on a laptop." |
| 7 | 1:05–1:15 | **Closing card.** Logo + calls to action. | "robium.ai" · `npx robium-ai install` · "25 hand-crafted robotics skills for your coding agent." |

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
- "25 versioned robotics skills — ROS 2, Nav2, Gazebo, LeRobot, Isaac, MuJoCo."
- "Tested against real builds, not vibes."
- Closing: "robium.ai · `npx robium-ai install`"

---

## Reproducibility checklist (before you hit record)

- [ ] `node --version` ≥ 18 and network access (for the `npx` beat).
- [ ] Claude Code installed (`claude --version`) so `install`/`doctor` show real success lines.
- [ ] `vhs --version` present (`brew install vhs`) to render the terminal GIF.
- [ ] `cd ../robium-apps/robot-navigation && ./app doctor` passes.
- [ ] `./app run` opens the Dashboard and the selected map loads.
- [ ] A goal sent from the 3D view produces visible plans and robot motion.
- [ ] `./app stop` cleanly tears down the application between takes.
