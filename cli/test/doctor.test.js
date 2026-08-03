import test from 'node:test';
import assert from 'node:assert/strict';
import { runChecks, doctor } from '../src/doctor.js';

// Fake exec keyed on "cmd arg0" prefixes; everything unlisted fails as missing.
function fakeExec(table) {
  return async (cmd, args = []) => {
    const key = [cmd, ...args].join(' ');
    for (const [prefix, result] of Object.entries(table)) {
      if (key.startsWith(prefix)) return { ok: true, code: 0, stdout: '', stderr: '', ...result };
    }
    return { ok: false, code: 1, stdout: '', stderr: `${cmd}: not found` };
  };
}

const ALL_GOOD = {
  'claude --version': { stdout: '2.1.211 (Claude Code)\n' },
  'claude plugin list': { stdout: '[{"id":"robium@robium","enabled":true}]' },
  'docker --version': { stdout: 'Docker version 27.0.0\n' },
  'docker info': { stdout: '27.0.0\n' },
  df: { stdout: 'Filesystem 1024-blocks Used Available Capacity Mounted\n/dev/disk 999 1 209715200 1% /\n' },
  'python3 --version': { stdout: 'Python 3.12.4\n' },
  'uv --version': { stdout: 'uv 0.7.0\n' },
  'ros2 --help': { stdout: 'usage: ros2\n' },
  'nvidia-smi': { stdout: 'NVIDIA RTX 4090, 550.00\n' },
};

test('doctor: all healthy on linux → no fail, exit 0', async () => {
  const results = await runChecks({ exec: fakeExec(ALL_GOOD), platform: 'linux', arch: 'x64', env: { DISPLAY: ':0' } });
  assert.ok(results.every((r) => r.status !== 'fail'));
  const code = await doctor({ exec: fakeExec(ALL_GOOD), platform: 'linux', arch: 'x64', env: { DISPLAY: ':0' }, log: () => {} });
  assert.equal(code, 0);
});

test('doctor: missing claude → fail check and exit 1', async () => {
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  assert.equal(results.find((r) => r.id === 'claude').status, 'fail');
  assert.equal(results.find((r) => r.id === 'plugin').status, 'skip');
  const code = await doctor({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {}, log: () => {} });
  assert.equal(code, 1);
});

test('doctor: plugin not installed → warn with install hint', async () => {
  const table = { ...ALL_GOOD, 'claude plugin list': { stdout: '[]' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'plugin');
  assert.equal(plugin.status, 'warn');
  assert.match(plugin.hint, /npx robium-ai install/);
});

test('doctor: plugin installed but failed to load → warn "not loaded", not "not installed"', async () => {
  const table = { ...ALL_GOOD, 'claude plugin list': { stdout: '[{"id":"robium@robium","enabled":false}]' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'plugin');
  assert.equal(plugin.status, 'warn');
  assert.match(plugin.detail, /not loaded/);
});

test('doctor: docker daemon down → warn, not fail', async () => {
  const table = { ...ALL_GOOD, 'docker info': { ok: false, stderr: 'Cannot connect to the Docker daemon' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  assert.equal(results.find((r) => r.id === 'docker').status, 'warn');
});

test('doctor: apple silicon reports MPS without calling nvidia-smi', async () => {
  const results = await runChecks({ exec: fakeExec(ALL_GOOD), platform: 'darwin', arch: 'arm64', env: {} });
  const gpu = results.find((r) => r.id === 'gpu');
  assert.equal(gpu.status, 'pass');
  assert.match(gpu.detail, /MPS/);
});

test('doctor: low disk → warn', async () => {
  const table = { ...ALL_GOOD, df: { stdout: 'Filesystem 1024-blocks Used Available Capacity Mounted\n/dev/disk 999 1 1048576 1% /\n' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  assert.equal(results.find((r) => r.id === 'disk').status, 'warn');
});

test('doctor --json emits parseable report', async () => {
  let out = '';
  const code = await doctor({ exec: fakeExec(ALL_GOOD), platform: 'linux', arch: 'x64', env: {}, json: true, log: (s) => { out += s; } });
  const report = JSON.parse(out);
  assert.equal(report.ok, true);
  assert.equal(code, 0);
  assert.ok(Array.isArray(report.checks) && report.checks.length >= 8);
});
