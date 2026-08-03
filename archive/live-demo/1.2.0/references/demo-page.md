# The mission-control demo page

Anatomy and session flow of `/demos/<app>` — as shipped on
robium.ai/demos/nav-trial (2026-07-13).

## Anatomy (top → bottom)

1. **Controls bar:** status pill (`idle → starting… → booting… →
   ready · rtf <x> → ended/busy`) · **Start instance** (primary) ·
   **Stop instance** (disabled until started) · **Open in Foxglove →**
   (disabled until `ready:true`; `target="_blank"`).
2. **Lede paragraph:** one honest sentence per fact — what boots, how
   long it takes, that closing the tab stops the instance — plus the
   fleet line (static "budget: N concurrent instances" before a session,
   live "running: n of N" during one).
3. **The terminal — the page's majority element** (~50 vh): a header
   status line (`uptime · nodes · session ends in mm:ss`) over a
   scrolling log fed by the gateway's `log[]` (real stack output, not
   theater). Before Start it shows a usage legend; boot phases and
   watchdog retries narrate themselves.
4. **Viewer setup hint:** layout-file download link + the one-time
   "Layout → Import" instruction (needed for the app.foxglove.dev
   flow; a self-hosted viewer with a baked layout deletes this block).
5. **Reproduction story:** the brief that produced the app (verbatim),
   link to the source repo, and a "Get the plugin" CTA — the demo's job
   is selling the workflow, not just the robot.

## Session JS flow (the whole contract)

```
Start click:  session = crypto.randomUUID()
              POST /start?session   (503 → "all robots busy" + reset)
              poll GET /status?session every 2 s  (credentials:'include')
Poll:         409           → transient note, keep polling
              claimed:false → re-POST /start (watchdog restarted the
                              instance; re-claim silently)
              ready:true    → unlock viewer button with
                              app.foxglove.dev/~/view?ds=foxglove-websocket
                              &ds.url=<urlencoded wss://host/?session=UUID>
Stop click:   POST /shutdown?session → reset UI
Tab close:    pagehide → navigator.sendBeacon(/shutdown?session)
```

All demo-host fetches carry `credentials:'include'` (same-site affinity
cookie — see cloud-run-tuning.md). No polling before Start (cost).

**The stale-host trap.** As soon as Start picks the backend host at runtime
(an orchestrator hands back a per-instance host/port — see
`orchestrator-pattern.md`), a `setInterval` poll created before that point
closes over the *old* host and cheerfully polls the wrong backend forever.
It fails in a maddening way: parts of the page that re-render (a log
stream in a child component) look perfectly alive while the ready-state
never flips and the viewer button never unlocks. Poll through a ref
(`hostRef.current`), never the `host` captured at interval-creation time.
Applies to any UI whose backend address can change mid-session.

## Placement on the site

- The homepage apps/proof card for the app carries the primary
  **"Try the live demo →"** button to `/demos/<app>/` (trailing slash —
  behind Cloud Run, nginx needs `absolute_redirect off;` or slash-less
  URLs redirect to an unreachable internal port).
- The demo page is part of the site's smoke test: assert the Start
  button, the demo host string, the shutdown wiring, the budget text,
  and the homepage link in the built HTML.

## Copy honesty checklist

- Cold boot: "30–90 s; unlucky boots self-restart once — the terminal
  narrates" (matches the watchdog reality).
- Session cap and busy state: say the cap (e.g. 30 min) and the budget;
  on 503 tell them to retry in a few minutes.
- Foxglove account: say a free login is needed *before* they click.
