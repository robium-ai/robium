# indoor-navigation Two-Flavor Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the indoor-navigation demo into two flavors sharing one container: a browser live demo with an embedded, container-served Lichtblick viewer, and a self-contained run-it-locally experience at http://localhost:8765; archive today's IDE-workspace version as a sibling app.

**Architecture:** The demo image bakes in the Lichtblick web bundle (extracted from the official `ghcr.io/lichtblick-suite/lichtblick` image) with the nav layout injected as its default layout. The session gateway loses `/pty` and `/fs/*` and gains static serving of the viewer plus an auto-connect redirect, so viewer and WebSocket are same-origin in both flavors. The robium.ai page becomes a slim two-path page that iframes the instance-served viewer; the orchestrator is untouched except for stale image/package names.

**Tech Stack:** ROS 2 Jazzy, Nav2, Gazebo Harmonic, Docker/compose, stdlib-asyncio Python gateway, Lichtblick web build (caddy-less, served by the gateway), Astro + React (website), Node/Fastify orchestrator.

**Spec:** `docs/superpowers/specs/2026-08-03-indoor-navigation-two-flavor-demo-design.md` (robium repo)

## Global Constraints

- Apps work happens in the existing worktree: `/Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation` (branch `work/indoor-navigation`). Website work happens in `/Users/mdemirst/repos/robium-website` on a new branch `nav-two-flavor-demo`.
- Two-hats rule: never edit robium `skills/**` during this build. Capture learnings to `/Users/mdemirst/repos/robium/learnings/2026-08-03-indoor-navigation.md` the moment friction happens (schema v2 first line: `[skill] signal-type <!-- id: lrn-0803-NN -->`).
- REGISTRY.md updates land in the SAME commit as the app change they describe.
- macOS host: `timeout(1)` does not exist; use bounded shell loops (the Makefile already does).
- No em dashes in any prose or docs written for these repos.
- Commit messages end with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- The app pass bar `make smoke` must remain green and UNCHANGED in behavior for `indoor-navigation`.
- Verified upstream facts used below (all by direct fetch on 2026-08-03, from lichtblick-suite/lichtblick@main): web assets live at `/src` inside `ghcr.io/lichtblick-suite/lichtblick:latest`; `index.html` contains the literal placeholder `/*LICHTBLICK_SUITE_DEFAULT_LAYOUT_PLACEHOLDER*/` for default-layout injection; URL params `ds=foxglove-websocket` (id confirmed in FoxgloveWebSocketDataSourceFactory.ts) and `ds.url=<ws-url>` auto-open the connection (appURLState.ts); `layoutUrl` exists but requires absolute http/https URLs, and we do NOT need it (we bake the default layout instead).

## File Structure

robium-apps (worktree):

```
indoor-navigation-workspace/        # Task 1: verbatim copy of today's app (image retagged)
indoor-navigation/
├── docker/Dockerfile               # Task 2: + lichtblick stage, asset copy, layout injection
├── lichtblick/nav-layout.json      # Task 2: new, default layout for the bundled viewer
├── scripts/demo_gateway.py         # Task 3: slim + static serving + auto-connect redirect
├── Makefile                        # Task 4: demo-smoke reshaped
├── tests/pty_probe.py              # Task 3: deleted (lives on in the workspace copy)
├── README.md                       # Task 5: local-first quickstart rewrite
REGISTRY.md                         # Tasks 1 & 5: workspace card added, nav card updated
```

robium-website (branch `nav-two-flavor-demo`):

```
demo-orchestrator/src/demos/nav-trial.json   # Task 7: post-rename image/package names
src/components/demo/NavLiveDemo.tsx          # Task 8: new slim live-demo component
src/pages/demos/nav-trial.astro              # Task 8: swaps Workspace for NavLiveDemo
src/lib/demoClient.ts                        # Task 8: + viewerUrl helper
tests/ (site smoke)                          # Task 9: assertions updated
```

---

### Task 1: Archive the workspace flavor as `indoor-navigation-workspace/`

**Files:**
- Create: `indoor-navigation-workspace/` (copy of `indoor-navigation/`)
- Modify: `indoor-navigation-workspace/docker/compose.yaml` (image tag)
- Modify: `indoor-navigation-workspace/README.md` (title + shelved note)
- Modify: `indoor-navigation-workspace/Makefile` (remove Cloud Run deploy targets)
- Modify: `REGISTRY.md` (quick-index row + card)

