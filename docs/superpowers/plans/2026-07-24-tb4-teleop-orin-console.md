# tb4-teleop Orin Web Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An Orin-served web console to drive a real TurtleBot 4 (on-page teleop + dock/undock), show a live USB-webcam feed, and launch Foxglove — all talking browser→robot `foxglove_bridge`, with the Orin running only nginx + a webcam streamer.

**Architecture:** Static page served by nginx on the Orin; the page client-publishes `/cmd_vel` (Twist) and `/teleop/{dock,undock}` (Empty) to the robot's existing `foxglove_bridge` over the Foxglove WebSocket protocol; a USB webcam is streamed as MJPEG by `ustreamer`; an "Open in Foxglove" button deep-links to `app.foxglove.dev`. No ROS on the Orin. Env-configurable so one image repoints at any bridge.

**Tech Stack:** vanilla JS ES modules, `node --test` (unit tests, no deps), nginx:alpine + `envsubst`, `ustreamer` (MJPEG), Docker Compose.

## Global Constraints

- **New phase of the EXISTING `tb4-teleop` app** — build under `apps/tb4-teleop/orin/`; do not create a new app. Leave the Phase-1 `bridge`/`teleop`/`smoke` Makefile targets untouched.
- **No ROS on the Orin.** All robot commands go browser → robot `foxglove_bridge` (`ws://192.168.0.100:8765`, subprotocol `foxglove.sdk.v1`).
- **`/cmd_vel` = `geometry_msgs/msg/Twist`** (plain Twist). Dock/undock = `std_msgs/msg/Empty` on `/teleop/dock` and `/teleop/undock` (Phase-1 `robot/teleop_actions.py` turns those into Create 3 actions; it runs via `make bridge`).
- **Speed caps:** linear ≤ 0.15 m/s, angular ≤ 0.4 rad/s. On-page controls are **hold-to-drive** (publish zero Twist on release / keyup / window blur).
- **Repointable via env:** `ROBOT_HOST` (default `192.168.0.100`), `ROBOT_WS_PORT` (`8765`), `WEBCAM_STREAM_URL` (blank ⇒ hide webcam panel), `FOXGLOVE_LAYOUT_ID` (empty ⇒ omit the param). Also `WEBCAM_DEVICE` (`/dev/video0`) for the streamer.
- **Multi-arch / small images** (Orin is arm64; internet is a metered hotspot — keep pulls small): `nginx:alpine`, `alpine`-built ustreamer.
- **ES modules everywhere:** browser files and Node tests share `web/protocol.js`; `orin/package.json` sets `{"type":"module"}` so `node --test` treats `.js` as ESM and nginx serves `.js` as `application/javascript`.
- **Deep-link (web, no layoutId):** `https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://<host>:<port>` — append `&layoutId=<id>` only when set. `ds.url` is left un-encoded to match Foxglove's documented form.
- **Test bar:** `make orin-smoke` covers the **console contract** (unit tests + the container serving the page). Live webcam and live drive are the **manual HIL bar**, like Phase 1's `make smoke`.
- **Orin access (for HIL tasks):** `ssh robium@192.168.55.1` (USB link, keyless from this Mac); `sudo` needs the operator's password. Board: JetPack 6.2, Docker GPU-ready (not needed here).

---

### Task 1: Scaffold `orin/` + Node test harness + Makefile targets

**Files:**
- Create: `apps/tb4-teleop/orin/package.json`
- Create: `apps/tb4-teleop/orin/web/.gitkeep`, `apps/tb4-teleop/orin/tests/.gitkeep`, `apps/tb4-teleop/orin/docker/.gitkeep`
- Modify: `apps/tb4-teleop/Makefile`

**Interfaces:**
- Produces: `make orin-test` (runs `node --test` in `orin/`), and `orin-build`/`orin-serve`/`orin-smoke`/`orin-down` targets (bodies filled in Task 6). The `{"type":"module"}` package.json every later `.js` relies on.

- [ ] **Step 1: Create `orin/package.json`.**

```json
{
  "name": "tb4-teleop-orin",
  "private": true,
  "type": "module",
  "scripts": { "test": "node --test" }
}
```

- [ ] **Step 2: Create the dir placeholders.** `orin/web/.gitkeep`, `orin/tests/.gitkeep`, `orin/docker/.gitkeep` (empty files).

- [ ] **Step 3: Add Makefile targets** (append to `apps/tb4-teleop/Makefile`, keep existing targets):

