import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { findCodexRobiumPlugin, findRobiumPlugin } from './plugins.js';
import { listManagedSkills } from './managedSkills.js';
import { inspectCursorPlugin } from './cursorPlugin.js';

let packageInfoPromise;

export async function integrationVersions() {
  packageInfoPromise ??= Promise.all([
    readFile(new URL('../package.json', import.meta.url), 'utf8').then(JSON.parse),
    readFile(new URL('./catalog.json', import.meta.url), 'utf8').then(JSON.parse),
  ])
    .then(([pkg, catalog]) => ({
      cli: pkg.version ?? null,
      plugin: pkg.robiumPluginVersion ?? null,
      skills: Object.fromEntries((catalog.skills ?? []).map((skill) => [skill.name, skill.version])),
    }))
    .catch(() => ({ cli: null, plugin: null, skills: {} }));
  return packageInfoPromise;
}

function numericVersion(version) {
  const match = String(version ?? '').match(/^(\d+)\.(\d+)\.(\d+)$/);
  return match ? match.slice(1).map(Number) : null;
}

export function isOlderVersion(installed, expected) {
  const left = numericVersion(installed);
  const right = numericVersion(expected);
  if (!left || !right) return false;
  for (let index = 0; index < 3; index++) {
    if (left[index] !== right[index]) return left[index] < right[index];
  }
  return false;
}

function pluginResult(plugin, expectedVersion) {
  if (!plugin || plugin.installed === false) return { state: 'missing', outdated: false };
  const installedVersion = plugin.version ?? null;
  const outdated = isOlderVersion(installedVersion, expectedVersion);
  const state = plugin.enabled === false
    ? 'inactive'
    : plugin.enabled === true
      ? 'active'
      : 'unknown';
  return { state, outdated, installedVersion, expectedVersion };
}

export async function inspectClaudeIntegration({ exec, command = 'claude', expectedVersion } = {}) {
  const listed = await exec(command, ['plugin', 'list', '--json']);
  if (!listed.ok) return { state: 'unknown', outdated: false, apiAvailable: false };
  return { ...pluginResult(findRobiumPlugin(listed.stdout), expectedVersion), apiAvailable: true };
}

export async function inspectCodexIntegration({ exec, command = 'codex', expectedVersion } = {}) {
  const listed = await exec(command, ['plugin', 'list', '--json']);
  if (!listed.ok) return { state: 'unknown', outdated: false, apiAvailable: false };
  return { ...pluginResult(findCodexRobiumPlugin(listed.stdout), expectedVersion), apiAvailable: true };
}

export function parseGeminiExtensions(stdout) {
  try {
    const extensions = JSON.parse(stdout);
    return Array.isArray(extensions) ? extensions : null;
  } catch {
    return null;
  }
}

export function parseGeminiExtensionText(stdout) {
  const clean = String(stdout ?? '').replace(/\x1b\[[0-9;]*m/g, '');
  const heading = clean.match(/^[^\w\n]*robium\s+\((\d+\.\d+\.\d+)\)\s*$/m);
  if (!heading) return null;
  const disabled = /^\s*Enabled \((?:User|Workspace)\):\s*false\s*$/m.test(clean)
    && !/^\s*Enabled \((?:User|Workspace)\):\s*true\s*$/m.test(clean);
  return { name: 'robium', version: heading[1], isActive: !disabled };
}

export function parseGeminiSkills(stdout) {
  const records = [];
  let current = null;
  const clean = stdout.replace(/\x1b\[[0-9;]*m/g, '');
  for (const line of clean.split('\n')) {
    const heading = line.match(/^(.+?)\s+\[(Enabled|Disabled)\](?:\s+\[Built-in\])?\s*$/);
    if (heading) {
      if (current) records.push(current);
      current = { name: heading[1].trim(), enabled: heading[2] === 'Enabled', location: null };
      continue;
    }
    const location = line.match(/^\s*Location:\s+(.+?)\s*$/);
    if (current && location) current.location = location[1];
  }
  if (current) records.push(current);
  return records;
}

function managedSkillsOutdated(managed, skillVersions = {}) {
  return managed.some((item) => item.name
    && isOlderVersion(item.version, skillVersions[item.name]));
}

function normalizedLocations(managed) {
  const locations = new Set();
  for (const item of managed) {
    locations.add(path.resolve(item.path));
    locations.add(path.resolve(item.resolved));
  }
  return locations;
}

export async function inspectGeminiIntegration({
  exec,
  home,
  expectedPluginVersion,
  skillVersions,
} = {}) {
  const extensions = await exec('gemini', [
    'extensions', 'list', '--output-format', 'json',
  ]);
  if (extensions.ok) {
    const parsed = parseGeminiExtensions(extensions.stdout);
    const extension = parsed?.find((item) => item?.name === 'robium');
    if (extension) {
      return {
        ...pluginResult({
          version: extension.version,
          enabled: typeof extension.isActive === 'boolean' ? extension.isActive : undefined,
        }, expectedPluginVersion),
        apiAvailable: true,
        source: 'extension',
      };
    }
  }

  const textList = await exec('gemini', ['extensions', 'list']);
  const textExtension = textList.ok ? parseGeminiExtensionText(textList.stdout) : null;
  if (textExtension) {
    return {
      ...pluginResult({
        version: textExtension.version,
        enabled: textExtension.isActive,
      }, expectedPluginVersion),
      apiAvailable: true,
      source: 'extension',
    };
  }

  const root = path.join(home, '.gemini', 'skills');
  const managed = await listManagedSkills(root);
  if (!managed.length) return { state: 'missing', outdated: false, apiAvailable: extensions.ok };

  const listed = await exec('gemini', ['skills', 'list']);
  const outdated = managedSkillsOutdated(managed, skillVersions);
  if (!listed.ok) {
    return { state: 'unknown', outdated, apiAvailable: false, source: 'skills', count: managed.length };
  }

  const locations = normalizedLocations(managed);
  const discovered = parseGeminiSkills(listed.stdout).filter((item) => item.location
    && locations.has(path.resolve(item.location)));
  if (!discovered.length) {
    return { state: 'inactive', outdated, apiAvailable: true, source: 'skills', count: managed.length };
  }
  return {
    state: discovered.length === managed.length && discovered.every((item) => item.enabled)
      ? 'active'
      : 'inactive',
    outdated,
    apiAvailable: true,
    source: 'skills',
    count: managed.length,
    discoveredCount: discovered.length,
    activeCount: discovered.filter((item) => item.enabled).length,
  };
}

export async function inspectCursorIntegration({ home, expectedPluginVersion, skillVersions } = {}) {
  const plugin = await inspectCursorPlugin({ home, expectedVersion: expectedPluginVersion });
  if (plugin.state !== 'missing') return plugin;

  // setup <=0.10 installed skill links only; retain detection for migration.
  const managed = await listManagedSkills(path.join(home, '.cursor', 'skills'));
  if (!managed.length) return { state: 'missing', outdated: false, apiAvailable: false };
  return {
    state: 'unknown',
    outdated: managedSkillsOutdated(managed, skillVersions),
    apiAvailable: false,
    source: 'skills',
    count: managed.length,
  };
}
