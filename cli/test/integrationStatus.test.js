import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import {
  inspectGeminiIntegration,
  integrationVersions,
  isOlderVersion,
  parseGeminiSkills,
  parseGeminiExtensionText,
} from '../src/integrationStatus.js';

test('integrationVersions loads CLI, plugin, and skill release versions', async () => {
  const versions = await integrationVersions();
  assert.equal(versions.cli, '0.11.0');
  assert.equal(versions.plugin, '0.5.0');
  assert.match(versions.skills.nav2, /^\d+\.\d+\.\d+$/);
});

test('isOlderVersion compares numeric releases and ignores unknown versions', () => {
  assert.equal(isOlderVersion('0.2.9', '0.3.0'), true);
  assert.equal(isOlderVersion('0.3.0', '0.3.0'), false);
  assert.equal(isOlderVersion('0.4.0', '0.3.0'), false);
  assert.equal(isOlderVersion('unknown', '0.3.0'), false);
});

test('parseGeminiSkills reads enabled state and location', () => {
  const parsed = parseGeminiSkills(`Discovered Agent Skills:\n\nnav2 [Enabled]\n  Description: nav\n  Location:    /tmp/nav2\n\nros2 [Disabled]\n  Description: ros\n  Location:    /tmp/ros2\n`);
  assert.deepEqual(parsed, [
    { name: 'nav2', enabled: true, location: '/tmp/nav2' },
    { name: 'ros2', enabled: false, location: '/tmp/ros2' },
  ]);
});

test('parseGeminiExtensionText reads version and enablement from concise output', () => {
  assert.deepEqual(parseGeminiExtensionText(`✓ robium (0.4.0)\n Enabled (User): true\n Enabled (Workspace): true\n`), {
    name: 'robium', version: '0.4.0', isActive: true,
  });
  assert.equal(parseGeminiExtensionText('No extensions installed.\n'), null);
});

test('Gemini inspection falls back to concise extension output', async () => {
  const exec = async (_command, args) => args.includes('--output-format')
    ? { ok: true, stdout: '[{"name":"robium"', stderr: '', code: 0 }
    : { ok: true, stdout: '✓ robium (0.4.0)\n Enabled (User): true\n', stderr: '', code: 0 };
  const result = await inspectGeminiIntegration({
    exec, home: '/not-used', expectedPluginVersion: '0.4.0', skillVersions: {},
  });
  assert.equal(result.state, 'active');
  assert.equal(result.source, 'extension');
  assert.equal(result.installedVersion, '0.4.0');
});

test('Gemini managed copy is active when discovered and reports stale skill version', async () => {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-gemini-status-'));
  const home = path.join(base, 'home');
  const skill = path.join(home, '.gemini', 'skills', 'nav2');
  await mkdir(skill, { recursive: true });
  await writeFile(path.join(skill, 'SKILL.md'), 'name: nav2\nversion: 1.0.0\n');
  await writeFile(path.join(skill, '.robium-managed'), 'robium-ai 0.8.0\n');
  const exec = async (_command, args) => {
    if (args[0] === 'extensions') return { ok: true, stdout: '[]', stderr: '', code: 0 };
    return { ok: true, stderr: '', code: 0,
      stdout: `nav2 [Enabled]\n  Location:    ${skill}\n` };
  };
  const result = await inspectGeminiIntegration({
    exec, home, expectedPluginVersion: '0.3.0', skillVersions: { nav2: '1.1.0' },
  });
  assert.equal(result.state, 'active');
  assert.equal(result.outdated, true);
  assert.equal(result.activeCount, 1);
  await rm(base, { recursive: true, force: true });
});

test('Gemini managed skills are inactive when the host does not discover them', async () => {
  const base = await mkdtemp(path.join(os.tmpdir(), 'robium-gemini-status-'));
  const home = path.join(base, 'home');
  const skill = path.join(home, '.gemini', 'skills', 'nav2');
  await mkdir(skill, { recursive: true });
  await writeFile(path.join(skill, 'SKILL.md'), 'name: nav2\nversion: 1.1.0\n');
  await writeFile(path.join(skill, '.robium-managed'), 'robium-ai 0.9.0\n');
  const exec = async (_command, args) => args[0] === 'extensions'
    ? { ok: true, stdout: '[]', stderr: '', code: 0 }
    : { ok: true, stdout: 'No skills discovered.\n', stderr: '', code: 0 };
  const result = await inspectGeminiIntegration({ exec, home, skillVersions: { nav2: '1.1.0' } });
  assert.equal(result.state, 'inactive');
  assert.equal(result.apiAvailable, true);
  await rm(base, { recursive: true, force: true });
});
