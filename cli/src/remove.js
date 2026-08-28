import { homedir } from 'node:os';
import path from 'node:path';
import { lstat, readdir, rm, rmdir } from 'node:fs/promises';
import { run } from './exec.js';
import { detectAgentSupport } from './agentCommands.js';
import { uninstallClaude, uninstallCodex } from './install.js';
import { AGENTS, LABEL, isManagedSkill } from './setup.js';

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

  // setup creates the skills directory. Remove it only when it is empty;
  // never remove the host directory or a directory containing foreign skills.
  try { await rmdir(targetDir); } catch {}
  return result;
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
} = {}) {
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
  }

  if (!targets.length) {
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
    } else {
      result = await removeManagedSkills({
        targetDir: path.join(home, `.${target}`, 'skills'),
      });
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

  if (!total.removed.length && !total.errors.length) {
    log('Nothing managed by Robium was installed for the selected agent(s).');
  } else if (!total.errors.length) {
    log(`Done. Removed ${total.removed.length} managed artifact(s). The Robium checkout was preserved.`);
  }
  return total.errors.length ? 1 : 0;
}
