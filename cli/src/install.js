import { run } from './exec.js';
import { findRobiumPlugin } from './plugins.js';

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
// Other agents are handled by setup.js via the shared ~/.agents/skills dir.
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
    log(`✓ Plugin already installed: ${PLUGIN_SPEC}`);
  } else {
    error(`✗ Could not install plugin ${PLUGIN_SPEC}:\n${(inst.stderr || inst.stdout).trim()}`);
    return 1;
  }

  const list = await exec('claude', ['plugin', 'list', '--json']);
  const plugin = list.ok ? findRobiumPlugin(list.stdout) : null;
  const verified = !!plugin && plugin.enabled !== false;
  log(verified
    ? '✓ Verified: robium is installed and enabled'
    : '! Could not verify install (run `claude plugin list` to check)');
  return 0;
}
