import { homedir } from 'node:os';
import path from 'node:path';
import { cp, lstat, mkdir, readdir, realpath, rm, stat, symlink, writeFile } from 'node:fs/promises';
import { run } from './exec.js';
import { installClaude, installCodex } from './install.js';
import { resolveRepo } from './repo.js';
import { detectAgentSupport } from './agentCommands.js';

// Claude Code and Codex install the native plugin (skills + capture hooks),
// served from the clone. Gemini and Cursor receive Agent Skills symlinks in
// their own user directories. Keeping those links out of ~/.agents/skills
// avoids duplicate Codex skill registrations when the plugin is enabled.
export const AGENTS = ['claude', 'codex', 'gemini', 'cursor'];

const LABEL = {
  claude: 'Claude Code',
  codex: 'Codex',
  gemini: 'Gemini CLI',
  cursor: 'Cursor',
};

// Marker file for COPIED skill dirs (symlinks are self-identifying: they
// resolve into a robium checkout). Lets re-runs upgrade our copies without
// ever clobbering someone else's same-named skill.
const MARKER = '.robium-managed';

async function isFile(p) {
  try { return (await stat(p)).isFile(); } catch { return false; }
}

export async function detectAgents(opts = {}) {
  return (await detectAgentSupport(opts)).agents;
}

// A path is "ours" when it resolves to a skill dir inside a robium checkout.
async function isRobiumSkillTarget(resolved) {
  return (await isFile(path.join(resolved, 'SKILL.md')))
    && ((await isFile(path.join(resolved, '..', '..', '.codex-plugin', 'plugin.json')))
      || (await isFile(path.join(resolved, '..', '..', '.claude-plugin', 'plugin.json'))));
}

// Decide whether we may replace what's at dest. Returns true for: nothing,
// broken symlinks, symlinks into any robium checkout, dirs carrying our
// copy marker. False (skip) for foreign dirs/symlinks.
async function canReplace(dest) {
  let st;
  try { st = await lstat(dest); } catch { return true; }
  if (st.isSymbolicLink()) {
    let resolved;
    try { resolved = await realpath(dest); } catch { return true; } // broken link
    return isRobiumSkillTarget(resolved);
  }
  if (st.isDirectory()) return isFile(path.join(dest, MARKER));
  return false;
}

export async function linkSkills({ src, targetDir, copyMode = false, version = '', log = () => {} }) {
  await mkdir(targetDir, { recursive: true });
  const entries = await readdir(src, { withFileTypes: true });
  let linked = 0;
  let copied = 0;
  const skipped = [];
  for (const e of entries) {
    if (!e.isDirectory() || e.name.startsWith('_') || e.name.startsWith('.')) continue;
    const from = path.join(src, e.name);
    if (!(await isFile(path.join(from, 'SKILL.md')))) continue;
    const dest = path.join(targetDir, e.name);
    if (!(await canReplace(dest))) {
      skipped.push(e.name);
      continue;
    }
    await rm(dest, { recursive: true, force: true });
    if (copyMode) {
      await cp(from, dest, { recursive: true });
      await writeFile(path.join(dest, MARKER), `robium-ai ${version}\n`.trimStart());
      copied++;
    } else {
      try {
        await symlink(from, dest, 'dir');
        linked++;
      } catch {
        await cp(from, dest, { recursive: true });
        await writeFile(path.join(dest, MARKER), `robium-ai ${version}\n`.trimStart());
        copied++;
      }
    }
  }
  if (skipped.length) {
    log(`! Skipped ${skipped.length} name collision(s) not managed by robium: ${skipped.join(', ')}`);
  }
  return { linked, copied, skipped };
}

const NONE_FOUND = `✗ No supported coding agent found.

  robium sets up skills for: Claude Code, Codex, Gemini CLI, Cursor.
  Install one, then re-run:  npx robium-ai setup

  Or target one explicitly:  npx robium-ai setup --agent codex`;

export async function setup({
  agent,
  dir,
  yes = false,
  copy = false,
  exec = run,
  log = console.log,
  error = console.error,
  home = homedir(),
  cwd = process.cwd(),
  platform = process.platform,
  interactive,
  ask,
} = {}) {
  if (agent && !AGENTS.includes(agent)) {
    error(`Unknown agent "${agent}". Supported: ${AGENTS.join(', ')}.`);
    return 1;
  }

  const support = await detectAgentSupport({ exec, home, platform });
  const detected = support.agents;
  const targets = agent ? [agent] : detected;
  if (!targets.length) {
    error(NONE_FOUND);
    return 1;
  }
  if (!agent) {
    log(`✓ Detected: ${targets.map((a) => LABEL[a]).join(', ')}`);
  } else if (!detected.includes(agent)) {
    log(`! ${LABEL[agent]} not detected; installing its skills anyway.`);
  }

  const repoOpts = { exec, home, cwd, dir, yes, log, error };
  if (interactive !== undefined) repoOpts.interactive = interactive;
  if (ask) repoOpts.ask = ask;
  const repo = await resolveRepo(repoOpts);
  if (!repo) return 1;

  let failed = false;

  if (targets.includes('claude')) {
    const rc = await installClaude({ exec, log, error, marketplaceRef: repo });
    if (rc !== 0) failed = true;
  }

  if (targets.includes('codex')) {
    const rc = await installCodex({
      exec,
      log,
      error,
      marketplaceRef: repo,
      command: support.codex?.command ?? 'codex',
    });
    if (rc !== 0) failed = true;
  }

  const skillTargets = targets.filter((a) => a === 'gemini' || a === 'cursor');
  for (const target of skillTargets) {
    const targetDir = path.join(home, target === 'gemini' ? '.gemini' : '.cursor', 'skills');
    try {
      const { linked, copied } = await linkSkills({
        src: path.join(repo, 'skills'),
        targetDir,
        copyMode: copy,
        version: await cliVersion(),
        log,
      });
      const how = [linked && `${linked} linked`, copied && `${copied} copied`].filter(Boolean).join(', ');
      log(`✓ Agent Skills installed to ${path.join('~', target === 'gemini' ? '.gemini' : '.cursor', 'skills')} (${how || 'up to date'})`);
      log(`  Read natively by ${LABEL[target]}; git pull in the repo updates them.`);
    } catch (e) {
      error(`✗ Could not install skills for ${LABEL[target]}: ${e.message}`);
      failed = true;
    }
  }

  if (!failed) {
    log(`
Done. The robium repo is your skill source: ${repo}
  update:      npx robium-ai update
  contribute:  cd ${repo} && ./scripts/bootstrap.sh

Open your agent and try:

  > build a mobile robot that navigates in sim

Environment check:  npx robium-ai doctor`);
  }
  return failed ? 1 : 0;
}

async function cliVersion() {
  try {
    const { readFile } = await import('node:fs/promises');
    const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
    return pkg.version ?? '';
  } catch {
    return '';
  }
}
