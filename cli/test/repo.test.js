import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { findEnclosingRepo, resolveRepo, REPO_URL } from '../src/repo.js';

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

async function makeRepo(dir) {
  await mkdir(path.join(dir, '.claude-plugin'), { recursive: true });
  await writeFile(path.join(dir, '.claude-plugin', 'plugin.json'), '{}');
  await mkdir(path.join(dir, 'skills', 'ros2'), { recursive: true });
  await writeFile(path.join(dir, 'skills', 'ros2', 'SKILL.md'), '---\nname: ros2\nversion: 1.0.0\ndescription: t\n---\n');
}

async function scratch() {
  return mkdtemp(path.join(os.tmpdir(), 'robium-repo-'));
}

test('findEnclosingRepo: finds checkout from nested dir; null outside', async () => {
  const base = await scratch();
  const repo = path.join(base, 'robium');
  await makeRepo(repo);
  const nested = path.join(repo, 'apps', 'demo');
  await mkdir(nested, { recursive: true });
  assert.equal(await findEnclosingRepo(nested), repo);
  assert.equal(await findEnclosingRepo(base), null);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: inside checkout → uses it, zero git calls', async () => {
  const base = await scratch();
  const repo = path.join(base, 'robium');
  await makeRepo(repo);
  const { exec, calls } = recordingExec({});
  const out = await resolveRepo({ exec, home: base, cwd: repo, log: () => {}, error: () => {} });
  assert.equal(out, repo);
  assert.equal(calls.length, 0);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: no git → null with manual clone recipe', async () => {
  const base = await scratch();
  const { exec } = recordingExec({});
  let err = '';
  const out = await resolveRepo({ exec, home: base, cwd: base, yes: true, log: () => {}, error: (s) => { err += s; } });
  assert.equal(out, null);
  assert.match(err, /git clone/);
  assert.match(err, /git not found/);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: existing clean clone → pull --ff-only', async () => {
  const base = await scratch();
  const repo = path.join(base, 'robium');
  await makeRepo(repo);
  const { exec, calls } = recordingExec({
    'git --version': {},
    'git -C': {}, // status (empty stdout) and pull both ok
  });
  const out = await resolveRepo({ exec, home: base, cwd: base, yes: true, log: () => {}, error: () => {} });
  assert.equal(out, repo);
  assert.ok(calls.some((c) => c === `git -C ${repo} pull --ff-only`));
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: dirty clone → no pull, still returns path', async () => {
  const base = await scratch();
  const repo = path.join(base, 'robium');
  await makeRepo(repo);
  const { exec, calls } = recordingExec({
    'git --version': {},
    'git -C': { stdout: ' M skills/ros2/SKILL.md\n' },
  });
  let out = '';
  const result = await resolveRepo({ exec, home: base, cwd: base, yes: true, log: (s) => { out += s; }, error: () => {} });
  assert.equal(result, repo);
  assert.ok(!calls.some((c) => c.includes('pull')));
  assert.match(out, /local changes/);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: target exists but not robium → error', async () => {
  const base = await scratch();
  await mkdir(path.join(base, 'robium', 'something'), { recursive: true });
  const { exec } = recordingExec({ 'git --version': {} });
  let err = '';
  const out = await resolveRepo({ exec, home: base, cwd: base, yes: true, log: () => {}, error: (s) => { err += s; } });
  assert.equal(out, null);
  assert.match(err, /not a robium checkout/);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: missing target → git clone', async () => {
  const base = await scratch();
  const { exec, calls } = recordingExec({ 'git --version': {}, 'git clone': {} });
  const out = await resolveRepo({ exec, home: base, cwd: base, yes: true, log: () => {}, error: () => {} });
  assert.equal(out, path.join(base, 'robium'));
  assert.ok(calls.includes(`git clone ${REPO_URL} ${path.join(base, 'robium')}`));
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: interactive prompt answer wins; -y skips prompt', async () => {
  const base = await scratch();
  const custom = path.join(base, 'elsewhere');
  const { exec } = recordingExec({ 'git --version': {}, 'git clone': {} });
  let asked = 0;
  const out = await resolveRepo({
    exec, home: base, cwd: base, interactive: true,
    ask: async () => { asked++; return custom; },
    log: () => {}, error: () => {},
  });
  assert.equal(out, custom);
  assert.equal(asked, 1);

  let askedY = 0;
  const outY = await resolveRepo({
    exec, home: base, cwd: base, yes: true, interactive: true,
    ask: async () => { askedY++; return 'ignored'; },
    log: () => {}, error: () => {},
  });
  assert.equal(outY, path.join(base, 'robium'));
  assert.equal(askedY, 0);
  await rm(base, { recursive: true, force: true });
});

test('resolveRepo: ~ expansion in prompt answer', async () => {
  const base = await scratch();
  const { exec } = recordingExec({ 'git --version': {}, 'git clone': {} });
  const out = await resolveRepo({
    exec, home: base, cwd: base, interactive: true,
    ask: async () => '~/tools/robium',
    log: () => {}, error: () => {},
  });
  assert.equal(out, path.join(base, 'tools', 'robium'));
  await rm(base, { recursive: true, force: true });
});
