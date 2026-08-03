import os from 'node:os';
import { run } from './exec.js';
import { findRobiumPlugin } from './plugins.js';

const GLYPH = { pass: '✓', warn: '!', fail: '✗', info: '·', skip: '-' };

export function buildChecks({ exec = run, platform = process.platform, arch = process.arch, env = process.env } = {}) {
  const appleSilicon = platform === 'darwin' && arch === 'arm64';
  return [
    {
      id: 'platform', label: 'Platform',
      async run() {
        if (appleSilicon) {
          return { status: 'pass', detail: 'macOS arm64 (Apple Silicon — MPS available for local training)' };
        }
        if (platform === 'linux' && !env.DISPLAY) {
          return { status: 'pass', detail: `linux ${arch} (no DISPLAY — headless; use headless render backends)` };
        }
        return { status: 'pass', detail: `${platform} ${arch}` };
      },
    },
    {
      id: 'claude', label: 'Claude Code',
      async run() {
        const r = await exec('claude', ['--version']);
        if (!r.ok) return { status: 'fail', detail: 'not found on PATH', hint: 'install: https://claude.com/claude-code' };
        return { status: 'pass', detail: r.stdout.trim() };
      },
    },
    {
      id: 'plugin', label: 'robium plugin',
      async run() {
        const r = await exec('claude', ['plugin', 'list', '--json']);
        if (!r.ok) return { status: 'skip', detail: 'could not query plugin list' };
        const plugin = findRobiumPlugin(r.stdout);
        if (!plugin) return { status: 'warn', detail: 'not installed', hint: 'run: npx robium-ai install' };
        if (plugin.enabled === false) {
          return { status: 'warn', detail: 'installed but not loaded', hint: 'check plugin dependencies: claude plugin list' };
        }
        return { status: 'pass', detail: 'installed' };
      },
    },
    {
      id: 'docker', label: 'Docker',
      async run() {
        const v = await exec('docker', ['--version']);
        if (!v.ok) {
          return { status: 'warn', detail: 'not found', hint: 'ROS 2 / Gazebo workflows run in containers — install Docker' };
        }
        const info = await exec('docker', ['info', '--format', '{{.ServerVersion}}'], { timeout: 15_000 });
        if (!info.ok) return { status: 'warn', detail: `${v.stdout.trim()} — daemon not running`, hint: 'start Docker' };
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
          return { status: 'pass', detail: 'Apple Silicon MPS (no CUDA — Isaac Sim/Lab need an NVIDIA RTX-class GPU, local or remote)' };
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
          : { status: 'info', detail: 'not on PATH — fine; container workflows cover ROS 2' };
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
    : '\nBlockers found — fix the ✗ items above.');
  return exitCode;
}
