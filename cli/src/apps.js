import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { spawn } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import { runChecks } from './doctor.js';
import { appValidate } from './appValidate.js';
import { scaffoldApp } from './appNew.js';

// ---------------------------------------------------------------------------
// robium-app.yaml parser. Deliberately a YAML *subset* so the CLI stays
// zero-dependency: 2-space-indented nested maps, scalar values, inline
// arrays [a, b], empty maps {}, quoted strings, null/true/false/numbers,
// and comments (full-line or trailing after whitespace). The reference-apps
// spec (section 5) keeps files inside this subset; the future validator
// (v1.1) enforces it.
// ---------------------------------------------------------------------------

function parseScalar(raw) {
  let s = raw.trim();
  // trailing comment: " #" outside quotes
  if (!s.startsWith('"') && !s.startsWith("'")) {
    const m = s.match(/\s+#.*$/);
    if (m) s = s.slice(0, m.index).trim();
  }
  if (s === '' || s === 'null' || s === '~') return null;
  if (s === '{}') return {};
  if (s === '[]') return [];
  if (s === 'true') return true;
  if (s === 'false') return false;
  if (s.startsWith('[') && s.endsWith(']')) {
    const inner = s.slice(1, -1).trim();
    return inner === '' ? [] : inner.split(',').map((x) => parseScalar(x));
  }
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    return s.slice(1, -1);
  }
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
  return s;
}

export function parseAppYaml(text) {
  const root = {};
  // stack of [indent, object] — the object currently collecting keys
  const stack = [[-1, root]];
  const lines = text.split('\n');
  for (let n = 0; n < lines.length; n++) {
    const line = lines[n];
    if (!line.trim() || line.trim().startsWith('#')) continue;
    const indent = line.length - line.trimStart().length;
    const m = line.trim().match(/^([A-Za-z0-9_-]+):(.*)$/);
    if (!m) throw new Error(`robium-app.yaml line ${n + 1}: expected "key: value", got "${line.trim()}"`);
    const [, key, rest] = m;
    while (stack.length > 1 && indent <= stack[stack.length - 1][0]) stack.pop();
    const parent = stack[stack.length - 1][1];
    if (rest.trim() === '' || /^\s+#/.test(rest)) {
      const child = {};
      parent[key] = child;
      stack.push([indent, child]);
    } else {
      const v = parseScalar(rest);
      parent[key] = v;
      if (v && typeof v === 'object' && !Array.isArray(v)) stack.push([indent, v]);
    }
  }
  return root;
}

// ---------------------------------------------------------------------------
// Apps-directory resolution. Documented rule, no hardcoded layouts:
//   1. --dir flag
//   2. ROBIUM_APPS_DIR environment variable
//   3. walk up from cwd: the first directory that contains REGISTRY.md and
//      at least one <app>/robium-app.yaml (covers running from inside an
//      apps repo or any app subdirectory)
// ---------------------------------------------------------------------------

function looksLikeAppsRepo(dir) {
  if (!existsSync(path.join(dir, 'REGISTRY.md'))) return false;
  try {
    return readdirSync(dir).some((e) => existsSync(path.join(dir, e, 'robium-app.yaml')));
  } catch {
    return false;
  }
}

export function findAppsDir({ dir, env = process.env, cwd = process.cwd() } = {}) {
  if (dir) return existsSync(dir) ? path.resolve(dir) : null;
  if (env.ROBIUM_APPS_DIR) return existsSync(env.ROBIUM_APPS_DIR) ? path.resolve(env.ROBIUM_APPS_DIR) : null;
  let d = path.resolve(cwd);
  const home = os.homedir();
  while (true) {
    if (looksLikeAppsRepo(d)) return d;
    const up = path.dirname(d);
    if (up === d || d === home) return null;
    d = up;
  }
}

export function loadApps(appsDir) {
  const apps = [];
  for (const entry of readdirSync(appsDir)) {
    const yamlPath = path.join(appsDir, entry, 'robium-app.yaml');
    if (!existsSync(yamlPath) || !statSync(path.join(appsDir, entry)).isDirectory()) continue;
    try {
      const meta = parseAppYaml(readFileSync(yamlPath, 'utf8'));
      apps.push({ dir: path.join(appsDir, entry), ...meta });
    } catch (e) {
      apps.push({ dir: path.join(appsDir, entry), id: entry, parse_error: e.message });
    }
  }
  return apps.sort((a, b) => String(a.id).localeCompare(String(b.id)));
}

// Resolve what `app run`/`app check` should execute. Commands are argv-split
// on whitespace (the contract is plain commands like "make demo" — no shell).
export function resolveCommand(app, { verb, scenario } = {}) {
  if (scenario) {
    const s = app.scenarios?.[scenario];
    if (!s?.command) {
      const known = Object.keys(app.scenarios ?? {});
      return { error: `unknown scenario "${scenario}" for ${app.id}${known.length ? ` (known: ${known.join(', ')})` : ' (none declared)'}` };
    }
    return { command: s.command };
  }
  const cmd = app.verbs?.[verb] ?? (verb === 'demo' ? app.runtime?.entrypoint : undefined);
  if (!cmd) return { error: `${app.id} declares no "${verb}" verb in robium-app.yaml` };
  return { command: cmd };
}

