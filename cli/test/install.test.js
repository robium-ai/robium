import test from 'node:test';
import assert from 'node:assert/strict';
import {
  installClaude, installCodex, uninstallClaude, uninstallCodex,
} from '../src/install.js';

function recordingExec(responses) {
  const calls = [];
  const exec = async (cmd, args) => {
    const key = [cmd, ...args].join(' ');
    calls.push(key);
    for (const [prefix, result] of Object.entries(responses)) {
      if (key.startsWith(prefix)) return { ok: true, code: 0, stdout: '', stderr: '', ...result };
    }
    return { ok: false, code: 1, stdout: '', stderr: 'not found' };
  };
  return { exec, calls };
}

const HAPPY = {
  'claude --version': { stdout: '2.1.211 (Claude Code)\n' },
  'claude plugin marketplace add': {},
  'claude plugin install': {},
  'claude plugin list': { stdout: '[{"id":"robium@robium","enabled":true}]' },
};

const CODEX_HAPPY = {
  'codex --version': { stdout: 'codex-cli 0.146.0\n' },
  'codex plugin marketplace add': {},
  'codex plugin add': { stdout: '{"installed":true}\n' },
  'codex plugin list': { stdout: '{"installed":[{"pluginId":"robium@robium","enabled":true}]}' },
};

test('installClaude: happy path runs add → install → verify, exit 0', async () => {
  const { exec, calls } = recordingExec(HAPPY);
  const code = await installClaude({ exec, log: () => {}, error: () => {} });
  assert.equal(code, 0);
  assert.deepEqual(calls, [
    'claude --version',
    'claude plugin marketplace add robium-ai/robium',
    'claude plugin install robium@robium --scope user',
    'claude plugin list --json',
  ]);
});

test('installClaude: claude missing → exit 1 with install pointer', async () => {
  const { exec } = recordingExec({});
  let err = '';
  const code = await installClaude({ exec, log: () => {}, error: (s) => { err += s; } });
  assert.equal(code, 1);
  assert.match(err, /claude\.com\/claude-code/);
});

test('installClaude: marketplace already exists → falls back to update', async () => {
  const { exec, calls } = recordingExec({
    ...HAPPY,
    'claude plugin marketplace add': { ok: false, stderr: 'Marketplace robium already exists' },
    'claude plugin marketplace update': {},
  });
  const code = await installClaude({ exec, log: () => {}, error: () => {} });
  assert.equal(code, 0);
  assert.ok(calls.includes('claude plugin marketplace update robium'));
});

test('installClaude: an existing plugin is updated instead of silently reused', async () => {
  const { exec, calls } = recordingExec({
    ...HAPPY,
    'claude plugin install': { ok: false, stderr: 'Plugin already installed' },
    'claude plugin update': {},
  });
  assert.equal(await installClaude({ exec, log: () => {}, error: () => {} }), 0);
  assert.ok(calls.includes('claude plugin update robium@robium --scope user'));
});

test('installClaude: enables an installed but disabled Robium plugin', async () => {
  const { exec, calls } = recordingExec({
    ...HAPPY,
    'claude plugin list': { stdout: '[{"id":"robium@robium","enabled":false}]' },
    'claude plugin enable': {},
  });
  assert.equal(await installClaude({ exec, log: () => {}, error: () => {} }), 0);
  assert.ok(calls.includes('claude plugin enable robium@robium --scope user'));
});

test('installCodex: happy path runs marketplace add → plugin add → verify', async () => {
  const { exec, calls } = recordingExec(CODEX_HAPPY);
  const code = await installCodex({ exec, log: () => {}, error: () => {} });
  assert.equal(code, 0);
  assert.deepEqual(calls, [
    'codex --version',
    'codex plugin marketplace add robium-ai/robium',
    'codex plugin add robium@robium --json',
    'codex plugin list --json',
  ]);
});

test('installCodex: marketplace already exists → upgrades it', async () => {
  const { exec, calls } = recordingExec({
    ...CODEX_HAPPY,
    'codex plugin marketplace add': { ok: false, stderr: 'marketplace already configured' },
    'codex plugin marketplace upgrade': {},
  });
  const code = await installCodex({ exec, log: () => {}, error: () => {} });
  assert.equal(code, 0);
  assert.ok(calls.includes('codex plugin marketplace upgrade robium'));
});

test('installCodex: missing binary is actionable', async () => {
  const { exec } = recordingExec({});
  let err = '';
  const code = await installCodex({ exec, log: () => {}, error: (s) => { err += s; } });
  assert.equal(code, 1);
  assert.match(err, /setup --agent codex/);
});

test('installCodex: uses an explicitly resolved desktop command', async () => {
  const desktop = '/Applications/ChatGPT.app/Contents/Resources/codex';
  const { exec, calls } = recordingExec({
    [`${desktop} --version`]: { stdout: 'codex-cli desktop\n' },
    [`${desktop} plugin marketplace add`]: {},
    [`${desktop} plugin add`]: {},
    [`${desktop} plugin list`]: { stdout: '{"installed":[{"pluginId":"robium@robium","enabled":true}]}' },
  });
  assert.equal(await installCodex({ exec, command: desktop, log: () => {}, error: () => {} }), 0);
  assert.ok(calls.includes(`${desktop} plugin add robium@robium --json`));
  assert.ok(!calls.some((call) => call.startsWith('codex ')));
});

test('uninstallClaude removes only the Robium plugin and marketplace', async () => {
  const { exec, calls } = recordingExec({
    'claude plugin list': { stdout: '[{"id":"robium@robium","enabled":true}]' },
    'claude plugin uninstall': {},
    'claude plugin marketplace list': { stdout: '[{"name":"robium"},{"name":"other"}]' },
    'claude plugin marketplace remove': {},
  });
  const result = await uninstallClaude({ exec });
  assert.equal(result.errors.length, 0);
  assert.equal(result.removed.length, 2);
  assert.deepEqual(calls, [
    'claude plugin list --json',
    'claude plugin uninstall robium@robium --scope user',
    'claude plugin marketplace list --json',
    'claude plugin marketplace remove robium --scope user',
  ]);
});

test('uninstallCodex is idempotent when Robium is already absent', async () => {
  const { exec, calls } = recordingExec({
    'codex plugin list': { stdout: '{"installed":[]}' },
    'codex plugin marketplace list': { stdout: '{"marketplaces":[]}' },
  });
  const result = await uninstallCodex({ exec });
  assert.equal(result.errors.length, 0);
  assert.equal(result.removed.length, 0);
  assert.equal(result.skipped.length, 2);
  assert.deepEqual(calls, [
    'codex plugin list --json',
    'codex plugin marketplace list --json',
  ]);
});

test('uninstallClaude cleans a partial marketplace-only install', async () => {
  const { exec, calls } = recordingExec({
    'claude plugin list': { stdout: '[]' },
    'claude plugin marketplace list': { stdout: '[{"name":"robium"}]' },
    'claude plugin marketplace remove': {},
  });
  const result = await uninstallClaude({ exec });
  assert.equal(result.errors.length, 0);
  assert.deepEqual(result.removed, ['Claude Code marketplace robium']);
  assert.equal(result.skipped.length, 1);
  assert.ok(!calls.some((call) => call.startsWith('claude plugin uninstall')));
  assert.ok(calls.includes('claude plugin marketplace remove robium --scope user'));
});
