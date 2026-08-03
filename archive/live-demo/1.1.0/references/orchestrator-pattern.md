# The orchestrator: who starts the instance

The gateway (`gateway-pattern.md`) lives *inside* the demo container, and
that ceiling is structural: **it cannot manage its own lifecycle**, because
it dies with the container it would have to restart. A browser can't fill
the gap either — no web page starts a container. So a demo whose page has a
real Start button needs a third party that outlives any instance: a
host-level **orchestrator**.

On Cloud Run this role is played *for* you (the control plane cold-boots an
instance on the first request, which is why the deep-link flow needs no
orchestrator at all). The moment you want the same demo to run locally —
for development, for a laptop demo, for a self-hosted deployment — you have
to build that control plane yourself, and discover it was a distinct
component all along. Verified end-to-end 2026-07-13 (nav-trial demo v4):
page Start spawns a fresh container on an ephemeral port → sim ready at
RTF 1.2 → Stop removes it, with no manual `make demo` anywhere.

## The split

Draw the line by lifetime, and keep the orchestrator **out of the data
path** — it is a control plane, not a proxy. Visitor bytes (the viewer
WebSocket, the terminal, logs) go browser → instance gateway directly.

| | Orchestrator (host, always on) | Gateway (in-container, per instance) |
| --- | --- | --- |
| Lifetime | Outlives every instance | Dies with its instance |
| Owns | start / stop / list, fleet cap, port + domain-ID allocation | session claim, readiness, ws tunnel, shutdown |
| Knows | *which* instances exist | everything *inside* one instance |
| In the data path? | **No** — hands the browser a connect host and gets out of the way | Yes — every visitor byte |

A small Node/TS service with `dockerode` is enough; the whole surface is
`POST /instances` (returns the connect host), `DELETE /instances/:id`,
`GET /instances`.

## The driver seam

The one design decision worth making up front: put the container backend
behind a `Driver` interface, not inline `dockerode` calls.

```ts
interface Driver {
  start(app: string): Promise<{ id: string; host: string }>  // host the browser connects to
  stop(id: string): Promise<void>
  list(): Promise<Instance[]>
}
```

`LocalDockerDriver` (dockerode, ephemeral host port) and a future
`CloudRunDriver` (Admin API, service URL) then satisfy the same contract,
and the page's Start/Stop mean the same thing in both worlds. Without the
seam, "run the demo locally" quietly becomes a fork of the demo.

This is also what fixes the local-dev weirdness people paper over: cloud
Stop semantics ("dispose the container") are *wrong* against a warm local
container you didn't start, so the temptation is a `if (localhost)`
special-case. Don't — make Stop genuinely remove and Start genuinely spawn
everywhere, and the special case evaporates.

## Per-instance `ROS_DOMAIN_ID` (not optional)

The orchestrator's first real bug. Every ROS container in a project
normally pins one `ROS_DOMAIN_ID` (integration's guidance, and correct for
one-stack-per-host). Concurrent instances on a shared Docker network make
that pin actively wrong: the graphs **merge**, so two Gazebo servers
publish `/clock` into one graph and the logs flood forever with

```
[robot_state_publisher] Moved backwards in time, re-publishing joint transforms!
```

— physics nonsense, not a discovery error, which is what makes it slow to
diagnose. The driver must assign the **lowest free domain ID (1–200)** per
instance, label the container with it, and exclude in-use IDs. (gz-transport
needs no equivalent fix: `GZ_RELAY=127.0.0.1` is loopback-only, so each
container's gz discovery is already private to it.)

## Fleet cap

The orchestrator owns the budget, because it is the only component that can
count. `list()` filtered by label → refuse `start` past the cap with a
"all robots busy" response the page can render. On Cloud Run the equivalent
number comes from Cloud Monitoring (see `cloud-run-tuning.md`); behind the
`Driver` seam the page doesn't care which.

## In-browser terminal (PTY over WebSocket)

If the demo's pitch is "you get a real machine", the console has to be a
real shell, and that is less work than it sounds: **xterm.js** in the page,
a **PTY over WebSocket** on the gateway.

- Server: `pty.fork()` + `os.execvp('bash', ...)` in the child, then pipe
  bytes both ways between the master fd and the socket.
- No `ws` dependency needs to enter the container — hand-rolling the
  RFC 6455 frame codec (mask/unmask, opcodes, close) is ~40 lines of
  stdlib, and the gateway is already doing raw socket work for its tunnel.
- Resize: forward xterm's `onResize` as a control message → `TIOCSWINSZ`.

A public shell is a real attack surface and needs a threat model before it
ships — container escape is the least of it; the exposures that matter are
the instance's **credentials** and its **network egress**. robium has a
candidate hardening shape for this (zero-role service account + locked-down
egress) that is deployed but not yet verified end-to-end, so this skill
does not yet prescribe it. Until it does: don't put a public shell on a
container that holds any credential you'd mind losing.

## Local development loop

Worth ten minutes on day one; these are the difference between a demo you
can iterate on and one you fight.

- **`?host=` switcher** on the demo page — point a hot-reloading frontend
  at either the deployed backend or a local orchestrator without a rebuild.
- **Same-site subdomain** (`demo.<your-domain>`) + `credentials:'include'`
  + localhost origins allowed in the gateway's CORS, so the Cloud Run
  affinity cookie actually rides (see `cloud-run-tuning.md`).
- **One `npm run dev`** that boots the site *and* the orchestrator together
  (`concurrently`) — a demo whose backend has to be started by hand is a
  demo that gets tested rarely.
