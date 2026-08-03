import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdtemp, mkdir, writeFile, readFile, readdir, readlink, rm, lstat, symlink } from 'node:fs/promises';
import { setup, detectAgents, linkSkills } from '../src/setup.js';

// exec mock: agents listed in `present` answer --version; everything else fails.
function agentExec(present) {
  const calls = [];
  const exec = async (cmd, args) => {
    const key = [cmd, ...args].join(' ');
    calls.push(key);
    if (args[0] === '--version' && present.includes(cmd)) {
      return { ok: true, code: 0, stdout: '1.0.0\n', stderr: '' };
    }
    if (present.includes('claude') && cmd === 'claude' && args[0] === 'plugin') {
      if (args[1] === 'list') {
        return { ok: true, code: 0, stdout: '[{"id":"robium@robium","enabled":true}]', stderr: '' };
      }
      return { ok: true, code: 0, stdout: '', stderr: '' };
    }
    return { ok: false, code: 1, stdout: '', stderr: 'not found' };
  };
  return { exec, calls };
}

// Fixture: a fake robium checkout (repo detection needs .claude-plugin +
// skills/), two skills, a _TEMPLATE that must never install.
async function makeFixtures() {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-setup-'));
  const home = path.join(base, 'home');
  const repo = path.join(base, 'robium');
  await mkdir(home, { recursive: true });
  await mkdir(path.join(repo, '.claude-plugin'), { recursive: true });
  await writeFile(path.join(repo, '.claude-plugin', 'plugin.json'), '{}');
  for (const name of ['ros2', 'gazebo']) {
    await mkdir(path.join(repo, 'skills', name, 'references'), { recursive: true });
    await writeFile(path.join(repo, 'skills', name, 'SKILL.md'), `---\nname: ${name}\nversion: 1.0.0\ndescription: test\n---\nbody\n`);
    await writeFile(path.join(repo, 'skills', name, 'references', 'notes.md'), 'ref\n');
  }
  await mkdir(path.join(repo, 'skills', '_TEMPLATE'), { recursive: true });
  await writeFile(path.join(repo, 'skills', '_TEMPLATE', 'SKILL.template.md'), 'skeleton\n');
  return { base, home, repo, src: path.join(repo, 'skills') };
}

async function exists(p) {
  try { await lstat(p); return true; } catch { return false; }
}

// Run setup with cwd inside the fixture checkout → repo resolution needs no git.
function opts(fx, extra = {}) {
  return { home: fx.home, cwd: fx.repo, log: () => {}, error: () => {}, ...extra };
}

test('detectAgents: finds binaries on PATH, cursor via ~/.cursor dir', async () => {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-det-'));
  const homeDir = path.join(base, 'home');
  await mkdir(path.join(homeDir, '.cursor'), { recursive: true });
  const { exec } = agentExec(['codex', 'gemini']);
  const found = await detectAgents({ exec, home: homeDir });
  assert.deepEqual(found, ['codex', 'gemini', 'cursor']);
  await rm(base, { recursive: true, force: true });
});

test('setup: codex+gemini → symlinks into the checkout, no claude calls, exit 0', async () => {
  const fx = await makeFixtures();
  const { exec, calls } = agentExec(['codex', 'gemini']);
  let out = '';
  const code = await setup(opts(fx, { exec, log: (s) => { out += `${s}\n`; } }));
  assert.equal(code, 0);
  const target = path.join(fx.home, '.agents', 'skills');
  const st = await lstat(path.join(target, 'ros2'));
  assert.ok(st.isSymbolicLink());
  assert.equal(await readlink(path.join(target, 'ros2')), path.join(fx.src, 'ros2'));
  assert.ok(await exists(path.join(target, 'gazebo', 'references', 'notes.md')));
  assert.ok(!(await exists(path.join(target, '_TEMPLATE'))));
  assert.ok(!calls.some((c) => c.startsWith('claude plugin')));
  assert.match(out, /2 linked/);
  assert.match(out, /Codex, Gemini CLI/);
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: claude-only → plugin flow with the checkout as marketplace ref', async () => {
  const fx = await makeFixtures();
  const { exec, calls } = agentExec(['claude']);
  const code = await setup(opts(fx, { exec }));
  assert.equal(code, 0);
  assert.ok(calls.includes(`claude plugin marketplace add ${fx.repo}`));
  assert.ok(calls.includes('claude plugin install robium@robium --scope user'));
  assert.ok(!(await exists(path.join(fx.home, '.agents'))));
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: foreign real dir with same name is skipped, not clobbered', async () => {
  const fx = await makeFixtures();
  const foreign = path.join(fx.home, '.agents', 'skills', 'ros2');
  await mkdir(foreign, { recursive: true });
  await writeFile(path.join(foreign, 'SKILL.md'), 'someone elses ros2 skill\n');
  const { exec } = agentExec(['codex']);
  let out = '';
  const code = await setup(opts(fx, { exec, log: (s) => { out += `${s}\n`; } }));
  assert.equal(code, 0);
  assert.equal(await readFile(path.join(foreign, 'SKILL.md'), 'utf8'), 'someone elses ros2 skill\n');
  assert.match(out, /Skipped 1 name collision/);
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: v0.3 marker copy upgrades to symlink', async () => {
  const fx = await makeFixtures();
  const old = path.join(fx.home, '.agents', 'skills', 'ros2');
  await mkdir(old, { recursive: true });
  await writeFile(path.join(old, 'SKILL.md'), 'old copied version\n');
  await writeFile(path.join(old, '.robium-managed'), 'robium-ai 0.3.0\n');
  const { exec } = agentExec(['codex']);
  const code = await setup(opts(fx, { exec }));
  assert.equal(code, 0);
  assert.ok((await lstat(old)).isSymbolicLink());
  await rm(fx.base, { recursive: true, force: true });
});

