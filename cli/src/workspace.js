import path from 'node:path';
import { homedir } from 'node:os';
import { readFileSync, existsSync } from 'node:fs';
import { mkdir, writeFile, rename } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';

export const REPOSITORIES = [
  { name: 'robium', url: 'https://github.com/robium-ai/robium' },
  { name: 'robium-apps', url: 'https://github.com/robium-ai/robium-apps' },
];

// The workspace root itself. It carries the cross-agent map (AGENTS.md plus
// its CLAUDE.md import and GEMINI.md symlink) and ignores the checkouts
// cloned into it. Not a submodule host: every child keeps its own remote,
// branches, and history so `update` can leave user work untouched.
export const WORKSPACE_REPO = {
  name: 'robium-workspace',
  url: 'https://github.com/robium-ai/robium-workspace',
};

// Where a user's own applications live. Kept out of robium-apps/ so that
// checkout stays clean and `update` never refuses it for local changes.
export const USER_APPS_DIR = 'my-apps';

export function workspaceConfigPath(home = homedir()) {
  return path.join(home, '.config', 'robium', 'workspace.json');
}

export function readWorkspaceConfig(home = homedir()) {
  try {
    const value = JSON.parse(readFileSync(workspaceConfigPath(home), 'utf8'));
    if (typeof value.root !== 'string' || !path.isAbsolute(value.root)) throw new Error('invalid root');
    return value;
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw new Error(`Cannot read ${workspaceConfigPath(home)}: ${error.message}`);
  }
}

export async function saveWorkspaceConfig(config, home = homedir()) {
  const file = workspaceConfigPath(home);
  await mkdir(path.dirname(file), { recursive: true });
  const temp = `${file}.${randomUUID()}.tmp`;
  await writeFile(temp, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
  await rename(temp, file);
}

export function expandPath(dir, { home = homedir(), cwd = process.cwd() } = {}) {
  if (dir === '~' || dir.startsWith('~/')) dir = path.join(home, dir.slice(2));
  return path.resolve(cwd, dir);
}

export function workspacePaths(root) {
  return {
    root,
    repo: path.join(root, 'robium'),
    apps: path.join(root, 'robium-apps'),
    userApps: path.join(root, USER_APPS_DIR),
  };
}

// Explicit choice wins; then the current workspace, then the saved default.
export function findWorkspace({ dir, cwd = process.cwd(), home = homedir() } = {}) {
  if (dir) return workspacePaths(expandPath(dir, { home, cwd }));
  let candidate = path.resolve(cwd);
  while (true) {
    if (existsSync(path.join(candidate, 'robium', '.git')) &&
        existsSync(path.join(candidate, 'robium-apps', '.git'))) return workspacePaths(candidate);
    const parent = path.dirname(candidate);
    if (parent === candidate) break;
    candidate = parent;
  }
  const config = readWorkspaceConfig(home);
  return config ? workspacePaths(config.root) : null;
}
