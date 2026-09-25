import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { firstSentence } from '../src/skills.js';

const bin = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'bin', 'robium.js');
const runCli = (...args) => spawnSync(process.execPath, [bin, ...args], { encoding: 'utf8' });

test('--help prints usage, exit 0', () => {
  const r = runCli('--help');
  assert.equal(r.status, 0);
  assert.match(r.stdout, /Usage:/);
  assert.match(r.stdout, /npx robium-ai remove/);
});

test('no args prints usage, exit 0', () => {
  const r = runCli();
  assert.equal(r.status, 0);
  assert.match(r.stdout, /npx robium-ai install/);
});

test('--version prints package version', () => {
  const r = runCli('--version');
  assert.equal(r.status, 0);
  assert.match(r.stdout.trim(), /^\d+\.\d+\.\d+$/);
});

test('unknown command → usage on stderr, exit 1', () => {
  const r = runCli('frobnicate');
  assert.equal(r.status, 1);
  assert.match(r.stderr, /Unknown command/);
});

test('workspace help describes both repos and readonly update-check flow', () => {
  const r = runCli('--help');
  assert.match(r.stdout, /robium-apps/);
  assert.match(r.stdout, /workspace \[--json\]/);
  assert.match(r.stdout, /update --check/);
});

test('missing paths and misplaced check flags fail before setup can mutate anything', () => {
  for (const args of [['setup', '--dir'], ['setup', '--dir='], ['setup', '--check'], ['setup', '--all']]) {
    const r = runCli(...args);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /--dir requires|update options|remove option/);
  }
});

test('remove --all cannot be narrowed to one agent', () => {
  const r = runCli('remove', '--all', '--agent', 'cursor');
  assert.equal(r.status, 1);
  assert.match(r.stderr, /cannot be combined/);
});

test('ambiguous machine-readable or quiet update requests fail before mutation', () => {
  for (const args of [['update', '--json'], ['update', '--check', '--quiet', '--json']]) {
    const r = runCli(...args);
    assert.equal(r.status, 1);
    assert.match(r.stderr, /--json requires|not both/);
  }
});

test('skills lists the real generated catalog', () => {
  const r = runCli('skills');
  assert.equal(r.status, 0);
  assert.match(r.stdout, /architect/);
  assert.match(r.stdout, /ros2/);
});

test('skills with no-match query → exit 1', () => {
  const r = runCli('skills', 'zzz-no-such-skill');
  assert.equal(r.status, 1);
});

test('firstSentence truncates long text and cuts at sentence boundary', () => {
  assert.equal(firstSentence('Short. Rest ignored.'), 'Short.');
  const long = 'x'.repeat(300);
  assert.ok(firstSentence(long).length <= 120);
  assert.match(firstSentence(long), /…$/);
});
