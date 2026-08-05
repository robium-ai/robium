import path from 'node:path';
import { loadApps } from './apps.js';

// robium-app.yaml schema "1" validation (reference-apps spec section 5).
// Precise, per-field errors; JSON output for CI.

const STATUS = ['experimental', 'stable', 'archived'];
const KIND = ['docker', 'uv', 'remote-gpu', 'hardware'];
const GPU = ['none', 'optional', 'required', 'remote'];

export function validateApp(app) {
  const errors = [];
  const warn = [];
  const need = (cond, msg) => { if (!cond) errors.push(msg); };

  need(app.schema_version === '1', `schema_version must be "1" (got ${JSON.stringify(app.schema_version)})`);
  need(typeof app.id === 'string' && app.id.length > 0, 'id is required');
  if (app.id && app.dir) {
    need(path.basename(app.dir) === app.id, `id "${app.id}" must equal the directory name "${path.basename(app.dir)}"`);
  }
  need(typeof app.name === 'string' && app.name.length > 0, 'name is required');
  need(typeof app.summary === 'string' && app.summary.length > 0, 'summary is required');
  need(typeof app.version === 'string' && /^\d+\.\d+\.\d+$/.test(app.version ?? ''), `version must be MAJOR.MINOR.PATCH (got ${JSON.stringify(app.version)})`);
  need(STATUS.includes(app.status), `status must be one of ${STATUS.join(' | ')} (got ${JSON.stringify(app.status)})`);
  need(typeof app.license === 'string' && app.license.length > 0, 'license is required');

  need(app.runtime && typeof app.runtime === 'object', 'runtime section is required');
  if (app.runtime) {
    need(KIND.includes(app.runtime.kind), `runtime.kind must be one of ${KIND.join(' | ')} (got ${JSON.stringify(app.runtime.kind)})`);
    need(typeof app.runtime.entrypoint === 'string' && app.runtime.entrypoint.length > 0, 'runtime.entrypoint is required');
  }

  need(app.verbs && typeof app.verbs === 'object', 'verbs section is required');
  if (app.verbs) {
    need(typeof app.verbs.smoke === 'string', 'verbs.smoke is required (the pass bar)');
    for (const [k, v] of Object.entries(app.verbs)) {
      need(typeof v === 'string' && v.length > 0, `verbs.${k} must be a command string`);
    }
    if (app.status !== 'archived' && !app.verbs.check) warn.push('no verbs.check: preflight is doctor-facts only');
  }

  const scenarioNames = Object.keys(app.scenarios ?? {});
  for (const [nameKey, s] of Object.entries(app.scenarios ?? {})) {
    need(s && typeof s === 'object' && typeof s.command === 'string', `scenarios.${nameKey}.command is required`);
    if (s && typeof s === 'object' && !s.summary) warn.push(`scenarios.${nameKey} has no summary`);
  }

  need(app.requirements && typeof app.requirements === 'object', 'requirements section is required');
  if (app.requirements) {
    need(Array.isArray(app.requirements.hardware), 'requirements.hardware must be an array');
    need(GPU.includes(app.requirements.gpu), `requirements.gpu must be one of ${GPU.join(' | ')} (got ${JSON.stringify(app.requirements.gpu)})`);
  }

  need(app.demo && typeof app.demo === 'object', 'demo section is required');
  if (app.demo) {
    need(typeof app.demo.hosted === 'boolean', 'demo.hosted must be true or false');
    const ds = app.demo.default_scenario;
    need(typeof ds === 'string', 'demo.default_scenario is required');
    if (typeof ds === 'string') {
      const known = ds === 'demo' || scenarioNames.includes(ds) || typeof app.verbs?.[ds] === 'string';
      need(known, `demo.default_scenario "${ds}" matches no verb or scenario`);
    }
    if (app.demo.estimated_startup_seconds != null) {
      need(typeof app.demo.estimated_startup_seconds === 'number', 'demo.estimated_startup_seconds must be a number');
    }
    // hosted apps that want a derived orchestrator config declare how to run
    if (app.demo.orchestrator) {
      const o = app.demo.orchestrator;
      need(typeof o.image === 'string', 'demo.orchestrator.image is required when the section is present');
      need(Array.isArray(o.command) || typeof o.command === 'string', 'demo.orchestrator.command must be a string or array');
      need(typeof o.gateway_port === 'number', 'demo.orchestrator.gateway_port must be a number');
    } else if (app.demo.hosted === true) {
      warn.push('demo.hosted is true but no demo.orchestrator section: the orchestrator config cannot be derived');
    }
  }

  return { id: app.id ?? path.basename(app.dir ?? '?'), ok: errors.length === 0, errors, warnings: warn };
}

export function validateApps(apps) {
  const results = apps.map((a) =>
    a.parse_error
      ? { id: a.id, ok: false, errors: [`robium-app.yaml failed to parse: ${a.parse_error}`], warnings: [] }
      : validateApp(a));
  return { ok: results.every((r) => r.ok), results };
}

export function appValidate({ appsDir, flags = {}, log = console.log } = {}) {
  const { ok, results } = validateApps(loadApps(appsDir));
  if (flags.json) {
    log(JSON.stringify({ ok, apps_dir: appsDir, results }, null, 2));
    return ok ? 0 : 1;
  }
  log(`validating robium-app.yaml files in ${appsDir}\n`);
  for (const r of results) {
    log(`  ${r.ok ? '✓' : '✗'} ${r.id}`);
    for (const e of r.errors) log(`      error: ${e}`);
    for (const w of r.warnings) log(`      warn:  ${w}`);
  }
  log(ok ? '\nAll apps valid.' : '\nValidation failed: fix the errors above.');
  return ok ? 0 : 1;
}
