---
name: testing
version: 1.4.1
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
    actions, assertions) → the upstream launch_testing README and ROS 2
    testing docs (linked in References). The `ros2` skill does not yet
    carry launch_testing content — until it does, go upstream directly
    rather than hunting for it there. This skill frames launch/node testing
    as a pyramid layer either way.
  - The `lerobot-eval` CLI and its flags → `lerobot`. This skill frames policy
    eval as a test-pyramid layer with a pass/fail bar; `lerobot` owns the eval
    mechanics.
  - Setting up the simulator a regression test runs against → `gazebo` or
    `isaac-sim` (or `simulation` if the choice isn't made yet).
  - Where the test *data* comes from — worlds, robot models, sample
    datasets, fixture folders, goldens → `test-assets`. This skill decides
    what to test and when it passes; `test-assets` supplies what it runs
    against.
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
- **A sample app is not done until its smoke test passes.** <!-- id: smoke-test-is-the-done-bar --> This is the
  concrete acceptance bar for any robium trial run: "it builds" or "it starts
  without crashing" is not sufficient — a launch/node-level smoke test
  actually passing is the minimum evidence of "done." Treat a missing or
  failing smoke test as an open task, not a detail to fix later.
- **Test at the right layer — don't push everything into sim.** <!-- id: test-at-right-layer-not-everything-in-sim --> Logic that
  doesn't depend on ROS or a running robot belongs in a plain unit test, not a
  slow sim scenario; reserve sim-based regression tests for behavior that
  genuinely requires the simulated environment. See the pyramid in Decision
  guidance.
- **Determinism is what makes a test a test.** <!-- id: determinism-makes-a-test-a-test --> A sim scenario or policy eval
  that isn't seeded/repeatable produces flaky results that get blamed on the
  code instead of the test — apply `simulation`'s determinism guidance (seeded
  physics, `use_sim_time`) and `lerobot`'s small-scale-before-long-run
  discipline (a short, deterministic eval run as a CI gate, not a long
  training-scale rollout) to every automated test.
- **Both verticals get equal treatment.** <!-- id: both-verticals-equal-treatment --> The ROS/navigation vertical tests
  with `launch_testing` + pytest; the manipulation vertical tests with
  deterministic small-scale policy eval runs. Neither is "the real test
  framework" and the other an afterthought — plan both when a project spans
  both verticals.
- **Assert against config constants, not re-typed literals.** <!-- id: assert-against-config-constants-not-literals --> A regression
  test that hardcodes a rendered value (e.g. asserting the literal string
  `--steps=2000`) can keep "passing" while the fact it checks goes stale — a
  config constant dropped to `100` and the test never noticed. When a test
  asserts a value derived from a config constant, import and assert against
  the constant itself, not a re-typed copy (vla-trial).
- **A measurement harness needs a guard that it didn't silently measure
  nothing.** <!-- id: measurement-harness-zero-measured-guard --> A benchmark CLI that catches and prints per-device exceptions can
  still exit 0 having measured zero devices — this happened on a transient HF
  401 with no real code bug. Add a regression test for the harness itself, or a
  `return 1 if measured == 0` inside it, so "ran clean" and "measured nothing"
  can't look the same (vla-trial).
- **Gate every paid remote run behind a free local dry-run.** <!-- id: gate-paid-remote-run-behind-free-dry-run --> Before submitting
  any paid remote job (a cloud GPU training run, a paid inference batch), run
  the pipeline-smoke layer end-to-end locally first — same pipeline, tiny
  scale, CPU is fine. It catches plumbing bugs (a camera-feature mismatch, a
  bad local-output-dir path) before they cost a paid run, not just before they
  cost wall-clock time (vla-trial).

## Quick start

**1. Identify what layer a new piece of behavior belongs at** using the
pyramid in Decision guidance — don't default to "write a sim test" for
everything.

**2. For ROS 2 apps:** <!-- id: ros2-pytest-vs-launch-testing-split --> write plain pytest for ROS-independent logic, and a
`launch_testing` case for anything that needs a running node or launch file —
mechanics in the upstream launch_testing docs (see References). Run both
through `colcon test` as part of the build.

**3. For ML/policy apps:** <!-- id: ml-policy-smoke-vs-regression-gate --> treat a short, deterministic `lerobot-eval` run
against a fixed dataset/seed as the smoke test — mechanics in `lerobot`.
Two distinct pass bars; don't mix them: a **pipeline smoke** (tiny
train-from-scratch, then a few eval episodes) asserts exit codes and
numeric metrics only — no success threshold, because an undertrained
policy legitimately scores 0 (verified 2026-07-12, manip-trial); a
**regression gate** (a handful of episodes against a known-good
checkpoint) is where a stated success-rate threshold belongs. Save
large-scale eval runs for manual validation, not every CI run — and don't
let a benchmark masquerade as a regression test: a benchmark that
re-derives an already-recorded number or loads a large model belongs
marked `slow`/deselected from the default suite (e.g. pytest `-m "not
slow"`), run on demand, not on every push. Leaving benchmarks in the
default suite bloated one suite's runtime unnecessarily (3.5min → 8min,
vla-trial).

**4. Before declaring a sample app or feature done, run its smoke test and
confirm it passes** <!-- id: confirm-smoke-passes-before-done --> — this is the trial-run bar, not optional polish.

