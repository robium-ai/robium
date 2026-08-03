import path from 'node:path';
import { homedir } from 'node:os';
import { stat } from 'node:fs/promises';
import { createInterface } from 'node:readline/promises';
import { run } from './exec.js';

// The clone is the ONLY source of skills: npm ships CLI code, git ships
// knowledge. Skill updates reach users via `git pull`, never via npm.
export const REPO_URL = 'https://github.com/robium-ai/robium';

async function isDir(p) {
  try { return (await stat(p)).isDirectory(); } catch { return false; }
}
async function isFile(p) {
  try { return (await stat(p)).isFile(); } catch { return false; }
}

export async function isRobiumRepo(dir) {
  return (await isFile(path.join(dir, '.claude-plugin', 'plugin.json')))
    && (await isDir(path.join(dir, 'skills')));
}

// Walk up from cwd: running setup from inside a checkout (contributors,
// clone-only users) always uses that checkout.
export async function findEnclosingRepo(startDir) {
  let d = path.resolve(startDir);
  for (;;) {
    if (await isRobiumRepo(d)) return d;
    const parent = path.dirname(d);
    if (parent === d) return null;
    d = parent;
  }
}

const NO_GIT = `✗ git not found. robium setup clones the robium repo (the source of all skills).

  Install git and re-run:  npx robium-ai setup

  Or clone manually, then run setup from inside the clone:

    git clone ${REPO_URL} ~/robium
    cd ~/robium && npx robium-ai setup`;

async function defaultAsk(question) {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    return await rl.question(question);
  } finally {
    rl.close();
  }
}

// Resolve the robium checkout to install from. Returns an absolute path or
// null (error already reported). Exactly one prompt, and only when there is
// a genuine choice: TTY, no --dir, no -y.
export async function resolveRepo({
  exec = run,
  home = homedir(),
  cwd = process.cwd(),
  dir,
  yes = false,
  interactive = Boolean(process.stdout.isTTY && process.stdin.isTTY),
  ask = defaultAsk,
  log = console.log,
  error = console.error,
} = {}) {
  const enclosing = await findEnclosingRepo(cwd);
  if (enclosing) {
    log(`✓ Using this robium checkout: ${enclosing}`);
    return enclosing;
  }

  const git = await exec('git', ['--version']);
  if (!git.ok) {
    error(NO_GIT);
    return null;
  }

  const fallback = path.join(home, 'robium');
  let target = dir;
  if (!target && !yes && interactive) {
    const answer = (await ask(`Where should the robium repo live? [${fallback}]: `)).trim();
    target = answer || fallback;
  }
  target = target || fallback;
  if (target === '~' || target.startsWith('~/')) target = path.join(home, target.slice(2));
  target = path.resolve(target);

  if (await isRobiumRepo(target)) {
    const dirty = await exec('git', ['-C', target, 'status', '--porcelain']);
    if (dirty.ok && dirty.stdout.trim()) {
      log(`! ${target} has local changes; skipped git pull (update it manually).`);
    } else {
      const pull = await exec('git', ['-C', target, 'pull', '--ff-only'], { timeout: 60_000 });
      log(pull.ok
        ? `✓ Repo up to date: ${target}`
        : `! Could not fast-forward ${target}; continuing with the current checkout.`);
    }
    return target;
  }

  if (await isDir(target)) {
    error(`✗ ${target} exists but is not a robium checkout; pick another location with --dir <path>.`);
    return null;
  }

  log(`Cloning ${REPO_URL} → ${target}`);
  const clone = await exec('git', ['clone', REPO_URL, target], { timeout: 300_000 });
  if (!clone.ok) {
    error(`✗ git clone failed:\n${(clone.stderr || clone.stdout).trim()}`);
    return null;
  }
  log('✓ Cloned');
  return target;
}
