# The session gateway pattern

One stdlib-python asyncio process inside the demo container, owning the
Cloud Run port. It is the only public surface; the visualization bridge
moves to an internal port behind it. Production reference:
`examples/demo_gateway.py` (verified 2026-07-13, nav-trial).

## Why a gateway at all

Cloud Run routes exactly one port, and three demo needs share it: the
viewer's WebSocket, a status feed for the demo page's terminal, and a
stop control. Vanilla nginx can't express the session-claim logic, and a
separate status server can't guarantee it lands on the same instance;
one process that tunnels AND owns session state is the smallest correct
shape.

## Endpoint contract

| Route | Behavior |
| --- | --- |
| `POST /start?session=U` | Claim the instance for U. 503 `busy` if a live tunnel belongs to another session. Starts the session clock. |
| ws upgrade (any path, `?session=U`) | Raw byte tunnel to the bridge (internal port). Claims like /start. One live tunnel max: a second concurrent viewer gets 503 (their retry reaches a fresh instance since this one reports busy). |
| `GET /status?session=U` | 200 JSON `{claimed, ready, rtf, nodes, uptime_s, remaining_s, fleet:{running,budget}, log:[…]}`; **409** if claimed by a different session. Unclaimed instances answer (booting state); the page re-claims via /start when it sees `claimed:false`. |
| `POST /shutdown?session=U` | 200 then SIGINT to PID 1 → the launch shuts down → container exits → instance gone. **403** on session mismatch. |

## Claim semantics (the part that took iteration)

- A claim is sacred **only while its tunnel is live**. Concurrent foreign
  ws → 503 (hijack guard).
- An **idle claim is takeable** by a new session; this is the page-reload
  path: the new UUID + affinity cookie land on the old, already-booted
  instance and inherit it (instant ready). Without takeover, reloads 503
  for up to ~15 min of instance retention.
- Session clock (`claimed_at`) resets when a *different* session takes
  over; survives same-session reconnects.

## Readiness + status data

A status node in the app (e.g. extending the auto-init node) writes
`/tmp/demo_status.json` every ~2 s: `{start, ready, rtf, nodes, log:[last
~40 rosout lines]}`. The gateway serves it with session/uptime/fleet
folded in. Readiness is app-defined; log a greppable line
(`DEMO READY rtf=…`); the demo smoke and cloud verification key on it.

## Boot watchdog (required for gz-based sims on Cloud Run)

gz-transport's relay discovery loses a sticky per-boot race (see
cloud-run-tuning.md): the same status node watches for first sim data
(e.g. `/odom`) with a ~120 s deadline; on miss it logs a retry line,
writes status, and SIGINTs PID 1. The client's auto-reconnect (viewer) or
poll-triggered re-claim (page) gets a fresh instance. Converts a ~50%
boot failure into a bounded retry.

## Hard-won details

- Every HTTP response carries `Connection: close` (Cloud Run proxy pools
  keep-alive; silent close = edge 503 "malformed").
- Exact-origin CORS + `Access-Control-Allow-Credentials: true` (the page
  fetches with `credentials:'include'` so the affinity cookie rides).
- `os.kill(1, SIGINT)`: SIGTERM to PID 1 is dropped by the kernel
  (`ros2 launch` installs no handler).
- The ws tunnel is a dumb byte pipe (`asyncio.gather(pipe(a,b),
  pipe(b,a))`); no ws parsing needed beyond detecting the Upgrade
  header and forwarding the original request bytes.
