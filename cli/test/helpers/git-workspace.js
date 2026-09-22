import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import { run } from '../../src/exec.js';
import { REPOSITORIES, WORKSPACE_REPO } from '../../src/workspace.js';

export async function fixture(t) {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-workspace-test-'));
  t.after(() => rm(base, { recursive: true, force: true }));
  const home = path.join(base, 'home');
  const root = path.join(base, 'my robotics');
  await mkdir(home);
  const upstreams = {};
  const git = async (cwd, ...args) => {
    const result = await run('git', ['-C', cwd, ...args]);
    assert.ok(result.ok, `${args.join(' ')}: ${result.stderr}`);
    return result.stdout.trim();
  };
  for (const spec of [...REPOSITORIES, WORKSPACE_REPO]) {
    const source = path.join(base, `source-${spec.name}`);
    await mkdir(source);
    await git(source, 'init', '-b', 'main');
    await git(source, 'config', 'user.name', 'Test');
    await git(source, 'config', 'user.email', 'test@example.invalid');
    await writeFile(path.join(source, 'sample.txt'), 'baseline\n');
    await git(source, 'add', '.');
    await git(source, 'commit', '-m', 'baseline');
    upstreams[spec.url] = source;
  }
  const calls = [];
  const exec = async (cmd, args, options) => {
    calls.push([cmd, ...args]);
    // Keep the product's official remote validation; redirect transport only.
    const mapped = args.map(arg => upstreams[arg] ?? arg);
    const result = await run(cmd, mapped, options);
    if (cmd === 'git' && args[0] === 'clone' && result.ok) {
      const dest = args.at(-1);
      await git(dest, 'remote', 'set-url', 'origin', args.at(-2));
      await git(dest, 'config', 'user.name', 'Test');
      await git(dest, 'config', 'user.email', 'test@example.invalid');
    }
    return result;
  };
  const advance = async (name = 'robium') => {
    const source = upstreams[REPOSITORIES.find(r => r.name === name).url];
    await writeFile(path.join(source, 'sample.txt'), `next-${Date.now()}-${Math.random()}\n`);
    await git(source, 'add', '.');
    await git(source, 'commit', '-m', 'next');
    return git(source, 'rev-parse', 'HEAD');
  };
  const options = { dir: root, home, cwd: base, exec, yes: true, log: () => {}, error: () => {} };
  return { base, home, root, git, exec, calls, advance, options };
}
