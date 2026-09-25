import { homedir } from 'node:os';
import path from 'node:path';
import { lstat, readFile, readlink, rm } from 'node:fs/promises';

const INSTALL_METADATA = '.gemini-extension-install.json';

export function geminiExtensionPath(home = homedir()) {
  return path.join(home, '.gemini', 'extensions', 'robium');
}

function resolveMetadataSource(source, home) {
  if (typeof source !== 'string' || !source) return null;
  if (path.isAbsolute(source)) return path.normalize(source);
  if (source === '~') return home;
  if (source.startsWith('~/') || source.startsWith('~\\')) {
    return path.resolve(home, source.slice(2));
  }
  return null;
}

// Gemini 0.40.x represents `extensions link` as a real directory containing
// `.gemini-extension-install.json`; older versions and some platforms may use
// a filesystem symlink. Recognize only those two explicit link shapes. Every
// other real directory at the reserved destination remains untouched.
export async function inspectGeminiExtensionLink({ home = homedir() } = {}) {
  const target = geminiExtensionPath(home);
  let info;
  try { info = await lstat(target); } catch (error) {
    if (error.code === 'ENOENT') return { target, state: 'missing' };
    throw error;
  }
  if (info.isSymbolicLink()) {
    const source = await readlink(target);
    return {
      target,
      state: 'linked',
      storage: 'symlink',
      source: path.resolve(path.dirname(target), source),
    };
  }
  if (info.isDirectory()) {
    try {
      const metadata = JSON.parse(await readFile(path.join(target, INSTALL_METADATA), 'utf8'));
      const source = metadata?.type === 'link'
        ? resolveMetadataSource(metadata.source, home)
        : null;
      if (source) return { target, state: 'linked', storage: 'metadata', source };
    } catch {}
  }
  return { target, state: 'conflict' };
}

export async function removeGeminiExtensionLink({ home = homedir() } = {}) {
  const link = await inspectGeminiExtensionLink({ home });
  if (link.state !== 'linked') return { ...link, removed: false };
  await rm(link.target, { recursive: link.storage === 'metadata', force: true });
  return { ...link, removed: true };
}
