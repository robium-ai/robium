import path from 'node:path';
import { homedir } from 'node:os';
import { lstat, readdir, realpath, stat, mkdir } from 'node:fs/promises';
import { createInterface } from 'node:readline/promises';
import { run } from './exec.js';
import { REPOSITORIES, WORKSPACE_REPO, findWorkspace, workspacePaths, expandPath, readWorkspaceConfig, saveWorkspaceConfig } from './workspace.js';

async function exists(target) {
  try { await lstat(target); return true; } catch (e) { if (e.code === 'ENOENT') return false; throw e; }
}
export async function isRobiumRepo(dir) {
  try { return (await stat(path.join(dir, 'skills'))).isDirectory() &&
    (await stat(path.join(dir, '.claude-plugin', 'plugin.json'))).isFile(); } catch { return false; }
}

async function defaultAsk(question) {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try { return await rl.question(question); } finally { rl.close(); }
}

// Forks are welcome when a canonical upstream remote is present. Never adopt
// a random directory, nested checkout, or unrelated repository as Robium.
export async function validateCheckout(repo, spec, exec = run) {
  const top = await exec('git', ['-C', repo, 'rev-parse', '--show-toplevel']);
  if (!top.ok || await realpath(repo) !== await realpath(top.stdout.trim())) {
    throw new Error(`${repo} is not a repository root; leave it untouched and choose another workspace.`);
  }
  const remotes = await exec('git', ['-C', repo, 'remote', '-v']);
  const expected = `github.com/robium-ai/${spec.name}`;
  const matches = remotes.ok && remotes.stdout.split('\n').some(line => {
    const url = line.trim().split(/\s+/)[1] ?? '';
    return url.replace(/^git@github\.com:/, 'github.com/').replace(/^https:\/\//, '').replace(/\.git\/?$/, '').replace(/\/$/, '') === expected;
  });
  if (!matches) throw new Error(`${repo} has no official Robium remote. Add the official upstream explicitly or choose another workspace.`);
}


async function isEmptyDir(dir) {
  try { return (await readdir(dir)).length === 0; } catch (e) { if (e.code === 'ENOENT') return true; throw e; }
}

// The workspace root is itself a small repository carrying the cross-agent
// map. It holds no code and no submodules: robium/ and robium-apps/ are
// ignored there and stay independent checkouts.
//
// Three cases, in order: an existing official checkout is reused untouched; an
// empty or missing root is cloned; anything else stays a plain folder, which
// is what every workspace created before this existed already is.
async function ensureWorkspaceRepo({ root, exec, log }) {
  if (await exists(path.join(root, '.git'))) {
    try {
      await validateCheckout(root, WORKSPACE_REPO, exec);
    } catch {
      throw new Error(`${root} is a repository, not a workspace parent. Choose a folder that will contain robium/ and robium-apps/.`);
    }
    log(`✓ Using workspace repository (unchanged): ${root}`);
    return 'checkout';
  }
  if (!(await isEmptyDir(root))) return 'folder';
  const clone = await exec('git', ['clone', '--branch', 'main', '--', WORKSPACE_REPO.url, root], { timeout: 300_000 });
  if (!clone.ok) {
    // Never fatal: the map is a convenience, the checkouts below are the
    // product. A plain parent folder works exactly as it did before.
    log(`! Could not clone ${WORKSPACE_REPO.name}; continuing with a plain workspace folder.`);
    return 'folder';
  }
  log(`✓ Workspace repository cloned: ${root}`);
  return 'checkout';
}

export async function resolveWorkspace({
  exec = run, home = homedir(), cwd = process.cwd(), dir, yes = false,
  interactive = Boolean(process.stdout.isTTY && process.stdin.isTTY), ask = defaultAsk,
  log = console.log, error = console.error,
} = {}) {
  try {
    const config = readWorkspaceConfig(home);
    let workspace = findWorkspace({ dir, cwd, home });
    if (!dir && workspace && config?.root === workspace.root && !(await exists(workspace.root))) {
      throw new Error(`Saved workspace ${workspace.root} is missing. If you moved it, run setup --dir <new-parent>; no replacement was cloned.`);
    }
    if (!workspace) {
      let root = path.join(home, 'robium-workspace');
      if (!yes && interactive) root = (await ask(`Where should the Robium workspace live? [${root}]: `)).trim() || root;
      workspace = workspacePaths(expandPath(root, { home, cwd }));
    }
    if (!(await exec('git', ['--version'])).ok) {
      throw new Error('git not found. Install git, then re-run npx robium-ai setup. Manual setup: git clone each official repository into <workspace>/robium and <workspace>/robium-apps.');
    }
    if (await isRobiumRepo(workspace.root)) {
      throw new Error(`${workspace.root} is a repository, not a workspace parent. Choose a folder that will contain robium/ and robium-apps/.`);
    }
    for (const spec of REPOSITORIES) {
      const target = path.join(workspace.root, spec.name);
      if (await exists(target)) await validateCheckout(target, spec, exec);
    }
    await mkdir(workspace.root, { recursive: true });
    await ensureWorkspaceRepo({ root: workspace.root, exec, log });
    for (const spec of REPOSITORIES) {
      const target = path.join(workspace.root, spec.name);
      if (await exists(target)) log(`✓ Using checkout (unchanged): ${target}`);
      else {
        log(`Cloning ${spec.url} → ${target}`);
        const clone = await exec('git', ['clone', '--branch', 'main', '--', spec.url, target], { timeout: 300_000 });
        if (!clone.ok) throw new Error(`Could not clone ${spec.name}; existing files were left in place. Check network access and ${target}, then retry setup.`);
      }
    }
    await saveWorkspaceConfig({ ...config, root: workspace.root }, home);
    log(`✓ Workspace remembered: ${workspace.root}`);
    return workspace;
  } catch (e) { error(`✗ ${e.message}`); return null; }
}