**Interfaces:**
- Consumes: nothing from other tasks (runs first, against today's tree).
- Produces: a frozen-but-runnable sibling app; later tasks may delete workspace-only files from `indoor-navigation/` because this copy preserves them.

- [ ] **Step 1: Copy the app directory**

```bash
cd /Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation
cp -R indoor-navigation indoor-navigation-workspace
```

- [ ] **Step 2: Retag the image so the two apps cannot clobber each other**

In `indoor-navigation-workspace/docker/compose.yaml` change:

```yaml
  image: indoor-navigation:latest
```

to:

```yaml
  image: indoor-navigation-workspace:latest
```

- [ ] **Step 3: Mark the app shelved in its README and Makefile**

In `indoor-navigation-workspace/README.md`, change the H1 to `# indoor-navigation-workspace` and insert directly under it:

```markdown
The IDE-workspace flavor of indoor-navigation: the same sim/SLAM/nav stack
plus a browser file tree, editor, and PTY terminal served by the demo
gateway. Shelved 2026-08-03: runnable and deployable, but not routed on
robium.ai (the slim two-flavor demo in ../indoor-navigation replaced it).
```

In `indoor-navigation-workspace/Makefile`, delete the `demo-image` and `demo-deploy` targets and the `DEMO_IMAGE` variable (this copy must never push to the `demo-nav-trial` Cloud Run service), and remove `demo-image demo-deploy` from the `.PHONY` line. Delete `indoor-navigation-workspace/cloudbuild.yaml`.

- [ ] **Step 4: Build and run the workspace demo gate**

```bash
cd indoor-navigation-workspace
make build          # cache-warm, minutes not tens of minutes
make demo-smoke     # full original gate incl. PTY probe and fs API
make down
```

Expected: `DEMO SMOKE PASS`. If the WS ready-loop times out, re-run once (local boots are reliable; see the app brief).

- [ ] **Step 5: Add the registry row + card**

In `REGISTRY.md` quick index, add below the indoor-navigation row:

```markdown
| [indoor-navigation-workspace](#indoor-navigation-workspace) | Classical ROS navigation (IDE-workspace demo) | ROS 2 Jazzy + Nav2 + slam_toolbox | Gazebo Harmonic (headless) | Docker (arm64) | Foxglove (browser) + in-page IDE | `make smoke` / `make demo-smoke` | 2026-08-03 |
```

Add a card after the indoor-navigation card:

```markdown
### indoor-navigation-workspace

**One-liner:** the shelved IDE-workspace flavor of indoor-navigation: same
TB3 SLAM/Nav2 stack, plus the demo gateway's browser file tree, editor, and
PTY terminal. Kept runnable as the reference for the gateway's /pty and
/fs/* surfaces; not routed on robium.ai.

- **Stack/Env/Pass bar:** identical to indoor-navigation as of 2026-08-03
  (image tag `indoor-navigation-workspace:latest`); Cloud Run deploy targets
  removed on purpose.
- **Why it exists:** the two-flavor demo redesign (see the robium repo spec
  docs/superpowers/specs/2026-08-03-indoor-navigation-two-flavor-demo-design.md)
  removed the workspace surfaces from the live app; this copy preserves them
  as working code, per the archive decision.
- **Bootstrap for:** any in-container browser IDE surface (PTY over
  WebSocket, jailed fs API, session guards) worth grafting onto another demo.
```

- [ ] **Step 6: Commit (app + registry together)**

```bash
cd /Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation
git add indoor-navigation-workspace REGISTRY.md
git commit -m "feat: archive IDE-workspace demo flavor as indoor-navigation-workspace

Verbatim copy of indoor-navigation before the two-flavor slimming; image
retagged, Cloud Run deploy targets removed, registry card added. demo-smoke
passes.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Bake the Lichtblick viewer into the demo image

**Files:**
- Create: `indoor-navigation/lichtblick/nav-layout.json`
- Modify: `indoor-navigation/docker/Dockerfile`
- Modify: `indoor-navigation/.dockerignore` (ensure `lichtblick/` not excluded)

**Interfaces:**
- Consumes: nothing.
- Produces: `/opt/lichtblick/` inside the image (static web bundle, `index.html` with the nav layout injected as default). Task 3's gateway serves exactly this directory as `STATIC_ROOT = '/opt/lichtblick'`.

- [ ] **Step 1: Create the default layout**

```bash
cd /Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation/indoor-navigation
mkdir lichtblick
cp foxglove/indoor-navigation-layout.json lichtblick/nav-layout.json
```

The committed Foxglove layout is already LayoutData-shaped (`configById`, `globalVariables`, `userNodes`, `playbackConfig`, `layout`), which is the shape the Lichtblick placeholder expects. Visual verification happens in Task 4 Step 4; adjust panels there if Lichtblick renders any of them empty.

- [ ] **Step 2: Add the Lichtblick stage to the Dockerfile**

At the very top of `indoor-navigation/docker/Dockerfile`, before `FROM ros:jazzy-ros-base-noble`, add:

```dockerfile
# Lichtblick web bundle donor. Assets are arch-neutral JS/wasm, so pinning
# the platform lets arm64 hosts pull the amd64 image just to copy files.
# Web assets live at /src in this image; index.html carries the literal
# /*LICHTBLICK_SUITE_DEFAULT_LAYOUT_PLACEHOLDER*/ token for default-layout
# injection (both verified against lichtblick-suite/lichtblick@main
# Dockerfile by direct fetch, 2026-08-03).
FROM --platform=linux/amd64 ghcr.io/lichtblick-suite/lichtblick:latest AS lichtblick
```

Then after the `COPY docker/entrypoint.sh /entrypoint.sh` line, add:

```dockerfile
# Bundled viewer: the demo gateway serves /opt/lichtblick on non-API GETs.
COPY --from=lichtblick /src /opt/lichtblick
COPY lichtblick/nav-layout.json /opt/lichtblick/nav-layout.json
RUN python3 - <<'PYEOF'
from pathlib import Path
idx = Path('/opt/lichtblick/index.html')
html = idx.read_text()
token = '/*LICHTBLICK_SUITE_DEFAULT_LAYOUT_PLACEHOLDER*/'
assert token in html, 'Lichtblick default-layout placeholder missing: upstream image changed, re-verify'
layout = Path('/opt/lichtblick/nav-layout.json').read_text()
idx.write_text(html.replace(token, layout))
print('lichtblick default layout injected')
PYEOF
```

- [ ] **Step 3: Verify `.dockerignore` does not exclude `lichtblick/`**

```bash
cat .dockerignore
```

If it uses an allowlist pattern, add `!lichtblick/`; if a denylist, confirm nothing matches `lichtblick/`.

- [ ] **Step 4: Build and assert the assets landed**

```bash
make build
docker run --rm --entrypoint bash indoor-navigation:latest -lc \
  "ls /opt/lichtblick/index.html && grep -c configById /opt/lichtblick/index.html && ! grep -q LICHTBLICK_SUITE_DEFAULT_LAYOUT_PLACEHOLDER /opt/lichtblick/index.html && echo INJECTED"
```

Expected: the index path prints, `configById` count >= 1, and `INJECTED`.

- [ ] **Step 5: Pin the donor image**

```bash
docker buildx imagetools inspect ghcr.io/lichtblick-suite/lichtblick:latest | head -5
```

Replace `:latest` in the new `FROM` line with `@sha256:<digest printed above>` and add a comment `# lichtblick <version-or-date> pinned 2026-08-03`. Rebuild (`make build`) to confirm the pin resolves.

- [ ] **Step 6: Commit**

```bash
git add docker/Dockerfile lichtblick/ .dockerignore
git commit -m "feat: bundle Lichtblick web viewer in the demo image

Assets copied from the pinned official image; nav layout injected as the
viewer's default via the upstream index.html placeholder.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Slim the gateway and serve the viewer

**Files:**
- Modify: `indoor-navigation/scripts/demo_gateway.py`
- Delete: `indoor-navigation/tests/pty_probe.py`

**Interfaces:**
- Consumes: `/opt/lichtblick` from Task 2.
- Produces: gateway HTTP contract used by Task 4's smoke and Task 8's page:
  - `GET /` with no `ds` query param: `302` to `/?ds=foxglove-websocket&ds.url=<url-encoded ws(s)://host/?session=...>[&session=...]`
  - `GET <asset path>`: `200` with the file from `/opt/lichtblick` (traversal-jailed; directories resolve to their index.html; no SPA fallback, missing paths 404)
  - `GET /fs/list` (and any unknown path): `404` JSON `{"error": "not found"}`
  - WS upgrade, `/start`, `/status`, `/shutdown`, `/logs`, CORS preflight: unchanged from today.

- [ ] **Step 1: Delete the workspace-only code**

In `scripts/demo_gateway.py` remove:
- the `import pty` line (keep `signal`; keep `base64`/`hashlib`, still used by `ws_accept` for `/logs`)
- the `ws_unframe` function (only the PTY read path used it)
- `WORKSPACE_ROOT = '/ws'  # fs API jail`
- the `safe_path` function
- the whole `pty_bridge` function
- the `/pty` upgrade route block (`if is_upgrade and url.path == '/pty': ...`)
- the whole `/fs/` route block (`if url.path.startswith('/fs/'): ...`)
- in the module docstring, the route list lines describing pty/fs surfaces

- [ ] **Step 2: Add static serving constants and helpers**

After the `WS_GUID` constant, add:

```python
STATIC_ROOT = '/opt/lichtblick'  # bundled Lichtblick web build (Dockerfile)
MIME = {
    '.html': 'text/html; charset=utf-8', '.js': 'application/javascript',
    '.css': 'text/css', '.json': 'application/json', '.map': 'application/json',
    '.wasm': 'application/wasm', '.svg': 'image/svg+xml', '.png': 'image/png',
    '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff',
    '.webp': 'image/webp', '.txt': 'text/plain',
}


def static_file(path):
    """Resolve a URL path to (bytes, mime) under STATIC_ROOT, or None."""
    full = os.path.realpath(os.path.join(STATIC_ROOT, (path or '/').lstrip('/')))
    if full != STATIC_ROOT and not full.startswith(STATIC_ROOT + '/'):
        return None
    if os.path.isdir(full):
        full = os.path.join(full, 'index.html')
    if not os.path.isfile(full):
        # No SPA fallback on purpose: Lichtblick routes via query params
        # only, and a fallback would 200 the removed /pty and /fs/* paths.
        return None
    with open(full, 'rb') as f:
        data = f.read()
    return data, MIME.get(os.path.splitext(full)[1].lower(), 'application/octet-stream')


def http_bytes_response(status, body, ctype):
    return (f'HTTP/1.1 {status}\r\nContent-Type: {ctype}\r\n'
            f'Content-Length: {len(body)}\r\nCache-Control: no-cache\r\n'
            'Connection: close\r\n\r\n').encode() + body
```

- [ ] **Step 3: Add the auto-connect redirect**

In `handle()`, directly after the `OPTIONS` preflight block, add:

```python
    # Viewer front door: bare GET / bounces to the bundled Lichtblick with
    # ds params targeting this same host (ws locally, wss behind TLS).
    if method == 'GET' and url.path == '/' and 'ds' not in parse_qs(url.query):
        host, proto = f'localhost:{PORT}', 'ws'
        for line in head.split('\r\n'):
            low = line.lower()
            if low.startswith('host:'):
                host = line.split(':', 1)[1].strip()
            elif low.startswith('x-forwarded-proto:') and 'https' in low:
                proto = 'wss'
        ws_url = f'{proto}://{host}/' + (f'?session={session}' if session else '')
        target = ('/?ds=foxglove-websocket&ds.url=' + quote(ws_url, safe='')
                  + (f'&session={session}' if session else ''))
        writer.write((f'HTTP/1.1 302 Found\r\nLocation: {target}\r\n'
                      'Content-Length: 0\r\nConnection: close\r\n\r\n').encode())
        await writer.drain(); writer.close(); return
```

(`quote` is already imported from urllib.parse.)

- [ ] **Step 4: Replace the catch-all JSON response with static-then-404**

Replace the final three lines of `handle()`:

```python
    writer.write(http_response('200 OK', json.dumps({'service': 'robium demo gateway'})))
    await writer.drain()
    writer.close()
```

with:

```python
    if method == 'GET':
        res = static_file(url.path)
        if res is not None:
            body, ctype = res
            writer.write(http_bytes_response('200 OK', body, ctype))
            await writer.drain()
            writer.close()
            return
    writer.write(http_response('404 Not Found', json.dumps({'error': 'not found'})))
    await writer.drain()
    writer.close()
```

- [ ] **Step 5: Syntax check and delete the PTY probe**

```bash
python3 -m py_compile scripts/demo_gateway.py && echo OK
git rm tests/pty_probe.py
```

- [ ] **Step 6: Manual container probe (compose bind-mounts scripts, no rebuild needed)**

```bash
docker compose -f docker/compose.yaml --profile demo up -d demo
sleep 5
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' http://localhost:8765/          # expect 302 with ds params
curl -sL http://localhost:8765/ | grep -qi '<html' && echo VIEWER_HTML_OK
curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8765/fs/list?path=src"        # expect 404
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8765/status                     # expect 200
docker compose -f docker/compose.yaml --profile "*" down --remove-orphans
```

- [ ] **Step 7: Commit**

```bash
git add scripts/demo_gateway.py
git commit -m "feat: slim demo gateway to viewer + session API

Drop /pty and /fs/* (preserved in indoor-navigation-workspace); serve the
bundled Lichtblick build on non-API GETs with an auto-connect redirect on
bare /. Unknown paths now 404.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Reshape demo-smoke and pass it

**Files:**
- Modify: `indoor-navigation/Makefile` (demo-smoke target)

**Interfaces:**
- Consumes: gateway contract from Task 3, image from Task 2.
- Produces: the demo pass bar later tasks and the registry card cite.

- [ ] **Step 1: Edit the demo-smoke target**

Replace these four lines inside `demo-smoke`:

```make
	python3 tests/pty_probe.py localhost smoke
	curl -sf "http://localhost:8765/fs/list?session=smoke&path=src" | grep -q indoor_nav_bringup
	curl -sf "http://localhost:8765/fs/write?session=smoke&path=robium_demo_t.txt" --data "hello-fs" | grep -q '"ok": true'
	curl -sf "http://localhost:8765/fs/read?session=smoke&path=robium_demo_t.txt" | grep -q hello-fs
	test "$$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8765/fs/read?session=smoke&path=../../etc/passwd")" = "400"
