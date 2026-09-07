---
name: architect
description: Shape a new robotics application around its smallest useful slice, stack, and decision record.
---

# Architect

Choose the smallest robotics application slice that can disprove the biggest
assumption.

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
  re-architecture, not for every bounded change.
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
