import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { writeFile, readFile } from 'node:fs/promises';
import { resolveWorkspace } from '../src/repo.js';
import { updateWorkspace } from '../src/updates.js';
import { readWorkspaceConfig } from '../src/workspace.js';
import { fixture } from './helpers/git-workspace.js';

async function prepared(t) {
  const fx = await fixture(t);
  const workspace = await resolveWorkspace(fx.options);
  const output = [];
  return { ...fx, ...workspace, output, options: { ...fx.options, log: s => output.push(s) } };
}

test('check fetches official main without changing HEAD; explicit update fast-forwards both', async t => {
  const fx = await prepared(t);
  const old = await fx.git(fx.repo, 'rev-parse', 'HEAD');
  const next = await fx.advance();
  await fx.advance('robium-apps');
  assert.equal(await updateWorkspace({ ...fx.options, check: true, json: true }), 0);
  const report = JSON.parse(fx.output.at(-1));
  assert.equal(report.results[0].status, 'available');
  assert.equal(report.results[0].upstream, next);
  assert.equal(await fx.git(fx.repo, 'rev-parse', 'HEAD'), old);
  assert.equal(await updateWorkspace(fx.options), 0);
  assert.equal(await fx.git(fx.repo, 'rev-parse', 'HEAD'), next);
  assert.equal(await fx.git(fx.repo, 'status', '--porcelain'), '');
});

for (const mode of ['branch', 'dirty', 'diverged', 'detached']) {
  test(`update preserves ${mode} checkout and still reports the other repository`, async t => {
    const fx = await prepared(t);
    if (mode === 'branch') await fx.git(fx.repo, 'switch', '-c', 'my-work');
    if (mode === 'detached') await fx.git(fx.repo, 'checkout', '--detach');
    if (mode === 'dirty' || mode === 'diverged') await writeFile(path.join(fx.repo, 'sample.txt'), 'my work\n');
    if (mode === 'diverged') { await fx.git(fx.repo, 'add', '.'); await fx.git(fx.repo, 'commit', '-m', 'personal'); }
    const before = await fx.git(fx.repo, 'rev-parse', 'HEAD');
    const content = await readFile(path.join(fx.repo, 'sample.txt'), 'utf8');
    await fx.advance();
    await fx.advance('robium-apps');
    assert.equal(await updateWorkspace(fx.options), 1);
    assert.equal(await fx.git(fx.repo, 'rev-parse', 'HEAD'), before);
    assert.equal(await readFile(path.join(fx.repo, 'sample.txt'), 'utf8'), content);
    assert.match(fx.output.join('\n'), /robium: skipped/);
    assert.match(fx.output.join('\n'), /robium-apps: updated/);
  });
}

test('fork origin does not replace canonical main as the update source', async t => {
  const fx = await prepared(t);
  await fx.git(fx.repo, 'remote', 'rename', 'origin', 'upstream');
  await fx.git(fx.repo, 'remote', 'add', 'origin', 'https://github.com/example/my-fork');
  const next = await fx.advance();
  assert.equal(await updateWorkspace(fx.options), 0);
  assert.equal(await fx.git(fx.repo, 'rev-parse', 'HEAD'), next);
  assert.equal(await fx.git(fx.repo, 'remote', 'get-url', 'origin'), 'https://github.com/example/my-fork');
});

test('quiet checks are daily; notices weekly and only for new upstream revisions', async t => {
  const fx = await prepared(t);
  const day = 86400000;
  const start = 100 * day;
  await fx.advance();
  const check = now => updateWorkspace({ ...fx.options, check: true, quiet: true, now });
  await check(start);
  assert.equal(fx.output.length, 1);
  fx.calls.length = 0;
  await check(start + 1000);
  assert.equal(fx.calls.length, 0);
  await check(start + 8 * day);
  assert.equal(fx.output.length, 1); // same revision never nags again
  await fx.advance();
  await check(start + 9 * day);
  assert.equal(fx.output.length, 2);
  await fx.advance();
  await check(start + 10 * day);
  assert.equal(fx.output.length, 2); // new revision, but weekly cap
  await check(start + 17 * day);
  assert.equal(fx.output.length, 3);
  fx.calls.length = 0;
  await updateWorkspace({ ...fx.options, check: true, quiet: true, env: { ROBIUM_UPDATE_CHECKS: '0' }, now: start + 30 * day });
  assert.equal(fx.calls.length, 0);
  await updateWorkspace({ ...fx.options, check: true, json: true, now: start + 17 * day + 1 });
  assert.ok(fx.calls.length > 0); // explicit check bypasses quiet throttle
});

test('offline is unknown, not current; opportunistic errors are silent and throttled', async t => {
  const fx = await prepared(t);
  const exec = async (cmd, args, opts) => args.includes('fetch') ? { ok: false } : fx.exec(cmd, args, opts);
  assert.equal(await updateWorkspace({ ...fx.options, exec, check: true, quiet: true }), 0);
  assert.equal(fx.output.length, 0);
  assert.equal(readWorkspaceConfig(fx.home).checks[fx.root].results[0].status, 'unknown');
  assert.equal(await updateWorkspace({ ...fx.options, exec, check: true }), 1);
  assert.match(fx.output.join('\n'), /unknown/);
});

test('a paused Git operation prevents automatic updates even with a clean worktree', async t => {
  const fx = await prepared(t);
  const before = await fx.git(fx.repo, 'rev-parse', 'HEAD');
  await writeFile(path.join(fx.repo, '.git', 'CHERRY_PICK_HEAD'), `${before}\n`);
  await fx.advance();
  assert.equal(await updateWorkspace(fx.options), 1);
  assert.equal(await fx.git(fx.repo, 'rev-parse', 'HEAD'), before);
  assert.match(fx.output.join('\n'), /operation in progress/);
});

test('partial network failures do not make an already announced revision new again', async t => {
  const fx = await prepared(t);
  await fx.advance();
  await fx.advance('robium-apps');
  const day = 86400000;
  await updateWorkspace({ ...fx.options, check: true, quiet: true, now: 100 * day });
  const exec = async (cmd, args, opts) => args.includes('fetch') && args[1] === fx.apps
    ? { ok: false } : fx.exec(cmd, args, opts);
  await updateWorkspace({ ...fx.options, exec, check: true, quiet: true, now: 108 * day });
  await updateWorkspace({ ...fx.options, check: true, quiet: true, now: 116 * day });
  assert.equal(fx.output.length, 1);
});
