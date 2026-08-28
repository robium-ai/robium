#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { setup } from '../src/setup.js';
import { doctor } from '../src/doctor.js';
import { skills } from '../src/skills.js';
import { appCmd } from '../src/apps.js';

const USAGE = `robium: robotics skill pack for coding agents (https://robium.ai)

Usage:
  npx robium-ai setup [options]          Clone the robium repo and wire it into
                                         your coding agents (auto-detects:
                                         claude, codex, gemini, cursor)
  npx robium-ai install                  Alias for setup
  npx robium-ai update [options]         Pull the Robium checkout and refresh
                                         every detected agent integration
  npx robium-ai doctor [--json]          Check your environment
  npx robium-ai skills [query]           Browse the skill catalog
  npx robium-ai app <subcommand>         Work with reference applications
                                         (list | describe | help | doctor |
                                          build | run | status | logs | stop |
                                          validate | new)

Setup options:
  --agent <name>   Target one agent instead of auto-detecting
  --dir <path>     Where to clone/find the robium repo (default ~/robium)
  --copy           Copy skills from the repo instead of symlinking
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
  if (flags.help || !cmd) {
    console.log(USAGE);
    return flags.help || !cmd ? 0 : 1;
  }

  switch (cmd) {
    case 'setup':
    case 'install':
      return setup({ agent: flags.agent, dir: flags.dir, yes: flags.yes, copy: flags.copy });
    case 'update':
      return setup({ agent: flags.agent, dir: flags.dir, yes: true, copy: flags.copy });
    case 'doctor':
      return doctor({ json: flags.json });
    case 'skills':
      return skills({ query: pos[1] });
    case 'app':
      return appCmd({ args: pos.slice(1), flags });
    default:
      console.error(`Unknown command: ${cmd}\n\n${USAGE}`);
      return 1;
  }
}

process.exitCode = await main(process.argv.slice(2));
