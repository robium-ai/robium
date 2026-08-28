import test from 'node:test';
import assert from 'node:assert/strict';
import { detectAgentSupport, resolveCodexCommand } from '../src/agentCommands.js';

const DESKTOP_CODEX = '/Applications/ChatGPT.app/Contents/Resources/codex';

test('resolveCodexCommand: uses PATH when available', async () => {
  const exec = async (cmd) => ({
    ok: cmd === 'codex',
    code: cmd === 'codex' ? 0 : 1,
    stdout: cmd === 'codex' ? 'codex-cli 1.0.0\n' : '',
    stderr: '',
  });
  const resolved = await resolveCodexCommand({ exec, platform: 'darwin', home: '/Users/test' });
  assert.equal(resolved.command, 'codex');
  assert.equal(resolved.source, 'PATH');
});

test('resolveCodexCommand: finds the Codex Desktop bundled CLI', async () => {
  const calls = [];
  const exec = async (cmd) => {
    calls.push(cmd);
    return {
      ok: cmd === DESKTOP_CODEX,
      code: cmd === DESKTOP_CODEX ? 0 : 1,
      stdout: cmd === DESKTOP_CODEX ? 'codex-cli desktop\n' : '',
      stderr: '',
    };
  };
  const resolved = await resolveCodexCommand({ exec, platform: 'darwin', home: '/Users/test' });
  assert.equal(resolved.command, DESKTOP_CODEX);
  assert.equal(resolved.source, 'Codex Desktop');
  assert.deepEqual(calls.slice(0, 2), ['codex', DESKTOP_CODEX]);
});

test('detectAgentSupport: reports Codex Desktop as a supported agent', async () => {
  const exec = async (cmd) => ({
    ok: cmd === DESKTOP_CODEX,
    code: cmd === DESKTOP_CODEX ? 0 : 1,
    stdout: cmd === DESKTOP_CODEX ? 'codex-cli desktop\n' : '',
    stderr: '',
  });
  const support = await detectAgentSupport({ exec, platform: 'darwin', home: '/no/such/home' });
  assert.deepEqual(support.agents, ['codex']);
  assert.equal(support.codex.command, DESKTOP_CODEX);
});
