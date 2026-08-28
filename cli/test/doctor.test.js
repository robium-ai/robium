import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdir, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
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
  'claude plugin list': { stdout: '[{"id":"robium@robium","version":"0.4.0","enabled":true}]' },
  'codex --version': { stdout: 'codex-cli 0.146.0\n' },
  'codex plugin list': { stdout: '{"installed":[{"pluginId":"robium@robium","version":"0.4.0","enabled":true}]}' },
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

test('doctor: Codex-only setup is healthy', async () => {
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  assert.equal(results.find((r) => r.id === 'coding-agent').status, 'pass');
  assert.equal(results.find((r) => r.id === 'claude').status, 'skip');
  assert.equal(results.find((r) => r.id === 'codex-plugin').status, 'pass');
  const code = await doctor({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {}, log: () => {} });
  assert.equal(code, 0);
});

test('doctor: finds Codex Desktop when codex is not on PATH', async () => {
  const desktop = '/Applications/ChatGPT.app/Contents/Resources/codex';
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  delete table['codex --version'];
  delete table['codex plugin list'];
  table[`${desktop} --version`] = { stdout: 'codex-cli desktop\n' };
  table[`${desktop} plugin list`] = { stdout: '{"installed":[{"pluginId":"robium@robium","enabled":true}]}' };
  const results = await runChecks({ exec: fakeExec(table), platform: 'darwin', arch: 'arm64', env: {}, home: '/Users/test' });
  assert.match(results.find((r) => r.id === 'codex').detail, /Codex Desktop/);
  assert.equal(results.find((r) => r.id === 'codex-plugin').status, 'pass');
});

test('doctor: Gemini-only setup counts as a supported coding agent', async () => {
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  delete table['codex --version'];
  delete table['codex plugin list'];
  table['gemini --version'] = { stdout: '0.30.0\n' };
  table['gemini extensions list'] = { stdout: '[{"name":"robium","version":"0.4.0","isActive":true}]' };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {}, home: '/no/such/home' });
  assert.equal(results.find((r) => r.id === 'coding-agent').status, 'pass');
  assert.equal(results.find((r) => r.id === 'gemini').status, 'pass');
  assert.equal(results.find((r) => r.id === 'gemini-extension').status, 'pass');
});

test('doctor: Cursor reports installed skills with activation unknown', async () => {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-doctor-cursor-'));
  const home = path.join(base, 'home');
  const repo = path.join(base, 'robium');
  await mkdir(path.join(repo, '.codex-plugin'), { recursive: true });
  await writeFile(path.join(repo, '.codex-plugin', 'plugin.json'), '{}');
  await mkdir(path.join(repo, 'skills', 'nav2'), { recursive: true });
  await writeFile(path.join(repo, 'skills', 'nav2', 'SKILL.md'), '---\nname: nav2\ndescription: test\n---\n');
  await mkdir(path.join(home, '.cursor', 'skills'), { recursive: true });
  await symlink(path.join(repo, 'skills', 'nav2'), path.join(home, '.cursor', 'skills', 'nav2'), 'dir');
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  delete table['codex --version'];
  delete table['codex plugin list'];
  table['cursor-agent --version'] = { stdout: 'cursor-agent 1.0.0\n' };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {}, home });
  assert.equal(results.find((r) => r.id === 'coding-agent').status, 'pass');
  assert.equal(results.find((r) => r.id === 'cursor').status, 'pass');
  const skills = results.find((r) => r.id === 'cursor-skills');
  assert.equal(skills.status, 'warn');
  assert.match(skills.detail, /activation status unavailable/);
  assert.match(skills.hint, /new Cursor chat/);
  await rm(base, { recursive: true, force: true });
});

test('doctor: Claude plugin not installed → warn with install hint', async () => {
  const table = { ...ALL_GOOD, 'claude plugin list': { stdout: '[]' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'claude-plugin');
  assert.equal(plugin.status, 'warn');
  assert.equal(plugin.integrationState, 'missing');
  assert.match(plugin.hint, /setup --agent claude/);
});

test('doctor: plugin installed but inactive is distinct from not installed', async () => {
  const table = { ...ALL_GOOD, 'claude plugin list': { stdout: '[{"id":"robium@robium","version":"0.4.0","enabled":false}]' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'claude-plugin');
  assert.equal(plugin.status, 'warn');
  assert.equal(plugin.integrationState, 'inactive');
  assert.equal(plugin.outdated, false);
  assert.match(plugin.detail, /installed but inactive/);
  assert.match(plugin.hint, /new Claude Code session/);
});

test('doctor: obviously outdated plugin warns with update and restart guidance', async () => {
  const table = { ...ALL_GOOD,
    'codex plugin list': { stdout: '{"installed":[{"pluginId":"robium@robium","version":"0.2.0","enabled":true}]}' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'codex-plugin');
  assert.equal(plugin.status, 'warn');
  assert.equal(plugin.integrationState, 'active');
  assert.equal(plugin.outdated, true);
  assert.match(plugin.detail, /active but outdated/);
  assert.match(plugin.hint, /update --agent codex/);
  assert.match(plugin.hint, /new Codex task/);
});

test('doctor: unavailable activation API fails safely with an unknown state', async () => {
  const table = { ...ALL_GOOD,
    'claude plugin list': { ok: false, stderr: 'unsupported' } };
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  const plugin = results.find((r) => r.id === 'claude-plugin');
  assert.equal(plugin.status, 'warn');
  assert.equal(plugin.integrationState, 'unknown');
  assert.match(plugin.detail, /activation status unavailable/);
  assert.match(plugin.hint, /plugin list/);
});

test('doctor: no supported coding agent is a blocker', async () => {
  const table = { ...ALL_GOOD };
  delete table['claude --version'];
  delete table['claude plugin list'];
  delete table['codex --version'];
  delete table['codex plugin list'];
  const results = await runChecks({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {} });
  assert.equal(results.find((r) => r.id === 'coding-agent').status, 'fail');
  assert.equal(await doctor({ exec: fakeExec(table), platform: 'linux', arch: 'x64', env: {}, log: () => {} }), 1);
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
  const plugin = report.checks.find((check) => check.id === 'claude-plugin');
  assert.equal(plugin.integrationState, 'active');
  assert.equal(plugin.outdated, false);
});