test('linkSkills: robium symlink replaced; foreign symlink skipped; broken replaced', async () => {
  const fx = await makeFixtures();
  const target = path.join(fx.home, '.agents', 'skills');
  await mkdir(target, { recursive: true });
  // ours: points into the checkout already
  await symlink(path.join(fx.src, 'ros2'), path.join(target, 'ros2'), 'dir');
  // foreign: a valid skill dir NOT inside a robium checkout
  const foreignSkill = path.join(fx.base, 'other-pack', 'gazebo');
  await mkdir(foreignSkill, { recursive: true });
  await writeFile(path.join(foreignSkill, 'SKILL.md'), 'foreign gazebo\n');
  await symlink(foreignSkill, path.join(target, 'gazebo'), 'dir');
  const r1 = await linkSkills({ src: fx.src, targetDir: target });
  assert.equal(r1.linked, 1); // ros2 refreshed
  assert.deepEqual(r1.skipped, ['gazebo']);
  assert.equal(await readlink(path.join(target, 'gazebo')), foreignSkill);
  // broken symlink → replaced
  await rm(path.join(target, 'gazebo'));
  await symlink(path.join(fx.base, 'gone'), path.join(target, 'gazebo'), 'dir');
  const r2 = await linkSkills({ src: fx.src, targetDir: target });
  assert.equal(await readlink(path.join(target, 'gazebo')), path.join(fx.src, 'gazebo'));
  assert.equal(r2.skipped.length, 0);
  await rm(fx.base, { recursive: true, force: true });
});

test('setup --copy: real dirs with marker, sourced from the checkout', async () => {
  const fx = await makeFixtures();
  const { exec } = agentExec(['codex']);
  const code = await setup(opts(fx, { exec, copy: true }));
  assert.equal(code, 0);
  const dest = path.join(fx.home, '.agents', 'skills', 'ros2');
  assert.ok(!(await lstat(dest)).isSymbolicLink());
  assert.match(await readFile(path.join(dest, '.robium-managed'), 'utf8'), /robium-ai/);
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: re-run is idempotent', async () => {
  const fx = await makeFixtures();
  const { exec } = agentExec(['codex']);
  assert.equal(await setup(opts(fx, { exec })), 0);
  assert.equal(await setup(opts(fx, { exec })), 0);
  const names = (await readdir(path.join(fx.home, '.agents', 'skills'))).sort();
  assert.deepEqual(names, ['gazebo', 'ros2']);
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: explicit agent not detected → installs anyway with a note', async () => {
  const fx = await makeFixtures();
  const { exec } = agentExec([]);
  let out = '';
  const code = await setup(opts(fx, { exec, agent: 'codex', log: (s) => { out += `${s}\n`; } }));
  assert.equal(code, 0);
  assert.match(out, /not detected/);
  assert.ok(await exists(path.join(fx.home, '.agents', 'skills', 'ros2')));
  await rm(fx.base, { recursive: true, force: true });
});

test('setup: unknown agent → exit 1', async () => {
  const { exec } = agentExec([]);
  let err = '';
  const code = await setup({ agent: 'emacs', exec, home: os.tmpdir(), cwd: os.tmpdir(), error: (s) => { err += s; }, log: () => {} });
  assert.equal(code, 1);
  assert.match(err, /Unknown agent/);
});

test('setup: OpenCode is not advertised as a supported target', async () => {
  const { exec } = agentExec(['opencode']);
  let err = '';
  const code = await setup({ agent: 'opencode', exec, home: os.tmpdir(), cwd: os.tmpdir(), error: (s) => { err += s; }, log: () => {} });
  assert.equal(code, 1);
  assert.match(err, /Unknown agent/);
});

test('setup: no agents found → exit 1 with guidance', async () => {
  const fx = await makeFixtures();
  const { exec } = agentExec([]);
  let err = '';
  const code = await setup(opts(fx, { exec, error: (s) => { err += s; } }));
  assert.equal(code, 1);
  assert.match(err, /No supported coding agent/);
  await rm(fx.base, { recursive: true, force: true });
});
