import { homedir } from 'node:os';
import path from 'node:path';
import { lstat, readlink, rm } from 'node:fs/promises';

export function geminiExtensionPath(home = homedir()) {
  return path.join(home, '.gemini', 'extensions', 'robium');
}

// Gemini's `extensions list` ignores broken links, while `extensions link`
// refuses to replace them. Robium only removes the exact user-extension link
// bearing its reserved extension name; real directories are left untouched.
export async function inspectGeminiExtensionLink({ home = homedir() } = {}) {
  const target = geminiExtensionPath(home);
  let info;
  try { info = await lstat(target); } catch (error) {
    if (error.code === 'ENOENT') return { target, state: 'missing' };
    throw error;
  }
  if (!info.isSymbolicLink()) return { target, state: 'conflict' };
  const source = await readlink(target);
  return {
    target,
    state: 'linked',
    source: path.resolve(path.dirname(target), source),
  };
}

export async function removeGeminiExtensionLink({ home = homedir() } = {}) {
  const link = await inspectGeminiExtensionLink({ home });
  if (link.state !== 'linked') return { ...link, removed: false };
  await rm(link.target, { force: true });
  return { ...link, removed: true };
}
