#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { setup } from '../src/setup.js';
import { doctor } from '../src/doctor.js';
import { skills } from '../src/skills.js';
import { appCmd } from '../src/apps.js';
import { remove } from '../src/remove.js';
import { updateWorkspace } from '../src/updates.js';
import { findWorkspace } from '../src/workspace.js';

const USAGE = `robium: robotics skill pack for coding agents (https://robium.ai)

Usage:
  npx robium-ai setup [options]          Clone robium and robium-apps and wire into
                                         your coding agents (auto-detects:
                                         claude, codex, gemini, cursor)
  npx robium-ai install                  Alias for setup
  npx robium-ai workspace [--json]       Show the current or remembered workspace
  npx robium-ai update [options]         Fast-forward clean main in both repos;
                                         refresh detected agent integrations
  npx robium-ai update --check           Check official main without applying
                                         (--quiet: throttled, non-blocking notices)
  npx robium-ai remove [options]         Remove managed agent integrations;
                                         preserve the Robium checkout
  npx robium-ai doctor [--json]          Check environment and integration state
  npx robium-ai skills [query]           Browse the skill catalog
  npx robium-ai app <subcommand>         Work with reference applications
                                         (list | describe | help | doctor |
                                          build | run | status | logs | stop |
                                          validate | new)

Setup options:
  --agent <name>   Target one agent instead of auto-detecting
  --dir <path>     Workspace parent for setup/update (default ~/robium);
                    app commands use the apps repository itself
  --copy           Copy integration files instead of symlinking
  -y, --yes        No prompts; accept defaults

Options:
  -h, --help       Show this help
  -v, --version    Show version`;

export function parseArgs(argv) {
  const args = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-h' || a === '--help') args.flags.help = true;
    else if (a === '-v' || a === '--version') args.flags.version = true;
    else if (a === '--json') args.flags.json = true;
    else if (a === '--check') args.flags.check = true;
    else if (a === '--quiet') args.flags.quiet = true;
    else if (a === '--copy') args.flags.copy = true;
    else if (a === '-y' || a === '--yes') args.flags.yes = true;
    else if (a.startsWith('--agent=')) args.flags.agent = a.slice('--agent='.length);
    else if (a === '--agent') args.flags.agent = argv[++i];
    else if (a.startsWith('--dir=')) args.flags.dir = a.slice('--dir='.length);
    else if (a === '--dir') args.flags.dir = argv[++i];
    else if (a.startsWith('--mode=')) args.flags.mode = a.slice('--mode='.length);
    else if (a === '--mode') args.flags.mode = argv[++i];
    else if (a.startsWith('--from=')) args.flags.from = a.slice('--from='.length);
    else if (a === '--from') args.flags.from = argv[++i];
    else if (a.startsWith('-')) args.flags.unknown = a;
    else args._.push(a);
  }
  return args;
}

export async function main(argv) {
  const { _: pos, flags } = parseArgs(argv);
  const cmd = pos[0];

  if (flags.version) {
    const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
    console.log(pkg.version);
    return 0;
  }
  if (flags.unknown) {
    console.error(`Unknown option: ${flags.unknown}\n\n${USAGE}`);
    return 1;
  }
  if (Object.hasOwn(flags, 'dir') && (!flags.dir || flags.dir.startsWith('--'))) {
    console.error('--dir requires a workspace path (or an apps repository for app commands).');
    return 1;
  }
  if ((flags.check || flags.quiet) && cmd !== 'update') {
    console.error('--check and --quiet are update options; use robium-ai update --check.');
    return 1;
  }
  if (flags.help || !cmd) {
    console.log(USAGE);
    return flags.help || !cmd ? 0 : 1;
  }

  switch (cmd) {
    case 'setup':
    case 'install':
      return setup({ agent: flags.agent, dir: flags.dir, yes: flags.yes, copy: flags.copy });
    case 'workspace': {
      const workspace = findWorkspace({ dir: flags.dir });
      if (!workspace) { console.error('No workspace configured. Run npx robium-ai setup.'); return 1; }
      console.log(flags.json ? JSON.stringify(workspace, null, 2) :
        `Workspace: ${workspace.root}\nSkills: ${workspace.repo}\nExamples: ${workspace.apps}`);
      return 0;
    }
    case 'update': {
      if (flags.quiet && flags.json) { console.error('Use --quiet for occasional notices or --json for a fresh report, not both.'); return 1; }
      if (flags.json && !flags.check) { console.error('--json requires update --check.'); return 1; }
      const code = await updateWorkspace({ dir: flags.dir, check: flags.check, quiet: flags.quiet, json: flags.json });
      if (flags.check) return code;
      if (code !== 0) {
        console.error('Update incomplete. Integrations were not refreshed. Review the repository results; run setup to reconnect the current source without pulling.');
        return code;
      }
      return setup({ agent: flags.agent, dir: flags.dir, yes: true, copy: flags.copy });
    }
    case 'remove':
      return remove({ agent: flags.agent });
    case 'doctor':
      return doctor({ json: flags.json });
    case 'skills':
      return skills({ query: pos[1] });
    case 'app':
      if (pos[1] === 'list' && !flags.json && !flags.dir && !process.env.ROBIUM_APPS_DIR) {
        await updateWorkspace({ check: true, quiet: true });
      }
      return appCmd({ args: pos.slice(1), flags });
    default:
      console.error(`Unknown command: ${cmd}\n\n${USAGE}`);
      return 1;
  }
}

try { process.exitCode = await main(process.argv.slice(2)); }
catch (error) { console.error(error.message); process.exitCode = 1; }
