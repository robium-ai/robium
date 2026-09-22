import path from 'node:path';
import { lstat, mkdir } from 'node:fs/promises';
import { USER_APPS_DIR } from './workspace.js';

// The user's own application library, beside the reference checkout rather
// than inside it: editing robium-apps/ leaves it dirty and `update` then
// refuses it.
//
// Deliberately a plain directory. It inherits the workspace AGENTS.md from
// the parent, so it needs no map of its own, and staying out of git keeps the
// workspace repository the enclosing root every agent resolves guidance
// against. Run `git init` here yourself if you want your apps versioned.
export async function ensureUserApps({ root, log = () => {} } = {}) {
  const dir = path.join(root, USER_APPS_DIR);
  const created = !(await lstat(dir).then(() => true, () => false));
  await mkdir(dir, { recursive: true });
  if (created) log(`✓ Created your app library: ${dir}`);
  return { dir, created };
}
