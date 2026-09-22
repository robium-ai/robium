import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { mkdir, readFile, realpath, writeFile, lstat } from 'node:fs/promises';
import { resolveWorkspace } from '../src/repo.js';
import { ensureUserApps } from '../src/userApps.js';
import { scaffoldApp } from '../src/appNew.js';
import { fixture } from './helpers/git-workspace.js';

async function seedReferenceApp(appsDir, id) {
  const dir = path.join(appsDir, id);
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(dir, 'robium-app.yaml'),
    `id: ${id}\nname: ${id}\nsummary: reference\nversion: 1.2.3\nstatus: stable\n`);
  return dir;
}

test('the workspace root is cloned as its own repository, not a submodule host', async t => {
  const fx = await fixture(t);
  const workspace = await resolveWorkspace(fx.options);
  assert.ok(workspace, 'workspace resolved');

  // Root is the workspace checkout.
  assert.equal(await fx.git(fx.root, 'rev-parse', '--show-toplevel'), await realpath(fx.root));
  const remotes = await fx.git(fx.root, 'remote', '-v');
  assert.match(remotes, /robium-workspace/);

  // Children are independent checkouts with their own remotes and history.
  for (const [dir, name] of [[workspace.repo, 'robium'], [workspace.apps, 'robium-apps']]) {
    assert.equal(await fx.git(dir, 'rev-parse', '--show-toplevel'), await realpath(dir));
    assert.match(await fx.git(dir, 'remote', '-v'), new RegExp(`${name}(\\s|$)`));
  }
  // No submodule wiring anywhere.
  assert.equal(await lstat(path.join(fx.root, '.gitmodules')).then(() => true, () => false), false);
});

test('a second setup reuses the workspace checkout without cloning or resetting it', async t => {
  const fx = await fixture(t);
  await resolveWorkspace(fx.options);
  await fx.git(fx.root, 'switch', '-c', 'my-map-edits');
  await writeFile(path.join(fx.root, 'AGENTS.md'), '# my own map\n');
  fx.calls.length = 0;

  const again = await resolveWorkspace({ ...fx.options, dir: undefined, cwd: fx.home });
  assert.ok(again);
  assert.ok(!fx.calls.some(c => c.includes('clone')), 'no re-clone');
  assert.equal(await readFile(path.join(fx.root, 'AGENTS.md'), 'utf8'), '# my own map\n');
  assert.equal(await fx.git(fx.root, 'branch', '--show-current'), 'my-map-edits');
});

test('a foreign repository at the root is still refused as a workspace parent', async t => {
  const fx = await fixture(t);
  await mkdir(fx.root, { recursive: true });
  await fx.git(fx.root, 'init', '-b', 'main');
  const errors = [];
  const result = await resolveWorkspace({ ...fx.options, error: m => errors.push(m) });
  assert.equal(result, null);
  assert.match(errors.join('\n'), /is a repository, not a workspace parent/);
});

test('ensureUserApps creates a plain library directory beside the checkouts', async t => {
  const fx = await fixture(t);
  await mkdir(fx.root, { recursive: true });
  const first = await ensureUserApps({ root: fx.root });
  assert.equal(first.dir, path.join(fx.root, 'my-apps'));
  assert.equal(first.created, true);

  // No repository of its own: the workspace root stays the enclosing root
  // that every agent resolves AGENTS.md against, and no map is duplicated here.
  for (const name of ['.git', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md']) {
    assert.equal(await lstat(path.join(first.dir, name)).then(() => true, () => false), false, name);
  }
});

test('ensureUserApps is idempotent and never disturbs existing apps', async t => {
  const fx = await fixture(t);
  await mkdir(fx.root, { recursive: true });
  await ensureUserApps({ root: fx.root });
  const dir = path.join(fx.root, 'my-apps');
  await mkdir(path.join(dir, 'my-app'), { recursive: true });
  await writeFile(path.join(dir, 'my-app', 'keep.txt'), 'mine\n');

  const second = await ensureUserApps({ root: fx.root });
  assert.equal(second.created, false);
  assert.equal(await readFile(path.join(dir, 'my-app', 'keep.txt'), 'utf8'), 'mine\n');
});

test('scaffolding copies out of the reference checkout and leaves it untouched', async t => {
  const fx = await fixture(t);
  const workspace = await resolveWorkspace(fx.options);
  await seedReferenceApp(workspace.apps, 'robot-navigation');
  await fx.git(workspace.apps, 'add', '.');
  await fx.git(workspace.apps, 'commit', '-m', 'reference app');

  const { dir: userApps } = await ensureUserApps({ root: fx.root });
  const rc = scaffoldApp({
    srcDir: workspace.apps, dstDir: userApps,
    id: 'my-rover', from: 'robot-navigation', log: () => {},
  });
  assert.equal(rc, 0);

  const yaml = await readFile(path.join(userApps, 'my-rover', 'robium-app.yaml'), 'utf8');
  assert.match(yaml, /^id: my-rover$/m);
  assert.match(yaml, /^version: 0\.1\.0$/m);
  assert.match(yaml, /^status: experimental$/m);

  // The upstream checkout keeps neither the new app nor a dirty worktree, so
  // `update` will still apply there.
  assert.equal(await lstat(path.join(workspace.apps, 'my-rover')).then(() => true, () => false), false);
  assert.equal(await fx.git(workspace.apps, 'status', '--porcelain'), '');
});

test('scaffolding into a single apps repo still works for maintainers', async t => {
  const fx = await fixture(t);
  const appsDir = path.join(fx.base, 'solo-apps');
  await seedReferenceApp(appsDir, 'base-app');
  const rc = scaffoldApp({ appsDir, id: 'derived', from: 'base-app', log: () => {} });
  assert.equal(rc, 0);
  assert.match(await readFile(path.join(appsDir, 'derived', 'robium-app.yaml'), 'utf8'), /^id: derived$/m);
});
