import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import {
  lstat, mkdir, mkdtemp, readFile, rm, symlink, writeFile,
} from 'node:fs/promises';
import { remove, removeManagedSkills } from '../src/remove.js';
import { setup } from '../src/setup.js';

async function exists(target) {
  try { await lstat(target); return true; } catch { return false; }
}

async function fixture() {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-remove-'));
  const home = path.join(base, 'home');
  const repo = path.join(base, 'robium');
  await mkdir(home, { recursive: true });
  await mkdir(path.join(repo, '.claude-plugin'), { recursive: true });
  await mkdir(path.join(repo, '.codex-plugin'), { recursive: true });
  await writeFile(path.join(repo, '.claude-plugin', 'plugin.json'), '{}');
  await writeFile(path.join(repo, '.codex-plugin', 'plugin.json'), '{}');
  for (const name of ['ros2', 'gazebo']) {
    await mkdir(path.join(repo, 'skills', name), { recursive: true });
    await writeFile(path.join(repo, 'skills', name, 'SKILL.md'), `name: ${name}\n`);
  }
  return { base, home, repo };
}

function fullExec() {
  const calls = [];
  const exec = async (command, args) => {
    const key = [command, ...args].join(' ');
    calls.push(key);
    if (args[0] === '--version') {
      const present = ['claude', 'codex', 'gemini', 'cursor-agent'];
      return { ok: present.includes(command), code: present.includes(command) ? 0 : 1,
        stdout: present.includes(command) ? '1.0.0\n' : '', stderr: '' };
    }
    if (key === 'claude plugin list --json') {
      return { ok: true, code: 0, stdout: '[{"id":"robium@robium","enabled":true}]', stderr: '' };
    }
    if (key === 'claude plugin marketplace list --json') {
      return { ok: true, code: 0, stdout: '[{"name":"robium"}]', stderr: '' };
    }
    if (key === 'codex plugin list --json') {
      return { ok: true, code: 0, stdout: '{"installed":[{"pluginId":"robium@robium"}]}', stderr: '' };
    }
    if (key === 'codex plugin marketplace list --json') {
      return { ok: true, code: 0, stdout: '{"marketplaces":[{"name":"robium"}]}', stderr: '' };
    }
    if (args[0] === 'plugin') return { ok: true, code: 0, stdout: '', stderr: '' };
    return { ok: false, code: 1, stdout: '', stderr: 'not found' };
  };
  return { exec, calls };
}

test('removeManagedSkills removes only Robium links and marked copies', async () => {
  const fx = await fixture();
  const target = path.join(fx.home, '.gemini', 'skills');
  await mkdir(target, { recursive: true });
  await symlink(path.join(fx.repo, 'skills', 'ros2'), path.join(target, 'ros2'), 'dir');
  await mkdir(path.join(target, 'gazebo'));
  await writeFile(path.join(target, 'gazebo', '.robium-managed'), 'robium-ai 0.7.0\n');
  await writeFile(path.join(target, 'gazebo', 'SKILL.md'), 'copied\n');
  await mkdir(path.join(target, 'foreign'));
  await writeFile(path.join(target, 'foreign', 'SKILL.md'), 'keep me\n');
  await writeFile(path.join(target, 'notes.txt'), 'keep me too\n');

  const first = await removeManagedSkills({ targetDir: target });
  assert.deepEqual(first.removed.map((item) => path.basename(item)).sort(), ['gazebo', 'ros2']);
  assert.equal(first.skipped.length, 2);
  assert.equal(first.errors.length, 0);
  assert.equal(await readFile(path.join(target, 'foreign', 'SKILL.md'), 'utf8'), 'keep me\n');
  assert.ok(await exists(path.join(target, 'notes.txt')));
  assert.ok(await exists(fx.repo));

  const second = await removeManagedSkills({ targetDir: target });
  assert.equal(second.removed.length, 0);
  assert.equal(second.errors.length, 0);
  await rm(fx.base, { recursive: true, force: true });
});

test('remove reverses every supported setup integration and preserves checkout', async () => {
  const fx = await fixture();
  const { exec, calls } = fullExec();
  assert.equal(await setup({
    exec, home: fx.home, cwd: fx.repo, log: () => {}, error: () => {},
  }), 0);
  assert.ok(await exists(path.join(fx.home, '.gemini', 'skills', 'ros2')));
  assert.ok(await exists(path.join(fx.home, '.cursor', 'skills', 'ros2')));

  let output = '';
  const code = await remove({
    exec, home: fx.home, log: (line) => { output += `${line}\n`; }, error: () => {},
  });
  assert.equal(code, 0);
  assert.ok(calls.includes('claude plugin uninstall robium@robium --scope user'));
  assert.ok(calls.includes('claude plugin marketplace remove robium --scope user'));
  assert.ok(calls.includes('codex plugin remove robium@robium --json'));
  assert.ok(calls.includes('codex plugin marketplace remove robium --json'));
  assert.ok(!(await exists(path.join(fx.home, '.gemini', 'skills', 'ros2'))));
  assert.ok(!(await exists(path.join(fx.home, '.cursor', 'skills', 'ros2'))));
  assert.ok(await exists(fx.repo));
  assert.match(output, /checkout was preserved/);
  await rm(fx.base, { recursive: true, force: true });
});

test('remove explicit skill host works when the agent is not detected', async () => {
  const fx = await fixture();
  const target = path.join(fx.home, '.gemini', 'skills');
  await mkdir(target, { recursive: true });
  await symlink(path.join(fx.repo, 'skills', 'ros2'), path.join(target, 'ros2'), 'dir');
  const exec = async () => ({ ok: false, code: 1, stdout: '', stderr: 'missing' });
  assert.equal(await remove({ agent: 'gemini', exec, home: fx.home, log: () => {}, error: () => {} }), 0);
  assert.ok(!(await exists(path.join(target, 'ros2'))));
  await rm(fx.base, { recursive: true, force: true });
});

test('remove is a successful no-op when nothing is installed', async () => {
  const fx = await fixture();
  const exec = async () => ({ ok: false, code: 1, stdout: '', stderr: 'missing' });
  let output = '';
  const code = await remove({ exec, home: fx.home, log: (line) => { output += line; }, error: () => {} });
  assert.equal(code, 0);
  assert.match(output, /Nothing to remove/);
  await rm(fx.base, { recursive: true, force: true });
});

test('remove fails safely when native plugin state cannot be inspected', async () => {
  const fx = await fixture();
  const calls = [];
  const exec = async (command, args) => {
    calls.push([command, ...args].join(' '));
    return { ok: false, code: 1, stdout: '', stderr: 'unavailable' };
  };
  assert.equal(await remove({
    agent: 'codex', exec, home: fx.home, log: () => {}, error: () => {},
  }), 1);
  assert.ok(!calls.some((call) => call.includes('plugin remove')));
  assert.ok(await exists(fx.repo));
  await rm(fx.base, { recursive: true, force: true });
});

test('remove rejects unknown agents without touching files', async () => {
  const fx = await fixture();
  let message = '';
  const code = await remove({ agent: 'emacs', home: fx.home, log: () => {}, error: (line) => { message += line; } });
  assert.equal(code, 1);
  assert.match(message, /Unknown agent/);
  assert.ok(await exists(fx.repo));
  await rm(fx.base, { recursive: true, force: true });
});
