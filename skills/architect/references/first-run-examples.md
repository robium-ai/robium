# First-run examples

Use these candidates for first-run requests; the current homepage prompts map
to the first four rows. They are not universal defaults for every navigation
or manipulation project. The application repository owns
commands, dependency pins, platform instructions, and measured results. Read
the current README and launcher before running. Existing evidence for one host
does not certify a fresh installation on another.

The homepage uses outcome-based wording. A request to try a few interactive
robots in MuJoCo suggests `robot-zoo`; a pretrained reinforcement-learning
policy driving Gymnasium's CarRacing simulation suggests `car-racing-ppo`; a local simulated
Stack-chan with voice and face tracking suggests `stackchan-er2-sim`; mapping,
localization, and a navigation goal with ROS 2 and Gazebo suggest
`robot-navigation`. Other first-run requests may match the simulated Gemini
assistant in `silly-turtlebot` or pretrained two-arm cube transfer in
`act-aloha-cube-transfer`. These are candidates to inspect, not permission to
ignore platform constraints, model licenses, or paid-provider requirements.
For the Gemini assistant, explain the access requirement and possible charges
before live use.

| User outcome | Candidate and canonical instructions | First visible proof |
| --- | --- | --- |
| Try and interact with several robots in MuJoCo | [robot-zoo](https://github.com/robium-ai/robium-apps/tree/main/robot-zoo): existing native controller and standard MuJoCo viewer | The two native windows open side by side; switch robots, issue a movement command, stop, and reset. |
| Run pretrained visual driving on a Mac | [car-racing-ppo](https://github.com/robium-ai/robium-apps/tree/main/car-racing-ppo): pinned third-party PPO checkpoint and documented seed-1 scenario | The native CarRacing window opens, real CPU inference drives the generated track, and the steering/gas/brake overlay updates through a completed seed-1 lap. No training. |
| Talk to a simulated Stack-chan and use face tracking | [stackchan-er2-sim](https://github.com/robium-ai/robium-apps/tree/main/stackchan-er2-sim): local Whisper, Kokoro, browser face tracking, and pinned MuJoCo model | The local browser opens; typed or spoken commands move the head and speak locally, then optional camera permission enables face following. No API key in the default mode. |
| Map, localize, and navigate with a simulated TurtleBot | [robot-navigation](https://github.com/robium-ai/robium-apps/tree/main/robot-navigation): existing House environment and dashboard | Create and save a map, load it for localization, then reach a navigation goal. |
| Control a simulated TurtleBot with Gemini | [silly-turtlebot](https://github.com/robium-ai/robium-apps/tree/main/silly-turtlebot): fast TurtleBot3 simulation profile, not physical TurtleBot4 mode | An authorized live Gemini mission completes with camera updates; cancellation stops simulated motion. |
| Run pretrained ACT bimanual cube transfer | [act-aloha-cube-transfer](https://github.com/robium-ai/robium-apps/tree/main/act-aloha-cube-transfer): pinned checkpoint and documented default scenario | Viewer renders, actual inference runs, and the default transfer outcome is observed and reported honestly. No training. |

## First-user constraints

- Target simulation on Apple Silicon macOS or Linux x86_64 without requiring
  a dedicated GPU. Verify the selected app's actual compatibility before
  choosing its native or container path; do not extrapolate host support from
  a Docker image or macOS-only run.
- Robot Zoo needs a graphical desktop. Run `npx robium-ai app check robot-zoo`
  and the app's doctor before launching; use the existing checkout unchanged.
  It needs no Docker, GPU, checkpoint, API key, or hosted session. On Linux,
  require X11 or XWayland and report pure Wayland as unqualified.
- CarRacing PPO needs a graphical desktop and is qualified only on Apple
  Silicon macOS. Run `npx robium-ai app doctor car-racing-ppo`, then its bounded
  check before the visible seed-1 run. The first build downloads a pinned
  third-party checkpoint; no training or GPU is required. State that its
  license is unspecified, never redistribute the weights, and describe the app
  as a toy visual-control benchmark rather than a road-driving system.
- Stack-chan's local-first path is qualified on Apple Silicon macOS. Run its
  app doctor before launch; the first build needs network for pinned assets,
  while microphone and camera permissions are optional and requested only when
  used. Do not require Gemini access for the default mode or present its
  estimated dynamics as calibrated hardware behavior.
- Navigation and Gemini simulation require Docker/Compose. Check availability,
  resources, and port conflicts without stopping an unrelated running demo.
- Gemini additionally needs authorized model access and may incur API charges.
  Guide the user to configure `GEMINI_API_KEY` locally without pasting it into
  chat. Do not require the maintainer's secret-store account. Missing or denied
  access must be explained before attempting a live mission. Mock checks are
  useful diagnostics only and must be identified as such.
- ACT uses an existing pretrained checkpoint. Setup may download the model and
  dependencies. Keep randomized trials optional and distinguish successful
  bring-up from policy success across arbitrary layouts.
- Do not present hosted warm-start estimates as local installation times.
  Record cold/warm timing only when actually measured, including cache state,
  platform, source revision, scenario, and result. Report untested paths openly.
