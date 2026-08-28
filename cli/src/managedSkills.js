import path from 'node:path';
import {
  lstat, readFile, readdir, realpath, stat,
} from 'node:fs/promises';

export const MANAGED_MARKER = '.robium-managed';

async function isFile(target) {
  try { return (await stat(target)).isFile(); } catch { return false; }
}

async function isRobiumSkillTarget(resolved) {
  return (await isFile(path.join(resolved, 'SKILL.md')))
    && ((await isFile(path.join(resolved, '..', '..', '.codex-plugin', 'plugin.json')))
      || (await isFile(path.join(resolved, '..', '..', '.claude-plugin', 'plugin.json'))));
}

export async function inspectManagedSkill(dest) {
  let entry;
  try { entry = await lstat(dest); } catch { return null; }
  if (entry.isSymbolicLink()) {
    try {
      const resolved = await realpath(dest);
      if (!(await isRobiumSkillTarget(resolved))) return null;
      const text = await readFile(path.join(resolved, 'SKILL.md'), 'utf8');
      return { path: dest, resolved, kind: 'link', ...skillIdentity(text) };
    } catch {
      return null;
    }
  }
  if (!entry.isDirectory() || !(await isFile(path.join(dest, MANAGED_MARKER)))) {
    return null;
  }
  let text = '';
  try { text = await readFile(path.join(dest, 'SKILL.md'), 'utf8'); } catch {}
  return {
    path: dest,
    resolved: dest,
    kind: 'copy',
    ...skillIdentity(text),
  };
}

function skillIdentity(text) {
  return {
    name: text.match(/^name:\s*([^\s]+)\s*$/m)?.[1] ?? null,
    version: text.match(/^version:\s*(\d+\.\d+\.\d+)\s*$/m)?.[1] ?? null,
  };
}

export async function isManagedSkill(dest) {
  return !!(await inspectManagedSkill(dest));
}

export async function listManagedSkills(root) {
  let entries;
  try { entries = await readdir(root, { withFileTypes: true }); } catch { return []; }
  const managed = [];
  for (const entry of entries) {
    if (!entry.isDirectory() && !entry.isSymbolicLink()) continue;
    const item = await inspectManagedSkill(path.join(root, entry.name));
    if (item && await isFile(path.join(item.path, 'SKILL.md'))) managed.push(item);
  }
  return managed;
}

export async function readSkillVersions(root) {
  let entries;
  try { entries = await readdir(root, { withFileTypes: true }); } catch { return {}; }
  const versions = {};
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    try {
      const identity = skillIdentity(await readFile(path.join(root, entry.name, 'SKILL.md'), 'utf8'));
      if (identity.name && identity.version) versions[identity.name] = identity.version;
    } catch {}
  }
  return versions;
}