```makefile
ORIN := $(HERE)orin

.PHONY: orin-test orin-build orin-serve orin-smoke orin-down

orin-test:
	cd "$(ORIN)" && node --test

orin-build:
	docker compose -f "$(ORIN)/docker/compose.yaml" build

orin-serve:
	docker compose -f "$(ORIN)/docker/compose.yaml" up

orin-smoke:
	cd "$(ORIN)" && node --test
	"$(ORIN)/tests/serve_smoke.sh"

orin-down:
	docker compose -f "$(ORIN)/docker/compose.yaml" down
```

- [ ] **Step 4: Verify the harness runs** (0 tests is fine — it must exit clean).

Run: `cd apps/tb4-teleop/orin && node --test`
Expected: exits 0, "tests 0" (no test files yet).

- [ ] **Step 5: Commit.**

```bash
git add apps/tb4-teleop/orin apps/tb4-teleop/Makefile
git commit -m "feat(tb4-teleop/orin): scaffold web-console dir + node test harness + make targets"
```

---

### Task 2: Pure protocol module (CDR encoders + deep-link) — TDD

**Files:**
- Create: `apps/tb4-teleop/orin/web/protocol.js`
- Test: `apps/tb4-teleop/orin/tests/protocol.test.js`

**Interfaces:**
- Produces: `encodeTwist(linearX, angularZ) -> Uint8Array(52)`, `encodeEmpty() -> Uint8Array(4)`, `buildFoxgloveUrl({host, port, layoutId}) -> string`. Consumed by `foxglove-ws.js` (Task 4) and `app.js` (Task 5).

- [ ] **Step 1: Write the failing test** `tests/protocol.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { encodeTwist, encodeEmpty, buildFoxgloveUrl } from '../web/protocol.js';

test('encodeTwist: 52 bytes, CDR_LE header, values round-trip', () => {
  const bytes = encodeTwist(0.15, -0.4);
  assert.equal(bytes.length, 52);
  assert.deepEqual([...bytes.slice(0, 4)], [0x00, 0x01, 0x00, 0x00]);
  const dv = new DataView(bytes.buffer);
  assert.equal(dv.getFloat64(4, true), 0.15);    // linear.x
  assert.equal(dv.getFloat64(12, true), 0);      // linear.y
  assert.equal(dv.getFloat64(44, true), -0.4);   // angular.z
});

test('encodeEmpty: 4-byte CDR_LE header', () => {
  assert.deepEqual([...encodeEmpty()], [0x00, 0x01, 0x00, 0x00]);
});

test('buildFoxgloveUrl: without and with layoutId', () => {
  assert.equal(
    buildFoxgloveUrl({ host: '192.168.0.100', port: 8765 }),
    'https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://192.168.0.100:8765'
  );
  assert.equal(
    buildFoxgloveUrl({ host: 'r', port: 8765, layoutId: 'abc' }),
    'https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://r:8765&layoutId=abc'
  );
});
```

- [ ] **Step 2: Run it to see it fail.**

Run: `cd apps/tb4-teleop/orin && node --test`
Expected: FAIL — cannot find `../web/protocol.js`.

- [ ] **Step 3: Implement `web/protocol.js`:**

```js
// Foxglove/ROS 2 CDR encoders + the app.foxglove.dev deep-link builder.
// Pure functions — no DOM, no WebSocket — so they unit-test under `node --test`.

// CDR encapsulation header, little-endian (CDR_LE): representation id 0x0001, options 0x0000.
const CDR_LE_HEADER = [0x00, 0x01, 0x00, 0x00];

// geometry_msgs/msg/Twist = {linear:{x,y,z}, angular:{x,y,z}} — six float64, 8-aligned from
// the body start so no padding. 4-byte header + 48 bytes = 52 bytes.
export function encodeTwist(linearX, angularZ) {
  const buf = new ArrayBuffer(52);
  const dv = new DataView(buf);
  CDR_LE_HEADER.forEach((b, i) => dv.setUint8(i, b));
  dv.setFloat64(4, linearX, true);    // linear.x
  dv.setFloat64(12, 0, true);         // linear.y
  dv.setFloat64(20, 0, true);         // linear.z
  dv.setFloat64(28, 0, true);         // angular.x
  dv.setFloat64(36, 0, true);         // angular.y
  dv.setFloat64(44, angularZ, true);  // angular.z
  return new Uint8Array(buf);
}

// std_msgs/msg/Empty has no fields → CDR is just the encapsulation header.
// (If the bridge/helper ever rejects a 4-byte Empty, the fallback is a trailing 0 byte;
// the undock HIL check in Task 8 is the source of truth.)
export function encodeEmpty() {
  return new Uint8Array(CDR_LE_HEADER);
}

export function buildFoxgloveUrl({ host, port, layoutId }) {
  let url = `https://app.foxglove.dev/~/view?ds=foxglove-websocket&ds.url=ws://${host}:${port}`;
  if (layoutId) url += `&layoutId=${layoutId}`;
  return url;
}
```

- [ ] **Step 4: Run it to pass.**

Run: `cd apps/tb4-teleop/orin && node --test`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit.**

```bash
git add apps/tb4-teleop/orin/web/protocol.js apps/tb4-teleop/orin/tests/protocol.test.js
git commit -m "feat(tb4-teleop/orin): CDR Twist/Empty encoders + Foxglove deep-link builder (tested)"
```

---

### Task 3: Layout drift-guard test

**Files:**
- Test: `apps/tb4-teleop/orin/tests/layout.test.js`

**Interfaces:**
- Consumes: `apps/tb4-teleop/foxglove/tb4-teleop-layout.json` (Phase 1). Produces: a guard that fails if the Teleop panel / `/cmd_vel` binding is removed.

- [ ] **Step 1: Write the test** `tests/layout.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const path = fileURLToPath(new URL('../../foxglove/tb4-teleop-layout.json', import.meta.url));

