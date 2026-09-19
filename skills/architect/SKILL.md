---
name: architect
description: Start a robotics project or first demo from a proven example, or choose the stack and smallest useful slice for a new application. Not for routine fixes in an existing app.
---

# Architect

Get the closest proven example working before adapting it. When no compatible
example fits, choose the smallest slice that can disprove the biggest assumption.

## Start from the outcome

- Inspect the current repository, the Robium app registry, and the closest
  working example before asking questions.
- Define what the robot should visibly do, where it will run, and what evidence
  would make the first slice credible.
- Ask only about choices that change that slice. When a real choice exists,
  offer a few meaningful alternatives and recommend one.
- Treat versions, hardware, protocols, thresholds, and deployment details as
  provisional until compatibility, cost, safety, or a quick probe makes them
  consequential.

## Bring up the baseline, then adapt

- Discover candidates in the [Robium app registry](https://github.com/robium-ai/robium-apps/blob/main/REGISTRY.md),
  using a sibling checkout when available. Match the task, host architecture,
  runtime requirements, and relevant verification evidence, not just the name
  or a `stable` label. Read the selected app's README and launcher; distinguish
  tested conditions from assumptions. For the homepage's three first-run tasks,
  use [first-run examples](references/first-run-examples.md).
- For a clear compatible match, explain the choice and proceed within the
  user's request: "This matches Robium's navigation example. I'll get it
  running first, then we can adapt it." Ask only when different candidates or
  an incompatible platform materially change the outcome. Honor an explicit
  request to build from scratch. Routine maintenance stays in the owning skill.
- Use the existing checkout without resetting or pulling over user changes;
  acquire a separate checkout when necessary. Record the source revision and
  any local changes. Run the baseline unchanged with its launcher, pinned
  environment, assets, and viewer; do not create a derivative, upgrade
  dependencies, or recreate infrastructure just to demonstrate it.
- Check prerequisites, credentials, and occupied ports before lengthy builds.
  Explain first-run downloads and reuse caches on later starts. Missing model
  access is a blocker, not permission to substitute a mock and call it live.
  Keep secrets out of prompts/logs; explain API charges and obtain authorization
  before paid calls. Do not provision cloud resources or move physical hardware
  as an implicit part of onboarding.
- Verify the requested visible behavior, not merely an open port. Use the
  app's smallest relevant checks and stop only processes started for this run.
  If blocked, report the exact unmet prerequisite without inventing a new stack.
  After the baseline works, offer one small customization; create a derivative
  only when customization is requested. Keep a working baseline for comparison.

## Choose only the stack the slice needs

- Establish the environment early with `environments`.
- For mobile navigation, route through `ros2`, `navigation`, `simulation`, and
  the selected simulator and visualizer.
- For learned manipulation, route through `lerobot`, `data`, and
  `huggingface`; add a simulator only when the first slice needs one.
- Use `integration` when module boundaries or cross-process communication are
  themselves a design decision.
- Use `testing` to define the cheapest evidence for the slice, and
  `test-assets` when its fixtures are not already available.
- Route provider mechanics to `cloud-run` or `runpod` only after deployment is
  part of the approved slice. A public session layer belongs to `live-demo`;
  publishing a finished app belongs to `app-publishing`.

When the stack is genuinely undecided, read
[stack-selection.md](references/stack-selection.md). Keep upstream project
documentation as the source of truth for supported versions and hardware.

## Keep the decision record light

- Write `docs/architecture-brief.md` for a new application or genuine
  re-architecture, not for running an existing example or every bounded change.
- Record the outcome, chosen direction, provisional assumptions, risks, next
  probe, and allowed pivots. It is a living decision record, not a contract.
- Read [brief-template.md](references/brief-template.md) only when creating or
  revising that record. The
  [filled example](examples/architecture-brief-example.md) is illustrative,
  not a source of current compatibility facts.
- If no close app exists, read
  [scaffold-patterns.md](references/scaffold-patterns.md) and prune the starting
  shape to the first slice.

## Done

- The user-visible outcome and first proof are clear.
- The selected stack satisfies known platform, cost, and hardware constraints.
- High-risk assumptions have cheap probes and explicit fallback directions.
- Implementation can continue in the owning domain skills without another
  architecture gate unless the outcome or material scope changes.
