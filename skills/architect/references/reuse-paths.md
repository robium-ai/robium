# From a working example to the user's app

Use only the chosen path. This is not a checklist requiring all four paths or
a reason to delay a first demo for a design document.

## Adapt an example

- A request for a customized app authorizes a derivative, not changes to the
  shared reference checkout. Identify the source app and revision; preserve
  existing user work. Use the application's documented clone/copy workflow,
  a separate checkout, or a worktree as appropriate to its repository layout.
  A GitHub fork or push is optional and requires separate authorization.
- Prove the unchanged baseline before behavioral edits. Keep its launcher,
  compatible dependency pins, assets, viewer, and smallest relevant test.
  Reuse an already verified baseline when its revision, environment, and
  relevant behavior still match; do not repeat expensive setup ceremonially.
- Confirm or safely resolve the destination before copying. Never overwrite
  an existing project or drag secrets, virtual environments, build outputs,
  or large caches into a new repository. Preserve license and attribution;
  reference shared assets through the owning app's supported mechanism.
- Make the smallest requested customization, then check only the affected
  behavior once the change is coherent; do not rerun the whole baseline after
  every edit. Low-risk visual acceptance may be handed to the user with exact
  steps and an explicit unverified status.
  Keep unrelated behavior at the reference defaults rather than asking
  speculative customization questions. Keep an unchanged reference for
  comparison. Defer repo restructuring,
  optional services, training, and deployment until the user needs them.

## Reuse selected pieces

- Explain which concrete pieces fit and which do not: for example a bounded
  robot-control adapter, camera stream, simulator launcher, or viewer. Check
  interfaces, dependency coupling, platform evidence, and licensing before
  choosing extraction over a fresh implementation.
- Do not run or clone every candidate application just to reuse one module.
  Inspect its owning docs and existing evidence; run a focused check when
  compatibility is uncertain, without automatically writing a per-piece suite.
  Do not inherit a paid model dependency
  or an entire ROS stack for an unrelated dashboard component.
- Retain necessary configuration, pins, licenses, and source revision with
  the reused piece. Adapt only the boundary needed for the new app. A module
  that worked in its source app is not evidence that the new combination works.
- Create the smallest runnable app connecting those pieces and check one
  end-to-end behavior, or explicitly hand off low-risk manual acceptance.
  This need not be an automated harness. Expand only after that result is visible; do not build
  a general-purpose framework or complete all the source apps' features.

## Start fresh

- Briefly state why existing apps or pieces do not fit, unless the user already
  explicitly chose from scratch. Do not insist on running an unwanted example.
- Select domain skills for the first visible behavior, not every future feature.
  Research only unresolved compatibility or design decisions that could block
  that behavior. Bring in heavy architecture research only for a real ambiguity.
- Use [scaffold patterns](scaffold-patterns.md) as optional shapes, not required
  directory trees. One process or package may be enough. Keep any architecture
  brief short; do not make it a separate approval gate for an agreed build.
- Define one observable success check, get it running, then offer the next small
  customization. Keep hardware, paid APIs, and cloud provisioning behind their
  existing authorization boundaries.