test('phase-1 layout is valid JSON and still has a Teleop panel on /cmd_vel', () => {
  const layout = JSON.parse(readFileSync(path, 'utf8'));
  const cfg = layout.configById || {};
  const teleopKey = Object.keys(cfg).find((k) => k.startsWith('Teleop!'));
  assert.ok(teleopKey, 'no Teleop panel in layout');
  assert.equal(cfg[teleopKey].topic, '/cmd_vel');
});
```

- [ ] **Step 2: Run it — should PASS** (the Phase-1 layout has `Teleop!drive` on `/cmd_vel`).

Run: `cd apps/tb4-teleop/orin && node --test`
Expected: PASS (4 tests total now).

- [ ] **Step 3: Commit.**

```bash
git add apps/tb4-teleop/orin/tests/layout.test.js
git commit -m "test(tb4-teleop/orin): guard the phase-1 Teleop layout against drift"
```

---

### Task 4: Foxglove WebSocket publish client (browser)

**Files:**
- Create: `apps/tb4-teleop/orin/web/foxglove-ws.js`

**Interfaces:**
- Consumes: `encodeTwist`, `encodeEmpty` from `protocol.js`.
- Produces: `class FoxgloveClient(url, onStatus)` with `connect()`, `publishTwist(linearX, angularZ)`, `dock()`, `undock()`. Consumed by `app.js` (Task 5). Browser-only (uses `WebSocket`); HIL-verified in Task 8 — no unit test.

- [ ] **Step 1: Implement `web/foxglove-ws.js`:**

```js
import { encodeTwist, encodeEmpty } from './protocol.js';

// Minimal Foxglove WebSocket client for CLIENT PUBLISHING only (no subscribe).
// Wire format (foxglove ws-protocol):
//   client advertise (JSON): {"op":"advertise","channels":[{id,topic,encoding:"cdr",schemaName}]}
//   client data frame (binary): [0x01][channelId uint32 LE][payload]
// This is the same client-publish path Foxglove's own Teleop panel uses on this bridge
// (foxglove_bridge 3.4.2, subprotocol foxglove.sdk.v1). Verified live in Task 8.
const CLIENT_MSG_DATA = 0x01;

export class FoxgloveClient {
  constructor(url, onStatus = () => {}) {
    this.url = url;
    this.onStatus = onStatus;
    this.ws = null;
    this.nextId = 1;
    this.channels = {}; // topic -> { id }
  }

  connect() {
    this.onStatus('connecting');
    this.ws = new WebSocket(this.url, ['foxglove.sdk.v1']);
    this.ws.binaryType = 'arraybuffer';
    this.ws.onopen = () => this._advertiseAll();
    this.ws.onclose = () => { this.onStatus('disconnected'); setTimeout(() => this.connect(), 2000); };
    this.ws.onerror = () => this.onStatus('error');
    this.ws.onmessage = (ev) => {
      if (typeof ev.data === 'string') {
        const msg = JSON.parse(ev.data);
        if (msg.op === 'serverInfo') this.onStatus('connected');
      }
    };
  }

  _advertise(topic, schemaName) {
    const id = this.nextId++;
    this.channels[topic] = { id };
    this.ws.send(JSON.stringify({ op: 'advertise', channels: [{ id, topic, encoding: 'cdr', schemaName }] }));
  }

