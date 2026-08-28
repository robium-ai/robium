import { run } from './exec.js';
import { findCodexRobiumPlugin, findRobiumPlugin } from './plugins.js';

const MARKETPLACE_REF = 'robium-ai/robium';
const MARKETPLACE_NAME = 'robium';
const PLUGIN_SPEC = 'robium@robium';

const CLAUDE_MISSING = `✗ Claude Code not found on PATH.

  robium installs into Claude Code as a plugin. Install Claude Code first:

    https://claude.com/claude-code

  then re-run:  npx robium-ai setup`;

// Claude Code path: the full plugin (skills + robium-architect agent +
// capture hooks) via Claude's marketplace, served from the local clone when
// setup resolved one (marketplaceRef = clone path); `git pull` updates it.
// Gemini and Cursor are handled by setup.js through their native skill dirs.
export async function installClaude({
  exec = run,
  log = console.log,
  error = console.error,
  marketplaceRef = MARKETPLACE_REF,
} = {}) {
  const ver = await exec('claude', ['--version']);
  if (!ver.ok) {
    error(CLAUDE_MISSING);
    return 1;
  }
  log(`✓ Claude Code detected (${ver.stdout.trim()})`);

  const add = await exec('claude', ['plugin', 'marketplace', 'add', marketplaceRef]);
  if (add.ok) {
    log(`✓ Marketplace added: ${marketplaceRef}`);
  } else if (/already|exists/i.test(add.stderr + add.stdout)) {
    const upd = await exec('claude', ['plugin', 'marketplace', 'update', MARKETPLACE_NAME]);
    log(upd.ok
      ? '✓ Marketplace already present; refreshed to latest'
      : '! Marketplace already present (refresh failed; continuing)');
  } else {
    error(`✗ Could not add marketplace ${marketplaceRef}:\n${(add.stderr || add.stdout).trim()}`);
    return 1;
  }

  const inst = await exec('claude', ['plugin', 'install', PLUGIN_SPEC, '--scope', 'user']);
  if (inst.ok) {
    log(`✓ Plugin installed: ${PLUGIN_SPEC}`);
  } else if (/already/i.test(inst.stderr + inst.stdout)) {
    const upd = await exec('claude', ['plugin', 'update', PLUGIN_SPEC, '--scope', 'user']);
    log(upd.ok
      ? `✓ Plugin updated: ${PLUGIN_SPEC}`
      : `✓ Plugin already installed: ${PLUGIN_SPEC}`);
  } else {
    error(`✗ Could not install plugin ${PLUGIN_SPEC}:\n${(inst.stderr || inst.stdout).trim()}`);
    return 1;
  }

  let list = await exec('claude', ['plugin', 'list', '--json']);
  let plugin = list.ok ? findRobiumPlugin(list.stdout) : null;
  if (plugin?.enabled === false) {
    const enabled = await exec('claude', ['plugin', 'enable', PLUGIN_SPEC, '--scope', 'user']);
    if (enabled.ok) {
      log(`✓ Plugin enabled: ${PLUGIN_SPEC}`);
      list = await exec('claude', ['plugin', 'list', '--json']);
      plugin = list.ok ? findRobiumPlugin(list.stdout) : null;
    }
  }
  const verified = !!plugin && plugin.enabled !== false;
  log(verified
    ? '✓ Verified: robium is installed and enabled'
    : '! Could not verify install (run `claude plugin list` to check)');
  return 0;
}

const CODEX_MISSING = `✗ Codex not found on PATH.

  Install Codex first, then re-run:

    npx robium-ai setup --agent codex`;

// Codex path: install the native plugin so users receive the skills and the
// learning-capture hooks as one versioned bundle. The local clone remains the
// marketplace source, so updating it and refreshing the marketplace updates
// the plugin payload.
export async function installCodex({
  exec = run,
  log = console.log,
  error = console.error,
  marketplaceRef = MARKETPLACE_REF,
  command = 'codex',
} = {}) {
  const ver = await exec(command, ['--version']);
  if (!ver.ok) {
    error(CODEX_MISSING);
    return 1;
  }
  log(`✓ Codex detected (${ver.stdout.trim()})`);

  const add = await exec(command, ['plugin', 'marketplace', 'add', marketplaceRef]);
  if (add.ok) {
    log(`✓ Codex marketplace added: ${marketplaceRef}`);
  } else if (/already|exists|configured/i.test(add.stderr + add.stdout)) {
    const upd = await exec(command, ['plugin', 'marketplace', 'upgrade', MARKETPLACE_NAME]);
    log(upd.ok
      ? '✓ Codex marketplace already present; refreshed to latest'
      : '! Codex marketplace already present (refresh failed; continuing)');
  } else {
    error(`✗ Could not add Codex marketplace ${marketplaceRef}:\n${(add.stderr || add.stdout).trim()}`);
    return 1;
  }

  const inst = await exec(command, ['plugin', 'add', PLUGIN_SPEC, '--json']);
  if (inst.ok) {
    log(`✓ Codex plugin installed: ${PLUGIN_SPEC}`);
  } else if (/already|installed/i.test(inst.stderr + inst.stdout)) {
    log(`✓ Codex plugin already installed: ${PLUGIN_SPEC}`);
  } else {
    error(`✗ Could not install Codex plugin ${PLUGIN_SPEC}:\n${(inst.stderr || inst.stdout).trim()}`);
    return 1;
  }

  const list = await exec(command, ['plugin', 'list', '--json']);
  const plugin = list.ok ? findCodexRobiumPlugin(list.stdout) : null;
  const verified = !!plugin && plugin.enabled !== false;
  log(verified
    ? '✓ Verified: robium is installed and enabled in Codex'
    : '! Could not verify Codex install (run `codex plugin list` to check)');
  return 0;
}
