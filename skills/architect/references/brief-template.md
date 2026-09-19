# Architecture decision record template

Use `docs/architecture-brief.md` for a new application or a genuine
re-architecture. It records decisions and uncertainty; it is not an immutable
contract. Update it when evidence authorizes a pivot.

Only the four core sections are required. Add optional detail when it changes a
decision or helps the next implementation step.

Lock the user-visible outcome, genuine constraints, and the next risk-reducing
slice. Exact methods, versions, hardware SKUs, training parameters, metric
thresholds, protocols, and deployment details stay provisional unless the user
requires them, compatibility/safety/cost makes them necessary, or a cheap probe
has validated that choice for the next slice. Record what actually worked as
implementation evidence instead of predicting it in the architecture brief.

```markdown
# Architecture Brief: <app name>

**Date:** <YYYY-MM-DD>
**Status:** <draft | active | superseded>

## Goal and constraints

The user-visible outcome, robot/task, sim-vs-real target, available hardware,
GPU/budget limits, and local/remote constraints. Mark unconfirmed inputs as
provisional.

## Decisions

| Decision | Choice | Why now | Confidence |
|---|---|---|---|
| First working slice | ... | Cheapest useful risk reduction | validated/provisional |
| Environment | uv/Docker/... | ... | validated/provisional |
| Simulator/middleware | ... | ... | validated/provisional |

Include an alternative only when it was a genuine contender. Do not invent a
rejected option to make the record look complete.

## Provisional assumptions and risks

| Assumption or risk | Impact | Cheapest validation | Authorized pivot |
|---|---|---|---|
| ... | ... | ... | What may change without a new design gate |

## Implementation path

1. The smallest user-visible or risk-reducing slice.
2. The smallest relevant check, or an explicit low-risk manual acceptance handoff.
3. The next integration step if it passes.
```

## Optional sections

Add only those the application needs:

- **Module boundaries and communications** for multi-process, ROS 2, remote, or
  multi-container systems.
- **Environment and deployment detail** when GPU, system dependencies, or
  local/remote parity is a real risk.
- **Data lifecycle** for dataset sourcing, storage, recording, publication, or
  model artifacts.
- **Skill routing** when several Robium skills will be used across phases.
- **Alternatives considered** for a material product or stack choice.

## Updating the record

- Replace a provisional assumption with evidence as soon as a cheap probe
  resolves it.
- Treat a failed probe as information, not a specification violation. Use the
  documented authorized pivot when it remains within the approved direction.
- Ask for another direction decision only when the evidence creates a material
  product choice, scope expansion, external-cost action, or safety concern.
- Set the record to `superseded` only for a genuine re-architecture. Ordinary
  implementation discoveries are normal edits to the active record.

See `../examples/architecture-brief-example.md` for a filled instance; older
examples may be more detailed than a small project requires.
