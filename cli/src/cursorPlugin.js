import path from 'node:path';
import {
  cp, lstat, mkdir, readFile, realpath, rm, symlink, writeFile,
} from 'node:fs/promises';
import { isRobiumRepo } from './repo.js';

export const CURSOR_PLUGIN_MARKER = '.robium-managed';

function isOlderVersion(installed, expected) {
  const left = String(installed ?? '').match(/^(\d+)\.(\d+)\.(\d+)$/)?.slice(1).map(Number);
  const right = String(expected ?? '').match(/^(\d+)\.(\d+)\.(\d+)$/)?.slice(1).map(Number);
  if (!left || !right) return false;
  for (let index = 0; index < 3; index++) {
    if (left[index] !== right[index]) return left[index] < right[index];
  }
  return false;
}

export function cursorPluginPath(home) {
  return path.join(home, '.cursor', 'plugins', 'local', 'robium');
}

async function readManifest(root) {
  try {
    return JSON.parse(await readFile(path.join(root, '.cursor-plugin', 'plugin.json'), 'utf8'));
  } catch {
    return null;
  }
}

export async function isManagedCursorPlugin(target) {
  let info;
  try { info = await lstat(target); } catch { return false; }
  if (info.isSymbolicLink()) {
    try { return isRobiumRepo(await realpath(target)); } catch { return true; }
  }
  if (!info.isDirectory()) return false;
  try {
    const marker = await readFile(path.join(target, CURSOR_PLUGIN_MARKER), 'utf8');
    const manifest = await readManifest(target);
    return marker.startsWith('robium-ai ') && manifest?.name === 'robium';
  } catch {
    return false;
  }
}

async function copyPlugin(repo, target, version) {
  const components = [
    '.cursor-plugin',
    'skills',
    'agents',
    'hooks',
    path.join('scripts', 'engine'),
    path.join('assets', 'brand'),
  ];
  await mkdir(target, { recursive: true });
  for (const component of components) {
    const source = path.join(repo, component);
    const destination = path.join(target, component);
    await mkdir(path.dirname(destination), { recursive: true });
    await cp(source, destination, { recursive: true });
  }
  await writeFile(path.join(target, CURSOR_PLUGIN_MARKER), `robium-ai ${version}\n`);
}

export async function installCursorPlugin({ repo, home, copyMode = false, platform = process.platform, version = '' }) {
  const target = cursorPluginPath(home);
  let existing = false;
  try { await lstat(target); existing = true; } catch {}
  if (existing && !(await isManagedCursorPlugin(target))) {
    throw new Error(`${target} already exists and is not managed by Robium`);
  }

  if (existing) await rm(target, { recursive: true, force: true });
  await mkdir(path.dirname(target), { recursive: true });
  if (copyMode) {
    await copyPlugin(repo, target, version);
  } else {
    await symlink(repo, target, platform === 'win32' ? 'junction' : 'dir');
  }
  return { target, mode: copyMode ? 'copied' : 'linked' };
}

export async function inspectCursorPlugin({ home, expectedVersion } = {}) {
  const target = cursorPluginPath(home);
  const manifest = await readManifest(target);
  if (!manifest || manifest.name !== 'robium') {
    return { state: 'missing', outdated: false, apiAvailable: false };
  }
  const installedVersion = manifest.version ?? null;
  return {
    state: 'unknown',
    outdated: isOlderVersion(installedVersion, expectedVersion),
    installedVersion,
    expectedVersion,
    apiAvailable: false,
    source: 'plugin',
  };
}

export async function removeCursorPlugin({ home } = {}) {
  const target = cursorPluginPath(home);
  let exists = false;
  try { await lstat(target); exists = true; } catch {}
  if (!exists) return { removed: [], skipped: ['Cursor plugin robium (not installed)'], errors: [] };
  if (!(await isManagedCursorPlugin(target))) {
    return { removed: [], skipped: [`${target} (not managed by Robium)`], errors: [] };
  }
  try {
    await rm(target, { recursive: true, force: true });
    return { removed: ['Cursor plugin robium'], skipped: [], errors: [] };
  } catch (error) {
    return { removed: [], skipped: [], errors: [`Cursor plugin robium: ${error.message}`] };
  }
}