function execInApp(command, dir, { spawnFn = spawn } = {}) {
  return new Promise((resolve) => {
    const [bin, ...args] = command.split(/\s+/);
    const child = spawnFn(bin, args, { cwd: dir, stdio: 'inherit' });
    child.on('error', (e) => {
      console.error(`failed to start "${command}": ${e.message}`);
      resolve(1);
    });
    child.on('exit', (code) => resolve(code ?? 1));
  });
}

// ---------------------------------------------------------------------------
// Subcommands
// ---------------------------------------------------------------------------

const APP_USAGE = `robium app: work with reference applications (robium-app.yaml contract)

Usage:
  npx robium-ai app list [--json]                  List apps in the apps repo
  npx robium-ai app describe <id> [--json]         Show one app's metadata
  npx robium-ai app check <id>                     Preflight: doctor facts + the app's own make check
  npx robium-ai app run <id> [--scenario NAME]     Run the app's demo (or a declared scenario)
  npx robium-ai app validate [--json]              Validate every robium-app.yaml (CI-friendly)
  npx robium-ai app new <id> --from <existing-id>  Scaffold by copying the closest shipped app

Apps repo resolution: --dir <path>, else $ROBIUM_APPS_DIR, else walk up from
the current directory to the first repo with REGISTRY.md + robium-app.yaml files.`;

function requireAppsDir(flags, log) {
  const appsDir = findAppsDir({ dir: flags.dir });
  if (!appsDir) {
    log('No apps repo found. Pass --dir <path>, set ROBIUM_APPS_DIR, or run from inside an apps checkout.');
    return null;
  }
  return appsDir;
}

function requireApp(apps, id, log) {
  const app = apps.find((a) => a.id === id);
  if (!app) {
    log(`Unknown app "${id ?? ''}". Known: ${apps.map((a) => a.id).join(', ') || '(none)'}`);
    return null;
  }
  if (app.parse_error) {
    log(`robium-app.yaml for ${id} failed to parse: ${app.parse_error}`);
    return null;
  }
  return app;
}

export async function appCmd({ args = [], flags = {}, log = console.log, exec = execInApp, checks = runChecks } = {}) {
  const sub = args[0];
  const id = args[1];
  if (!sub || flags.help) {
    log(APP_USAGE);
    return sub ? 0 : 1;
  }
  const appsDir = requireAppsDir(flags, log);
  if (!appsDir) return 1;
  if (sub === 'validate') return appValidate({ appsDir, flags, log });
  if (sub === 'new') return scaffoldApp({ appsDir, id, from: flags.from, log });
  const apps = loadApps(appsDir);

  switch (sub) {
    case 'list': {
      if (flags.json) {
        log(JSON.stringify({ apps_dir: appsDir, apps }, null, 2));
        return 0;
      }
      log(`apps in ${appsDir}\n`);
      const w = Math.max(...apps.map((a) => String(a.id).length), 2);
      for (const a of apps) {
        if (a.parse_error) { log(`  ${String(a.id).padEnd(w)}  PARSE ERROR: ${a.parse_error}`); continue; }
        log(`  ${String(a.id).padEnd(w)}  ${String(a.status).padEnd(12)} ${a.runtime?.kind ?? '?'}  ${a.summary ?? ''}`);
      }
      return apps.some((a) => a.parse_error) ? 1 : 0;
    }
    case 'describe': {
      const app = requireApp(apps, id, log);
      if (!app) return 1;
      log(JSON.stringify(app, null, 2));
      return 0;
    }
    case 'check': {
      const app = requireApp(apps, id, log);
      if (!app) return 1;
      // Environment facts relevant to the app's declared runtime/requirements.
      const results = await checks();
      const relevant = results.filter((r) =>
        (app.runtime?.kind === 'docker' && ['docker', 'disk', 'platform'].includes(r.id)) ||
        (app.runtime?.kind === 'uv' && ['python', 'disk', 'platform', 'gpu'].includes(r.id)) ||
        (app.runtime?.kind === 'remote-gpu' && ['python', 'platform'].includes(r.id)) ||
        (app.runtime?.kind === 'hardware' && ['platform'].includes(r.id)));
      for (const r of relevant) log(`  doctor: ${r.label} — ${r.detail}`);
      if (app.requirements?.gpu === 'remote') log('  note: GPU work runs remotely for this app; nothing local to verify');
      const resolved = resolveCommand(app, { verb: 'check' });
      if (resolved.error) {
        log(`  ${resolved.error} — doctor facts above are the whole preflight`);
        return 0;
      }
      return exec(resolved.command, app.dir);
    }
    case 'run': {
      const app = requireApp(apps, id, log);
      if (!app) return 1;
      const resolved = resolveCommand(app, { verb: 'demo', scenario: flags.scenario });
      if (resolved.error) { log(resolved.error); return 1; }
      log(`→ ${resolved.command}  (in ${app.dir})`);
      return exec(resolved.command, app.dir);
    }
    default:
      log(`Unknown app subcommand: ${sub}\n\n${APP_USAGE}`);
      return 1;
  }
}
