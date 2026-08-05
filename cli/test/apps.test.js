import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { parseAppYaml, findAppsDir, loadApps, resolveCommand, appCmd } from '../src/apps.js';

const SAMPLE = `schema_version: "1"
id: indoor-navigation
name: Indoor navigation (TurtleBot 3 + Nav2)
summary: SLAM builds a map, Nav2 drives clicked goals.
version: 1.0.0
status: stable
license: MIT
tags: [navigation, ros2, nav2]

runtime:
  kind: docker
  entrypoint: make demo

verbs:
  build: make build
  demo: make demo
  smoke: make smoke
  check: make check
  down: make down

scenarios:
  slam:
    command: make slam
    summary: drive the mapping route and save the map
  nav:
    command: make nav
    summary: navigation on the saved map

requirements:
  hardware: []
  gpu: none              # trailing comment
  network: optional

demo:
  default_scenario: demo
  hosted: true
  estimated_startup_seconds: 45

artifacts:
  thumbnail: null
  case_study: null
`;

test('parseAppYaml: full reference-shape file', () => {
  const a = parseAppYaml(SAMPLE);
  assert.equal(a.schema_version, '1');           // quoted stays string
  assert.equal(a.id, 'indoor-navigation');
  assert.equal(a.name, 'Indoor navigation (TurtleBot 3 + Nav2)');
  assert.deepEqual(a.tags, ['navigation', 'ros2', 'nav2']);
  assert.equal(a.runtime.kind, 'docker');
  assert.equal(a.verbs.check, 'make check');
  assert.equal(a.scenarios.slam.command, 'make slam');
  assert.equal(a.scenarios.nav.summary, 'navigation on the saved map');
  assert.deepEqual(a.requirements.hardware, []);
  assert.equal(a.requirements.gpu, 'none');       // trailing comment stripped
  assert.equal(a.demo.hosted, true);
  assert.equal(a.demo.estimated_startup_seconds, 45);
  assert.equal(a.artifacts.thumbnail, null);
});

test('parseAppYaml: empty inline map and version-like strings', () => {
  const a = parseAppYaml('id: x\nscenarios: {}\nversion: 0.1.0\n');
  assert.deepEqual(a.scenarios, {});
  assert.equal(a.version, '0.1.0');               // not a number
});

test('parseAppYaml: rejects non key-value lines', () => {
  assert.throws(() => parseAppYaml('- just a list item\n'), /expected "key: value"/);
});

function makeAppsRepo() {
  const root = mkdtempSync(path.join(tmpdir(), 'robium-apps-'));
  writeFileSync(path.join(root, 'REGISTRY.md'), '# registry\n');
  mkdirSync(path.join(root, 'nav-app'));
  writeFileSync(path.join(root, 'nav-app', 'robium-app.yaml'), SAMPLE);
  mkdirSync(path.join(root, 'broken-app'));
  writeFileSync(path.join(root, 'broken-app', 'robium-app.yaml'), '- not: [valid\n');
  mkdirSync(path.join(root, 'not-an-app'));       // no yaml → ignored
  return root;
}

test('findAppsDir: explicit dir, env, and cwd walk-up', () => {
  const root = makeAppsRepo();
  assert.equal(findAppsDir({ dir: root }), root);
  assert.equal(findAppsDir({ env: { ROBIUM_APPS_DIR: root }, cwd: '/' }), root);
  const deep = path.join(root, 'nav-app');
  assert.equal(findAppsDir({ env: {}, cwd: deep }), root);
  assert.equal(findAppsDir({ dir: path.join(root, 'nope') }), null);
});

test('loadApps: parses good apps, flags broken ones, skips non-apps', () => {
  const apps = loadApps(makeAppsRepo());
  assert.equal(apps.length, 2);
  const broken = apps.find((a) => a.id === 'broken-app');
  assert.match(broken.parse_error, /expected "key: value"/);
  const nav = apps.find((a) => a.id === 'indoor-navigation');
  assert.equal(nav.runtime.kind, 'docker');
});

