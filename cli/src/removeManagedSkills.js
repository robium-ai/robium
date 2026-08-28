import path from 'node:path';
import { lstat, readdir, rm, rmdir } from 'node:fs/promises';
import { isManagedSkill } from './managedSkills.js';

async function exists(target) {
  try { await lstat(target); return true; } catch { return false; }
}

export async function removeManagedSkills({ targetDir }) {
  const result = { removed: [], skipped: [], errors: [] };
  if (!(await exists(targetDir))) return result;
  let entries;
  try {
    entries = await readdir(targetDir, { withFileTypes: true });
  } catch (error) {
    result.errors.push(`${targetDir}: ${error.message}`);
    return result;
  }
  for (const entry of entries) {
    const dest = path.join(targetDir, entry.name);
    if (!(await isManagedSkill(dest))) {
      result.skipped.push(`${dest} (not managed by Robium)`);
      continue;
    }
    try {
      await rm(dest, { recursive: true, force: true });
      result.removed.push(dest);
    } catch (error) {
      result.errors.push(`${dest}: ${error.message}`);
    }
  }
  try { await rmdir(targetDir); } catch {}
  return result;
}
