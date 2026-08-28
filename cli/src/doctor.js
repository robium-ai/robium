import os from 'node:os';
import { run } from './exec.js';
import { detectAgentSupport } from './agentCommands.js';
import {
  inspectClaudeIntegration,
  inspectCodexIntegration,
  inspectCursorIntegration,
  inspectGeminiIntegration,
  integrationVersions,
} from './integrationStatus.js';

const GLYPH = { pass: '✓', warn: '!', fail: '✗', info: '·', skip: '-' };
const AGENT_LABEL = {
  claude: 'Claude Code',
  codex: 'Codex',
  gemini: 'Gemini CLI',
  cursor: 'Cursor',
};

function integrationCheck(result, {
  missingHint,
  inactiveHint,
  outdatedHint,
  unknownHint,
} = {}) {
  const state = { integrationState: result.state, outdated: !!result.outdated };
  const version = result.installedVersion ? ` v${result.installedVersion}` : '';
  const count = result.count ? ` (${result.count} managed skill${result.count === 1 ? '' : 's'})` : '';
  const expected = result.expectedVersion ? `; expected v${result.expectedVersion}` : '';
  if (result.state === 'missing') {
    return { ...state, status: 'warn', detail: 'not installed', hint: missingHint };
  }
  if (result.state === 'inactive') {
    const stale = result.outdated ? ` and outdated${version}${expected}` : '';
    return { ...state, status: 'warn', detail: `installed but inactive${stale}${count}`, hint: inactiveHint };
  }
  if (result.outdated) {
    const activity = result.state === 'active' ? 'active' : 'installed';
    return { ...state, status: 'warn', detail: `${activity} but outdated${version}${expected}${count}`, hint: outdatedHint };
  }
  if (result.state === 'active') {
    return { ...state, status: 'pass', detail: `active${version}${count}` };
  }
  return {
    ...state,
    status: 'warn',
    detail: `installed${count}; activation status unavailable`,
    hint: unknownHint,
  };
}