```

with:

```make
	test "$$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8765/?session=smoke")" = "302"
	curl -sfL "http://localhost:8765/?session=smoke" | grep -qi "<html"
	test "$$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8765/fs/list?session=smoke&path=src")" = "404"
	test "$$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8765/pty?session=smoke")" = "404"
	test "$$(curl -s -o /dev/null --path-as-is -w '%{http_code}' "http://localhost:8765/../etc/passwd")" = "404"
```

Also update the comment above the target: replace the sentence about session guards to mention the viewer ("assert the gateway tunnels the Foxglove WebSocket, serves the bundled viewer, /status reaches ready, session guards hold, one nav goal succeeds, /shutdown kills the container").

- [ ] **Step 2: Run the gate**

```bash
make demo-smoke
```

Expected: `DEMO SMOKE PASS`.

- [ ] **Step 3: Visual layout verification (operator step)**

```bash
docker compose -f docker/compose.yaml --profile demo up -d demo
```

Open http://localhost:8765 in Chrome. Expected: Lichtblick loads, auto-connects (topic list fills as the stack boots, roughly 30 to 60 s), the default layout shows map/scan/plan panels, and clicking a goal with the layout's publish tool drives the robot. If any panel is blank or the publish tool is missing, edit the layout in-app, export it (Layout menu), overwrite `lichtblick/nav-layout.json` with the export, run `make build`, and re-verify. Then:

```bash
docker compose -f docker/compose.yaml --profile "*" down --remove-orphans
```

- [ ] **Step 4: Commit**

```bash
git add Makefile lichtblick/nav-layout.json
git commit -m "test: demo-smoke gates the bundled viewer, not the workspace APIs

