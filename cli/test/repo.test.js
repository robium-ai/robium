import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { mkdir, writeFile, readFile, rename } from 'node:fs/promises';
import { resolveWorkspace } from '../src/repo.js';
import { findWorkspace, readWorkspaceConfig, workspaceConfigPath } from '../src/workspace.js';
import { findAppsDir } from '../src/apps.js';
import { fixture } from './helpers/git-workspace.js';

test('custom parent clones both repositories, remembers paths, and reuses without pulling', async t => {
  const fx = await fixture(t);
  const workspace = await resolveWorkspace(fx.options);
  assert.equal(workspace.repo, path.join(fx.root, 'robium'));
  assert.equal(workspace.apps, path.join(fx.root, 'robium-apps'));
  assert.equal(readWorkspaceConfig(fx.home).root, fx.root);
  assert.equal(findWorkspace({ cwd: fx.home, home: fx.home }).root, fx.root);
  assert.equal(findWorkspace({ cwd: workspace.repo, home: fx.home }).root, fx.root);
  await fx.git(workspace.repo, 'switch', '-c', 'my-experiment');
  await writeFile(path.join(workspace.repo, 'sample.txt'), 'mine\n');
  fx.calls.length = 0;
  assert.deepEqual(await resolveWorkspace({ ...fx.options, dir: undefined, cwd: fx.home }), workspace);
  assert.ok(!fx.calls.some(c => c.includes('pull') || c.includes('fetch') || c.includes('clone')));
  assert.equal(await readFile(path.join(workspace.repo, 'sample.txt'), 'utf8'), 'mine\n');
  assert.equal(await fx.git(workspace.repo, 'branch', '--show-current'), 'my-experiment');
});

test('prompt expands tilde; --yes uses default; explicit dir wins saved and current paths', async t => {
  const fx = await fixture(t);
  let asked = 0;
  const first = await resolveWorkspace({ ...fx.options, dir: undefined, yes: false, interactive: true,
    ask: async () => { asked++; return '~/tools/robotics'; } });
  assert.equal(first.root, path.join(fx.home, 'tools/robotics'));
  assert.equal(asked, 1);
  assert.equal((await resolveWorkspace({ ...fx.options, cwd: first.repo })).root, fx.root);
  const otherHome = path.join(fx.base, 'other-home');
  const defaults = await resolveWorkspace({ ...fx.options, dir: undefined, home: otherHome, interactive: true,
    ask: async () => { throw new Error('must not ask'); } });
  assert.equal(defaults.root, path.join(otherHome, 'robium-workspace'));
});

test('foreign and interrupted destinations are preserved; no config is saved on failure', async t => {
  const fx = await fixture(t);
  const foreign = path.join(fx.root, 'robium-apps');
  await mkdir(foreign, { recursive: true });
  await writeFile(path.join(foreign, 'mine.txt'), 'keep');
  assert.equal(await resolveWorkspace(fx.options), null);
  assert.equal(await readFile(path.join(foreign, 'mine.txt'), 'utf8'), 'keep');
  assert.equal(readWorkspaceConfig(fx.home), null);
  assert.ok(!fx.calls.some(c => c.includes('clone')));
});

test('missing git and failed clone are explicit failures; second clone failure is retryable', async t => {
  const fx = await fixture(t);
  assert.equal(await resolveWorkspace({ ...fx.options, exec: async () => ({ ok: false }) }), null);
  const failed = async (cmd, args, opts) => args[0] === 'clone' && args.at(-1).endsWith('robium-apps')
    ? { ok: false } : fx.exec(cmd, args, opts);
  assert.equal(await resolveWorkspace({ ...fx.options, exec: failed }), null);
  assert.equal(readWorkspaceConfig(fx.home), null);
  const workspace = await resolveWorkspace(fx.options);
  assert.ok(workspace);
  assert.equal(fx.calls.filter(c => c.includes('clone') && c.at(-1) === workspace.repo).length, 1);
});

test('apps resolve from the saved workspace outside it; explicit choices still win', async t => {
  const fx = await fixture(t);
  const workspace = await resolveWorkspace(fx.options);
  await writeFile(path.join(workspace.apps, 'REGISTRY.md'), '# Apps');
  await mkdir(path.join(workspace.apps, 'demo'));
  await writeFile(path.join(workspace.apps, 'demo/robium-app.yaml'), 'id: demo');
  assert.equal(findAppsDir({ home: fx.home, cwd: fx.home, env: {} }), workspace.apps);
  assert.equal(findAppsDir({ home: fx.home, cwd: fx.home, env: {}, dir: fx.base }), fx.base);
});

test('invalid saved config is reported instead of silently choosing another location', async t => {
  const fx = await fixture(t);
  const file = workspaceConfigPath(fx.home);
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, 'broken');
  assert.throws(() => findWorkspace({ home: fx.home, cwd: fx.home }), /Cannot read/);
  assert.equal(await resolveWorkspace(fx.options), null);
  assert.equal(await readFile(file, 'utf8'), 'broken');
});

test('a moved saved workspace is not silently cloned again; explicit setup registers its new parent', async t => {
  const fx = await fixture(t);
  await resolveWorkspace(fx.options);
  const moved = path.join(fx.base, 'renamed workspace');
  await rename(fx.root, moved);
  fx.calls.length = 0;
  assert.equal(await resolveWorkspace({ ...fx.options, dir: undefined, cwd: fx.home }), null);
  assert.equal(fx.calls.length, 0);
  assert.equal((await resolveWorkspace({ ...fx.options, dir: moved })).root, moved);
  assert.equal(readWorkspaceConfig(fx.home).root, moved);
});