export function buildChecks({
  exec = run,
  platform = process.platform,
  arch = process.arch,
  env = process.env,
  home = os.homedir(),
} = {}) {
  const appleSilicon = platform === 'darwin' && arch === 'arm64';
  let supportPromise;
  let versionsPromise;
  const support = () => {
    supportPromise ??= detectAgentSupport({ exec, home, platform });
    return supportPromise;
  };
  const versions = () => {
    versionsPromise ??= integrationVersions();
    return versionsPromise;
  };
  return [
    {
      id: 'platform', label: 'Platform',
      async run() {
        if (appleSilicon) {
          return { status: 'pass', detail: 'macOS arm64 (Apple Silicon; MPS available for local training)' };
        }
        if (platform === 'linux' && !env.DISPLAY) {
          return { status: 'pass', detail: `linux ${arch} (no DISPLAY, headless; use headless render backends)` };
        }
        return { status: 'pass', detail: `${platform} ${arch}` };
      },
    },
    {
      id: 'coding-agent', label: 'Coding agent',
      async run() {
        const detected = await support();
        const found = detected.agents.map((name) => AGENT_LABEL[name]);
        return found.length
          ? { status: 'pass', detail: found.join(', ') }
          : { status: 'fail', detail: 'Claude Code, Codex, Gemini CLI, and Cursor were not detected', hint: 'install one, then run: npx robium-ai setup' };
      },
    },
    {
      id: 'claude', label: 'Claude Code',
      async run() {
        const detected = await support();
        if (!detected.claude) return { status: 'skip', detail: 'not installed (optional)' };
        return { status: 'pass', detail: detected.claude.version.stdout.trim() };
      },
    },
    {
      id: 'claude-plugin', label: 'Claude plugin',
      async run() {
        const detected = await support();
        if (!detected.claude) return { status: 'skip', detail: 'Claude Code not installed' };
        const expected = await versions();
        const result = await inspectClaudeIntegration({
          exec, command: detected.claude.command, expectedVersion: expected.plugin,
        });
        return integrationCheck(result, {
          missingHint: 'run: npx robium-ai setup --agent claude',
          inactiveHint: 'enable robium@robium, then start a new Claude Code session',
          outdatedHint: 'run: npx robium-ai update --agent claude; then start a new Claude Code session',
          unknownHint: 'run: claude plugin list --json',
        });
      },
    },
    {
      id: 'codex', label: 'Codex',
      async run() {
        const detected = await support();
        if (!detected.codex) return { status: 'skip', detail: 'not installed (optional)' };
        const suffix = detected.codex.source === 'PATH' ? '' : ` (${detected.codex.source})`;
        return { status: 'pass', detail: `${detected.codex.version.stdout.trim()}${suffix}` };
      },
    },
    {
      id: 'codex-plugin', label: 'Codex plugin',
      async run() {
        const detected = await support();
        if (!detected.codex) return { status: 'skip', detail: 'Codex not installed' };
        const expected = await versions();
        const result = await inspectCodexIntegration({
          exec, command: detected.codex.command, expectedVersion: expected.plugin,
        });
        return integrationCheck(result, {
          missingHint: 'run: npx robium-ai setup --agent codex',
          inactiveHint: 'enable robium in the Codex plugin browser, then start a new task',
          outdatedHint: 'run: npx robium-ai update --agent codex; then start a new Codex task',
          unknownHint: 'run: codex plugin list --json',
        });
      },
    },
    {
      id: 'gemini', label: 'Gemini CLI',
      async run() {
        const detected = await support();
        if (!detected.gemini) return { status: 'skip', detail: 'not installed (optional)' };
        return { status: 'pass', detail: detected.gemini.version.stdout.trim() };
      },
    },
    {
      id: 'gemini-skills', label: 'Gemini skills',
      async run() {
        const detected = await support();
        if (!detected.gemini) return { status: 'skip', detail: 'Gemini CLI not installed' };
        const expected = await versions();
        const result = await inspectGeminiIntegration({
          exec,
          home,
          expectedPluginVersion: expected.plugin,
          skillVersions: expected.skills,
        });
        return integrationCheck(result, {
          missingHint: 'run: npx robium-ai setup --agent gemini',
          inactiveHint: result.source === 'extension'
            ? 'run: gemini extensions enable robium; then start a new Gemini session'
            : 'run: gemini skills list; enable the Robium skills, then start a new Gemini session',
          outdatedHint: 'run: npx robium-ai update --agent gemini; then start a new Gemini session',
          unknownHint: 'start a new Gemini session and run: gemini skills list',
        });
      },
    },
    {
      id: 'cursor', label: 'Cursor',
      async run() {
        const detected = await support();
        if (!detected.cursor) return { status: 'skip', detail: 'not installed (optional)' };
        const version = detected.cursor.version?.stdout.trim();
        return { status: 'pass', detail: version || `detected via ${detected.cursor.source}` };
      },
    },
    {
      id: 'cursor-skills', label: 'Cursor skills',
      async run() {
        const detected = await support();
        if (!detected.cursor) return { status: 'skip', detail: 'Cursor not installed' };
        const expected = await versions();
        const result = await inspectCursorIntegration({ home, skillVersions: expected.skills });
        return integrationCheck(result, {
          missingHint: 'run: npx robium-ai setup --agent cursor',
          outdatedHint: 'run: npx robium-ai update --agent cursor; then start a new Cursor chat',
          unknownHint: 'start a new Cursor chat; Cursor does not expose a skill activation-status API',
        });
      },
    },
    {
      id: 'docker', label: 'Docker',
      async run() {
        const v = await exec('docker', ['--version']);
        if (!v.ok) {
          return { status: 'warn', detail: 'not found', hint: 'ROS 2 / Gazebo workflows run in containers; install Docker' };
        }
        const info = await exec('docker', ['info', '--format', '{{.ServerVersion}}'], { timeout: 15_000 });
        if (!info.ok) return { status: 'warn', detail: `${v.stdout.trim()} (daemon not running)`, hint: 'start Docker' };
        return { status: 'pass', detail: `${v.stdout.trim()} (daemon ${info.stdout.trim()})` };
      },
    },
    {
      id: 'disk', label: 'Disk space',
      async run() {
        const r = await exec('df', ['-Pk', os.homedir()]);
        if (!r.ok) return { status: 'skip', detail: 'could not check' };
        const fields = r.stdout.trim().split('\n').pop().trim().split(/\s+/);
        const availKb = Number(fields[3]);
        if (!Number.isFinite(availKb)) return { status: 'skip', detail: 'could not parse df output' };
        const gb = availKb / 1024 / 1024;
        const detail = `${gb.toFixed(0)} GB free`;
        return gb < 20
          ? { status: 'warn', detail, hint: 'sim images are large (5–20 GB); free up space' }
          : { status: 'pass', detail };
      },
    },
    {
      id: 'gpu', label: 'GPU',
      async run() {
        if (appleSilicon) {
          return { status: 'pass', detail: 'Apple Silicon MPS (no CUDA; Isaac Sim/Lab need an NVIDIA RTX-class GPU, local or remote)' };
        }
        const r = await exec('nvidia-smi', ['--query-gpu=name,driver_version', '--format=csv,noheader']);
        if (r.ok && r.stdout.trim()) return { status: 'pass', detail: r.stdout.trim().split('\n')[0] };
        return { status: 'info', detail: 'no NVIDIA GPU detected', hint: 'fine for most skills; Isaac Sim/Lab need an RTX-class GPU (local or remote)' };
      },
    },
    {
      id: 'python', label: 'Python / uv',
      async run() {
        const py = await exec('python3', ['--version']);
        if (!py.ok) return { status: 'warn', detail: 'python3 not found', hint: 'install Python 3' };
        const uv = await exec('uv', ['--version']);
        const pyVer = (py.stdout || py.stderr).trim();
        return uv.ok
          ? { status: 'pass', detail: `${pyVer}, ${uv.stdout.trim()}` }
          : { status: 'warn', detail: `${pyVer}, uv not found`, hint: 'install uv: https://docs.astral.sh/uv/' };
      },
    },
    {
      id: 'ros2', label: 'ROS 2 (native)',
      async run() {
        const r = await exec('ros2', ['--help'], { timeout: 15_000 });
        return r.ok
          ? { status: 'info', detail: 'ros2 CLI on PATH' }
          : { status: 'info', detail: 'not on PATH (fine; container workflows cover ROS 2)' };
      },
    },
  ];
}

export async function runChecks(opts = {}) {
  const checks = buildChecks(opts);
  return Promise.all(checks.map(async (c) => ({ id: c.id, label: c.label, ...(await c.run()) })));
}

export async function doctor({ json = false, log = console.log, ...opts } = {}) {
  const results = await runChecks(opts);
  const exitCode = results.some((r) => r.status === 'fail') ? 1 : 0;

  if (json) {
    log(JSON.stringify({ ok: exitCode === 0, checks: results }, null, 2));
    return exitCode;
  }

  log('robium doctor\n');
  const w = Math.max(...results.map((r) => r.label.length));
  for (const r of results) {
    log(`  ${GLYPH[r.status] ?? '?'} ${r.label.padEnd(w)}  ${r.detail}${r.hint ? `\n    ${' '.repeat(w)}→ ${r.hint}` : ''}`);
  }
  log(exitCode === 0
    ? '\nNo blockers found.'
    : '\nBlockers found: fix the ✗ items above.');
  return exitCode;
}