Viewer redirect + HTML assertions in; PTY/fs probes out (they now 404).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: README rewrite + registry card + smoke regression

**Files:**
- Modify: `indoor-navigation/README.md`
- Modify: `REGISTRY.md` (indoor-navigation card + quick-index row)

**Interfaces:**
- Consumes: everything landed in Tasks 1 to 4.
- Produces: the promotion-ready public-facing README; the updated registry.

- [ ] **Step 1: Rewrite the README's demo-facing sections**

Replace the `## Quick start`, `## Visualization`, and `## Live demo (maintainers)` sections with:

```markdown
## Try it in 2 commands

    make build   # one-time image build (about 10 min cold)
    make demo    # full stack: sim + Nav2 + built-in browser viewer

Then open http://localhost:8765 in your browser. The viewer (Lichtblick,
the open-source Foxglove fork, bundled in the image) auto-connects and
shows the map, laser scan, and planned paths. Click a navigation goal with
the layout's publish tool and watch the robot drive itself. Ctrl-C stops
everything.

This is byte-for-byte the same container that powers the live demo at
robium.ai/demos/nav-trial: same simulation, same Nav2 stack, same viewer.

## Other scenarios

- `make smoke`: the pass bar; launches the full nav scenario headless,
  sends two goals, exits 0 on success (about 90 s once built)
- `make sim`: bringup only; `make slam`: rebuild the map; `make nav`:
  navigation without the demo auto-init
- `make check-map`: host-side map sanity check; `make down`: teardown

External viewers still work too: with any scenario running, connect
Foxglove or a local Lichtblick to ws://localhost:8765 (the committed
layout for that flow is foxglove/indoor-navigation-layout.json).

## Live demo (maintainers)

`make demo-smoke` gates the demo scenario (viewer served, session guards,
one goal, shutdown). `make demo-image` + `make demo-deploy` push to Cloud
Run (robium GCP credentials required; not needed for anything else).
The IDE-workspace flavor of this demo lives in ../indoor-navigation-workspace.
```

