# Hosted session UI contract

The public project/publishing shell is owned by the app-publishing skill. This
reference owns the runtime states and transitions rendered inside its Live
surface.

## Shared lifecycle

```text
idle
  -> explicit Start
allocating
  -> provider returns instance ID
booting
  -> host/capability appears; claim gateway; poll readiness
ready
  -> render viewer; show remaining time; allow restart/stop
stopping
  -> orchestrator confirms deletion
idle or expired
```

Errors do not erase an existing instance ID. If the controller is temporarily
unreachable, keep polling the same session and offer Stop/Delete rather than
allocating another paid instance.

## Required visible states

- **Idle:** exact runtime that will start, expected session length, and an
  explicit Start action.
- **Allocating:** provider/capacity check in progress. Avoid fake percentage
  progress.
- **Booting:** real provider or gateway messages and a bounded startup
  expectation.
- **Ready:** healthy state, remaining time, viewer, restart, stop/delete, guide,
  and source links.
- **Busy/budget exhausted:** distinguish capacity from a technical failure and
  say when retry is reasonable.
- **Reconnecting:** keep the current instance; do not silently allocate a
  replacement.
- **Stopping/expired:** make deletion/end state unambiguous.

## Browser mechanics

- Generate or receive one opaque session/instance ID per start.
- Store the current host and capability in a ref/current-state cell read by the
  poll loop; do not close over the pre-allocation host.
- Claim the gateway when its host first appears or changes.
- Poll the orchestrator during allocation/deletion and the gateway for app
  readiness/metrics when a protected host exists.
- Render the viewer only after readiness.
- Use `pagehide`/`beforeunload` beacon teardown only as a best effort; provider
  expiry and orchestrator cleanup remain authoritative.
- Never poll or fetch fleet/provider state from catalog or overview pages.

## Reusable boundary

Share the lifecycle hook/state machine, top status bar, start/restart/stop
controls, boot log, error strip, countdown, and responsive viewer frame. An app
adapter supplies titles/copy, current availability, guide/source URLs, and a
viewer URL function. Evidence panels and interaction-specific controls remain
app-specific children of that shell.
