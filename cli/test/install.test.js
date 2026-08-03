import test from 'node:test';
import assert from 'node:assert/strict';
import { installClaude } from '../src/install.js';

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