Keep the intro, `## What you'll see`, `## Prerequisites` (drop the Safari sentence: the bundled viewer is same-origin, plain http), and `## How it's put together` (add one bullet: "the demo image bundles the Lichtblick web viewer; the gateway serves it on :8765 alongside the WebSocket tunnel").

- [ ] **Step 2: Update the registry card**

In the `### indoor-navigation` card: update the **Viz** bullet to "bundled Lichtblick served by the gateway (open http://localhost:8765); Foxglove/external viewers still supported", note the two-flavor split and the workspace sibling, and refresh the **Live demo** bullet to describe the iframe-the-instance-viewer model. In the quick index, change the Viz column to `Lichtblick (bundled, browser)`. Do NOT bump `verified` here; that happens after Task 6's smoke run.

- [ ] **Step 3: Run the app pass bar (regression) and set verified dates**

```bash
make smoke
```

Expected: `PASS: all goals reached`, exit 0. Then set `verified` = today for indoor-navigation in the quick index and confirm the workspace row's date from Task 1 is still accurate.

- [ ] **Step 4: Commit**

```bash
git add README.md ../REGISTRY.md
git commit -m "docs: local-first README + registry cards for the two-flavor demo

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Apps-repo PR

**Files:** none new.

- [ ] **Step 1: Push and open the PR**

```bash
cd /Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation
git push -u origin work/indoor-navigation
gh pr create --repo robium-ai/robium-apps \
  --title "indoor-navigation: two-flavor demo (bundled Lichtblick viewer) + workspace archive" \
  --body "$(cat <<'EOF'
