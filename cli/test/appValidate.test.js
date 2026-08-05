import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { parseAppYaml } from '../src/apps.js';
import { validateApp, validateApps } from '../src/appValidate.js';
import { scaffoldApp } from '../src/appNew.js';
import { appCmd } from '../src/apps.js';

const GOOD = `schema_version: "1"
id: good-app
name: Good app
summary: Does a thing.
version: 1.0.0
status: stable
license: MIT
runtime:
  kind: docker
  entrypoint: make demo
verbs:
  demo: make demo
  smoke: make smoke
  check: make check
scenarios:
  alt:
    command: make alt
    summary: alternative flow
requirements:
  hardware: []
  gpu: none
  network: optional
demo:
  default_scenario: demo
  hosted: false
  estimated_startup_seconds: 30
`;

function app(yaml, dirname = 'good-app') {
  return { dir: `/x/${dirname}`, ...parseAppYaml(yaml) };
}

test('validateApp: fully valid app has no errors', () => {
  const r = validateApp(app(GOOD));
  assert.deepEqual(r.errors, []);
  assert.ok(r.ok);
});

test('validateApp: precise per-field errors', () => {
  const r = validateApp(app(GOOD
    .replace('status: stable', 'status: shiny')
    .replace('version: 1.0.0', 'version: v1')
    .replace('kind: docker', 'kind: bare-metal')
    .replace('  smoke: make smoke\n', ''), 'good-app'));
  assert.ok(!r.ok);
  assert.ok(r.errors.some((e) => e.includes('status must be one of')));
  assert.ok(r.errors.some((e) => e.includes('version must be MAJOR.MINOR.PATCH')));
  assert.ok(r.errors.some((e) => e.includes('runtime.kind must be one of')));
  assert.ok(r.errors.some((e) => e.includes('verbs.smoke is required')));
});

test('validateApp: id must match directory name', () => {
  const r = validateApp(app(GOOD, 'other-dir'));
  assert.ok(r.errors.some((e) => e.includes('must equal the directory name')));
});

test('validateApp: default_scenario must resolve; hosted without orchestrator warns', () => {
  const r = validateApp(app(GOOD.replace('default_scenario: demo', 'default_scenario: ghost')));
  assert.ok(r.errors.some((e) => e.includes('matches no verb or scenario')));

  const hosted = validateApp(app(GOOD.replace('hosted: false', 'hosted: true')));
  assert.ok(hosted.ok);
  assert.ok(hosted.warnings.some((w) => w.includes('cannot be derived')));
});

test('validateApp: orchestrator section field checks', () => {
  const y = GOOD.replace('hosted: false', `hosted: true
  orchestrator:
    image: good-app:latest
    command: [/entrypoint.sh, make, demo]
    gateway_port: 8765`);
  const r = validateApp(app(y));
  assert.ok(r.ok, JSON.stringify(r.errors));

  const bad = validateApp(app(y.replace('    gateway_port: 8765', '    gateway_port: eight')));
  assert.ok(bad.errors.some((e) => e.includes('gateway_port must be a number')));
});

test('validateApps + app validate subcommand over a repo', async () => {
  const root = mkdtempSync(path.join(tmpdir(), 'robium-val-'));
  writeFileSync(path.join(root, 'REGISTRY.md'), '# r\n');
  mkdirSync(path.join(root, 'good-app'));
  writeFileSync(path.join(root, 'good-app', 'robium-app.yaml'), GOOD);
  mkdirSync(path.join(root, 'bad-app'));
  writeFileSync(path.join(root, 'bad-app', 'robium-app.yaml'), 'id: bad-app\n');

  const lines = [];
  const code = await appCmd({ args: ['validate'], flags: { dir: root }, log: (...a) => lines.push(a.join(' ')) });
  assert.equal(code, 1);
  assert.ok(lines.some((l) => l.includes('✓ good-app')));
  assert.ok(lines.some((l) => l.includes('✗ bad-app')));

  const j = [];
  await appCmd({ args: ['validate'], flags: { dir: root, json: true }, log: (...a) => j.push(a.join(' ')) });
  const out = JSON.parse(j.join('\n'));
  assert.equal(out.ok, false);
  assert.equal(out.results.length, 2);
});

test('app new: scaffolds by copy, resets metadata, excludes artifacts', async () => {
  const root = mkdtempSync(path.join(tmpdir(), 'robium-new-'));
  writeFileSync(path.join(root, 'REGISTRY.md'), '# r\n');
  mkdirSync(path.join(root, 'good-app', 'src'), { recursive: true });
  mkdirSync(path.join(root, 'good-app', '.venv'));
  mkdirSync(path.join(root, 'good-app', 'outputs'));
  writeFileSync(path.join(root, 'good-app', 'robium-app.yaml'), GOOD);
  writeFileSync(path.join(root, 'good-app', 'Makefile'), 'demo:\n\techo hi\n');
  writeFileSync(path.join(root, 'good-app', 'src', 'main.py'), 'print(1)\n');
  writeFileSync(path.join(root, 'good-app', '.venv', 'junk'), 'x');
  writeFileSync(path.join(root, 'good-app', 'outputs', 'big.bin'), 'x');

  const lines = [];
  const code = scaffoldApp({ appsDir: root, id: 'new-thing', from: 'good-app', log: (...a) => lines.push(a.join(' ')) });
  assert.equal(code, 0);
  assert.ok(existsSync(path.join(root, 'new-thing', 'Makefile')));
  assert.ok(existsSync(path.join(root, 'new-thing', 'src', 'main.py')));
  assert.ok(!existsSync(path.join(root, 'new-thing', '.venv')));
  assert.ok(!existsSync(path.join(root, 'new-thing', 'outputs')));
  const yaml = parseAppYaml(readFileSync(path.join(root, 'new-thing', 'robium-app.yaml'), 'utf8'));
  assert.equal(yaml.id, 'new-thing');
  assert.equal(yaml.version, '0.1.0');
  assert.equal(yaml.status, 'experimental');
  assert.ok(lines.some((l) => l.includes('REGISTRY.md')));

  // guards
  assert.equal(scaffoldApp({ appsDir: root, id: 'new-thing', from: 'good-app', log: () => {} }), 1); // exists
  assert.equal(scaffoldApp({ appsDir: root, id: 'Bad_Name', from: 'good-app', log: () => {} }), 1);
  assert.equal(scaffoldApp({ appsDir: root, id: 'x2', from: 'ghost', log: () => {} }), 1);
  assert.equal(scaffoldApp({ appsDir: root, id: 'x3', log: () => {} }), 1); // no --from
});
