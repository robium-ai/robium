---
name: testing
version: 1.0.0
description: >
  Test-driven robotics development: smoke tests for launch files, sim-based
  regression tests, node-level unit tests, policy eval as a test, and CI
  patterns for robotics repos. Use when: 'test the robot app', 'how do I test
  this node', 'smoke test', 'regression test in sim', setting up tests for a
  new robotics project, or before claiming any robotics app works. Applies to
  both verticals: launch_testing and pytest for ROS 2 apps; deterministic
  small-scale eval runs for ML policies. Load alongside whatever skill is
  building the thing under test. Not for: general (non-robotics) testing
  practices.
---

# testing

The cross-cutting testing umbrella for robium. Robotics apps fail in layers a
generic test suite misses — a node that never receives a message, a launch
file that starts everything except the one node that mattered, a policy that
looks fine on paper but never reaches the goal in sim. This skill frames the
robotics-specific test pyramid and states the non-negotiable bar: a robium
build is not done until its smoke test passes. It does not re-teach
`launch_testing`/pytest mechanics for ROS 2 (that's `ros2`) or the
`lerobot-eval` CLI (that's `lerobot`) — it frames both as test-pyramid layers
and routes to them.

## When to use this skill

- Setting up tests for any new robium project — this should be planned into
  the build from the start, not bolted on after the fact.
- The trigger phrases in the description: 'test the robot app', 'how do I test
  this node', 'smoke test', 'regression test in sim'.
- Before claiming any robotics app or sample works — a claim of "done" without
  a passing smoke test is not verified, it's a guess.
- Load alongside whatever skill is building the thing under test — `ros2`/
  `nav2`/`gazebo` for the navigation vertical, `lerobot` for the manipulation
  vertical — this skill supplies the test framing, not a replacement for
  either.
- Cross-references — go to the sibling skill instead when the question is:
  - ROS 2 `launch_testing`/pytest mechanics themselves (fixtures, process
    actions, assertions) → `ros2`. This skill frames launch/node testing as a
    pyramid layer; `ros2` owns how to actually write one.
  - The `lerobot-eval` CLI and its flags → `lerobot`. This skill frames policy
    eval as a test-pyramid layer with a pass/fail bar; `lerobot` owns the eval
    mechanics.
  - Setting up the simulator a regression test runs against → `gazebo` or
    `isaac-sim` (or `simulation` if the choice isn't made yet).
  - General (non-robotics) testing practices — unrelated to this skill; use
    whatever generic testing guidance already applies to the language/
    framework in question.
  - The whole-stack decision this feeds into → `architect` (plans testing into
    the brief, doesn't bolt it on later).

## Key directives

- **Delegation posture: route + embed the pyramid framing.** The test-pyramid
  structure, what belongs at each layer, and the trial-run bar live here;
  `launch_testing`/pytest syntax and `lerobot-eval` flags live downstream.
  Never re-teach either mechanism's syntax in this skill.
- **A sample app is not done until its smoke test passes.** This is the
  concrete acceptance bar for any robium trial run: "it builds" or "it starts
  without crashing" is not sufficient — a launch/node-level smoke test
  actually passing is the minimum evidence of "done." Treat a missing or
  failing smoke test as an open task, not a detail to fix later.
- **Test at the right layer — don't push everything into sim.** Logic that
  doesn't depend on ROS or a running robot belongs in a plain unit test, not a
  slow sim scenario; reserve sim-based regression tests for behavior that
  genuinely requires the simulated environment. See the pyramid in Decision
  guidance.
- **Determinism is what makes a test a test.** A sim scenario or policy eval
  that isn't seeded/repeatable produces flaky results that get blamed on the
  code instead of the test — apply `simulation`'s determinism guidance (seeded
  physics, `use_sim_time`) and `lerobot`'s small-scale-before-long-run
  discipline (a short, deterministic eval run as a CI gate, not a long
  training-scale rollout) to every automated test.
- **Both verticals get equal treatment.** The ROS/navigation vertical tests
  with `launch_testing` + pytest; the manipulation vertical tests with
  deterministic small-scale policy eval runs. Neither is "the real test
  framework" and the other an afterthought — plan both when a project spans
  both verticals.

## Quick start

**1. Identify what layer a new piece of behavior belongs at** using the
pyramid in Decision guidance — don't default to "write a sim test" for
everything.

**2. For ROS 2 apps:** write plain pytest for ROS-independent logic, and a
`launch_testing` case for anything that needs a running node or launch file —
mechanics in `ros2`. Run both through `colcon test` as part of the build.

**3. For ML/policy apps:** treat a short, deterministic `lerobot-eval` run
against a fixed dataset/seed as the smoke test — mechanics in `lerobot`. A
handful of episodes with a stated success-rate threshold is enough to gate CI;
save large-scale eval runs for manual validation, not every CI run.

**4. Before declaring a sample app or feature done, run its smoke test and
confirm it passes** — this is the trial-run bar, not optional polish.

**5. Wire the passing tests into CI** so the bar holds on every change, not
just the first time.

## Decision guidance

**The test pyramid for robotics** (narrower and faster at the top, broader and
slower at the bottom — most changes should be caught by a unit test, not a
full sim run):

| Layer | What it checks | Tool / pattern | Owning skill |
|---|---|---|---|
| Unit | Pure logic with no ROS/robot/sim dependency (a planner's math, a state-machine transition, a data-formatting function) | pytest | (generic — no robium skill needed) |
| Node / launch smoke | A node starts, a launch file brings up the expected set of nodes without crashing, expected topics/services appear | `launch_testing` + pytest | `ros2` |
| Sim scenario / regression | End-to-end behavior in a scripted scenario (robot reaches a goal, avoids an obstacle, completes a manipulation task) run headless and deterministically | A seeded Gazebo/Isaac Sim run driven by a test script, checked against expected outcomes | `gazebo`, `isaac-sim`, `simulation` |
| Policy eval | A learned policy's success rate over a small, fixed, seeded set of episodes meets a stated threshold | Deterministic small-scale `lerobot-eval` run as a pass/fail gate | `lerobot` |

**The trial-run bar:** for any sample app or feature this pyramid covers, the
minimum passing bar before calling it done is the node/launch smoke layer (ROS
vertical) or a policy-eval smoke run (manipulation vertical) — sim-scenario
and full-scale eval are the next layer up, expected for anything beyond a
first working sample.

## Platform gotchas

- **CI runners are headless by default** — sim-scenario tests must run
  headless (Gazebo server-only mode, Isaac Sim's `runheadless.sh`) rather than
  assuming a display; route the general headless strategy to `environments` if
  it isn't already decided.
- **GPU-gated eval inherits its gate in CI too.** A policy-eval smoke test
  that needs Isaac Sim inherits that skill's NVIDIA RTX GPU floor — confirm
  the CI runner actually has a qualifying GPU before wiring an Isaac-Sim-backed
  eval into every pipeline run, or keep CI on a `gazebo`/CPU-only eval path and
  reserve GPU-backed runs for manual/scheduled checks.
- **macOS CI runners can't run the ROS 2 layers natively** — the
  node/launch-smoke and sim-scenario layers need Docker on macOS, same as
  local development (see `ros2`'s and `gazebo`'s macOS gotchas); plan CI
  images accordingly rather than assuming a native macOS runner works.

## Customization

- **Small demo vs. a fleet-scale project:** a one-robot sim demo may only need
  the top two pyramid layers (unit + smoke) to meet the trial-run bar; a
  production-bound project should build out sim-scenario and eval-threshold
  layers too — scale the pyramid's depth to the project's stakes, but never
  skip the smoke layer entirely.
- **Adding a new vertical or module:** extend the same four-layer pyramid
  rather than inventing a project-specific test taxonomy — the layer names and
  owning skills stay consistent across robium projects.

## References

- Upstream: [ROS 2 testing overview](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Testing-Main.html),
  [ROS 2 launch package (launch_testing source)](https://github.com/ros2/launch/blob/rolling/launch_testing/README.md),
  [colcon test-result / test workflow](https://colcon.readthedocs.io/en/released/reference/verb/test.html),
  [pytest documentation](https://docs.pytest.org/en/stable/).
- Sibling skills: `ros2` (`launch_testing`/pytest mechanics), `lerobot`
  (`lerobot-eval` mechanics and small-scale-run discipline), `gazebo` and
  `isaac-sim` (sim-scenario execution), `simulation` (determinism guidance
  this skill's sim-scenario layer relies on), `environments` (headless CI
  setup), `architect` (plans testing into the brief).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->