Implements the two-flavor demo design (robium repo:
docs/superpowers/specs/2026-08-03-indoor-navigation-two-flavor-demo-design.md).

- indoor-navigation-workspace/: verbatim archive of the IDE flavor (demo-smoke green)
- indoor-navigation: gateway slimmed (no /pty, /fs), Lichtblick web build baked
  into the image with the nav layout as default, auto-connect redirect on /
- make demo now IS the local flavor: open http://localhost:8765
- demo-smoke reshaped (viewer assertions in, workspace probes out); make smoke untouched
- REGISTRY.md: new workspace card, nav card updated

Companion website PR: robium-website nav-two-flavor-demo (page rebuild + orchestrator config).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 7: Orchestrator config update (website repo)

**Files:**
- Modify: `demo-orchestrator/src/demos/nav-trial.json`

**Interfaces:**
- Consumes: image name `indoor-navigation:latest` and package `indoor_nav_bringup` (existing facts, fixed here).
- Produces: the orchestrator spawns the renamed image; Task 8's page keeps using demo id `nav-trial`.

- [ ] **Step 1: Branch**

```bash
cd /Users/mdemirst/repos/robium-website
git checkout -b nav-two-flavor-demo
```

- [ ] **Step 2: Fix the stale names**

In `demo-orchestrator/src/demos/nav-trial.json` set:

```json
  "image": "indoor-navigation:latest",
```

and in `command`, replace `"nav_trial_bringup"` with `"indoor_nav_bringup"`. Leave id, ports, env, budgets unchanged.

- [ ] **Step 3: Orchestrator tests**

```bash
cd demo-orchestrator && npm test && cd ..
```

Expected: green.

- [ ] **Step 4: Commit**

```bash
git add demo-orchestrator/src/demos/nav-trial.json
git commit -m "fix: nav-trial demo config uses post-rename image and package names

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Rebuild the demo page around the instance-served viewer

**Files:**
- Create: `src/components/demo/NavLiveDemo.tsx`
- Modify: `src/lib/demoClient.ts` (add `viewerUrl`)
- Modify: `src/pages/demos/nav-trial.astro`

**Interfaces:**
- Consumes: `createInstance(demo, session): Promise<{id, host, session}>`, `deleteInstance(id)`, `deleteInstanceBeacon(id)` from `src/lib/orchestrator.ts`; `start(h, s)`, `status(h, s): Promise<Status | null>`, `shutdown(h, s)` and the `Status` type from `src/lib/demoClient.ts`; gateway 302/viewer contract from Task 3.
- Produces: `viewerUrl(h: string, s: string): string` in demoClient; page component `<NavLiveDemo host={string} />`.

- [ ] **Step 1: Add the viewer URL helper to `src/lib/demoClient.ts`**

Next to the existing `foxgloveUrl` helper add:

```ts
// The instance serves its own Lichtblick build; ds params make it
// auto-connect back to the same host (Task 3 gateway contract).
export const viewerUrl = (h: string, s: string) =>
  `${HTTP(h)}/?session=${s}&ds=foxglove-websocket&ds.url=${encodeURIComponent(
    `${WS(h)}/?session=${s}`,
  )}`;
```

- [ ] **Step 2: Create `src/components/demo/NavLiveDemo.tsx`**

Model the lifecycle exactly on `Workspace.tsx` (same mode handling, same refs, same poll/claim loop, same stop/beacon paths) but with the workspace panels replaced by three states:

```tsx
import { useEffect, useRef, useState } from 'react';
import type { Status } from '../../lib/demoClient';
import { start as apiStart, status as apiStatus, shutdown as apiShutdown, viewerUrl } from '../../lib/demoClient';
import { createInstance, deleteInstance, deleteInstanceBeacon } from '../../lib/orchestrator';
import './demo.css';

