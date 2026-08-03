#!/usr/bin/env python3
"""Demo session gateway — single process on $PORT (8765).

Status: verified 2026-07-13 — this exact file runs the nav-trial live demo
on robium.ai (Cloud Run service demo-nav-trial). Adapt FLEET_BUDGET and
the CORS origin for your deployment.

Routes:
  * WebSocket upgrade (any path)  -> raw byte tunnel to the bridge :8766.
      First tunnel claims the instance for the request's ?session=UUID;
      a second concurrent viewer gets 503 (Cloud Run routes their retry to
      a fresh instance because this one is busy).
  * GET  /status?session=UUID     -> 200 JSON (contract in the plan header);
      409 if the instance is claimed by a different session.
  * POST /shutdown?session=UUID   -> 200 + SIGTERM PID 1 (container exits);
      403 on session mismatch.

stdlib only; runs alongside ros2 launch inside the demo container.
"""
import asyncio
import json
import os
import signal
import time
import urllib.request
from urllib.parse import parse_qs, quote, urlsplit

PORT = int(os.environ.get('PORT', '8765'))
BRIDGE = ('127.0.0.1', 8766)
STATUS_PATH = '/tmp/demo_status.json'
SESSION_SECONDS = 1800
FLEET_BUDGET = 5  # keep in sync with Cloud Run --max-instances
FLEET_CACHE_S = 30

state = {'session': None, 'tunnel_open': False, 'claimed_at': None}
fleet_cache = {'at': 0.0, 'running': None}


def fleet_running():
    """Service-wide live instance count via Cloud Monitoring (cached).

    Uses the metadata-server token; needs roles/monitoring.viewer on the
    runtime service account. Returns None off-GCP or on any error.
    """
    now = time.time()
    if now - fleet_cache['at'] < FLEET_CACHE_S:
        return fleet_cache['running']
    fleet_cache['at'] = now
    try:
        tok_req = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/'
            'service-accounts/default/token',
            headers={'Metadata-Flavor': 'Google'})
        token = json.load(urllib.request.urlopen(tok_req, timeout=2))['access_token']
        project = urllib.request.urlopen(urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/project/project-id',
            headers={'Metadata-Flavor': 'Google'}), timeout=2).read().decode()
        flt = quote('metric.type="run.googleapis.com/container/instance_count" '
                    'AND resource.labels.service_name="demo-nav-trial"')
        end = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))
        start = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 240))
        url = (f'https://monitoring.googleapis.com/v3/projects/{project}/timeSeries'
               f'?filter={flt}&interval.endTime={end}&interval.startTime={start}')
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        data = json.load(urllib.request.urlopen(req, timeout=5))
        total = 0
        for series in data.get('timeSeries', []):
            points = series.get('points', [])
            if points:
                total += int(points[0]['value'].get('int64Value', 0))
        fleet_cache['running'] = total
    except Exception:
        fleet_cache['running'] = None
    return fleet_cache['running']


def http_response(status, body, extra=''):
    # Connection: close is load-bearing behind Cloud Run's proxy: it pools
    # keep-alive connections to the instance, and closing the socket after a
    # response without declaring it surfaces as "malformed HTTP response"
    # 503s at the edge (verified 2026-07-13).
    # Exact-origin CORS + credentials: the page fetches with
    # credentials:'include' so Cloud Run's GAESA affinity cookie rides along
    # (same-site via demo.robium.ai — the cookie is SameSite-Lax and never
    # flows to run.app cross-site). ACAO:* is invalid with credentials.
    return (f'HTTP/1.1 {status}\r\nContent-Type: application/json\r\n'
            f'Content-Length: {len(body)}\r\n'
            f'Access-Control-Allow-Origin: https://robium.ai\r\n'
            f'Access-Control-Allow-Credentials: true\r\n'
            f'Connection: close\r\n'
            f'{extra}\r\n{body}').encode()