  _advertiseAll() {
    this._advertise('/cmd_vel', 'geometry_msgs/msg/Twist');
    this._advertise('/teleop/dock', 'std_msgs/msg/Empty');
    this._advertise('/teleop/undock', 'std_msgs/msg/Empty');
  }

  _sendData(topic, payload) {
    const ch = this.channels[topic];
    if (!ch || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const frame = new Uint8Array(5 + payload.length);
    frame[0] = CLIENT_MSG_DATA;
    new DataView(frame.buffer).setUint32(1, ch.id, true);
    frame.set(payload, 5);
    this.ws.send(frame);
  }

  publishTwist(linearX, angularZ) { this._sendData('/cmd_vel', encodeTwist(linearX, angularZ)); }
  dock() { this._sendData('/teleop/dock', encodeEmpty()); }
  undock() { this._sendData('/teleop/undock', encodeEmpty()); }
}
```

- [ ] **Step 2: Syntax-check it under Node** (it imports cleanly even though `WebSocket` is only used at runtime in the browser):

Run: `cd apps/tb4-teleop/orin && node -e "import('./web/foxglove-ws.js').then(()=>console.log('OK'))"`
Expected: `OK` (module parses and imports `protocol.js`).

- [ ] **Step 3: Commit.**

```bash
git add apps/tb4-teleop/orin/web/foxglove-ws.js
git commit -m "feat(tb4-teleop/orin): Foxglove WS client-publish for /cmd_vel + dock/undock"
```

---

### Task 5: Teleop controller + page (`teleop.js`, `index.html`, `app.js`, `env.js.tmpl`)

**Files:**
- Create: `apps/tb4-teleop/orin/web/teleop.js`
- Create: `apps/tb4-teleop/orin/web/index.html`
- Create: `apps/tb4-teleop/orin/web/app.js`
- Create: `apps/tb4-teleop/orin/web/env.js.tmpl`

**Interfaces:**
- Consumes: `FoxgloveClient` (Task 4), `buildFoxgloveUrl` (Task 2).
- Produces: `class Teleop(client)` with `set(lin, ang)`, `stop()`, `bindButton(el, lin, ang)`, `bindKeyboard()`, and exported `LIN`, `ANG`. The served page. HIL-verified in Task 8.

- [ ] **Step 1: Implement `web/teleop.js`:**

```js
// Hold-to-drive controller: buttons + keyboard → a ~10 Hz Twist publish loop; zero on release.
export const LIN = 0.15;   // m/s cap
export const ANG = 0.4;    // rad/s cap
const RATE_HZ = 10;

export class Teleop {
  constructor(client) {
    this.client = client;
    this.lin = 0; this.ang = 0; this.timer = null;
  }
  _tick() { this.client.publishTwist(this.lin, this.ang); }
  set(lin, ang) {
    this.lin = lin; this.ang = ang;
    if (!this.timer) this.timer = setInterval(() => this._tick(), 1000 / RATE_HZ);
    this._tick();
  }
  stop() {
    this.lin = 0; this.ang = 0;
    this.client.publishTwist(0, 0);
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
  }
  bindButton(el, lin, ang) {
    const down = (e) => { e.preventDefault(); this.set(lin, ang); };
    const up = (e) => { e.preventDefault(); this.stop(); };
    el.addEventListener('pointerdown', down);
    el.addEventListener('pointerup', up);
    el.addEventListener('pointerleave', up);
    el.addEventListener('pointercancel', up);
  }
  bindKeyboard() {
    const map = {
      'w': [LIN, 0], 'arrowup': [LIN, 0], 's': [-LIN, 0], 'arrowdown': [-LIN, 0],
      'a': [0, ANG], 'arrowleft': [0, ANG], 'd': [0, -ANG], 'arrowright': [0, -ANG],
    };
    let held = null;
    window.addEventListener('keydown', (e) => {
      const k = e.key.toLowerCase(); if (!(k in map)) return;
      e.preventDefault(); held = k; this.set(map[k][0], map[k][1]);
    });
    window.addEventListener('keyup', (e) => { if (e.key.toLowerCase() === held) { held = null; this.stop(); } });
    window.addEventListener('blur', () => { held = null; this.stop(); });
  }
}
```

- [ ] **Step 2: Implement `web/env.js.tmpl`** (envsubst fills these at container boot):

```js
window.ENV = {
  ROBOT_HOST: "${ROBOT_HOST}",
  ROBOT_WS_PORT: "${ROBOT_WS_PORT}",
  WEBCAM_STREAM_URL: "${WEBCAM_STREAM_URL}",
  FOXGLOVE_LAYOUT_ID: "${FOXGLOVE_LAYOUT_ID}"
};
```

- [ ] **Step 3: Implement `web/index.html`** (marker text `tb4-teleop console` is asserted by the smoke test):

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>tb4-teleop console</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #111; color: #eee; }
    header { padding: .5rem 1rem; display: flex; align-items: center; gap: .75rem; }
    h1 { font-size: 1rem; margin: 0; }
    #status { width: 12px; height: 12px; border-radius: 50%; background: #888; }
    #status[data-state="connected"] { background: #33cc55; }
    #status[data-state="error"], #status[data-state="disconnected"] { background: #cc3333; }
    main { display: grid; grid-template-columns: 1fr 320px; gap: 1rem; padding: 1rem; }
    .panel { background: #1c1c1c; border-radius: 8px; padding: 1rem; }
    #webcam { width: 100%; border-radius: 6px; background: #000; min-height: 240px; }
    .dpad { display: grid; grid-template-columns: repeat(3, 64px); gap: .5rem; justify-content: center; }
    .dpad button { height: 64px; font-size: 1.4rem; border: 0; border-radius: 8px; background: #2b6; color: #fff; }
    .row { display: flex; gap: .5rem; margin-top: .75rem; }
    .row button { flex: 1; height: 44px; border: 0; border-radius: 8px; color: #fff; }
    #undock { background: #d9822b; } #dock { background: #2b6cd9; } #foxglove { background: #6b4fbb; }
    .settings { margin-top: .75rem; font-size: .85rem; }
    .settings input { width: 8rem; }
  </style>
</head>
<body>
  <header>
    <span id="status" data-state="connecting" title="connecting"></span>
    <h1>tb4-teleop console</h1>
  </header>
  <main>
    <section class="panel">
      <img id="webcam" alt="webcam" />
    </section>
    <section class="panel">
      <div class="dpad">
        <span></span><button id="fwd">▲</button><span></span>
        <button id="left">◀</button><span></span><button id="right">▶</button>
        <span></span><button id="back">▼</button><span></span>
      </div>
      <div class="row"><button id="undock">UNDOCK</button><button id="dock">DOCK</button></div>
      <div class="row"><button id="foxglove">Open in Foxglove</button></div>
      <div class="settings">
        robot <input id="host" /> : <input id="port" style="width:4rem" />
        <button id="save">save</button>
      </div>
    </section>
  </main>
  <script src="env.js"></script>
  <script type="module" src="app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Implement `web/app.js`** (wiring):

```js
import { FoxgloveClient } from './foxglove-ws.js';
import { Teleop, LIN, ANG } from './teleop.js';
import { buildFoxgloveUrl } from './protocol.js';

const cfg = Object.assign(
  { ROBOT_HOST: '192.168.0.100', ROBOT_WS_PORT: '8765', WEBCAM_STREAM_URL: '', FOXGLOVE_LAYOUT_ID: '' },
  window.ENV || {}
);
const host = localStorage.getItem('robotHost') || cfg.ROBOT_HOST;
const port = localStorage.getItem('robotWsPort') || cfg.ROBOT_WS_PORT;

// Webcam (hide the panel if no stream configured).
const cam = document.getElementById('webcam');
if (cfg.WEBCAM_STREAM_URL) cam.src = cfg.WEBCAM_STREAM_URL;
else cam.closest('.panel').style.display = 'none';

// Connection + status dot.
const dot = document.getElementById('status');
const client = new FoxgloveClient(`ws://${host}:${port}`, (s) => { dot.dataset.state = s; dot.title = s; });
client.connect();

// Teleop: buttons + keyboard, hold-to-drive.
const teleop = new Teleop(client);
teleop.bindKeyboard();
teleop.bindButton(document.getElementById('fwd'), LIN, 0);
teleop.bindButton(document.getElementById('back'), -LIN, 0);
teleop.bindButton(document.getElementById('left'), 0, ANG);
teleop.bindButton(document.getElementById('right'), 0, -ANG);

// Dock / undock.
document.getElementById('dock').addEventListener('click', () => client.dock());
document.getElementById('undock').addEventListener('click', () => client.undock());

// Open in Foxglove (web deep-link).
document.getElementById('foxglove').addEventListener('click', () =>
  window.open(buildFoxgloveUrl({ host, port, layoutId: cfg.FOXGLOVE_LAYOUT_ID }), '_blank')
);

// Persist robot host/port edits.
document.getElementById('host').value = host;
document.getElementById('port').value = port;
document.getElementById('save').addEventListener('click', () => {
  localStorage.setItem('robotHost', document.getElementById('host').value);
  localStorage.setItem('robotWsPort', document.getElementById('port').value);
  location.reload();
});
```

- [ ] **Step 5: Sanity-check the JS parses** (imports resolve; `document`/`window` are only touched at runtime in the browser):

Run: `cd apps/tb4-teleop/orin && node --check web/app.js && node --check web/teleop.js && echo PARSE-OK`
Expected: `PARSE-OK`.

- [ ] **Step 6: Commit.**

```bash
git add apps/tb4-teleop/orin/web/teleop.js apps/tb4-teleop/orin/web/index.html apps/tb4-teleop/orin/web/app.js apps/tb4-teleop/orin/web/env.js.tmpl
git commit -m "feat(tb4-teleop/orin): console page — hold-to-drive teleop, dock/undock, foxglove button"
```

---

### Task 6: nginx container + entrypoint + compose (console) + serve smoke

**Files:**
- Create: `apps/tb4-teleop/orin/docker/Dockerfile`
- Create: `apps/tb4-teleop/orin/entrypoint.sh`
- Create: `apps/tb4-teleop/orin/docker/compose.yaml`
- Create: `apps/tb4-teleop/orin/tests/serve_smoke.sh`

**Interfaces:**
- Consumes: `web/*` (Tasks 2,4,5). Produces: `make orin-smoke` green (unit tests + the console container serving the page with env applied).

- [ ] **Step 1: Implement `entrypoint.sh`** (envsubst → env.js, then nginx):

```sh
#!/bin/sh
set -e
: "${ROBOT_HOST:=192.168.0.100}"
: "${ROBOT_WS_PORT:=8765}"
: "${WEBCAM_STREAM_URL:=}"
: "${FOXGLOVE_LAYOUT_ID:=}"
export ROBOT_HOST ROBOT_WS_PORT WEBCAM_STREAM_URL FOXGLOVE_LAYOUT_ID
envsubst < /usr/share/nginx/html/env.js.tmpl > /usr/share/nginx/html/env.js
exec nginx -g 'daemon off;'
```

- [ ] **Step 2: Implement `docker/Dockerfile`** (context is `orin/`):

```dockerfile
FROM nginx:alpine
RUN apk add --no-cache gettext
COPY web/ /usr/share/nginx/html/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 3: Implement `docker/compose.yaml`** (console service now; webcam added in Task 7):

```yaml
services:
  console:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8080:80"
    environment:
      ROBOT_HOST: ${ROBOT_HOST:-192.168.0.100}
      ROBOT_WS_PORT: ${ROBOT_WS_PORT:-8765}
      WEBCAM_STREAM_URL: ${WEBCAM_STREAM_URL:-}
      FOXGLOVE_LAYOUT_ID: ${FOXGLOVE_LAYOUT_ID:-}
```

- [ ] **Step 4: Implement `tests/serve_smoke.sh`:**

```bash
#!/usr/bin/env bash
# Console-contract smoke: build+run the console container, assert it serves the page with
# env applied. Webcam + live drive are manual HIL (Task 8).
set -uo pipefail
cd "$(dirname "$0")/.."
CMP="docker compose -f docker/compose.yaml"
ROBOT_HOST=10.0.0.9 $CMP up -d --build console || { echo "BUILD/UP FAILED"; exit 1; }
trap '$CMP down >/dev/null 2>&1' EXIT
n=0; until curl -sf http://localhost:8080/ >/dev/null 2>&1; do
  n=$((n+1)); [ "$n" -ge 20 ] && { echo "PAGE NOT SERVED"; exit 1; }; sleep 1; done
curl -sf http://localhost:8080/ | grep -q 'tb4-teleop console' || { echo "HTML MARKER MISSING"; exit 1; }
curl -sf http://localhost:8080/env.js | grep -q '10.0.0.9' || { echo "ENV NOT SUBSTITUTED"; exit 1; }
echo "ORIN CONSOLE SERVE OK"
```

Make it executable: `chmod +x apps/tb4-teleop/orin/tests/serve_smoke.sh`.

- [ ] **Step 5: Run `make orin-smoke`** (needs Docker running locally):

Run: `cd apps/tb4-teleop && make orin-smoke`
Expected: node tests PASS, then `ORIN CONSOLE SERVE OK`.

- [ ] **Step 6: Commit.**

```bash
git add apps/tb4-teleop/orin/docker/Dockerfile apps/tb4-teleop/orin/entrypoint.sh apps/tb4-teleop/orin/docker/compose.yaml apps/tb4-teleop/orin/tests/serve_smoke.sh
git commit -m "feat(tb4-teleop/orin): nginx console container + envsubst entrypoint + serve smoke"
```

---

### Task 7: USB webcam service (ustreamer) in compose

**Files:**
- Create: `apps/tb4-teleop/orin/docker/Dockerfile.webcam`
- Modify: `apps/tb4-teleop/orin/docker/compose.yaml`

**Interfaces:**
- Produces: a `webcam` compose service serving MJPEG on `:8081`. HIL-verified on the Orin with a real camera (Task 8) — no CI coverage (needs `/dev/video0`).

- [ ] **Step 1: Implement `docker/Dockerfile.webcam`** (build ustreamer from source, small runtime):

```dockerfile
FROM alpine:3.20 AS build
RUN apk add --no-cache build-base linux-headers libevent-dev libbsd-dev libjpeg-turbo-dev git
RUN git clone --depth 1 https://github.com/pikvm/ustreamer /src && make -C /src
FROM alpine:3.20
RUN apk add --no-cache libevent libbsd libjpeg-turbo
COPY --from=build /src/ustreamer /usr/local/bin/ustreamer
ENTRYPOINT ["/usr/local/bin/ustreamer"]
```

- [ ] **Step 2: Add the `webcam` service** to `docker/compose.yaml`:

```yaml
  webcam:
    build:
      context: ..
      dockerfile: docker/Dockerfile.webcam
    ports:
      - "8081:8081"
    devices:
      - "${WEBCAM_DEVICE:-/dev/video0}:/dev/video0"
    command: ["--host=0.0.0.0", "--port=8081", "--device=/dev/video0",
              "--resolution=640x480", "--desired-fps=15", "--format=MJPEG"]
    restart: unless-stopped
```

Also set the console's default webcam URL so the panel shows when both run together — change the console service's `WEBCAM_STREAM_URL` default:

```yaml
      WEBCAM_STREAM_URL: ${WEBCAM_STREAM_URL:-http://ORIN_HOST_PLACEHOLDER:8081/stream}
```

Note: the browser (not the console container) fetches the webcam, so this must be the Orin's LAN host/IP, injected at deploy time via `WEBCAM_STREAM_URL` (Task 8), not `localhost`.

- [ ] **Step 3: Verify the webcam image builds** (build only — no camera needed to compile):

Run: `cd apps/tb4-teleop/orin && docker compose -f docker/compose.yaml build webcam`
Expected: builds successfully (produces the ustreamer binary). If the build pulls too much over a metered link, run this step while on non-metered internet.

- [ ] **Step 4: Confirm the console smoke still passes** (webcam service isn't started by the serve smoke, which targets `console` only):

Run: `cd apps/tb4-teleop && make orin-smoke`
Expected: `ORIN CONSOLE SERVE OK`.

- [ ] **Step 5: Commit.**

```bash
git add apps/tb4-teleop/orin/docker/Dockerfile.webcam apps/tb4-teleop/orin/docker/compose.yaml
git commit -m "feat(tb4-teleop/orin): ustreamer USB-webcam MJPEG service in compose"
```

---

### Task 8: HIL end-to-end on the Orin + registry card (the real pass bar)

**Files:**
- Create: `apps/tb4-teleop/orin/README.md`
- Modify: `apps/tb4-teleop/docs/architecture-brief.md` (add the Orin console to the roadmap/§)
- Modify: `REGISTRY.md` (update the tb4-teleop card with the Orin phase)

**Interfaces:**
- Consumes: everything above + the running robot (`make bridge` from Phase 1, so `foxglove_bridge` + the dock/undock helper are up).

- [ ] **Step 1: Bring up the robot bridge (Phase 1).**

Run: `cd apps/tb4-teleop && make bridge`
Expected: `BRIDGE UP: ws://192.168.0.100:8765` and `TELEOP HELPER UP`.

- [ ] **Step 2: Deploy the console on the Orin.** Copy the repo (or just `orin/`) to the Orin and bring up compose with the Orin's own LAN IP for the webcam URL. On the Orin (`ssh robium@192.168.55.1`), from the app dir:

```bash
export WEBCAM_STREAM_URL="http://<orin-lan-ip>:8081/stream"   # the Orin's RobotWiFi IP
export ROBOT_HOST=192.168.0.100 ROBOT_WS_PORT=8765
docker compose -f orin/docker/compose.yaml up -d --build   # sudo only if the operator's docker needs it
```

Expected: `console` and `webcam` containers running (`docker ps`). (Build the images while on non-metered internet; serve while on RobotWiFi.)

- [ ] **Step 3: SAFETY + drive.** Undock the robot onto clear floor (use the page's **UNDOCK** button — this also verifies the `Empty` encoding end-to-end). Open `http://<orin-lan-ip>:8080` in a browser on the same LAN. Confirm:
  - status dot turns **green** (serverInfo received),
  - the **webcam** shows the USB camera,
  - holding **▲ / W** drives the robot forward and it **stops on release**; turns work,
  - **UNDOCK/DOCK** move the robot on/off the dock.

Expected: robot drives from the page; webcam is live. **If UNDOCK does nothing but drive works,** the `Empty` CDR length is the suspect — change `encodeEmpty()` to return 5 bytes (`[...CDR_LE_HEADER, 0x00]`), rebuild, retest (per Task 2's note). **If nothing publishes at all,** open browser devtools → Network → the WS frames, compare the `advertise` JSON / binary opcode against what the Foxglove app sends when its Teleop panel publishes (that app works on this bridge), and reconcile `foxglove-ws.js`.

- [ ] **Step 4: Write `orin/README.md`** — what it is, the env vars (§6 of the spec), `make orin-smoke`/`orin-serve`, the deploy recipe from Step 2, and the "build on non-metered internet, serve on RobotWiFi" note.

- [ ] **Step 5: Update the brief + registry.** In `apps/tb4-teleop/docs/architecture-brief.md`, mark the roadmap: **Phase 2 = Orin console (done)**, camera → 3, mapping → 4. In `REGISTRY.md`, extend the `tb4-teleop` card: add the Orin web console (browser→bridge teleop, MJPEG webcam, Foxglove launcher; `make orin-smoke` = console-contract, live drive = HIL) and bump `verified` to today.

- [ ] **Step 6: Commit.**

```bash
git add apps/tb4-teleop/orin/README.md apps/tb4-teleop/docs/architecture-brief.md REGISTRY.md
git commit -m "feat(tb4-teleop/orin): HIL-verified web console on Orin; brief + registry updated"
```

---

## Self-Review

**Spec coverage:**
- §1 goal (teleop + webcam + Foxglove launch, Dockerized, repointable) → Tasks 2,4,5 (teleop+launch), 7 (webcam), 6 (Docker), env everywhere. ✓
- §2 architecture (browser→bridge, Orin serves static+webcam, http avoids mixed-content) → Tasks 4,6,7. ✓
- §3 decisions (browser→bridge; ustreamer MJPEG; buttons+keyboard hold-to-drive; dock/undock on page; web-only Foxglove button; empty layoutId) → Tasks 4,5,7. ✓
- §4 components (protocol/foxglove-ws/teleop/app/index) → Tasks 2,4,5. ✓
- §5 CDR encoding (Twist 52B, Empty header, unit-tested; length verified via HIL) → Task 2 + Task 8 Step 3. ✓
- §6 config/env → entrypoint (Task 6) + compose (6,7) + app.js reading `window.ENV` (5). ✓
- §7 file shape → Tasks 1–7. ✓
- §8 test bar (serve + URL builder + CDR encoders + layout drift; live = HIL) → Tasks 2,3,6 + Task 8. ✓
- §9 out-of-scope (WebRTC/image-proc/ROS-on-Orin/auth/desktop button/wired layoutId) → not built. ✓
- §10 Orin access facts → used in Task 8. ✓
- §11 deep-link form → Task 2 `buildFoxgloveUrl` (matches, un-encoded `ds.url`, optional `layoutId`). ✓

**Placeholder scan:** `ORIN_HOST_PLACEHOLDER` in Task 7 is an intentional compose default that Task 8 Step 2 overrides with the real Orin IP via `WEBCAM_STREAM_URL` (the browser, not the container, fetches the cam, so `localhost` would be wrong) — it's documented at both sites, not a hand-wave. No other placeholders.

**Type consistency:** `FoxgloveClient(url, onStatus)` with `connect()/publishTwist(linearX, angularZ)/dock()/undock()` used identically in Task 4 (def) and Task 5 (`app.js`). `Teleop(client)` with `set/stop/bindButton/bindKeyboard` + exported `LIN`/`ANG` consistent across Tasks 5. `buildFoxgloveUrl({host,port,layoutId})`, `encodeTwist(linearX, angularZ)`, `encodeEmpty()` identical in Tasks 2, 4, 5. Env var names identical across spec §6, entrypoint, compose, `app.js`.