type Mode = 'orchestrator' | string;

export default function NavLiveDemo({ host: hostProp }: { host: string }) {
  const [mode] = useState<Mode>(() => {
    if (typeof window === 'undefined') return 'orchestrator';
    return new URLSearchParams(window.location.search).get('host') ?? 'orchestrator';
  });
  const [host, setHost] = useState(hostProp);
  const [session, setSession] = useState<string | null>(null);
  const [st, setSt] = useState<Status | null>(null);
  const timer = useRef<number | null>(null);
  const sessionRef = useRef<string | null>(null);
  const instanceRef = useRef<string | null>(null);
  const hostRef = useRef(host);

  function stopPolling() {
    if (timer.current) { clearInterval(timer.current); timer.current = null; }
  }

  async function poll() {
    const s = sessionRef.current;
    if (!s) return;
    const status = await apiStatus(hostRef.current, s).catch(() => null);
    if (!status) return;
    if (!status.claimed) { apiStart(hostRef.current, s).catch(() => {}); return; }
    setSt(status);
  }

  async function begin() {
    const s = crypto.randomUUID();
    sessionRef.current = s;
    setSession(s);
    setSt(null);
    let simHost = host;
    if (mode === 'orchestrator') {
      try {
        const inst = await createInstance('nav-trial', s);
        instanceRef.current = inst.id;
        simHost = inst.host;
      } catch (e) {
        sessionRef.current = null;
        setSession(null);
        alert((e as Error).message);
        return;
      }
    } else {
      simHost = mode;
    }
    hostRef.current = simHost;
    setHost(simHost);
    apiStart(simHost, s).catch(() => {});
    stopPolling();
    timer.current = window.setInterval(poll, 2000);
    poll();
  }

  async function end() {
    stopPolling();
    const id = instanceRef.current;
    const s = sessionRef.current;
    instanceRef.current = null;
    sessionRef.current = null;
    setSession(null);
    setSt(null);
    if (s) apiShutdown(hostRef.current, s).catch(() => {});
    if (id) await deleteInstance(id);
  }

  useEffect(() => {
    const bye = () => { if (instanceRef.current) deleteInstanceBeacon(instanceRef.current); };
    window.addEventListener('beforeunload', bye);
    return () => { window.removeEventListener('beforeunload', bye); stopPolling(); };
  }, []);

  const ready = !!st?.ready;
  return (
    <div className="nav-live-demo">
      {!session && (
        <button className="demo-start" onClick={begin}>Start a private robot</button>
      )}
      {session && !ready && (
        <div className="demo-boot">
          <p>Booting your private simulation (about 30 to 60 s)...</p>
          <pre className="demo-log">{(st?.log ?? ['requesting an instance...']).join('\n')}</pre>
        </div>
      )}
      {session && ready && (
        <>
          <div className="demo-meta">
            <span>RTF {st?.rtf ?? '?'}</span>
            <span>{Math.floor((st?.remaining_s ?? 0) / 60)} min left</span>
            <a href={viewerUrl(host, session)} target="_blank" rel="noreferrer">open in new tab</a>
            <button onClick={end}>Stop</button>
          </div>
          <iframe
            className="demo-viewer"
            src={viewerUrl(host, session)}
            title="Live robot viewer"
            allow="clipboard-write"
          />
        </>
      )}
    </div>
  );
}
```

Add minimal styles for `.nav-live-demo`, `.demo-viewer` (width 100%, height around 75vh, border 0), `.demo-boot pre` (scrollable, monospace) to `demo.css`, following its existing conventions.

- [ ] **Step 3: Rewrite `src/pages/demos/nav-trial.astro`**

Keep the `Base` layout wrapper and page metadata. Replace `Workspace` with `NavLiveDemo` and add the second path as static content under it:

```astro
---
import Base from '../../layouts/Base.astro';
import NavLiveDemo from '../../components/demo/NavLiveDemo.tsx';
---
<Base title="nav-trial live demo · robium"
  description="Drive a live ROS 2 + Nav2 + Gazebo robot simulation in your browser, built end-to-end by an AI coding agent with the Robium plugin.">
  <section>
    <h1>TurtleBot 3 autonomous navigation, live</h1>
    <p>A private Gazebo + Nav2 simulation boots for you on our servers.
       The viewer below is served by that same container. Click a goal
       with the publish tool and the robot plans and drives itself.
       Sessions last 30 minutes; up to 5 robots run at once.</p>
    <NavLiveDemo client:only="react" host="demo.robium.ai" />
  </section>
  <section>
    <h2>Run the same demo on your machine</h2>
    <p>The live demo above is a stock Docker container. Run the identical
       thing locally; the viewer is bundled, nothing else to install:</p>
    <pre><code>git clone https://github.com/robium-ai/robium-apps