**5. Wire the passing tests into CI** so the bar holds on every change, not
just the first time.

## Decision guidance

**The test pyramid for robotics** (narrower and faster at the top, broader and
slower at the bottom — most changes should be caught by a unit test, not a
full sim run):

| Layer | What it checks | Tool / pattern | Owning skill |
|---|---|---|---|
| Unit | Pure logic with no ROS/robot/sim dependency (a planner's math, a state-machine transition, a data-formatting function) | pytest | (generic — no robium skill needed) |
| Node / launch smoke | A node starts, a launch file brings up the expected set of nodes without crashing, expected topics/services appear | `launch_testing` + pytest | upstream launch_testing docs (see References; not yet in `ros2`) |
| Sim scenario / regression | End-to-end behavior in a scripted scenario (robot reaches a goal, avoids an obstacle, completes a manipulation task) run headless and deterministically | A seeded Gazebo/Isaac Sim run driven by a test script, checked against expected outcomes | `gazebo`, `isaac-sim`, `simulation` |
| Policy eval | Pipeline smoke: a tiny train+eval completes and emits numeric metrics (no threshold). Regression gate: a known-good policy's success rate over a small, fixed, seeded episode set meets a stated threshold | Deterministic small-scale `lerobot-eval` run as a pass/fail gate | `lerobot` |

**The trial-run bar:** for any sample app or feature this pyramid covers, the
minimum passing bar before calling it done is the node/launch smoke layer (ROS
vertical) or a policy-eval smoke run (manipulation vertical) — sim-scenario
and full-scale eval are the next layer up, expected for anything beyond a
first working sample.

## Platform gotchas

- **CI runners are headless by default** <!-- id: ci-runners-headless-by-default --> — sim-scenario tests must run
  headless (Gazebo server-only mode, Isaac Sim's `runheadless.sh`) rather than
  assuming a display; route the general headless strategy to `environments` if
  it isn't already decided.
- **GPU-gated eval inherits its gate in CI too.** <!-- id: gpu-eval-inherits-gate-in-ci --> A policy-eval smoke test
  that needs Isaac Sim inherits that skill's NVIDIA RTX GPU floor — confirm
  the CI runner actually has a qualifying GPU before wiring an Isaac-Sim-backed
  eval into every pipeline run, or keep CI on a `gazebo`/CPU-only eval path and
  reserve GPU-backed runs for manual/scheduled checks.
- **macOS CI runners can't run the ROS 2 layers natively** <!-- id: macos-ci-cant-run-ros2-natively --> — the
  node/launch-smoke and sim-scenario layers need Docker on macOS, same as
  local development (see `ros2`'s and `gazebo`'s macOS gotchas); plan CI
  images accordingly rather than assuming a native macOS runner works.
- **A free-space occupancy-map assertion must clear "unknown" gray, not just
  half-max** <!-- id: freespace-occupancy-threshold-above-080 --> (nav-trial, 2026-07-10). ROS trinary occupancy PGMs encode
  free=254, unknown=205, occupied=0, so a `pixel >= 0.75*maxval` free-space
  check counts unknown gray (205 > 191) as free — an all-unknown map then
  passes a free-space assertion falsely. Put the threshold above 0.80*maxval
  (0.9 works) so only genuinely-free pixels count.

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
  this skill's sim-scenario layer relies on), `test-assets` (the data the
  pyramid's layers consume), `environments` (headless CI setup), `architect`
  (plans testing into the brief).

## Changelog

<!-- One dated line per battle-tested change, added by skill-author hardening sessions. -->

- 1.4.1 (2026-08-01): anchor IDs added to claim-bearing items (learning-engine Phase 1); no content changes.
- 1.4.0 (2026-07-31): nav-trial absorption — new Platform gotcha: a
  free-space occupancy-map assertion must threshold above 0.80*maxval (0.9),
  because ROS trinary PGMs use free=254/unknown=205/occupied=0 and a
  0.75*maxval check counts unknown gray (205) as free, so an all-unknown map
  falsely passes.
- 1.3.0 (2026-07-18): route test-data sourcing to the new test-assets
  skill (cross-ref + sibling line); no content changes otherwise.
- 1.2.0 (2026-07-15): vla-trial absorption — Key directives gains three
  bullets (benchmarks aren't regression tests / mark `slow`; assert against
  config constants not literals; measurement harness zero-measured guard)
  and a free-local-gate-before-paid-remote-run rule; Quick start's
  large-scale-eval line extended with the `slow`-marker mechanism and
  3.5→8min suite-bloat evidence.
- 1.1.0 (2026-07-12): manip-trial absorption — policy-eval layer split
  into pipeline-smoke (exit codes + numeric metrics, no success threshold)
  vs regression-gate (threshold against a known-good checkpoint); the
  previous universal-threshold phrasing made train-from-scratch smoke
  tests impossible to pass honestly.
- 1.0.1 (2026-07-11): nav-trial absorption — fixed the launch_testing
  routing dead-end: three spots routed "mechanics → ros2" but the ros2
  skill has no launch_testing content; routes now point at the upstream
  docs until ros2 grows that section. Trial-run bar + smoke shape confirmed
  ✓ under real load (one-command compose smoke, exit-code chain).
