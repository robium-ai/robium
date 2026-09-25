import { homedir } from 'node:os';
import path from 'node:path';
import { lstat, readdir } from 'node:fs/promises';
import { run } from './exec.js';
import { detectAgentSupport } from './agentCommands.js';
import { uninstallClaude, uninstallCodex, uninstallGemini } from './install.js';
import { AGENTS, LABEL } from './setup.js';
import { isManagedSkill } from './managedSkills.js';
export { removeManagedSkills } from './removeManagedSkills.js';
import { removeManagedSkills } from './removeManagedSkills.js';
import { cursorPluginPath, isManagedCursorPlugin, removeCursorPlugin } from './cursorPlugin.js';
import { inspectGeminiExtensionLink, removeGeminiExtensionLink } from './geminiExtension.js';
import { removeWorkspaceConfig, workspaceConfigDir } from './workspace.js';

async function exists(target) {
  try { await lstat(target); return true; } catch { return false; }
}

async function hasManagedSkills(targetDir) {
  if (!(await exists(targetDir))) return false;
  try {
    for (const entry of await readdir(targetDir)) {
      if (await isManagedSkill(path.join(targetDir, entry))) return true;
    }
  } catch {}
  return false;
}

function mergeResult(total, result) {
  total.removed.push(...result.removed);
  total.skipped.push(...result.skipped);
  total.errors.push(...result.errors);
}

export async function remove({
  agent,
  exec = run,
  log = console.log,
  error = console.error,
  home = homedir(),
  platform = process.platform,
  all = false,
} = {}) {
  if (all && agent) {
    error('--all cannot be combined with --agent; it removes every detected integration.');
    return 1;
  }
  if (agent && !AGENTS.includes(agent)) {
    error(`Unknown agent "${agent}". Supported: ${AGENTS.join(', ')}.`);
    return 1;
  }

  const support = await detectAgentSupport({ exec, home, platform });
  let targets;
  if (agent) {
    targets = [agent];
  } else {
    targets = [...support.agents];
    for (const candidate of ['gemini', 'cursor']) {
      const targetDir = path.join(home, `.${candidate}`, 'skills');
      if (!targets.includes(candidate) && await hasManagedSkills(targetDir)) {
        targets.push(candidate);
      }
    }
    if (!targets.includes('cursor') && await isManagedCursorPlugin(cursorPluginPath(home))) {
      targets.push('cursor');
    }
    if (!targets.includes('gemini') && (await inspectGeminiExtensionLink({ home })).state === 'linked') {
      targets.push('gemini');
    }
  }

  if (!targets.length && !all) {
    log('Nothing to remove: no supported agent or managed Robium skills found.');
    return 0;
  }

  const total = { removed: [], skipped: [], errors: [] };
  for (const target of targets) {
    let result;
    if (target === 'claude') {
      result = await uninstallClaude({ exec, command: support.claude?.command ?? 'claude' });
    } else if (target === 'codex') {
      result = await uninstallCodex({ exec, command: support.codex?.command ?? 'codex' });
    } else if (target === 'gemini') {
      result = support.gemini
        ? await uninstallGemini({ exec, home })
        : { removed: [], skipped: ['Gemini extension (host not installed)'], errors: [] };
      if (!support.gemini) {
        const stale = await removeGeminiExtensionLink({ home });
        if (stale.removed) result.removed.push(`stale Gemini extension link ${stale.target}`);
      }
      const legacy = await removeManagedSkills({
        targetDir: path.join(home, '.gemini', 'skills'),
      });
      mergeResult(result, legacy);
    } else {
      result = await removeCursorPlugin({ home });
      const legacy = await removeManagedSkills({
        targetDir: path.join(home, '.cursor', 'skills'),
      });
      mergeResult(result, legacy);
    }
    mergeResult(total, result);
    const removed = result.removed.length
      ? `removed ${result.removed.length}`
      : 'nothing installed';
    const skipped = result.skipped.length ? `; skipped ${result.skipped.length}` : '';
    log(`${result.errors.length ? '!' : '✓'} ${LABEL[target]}: ${removed}${skipped}`);
  }

  for (const item of total.removed) log(`  removed: ${item}`);
  for (const item of total.skipped) log(`  skipped: ${item}`);
  for (const item of total.errors) error(`✗ ${item}`);

  let configRemoved = false;
  if (all && !total.errors.length) {
    configRemoved = await removeWorkspaceConfig(home);
    log(configRemoved
      ? `✓ Removed Robium configuration: ${workspaceConfigDir(home)}`
      : `✓ Robium configuration already absent: ${workspaceConfigDir(home)}`);
  }

  if (!total.removed.length && !total.errors.length) {
    log('Nothing managed by Robium was installed for the selected agent(s).');
  } else if (!total.errors.length) {
    log(`Done. Removed ${total.removed.length} managed artifact(s). The Robium checkout was preserved.`);
  }
  if (!all && !total.errors.length) {
    log('Robium configuration was preserved. Use `npx robium-ai remove --all` to remove it without deleting the checkout.');
  } else if (configRemoved) {
    log('The Robium checkout was preserved.');
  }
  return total.errors.length ? 1 : 0;
}