cd robium-apps/indoor-navigation
make build   # one-time, about 10 min
make demo    # then open http://localhost:8765</code></pre>
    <p>The repo is the full application robium built: launch files, Nav2
       params, the SLAM-produced map, tests, and the Dockerfile.</p>
  </section>
</Base>
```

(The public robium-apps clone URL is canonical.)

- [ ] **Step 4: Type-check and dev-run**

```bash
npm run build 2>&1 | tail -5    # astro build type errors surface here
```

Expected: build succeeds. Then `npm run dev` (site + orchestrator), open http://localhost:4321/demos/nav-trial with Docker running and `indoor-navigation:latest` built; click Start; expect boot log then the embedded viewer driving topics. If the iframe renders blank while the new-tab link works, capture the console error, apply the spec's fallback (swap the iframe for a prominent "open viewer" button) and note it as a learning.

- [ ] **Step 5: Commit**

```bash
git add src/components/demo/NavLiveDemo.tsx src/components/demo/demo.css src/lib/demoClient.ts src/pages/demos/nav-trial.astro
git commit -m "feat: nav-trial page embeds the instance-served Lichtblick viewer

Replaces the IDE workspace on this page; boot log + countdown + iframe,
plus a run-it-locally section. Workspace components remain for manip/vla.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: Website smoke + PR

**Files:**
- Modify: site smoke tests (locate with `grep -rn "nav-trial" tests/`)

- [ ] **Step 1: Update site smoke assertions**

Wherever tests assert the old page internals (Workspace markup, layout JSON link, app.foxglove.dev deep link), assert instead: page 200, contains "Run the same demo on your machine", and contains `demo.robium.ai`. Keep the `nav-trial-layout.json` static asset test only if other pages still reference the file; otherwise delete the asset and its test.

- [ ] **Step 2: Run the suites**

```bash
npm test
bash demo-orchestrator/scripts/e2e.sh   # needs Docker + indoor-navigation:latest
```

Expected: green. e2e proves the orchestrator spawns the renamed image end to end.

- [ ] **Step 3: Push and PR**

```bash
git push -u origin nav-two-flavor-demo
gh pr create --repo robium-ai/robium-website \
  --title "nav-trial: slim two-flavor demo page (instance-served Lichtblick)" \
  --body "$(cat <<'EOF'
Companion to the robium-apps two-flavor PR. The page drops the IDE
workspace for nav-trial, polls boot status, then iframes the viewer served
by the demo container itself; adds the run-it-locally section. Orchestrator
config updated to post-rename image/package names.

Spec: robium repo docs/superpowers/specs/2026-08-03-indoor-navigation-two-flavor-demo-design.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 10: End-to-end honesty check, learnings, retro

**Files:**
- Modify: `/Users/mdemirst/repos/robium/learnings/2026-08-03-indoor-navigation.md`

- [ ] **Step 1: Clean-clone local-flavor check**

Simulate a visitor: copy the app out of the repo context and follow the README verbatim.

```bash
rm -rf /private/tmp/claude-501/-Users-mdemirst-repos-robium/*/scratchpad/nav-clone 2>/dev/null
SCRATCH=$(ls -d /private/tmp/claude-501/-Users-mdemirst-repos-robium/*/scratchpad | head -1)
cp -R /Users/mdemirst/repos/robium-apps/.worktrees/indoor-navigation/indoor-navigation "$SCRATCH/nav-clone"
cd "$SCRATCH/nav-clone"
make build && make demo
```

Open http://localhost:8765; verify auto-connect, layout, and one clicked goal reaching SUCCEEDED. Ctrl-C, `make down`. Any deviation from the README is a README bug: fix it in the worktree and amend the apps PR.

- [ ] **Step 2: Consolidate learnings**

Ensure every friction hit during Tasks 1 to 9 has an entry in `/Users/mdemirst/repos/robium/learnings/2026-08-03-indoor-navigation.md` (schema v2). Likely candidates to check for: Lichtblick placeholder/params facts (a candidate `visualization`-skill addition: bundling Lichtblick as an in-container viewer), gateway static-serving pattern, iframe embedding behavior.

- [ ] **Step 3: End-of-block retro**

Append the retro block to the same learnings file: one line per robium skill that loaded during the block, scored fired/accurate/complete/lean; clean scores still get a line.

- [ ] **Step 4: Commit learnings (robium repo, main)**

```bash
cd /Users/mdemirst/repos/robium
git add learnings/2026-08-03-indoor-navigation.md
git commit -m "learnings: indoor-navigation two-flavor demo build

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