test('resolveCommand: verb, scenario, and error paths', () => {
  const app = parseAppYaml(SAMPLE);
  assert.deepEqual(resolveCommand(app, { verb: 'demo' }), { command: 'make demo' });
  assert.deepEqual(resolveCommand(app, { verb: 'check' }), { command: 'make check' });
  assert.deepEqual(resolveCommand(app, { scenario: 'slam' }), { command: 'make slam' });
  assert.match(resolveCommand(app, { scenario: 'zzz' }).error, /known: slam, nav/);
  const bare = parseAppYaml('id: y\nruntime:\n  entrypoint: make go\n');
  assert.deepEqual(resolveCommand(bare, { verb: 'demo' }), { command: 'make go' });
  assert.match(resolveCommand(bare, { verb: 'check' }).error, /no "check" verb/);
});

function capture() {
  const lines = [];
  return { log: (...a) => lines.push(a.join(' ')), lines };
}

test('app list: table and --json', async () => {
  const root = makeAppsRepo();
  const { log, lines } = capture();
  const code = await appCmd({ args: ['list'], flags: { dir: root }, log });
  assert.equal(code, 1); // broken-app is a parse error
  assert.ok(lines.some((l) => l.includes('indoor-navigation') && l.includes('docker')));
  assert.ok(lines.some((l) => l.includes('PARSE ERROR')));

  const j = capture();
  await appCmd({ args: ['list'], flags: { dir: root, json: true }, log: j.log });
  const parsed = JSON.parse(j.lines.join('\n'));
  assert.equal(parsed.apps.length, 2);
});

test('app run: execs resolved command in app dir; scenario flag; unknown id', async () => {
  const root = makeAppsRepo();
  const calls = [];
  const exec = async (command, dir) => { calls.push({ command, dir }); return 0; };
  const { log } = capture();

  assert.equal(await appCmd({ args: ['run', 'indoor-navigation'], flags: { dir: root }, log, exec }), 0);
  assert.equal(await appCmd({ args: ['run', 'indoor-navigation'], flags: { dir: root, scenario: 'slam' }, log, exec }), 0);
  assert.deepEqual(calls.map((c) => c.command), ['make demo', 'make slam']);
  assert.ok(calls[0].dir.endsWith('nav-app'));

  const bad = capture();
  assert.equal(await appCmd({ args: ['run', 'ghost'], flags: { dir: root }, log: bad.log, exec }), 1);
  assert.ok(bad.lines.some((l) => l.includes('Unknown app "ghost"')));
});

test('app check: doctor facts + app check verb; graceful when verb missing', async () => {
  const root = makeAppsRepo();
  const calls = [];
  const exec = async (command, dir) => { calls.push({ command, dir }); return 0; };
  const checks = async () => [
    { id: 'docker', label: 'Docker', status: 'pass', detail: '27.0.0' },
    { id: 'python', label: 'Python / uv', status: 'pass', detail: '3.12' },
  ];
  const { log, lines } = capture();
  assert.equal(await appCmd({ args: ['check', 'indoor-navigation'], flags: { dir: root }, log, exec, checks }), 0);
  assert.ok(lines.some((l) => l.includes('doctor: Docker')));       // docker runtime → docker fact shown
  assert.ok(!lines.some((l) => l.includes('doctor: Python')));      // not relevant to docker kind
  assert.deepEqual(calls.map((c) => c.command), ['make check']);

  // App without a check verb: doctor facts are the whole preflight, exit 0.
  mkdirSync(path.join(root, 'thin-app'));
  writeFileSync(path.join(root, 'thin-app', 'robium-app.yaml'),
    'id: thin-app\nstatus: experimental\nruntime:\n  kind: uv\n  entrypoint: make demo\n');
  const thin = capture();
  assert.equal(await appCmd({ args: ['check', 'thin-app'], flags: { dir: root }, log: thin.log, exec, checks }), 0);
  assert.ok(thin.lines.some((l) => l.includes('doctor facts above are the whole preflight')));
});

test('app describe: dumps metadata json', async () => {
  const root = makeAppsRepo();
  const { log, lines } = capture();
  assert.equal(await appCmd({ args: ['describe', 'indoor-navigation'], flags: { dir: root }, log }), 0);
  const obj = JSON.parse(lines.join('\n'));
  assert.equal(obj.verbs.smoke, 'make smoke');
});
