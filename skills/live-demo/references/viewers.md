# Viewer and interaction adapters

Choose the surface that exposes the demo outcome with the least extra runtime.
The shared Live page owns lifecycle state, boot logs, countdown, and stop; the
adapter owns only viewer URL formation and rendering.

| Surface | Prefer it when | Boundary |
| --- | --- | --- |
| Gradio | A policy or model needs structured inputs, progress, images, or video | Mount the app behind the session gateway; Gradio does not require Spaces |
| Self-hosted Lichtblick | A public ROS viewer must be inspectable and usable without a managed-viewer login | Route bridge protocol and layouts to `foxglove` |
| Foxglove deep link | A managed client and its current access model are acceptable | Verify current deep-link and account behavior in official Foxglove docs |
| Custom UI | The interaction cannot fit a maintained adapter | Keep the lifecycle contract shared and isolate only app-specific controls |

Do not embed a developer viewer merely to make the page look active. Gate the
surface on app-specific readiness and prove the real interaction through the
same route a visitor uses.

## Gradio behind the gateway

- Prefer mounting Gradio into the service that already owns lifecycle routes,
  for example with the current official `gr.mount_gradio_app` API, rather than
  adding another public port. Verify the API against
  [Gradio's official mounting documentation](https://www.gradio.app/docs/gradio/mount_gradio_app).
- A browser-provided claim ID only coordinates first use. If the demo is not
  otherwise trusted, validate a host-issued signed or high-entropy capability
  before serving `/ui`, API calls, files, queues, or WebSocket routes.
- A single local instance cannot rely on a 503 being rerouted to fresh capacity.
  Refreshing or replacing a claim can leave the old Gradio generator running
  after its browser has gone away.
- Give each run a cancellation token such as a `threading.Event`, signal it
  when the claim changes or the instance stops, and check it at meaningful
  boundaries inside long generators or robot actions.
- Acquire exclusive model, simulator, or hardware locks with a bounded timeout.
  Report busy/cancelled state and release in `finally`; an abandoned run must
  not block the next visitor forever.

Validate takeover or refresh, cancellation during a long run, bounded lock
failure, normal completion, and authoritative teardown. Viewer styling remains
isolated from the project shell; `app-publishing` owns that framing.