def read_status_file():
    try:
        with open(STATUS_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {'start': time.time(), 'ready': False, 'rtf': None,
                'nodes': 0, 'log': ['stack booting…']}


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle(reader, writer):
    try:
        raw = await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), timeout=30)
    except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError):
        writer.close()
        return
    head = raw.decode('latin1')
    request_line = head.split('\r\n', 1)[0]
    parts = request_line.split(' ')
    if len(parts) < 2:
        writer.close()
        return
    method, target = parts[0], parts[1]
    url = urlsplit(target)
    session = parse_qs(url.query).get('session', [None])[0]
    is_upgrade = 'upgrade: websocket' in head.lower()

    if is_upgrade:
        # A claim is sacred only while its tunnel is LIVE: a concurrent ws
        # from any session -> 503 (hijack guard; that visitor's retry gets a
        # fresh instance). With no live tunnel, a new session may take over
        # the claim — this is the page-reload path (new UUID + affinity
        # cookie routes to the old, already-booted instance: instant ready).
        if state['tunnel_open']:
            writer.write(http_response('503 Busy', json.dumps({'error': 'busy'})))
            await writer.drain()
            writer.close()
            return
        if session != state['session']:
            state['claimed_at'] = time.time()  # new visitor: fresh clock
        state['session'] = session or 'anonymous'
        state['tunnel_open'] = True
        state['claimed_at'] = state['claimed_at'] or time.time()
        try:
            br, bw = await asyncio.open_connection(*BRIDGE)
        except OSError:
            state['tunnel_open'] = False
            writer.write(http_response('502 Bad Gateway', json.dumps({'error': 'bridge not up'})))
            await writer.drain()
            writer.close()
            return
        bw.write(raw)
        await bw.drain()
        try:
            await asyncio.gather(pipe(reader, bw), pipe(br, writer))
        finally:
            state['tunnel_open'] = False
        return

    if url.path == '/start' and method == 'POST':
        # Explicit session claim, before any viewer connects. Busy only if a
        # live tunnel exists or another session actively holds the claim
        # with a live tunnel; an idle claim is takeable (reload semantics).
        if state['tunnel_open'] and session != state['session']:
            writer.write(http_response('503 Busy', json.dumps({'error': 'busy'})))
        else:
            if session != state['session']:
                state['claimed_at'] = time.time()
            state['session'] = session or 'anonymous'
            state['claimed_at'] = state['claimed_at'] or time.time()
            writer.write(http_response('200 OK', json.dumps({'ok': True})))
        await writer.drain()
        writer.close()
        return

    if url.path == '/status':
        if state['session'] and session != state['session']:
            writer.write(http_response('409 Conflict', json.dumps({'error': 'not your instance'})))
        else:
            s = read_status_file()
            up = int(time.time() - (state['claimed_at'] or s['start']))
            body = json.dumps({
                'claimed': state['session'] is not None,
                'ready': s['ready'], 'rtf': s['rtf'], 'nodes': s['nodes'],
                'uptime_s': up, 'remaining_s': max(0, SESSION_SECONDS - up),
                'fleet': {'running': fleet_running(), 'budget': FLEET_BUDGET},
                'log': s['log'],
            })
            writer.write(http_response('200 OK', body))
        await writer.drain()
        writer.close()
        return

    if url.path == '/shutdown' and method == 'POST':
        if state['session'] is None or session != state['session']:
            writer.write(http_response('403 Forbidden', json.dumps({'error': 'forbidden'})))
            await writer.drain()
            writer.close()
            return
        writer.write(http_response('200 OK', json.dumps({'bye': True})))
        await writer.drain()
        writer.close()
        await asyncio.sleep(0.2)
        # SIGINT, not SIGTERM: PID 1 (ros2 launch) has no SIGTERM handler
        # installed, and unhandled signals to PID 1 are ignored by the
        # kernel — SIGINT triggers launch's real shutdown (verified).
        os.kill(1, signal.SIGINT)
        return

    writer.write(http_response('200 OK', json.dumps({'service': 'robium demo gateway'})))
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(handle, '0.0.0.0', PORT)
    print(f'demo_gateway listening on :{PORT}', flush=True)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
