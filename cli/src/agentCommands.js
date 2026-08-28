import path from 'node:path';
import { stat } from 'node:fs/promises';
import { homedir } from 'node:os';
import { run } from './exec.js';

async function isDir(target) {
  try { return (await stat(target)).isDirectory(); } catch { return false; }
}

// Codex Desktop bundles the CLI but does not necessarily add it to the user's
// shell PATH. Probe the normal command first, then the stable macOS app bundle
// locations so `npx robium-ai setup` works from an ordinary terminal.
export async function resolveCodexCommand({
  exec = run,
  home = homedir(),
  platform = process.platform,
} = {}) {
  const onPath = await exec('codex', ['--version']);
  if (onPath.ok) return { command: 'codex', version: onPath, source: 'PATH' };

  const candidates = platform === 'darwin'
    ? [
        '/Applications/ChatGPT.app/Contents/Resources/codex',
        path.join(home, 'Applications', 'ChatGPT.app', 'Contents', 'Resources', 'codex'),
      ]
    : [];

  for (const command of candidates) {
    const version = await exec(command, ['--version']);
    if (version.ok) return { command, version, source: 'Codex Desktop' };
  }
  return null;
}

export async function detectAgentSupport({
  exec = run,
  home = homedir(),
  platform = process.platform,
} = {}) {
  const [claude, codex, gemini, cursorAgent, cursorBin, cursorDir] = await Promise.all([
    exec('claude', ['--version']),
    resolveCodexCommand({ exec, home, platform }),
    exec('gemini', ['--version']),
    exec('cursor-agent', ['--version']),
    exec('cursor', ['--version']),
    isDir(path.join(home, '.cursor')),
  ]);

  const agents = [];
  if (claude.ok) agents.push('claude');
  if (codex) agents.push('codex');
  if (gemini.ok) agents.push('gemini');
  if (cursorAgent.ok || cursorBin.ok || cursorDir) agents.push('cursor');

  return {
    agents,
    claude: claude.ok ? { command: 'claude', version: claude, source: 'PATH' } : null,
    codex,
    gemini: gemini.ok ? { command: 'gemini', version: gemini, source: 'PATH' } : null,
    cursor: cursorAgent.ok
      ? { command: 'cursor-agent', version: cursorAgent, source: 'PATH' }
      : cursorBin.ok
        ? { command: 'cursor', version: cursorBin, source: 'PATH' }
        : cursorDir
          ? { command: null, version: null, source: '~/.cursor' }
          : null,
  };
}
