# First-run examples

Use these candidates for the homepage prompts; they are not universal defaults
for every navigation or manipulation project. The application repository owns
commands, dependency pins, platform instructions, and measured results. Read
the current README and launcher before running. Existing evidence for one host
does not certify a fresh installation on another.

| User outcome | Candidate and canonical instructions | First visible proof |
| --- | --- | --- |
| Map, localize, and navigate with a simulated TurtleBot | [robot-navigation](https://github.com/robium-ai/robium-apps/tree/main/robot-navigation): existing House environment and dashboard | Create and save a map, load it for localization, then reach a navigation goal. |
| Control a simulated TurtleBot with Gemini | [silly-turtlebot](https://github.com/robium-ai/robium-apps/tree/main/silly-turtlebot): fast TurtleBot3 simulation profile, not physical TurtleBot4 mode | An authorized live Gemini mission completes with camera updates; cancellation stops simulated motion. |
| Run pretrained ACT bimanual cube transfer | [act-aloha-cube-transfer](https://github.com/robium-ai/robium-apps/tree/main/act-aloha-cube-transfer): pinned checkpoint and documented default scenario | Viewer renders, actual inference runs, and the default transfer outcome is observed and reported honestly. No training. |

## First-user constraints

- Target simulation on Apple Silicon macOS or Linux x86_64 without requiring
  a dedicated GPU. Verify the selected app's actual compatibility before
  choosing its native or container path; do not extrapolate host support from
  a Docker image or macOS-only run.
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
