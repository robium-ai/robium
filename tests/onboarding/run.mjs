// Opt-in native-host routing probes, not simulator bring-up tests.
// node tests/onboarding/run.mjs claude [case-id ...]
// node tests/onboarding/run.mjs codex [case-id ...]
// Uses the host's existing login/default model; consumes account usage.
// Writes transcripts only to a fresh temporary directory. Review against each
// case's rubric; exit 0 means host completion, NOT a semantic pass.
import { mkdtemp, mkdir, readdir, readFile, writeFile, symlink } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const root = fileURLToPath(new URL('../../', import.meta.url));
const [host, ...ids] = process.argv.slice(2);
if (!['claude', 'codex'].includes(host)) throw new Error('Choose claude or codex');
const all = JSON.parse(await readFile(new URL('./cases.json', import.meta.url), 'utf8'));
if (ids.some(id => !all.some(c => c.id === id))) throw new Error('Unknown case id');
const cases = all.filter(c => !ids.length || ids.includes(c.id));
const output = await mkdtemp(path.join(tmpdir(), `robium-routing-${host}-`));
console.log(`Transcripts: ${output}`);
const boundary = 'Read-only onboarding probe: loading skills and reading their linked instructions is allowed and does not authorize executing them. Inspect local guidance to decide the next concrete step, then stop before installing, writing, launching, fetching updates, or calling external services. Do not delegate. Do not read credentials or secrets.';
let failed = false;
for (const test of cases) {
  // Keep prior answers out of the workspace and its immediate parent listing.
  const cwd = await mkdtemp(path.join(tmpdir(), 'robium-probe-'));
  const digest = createHash('sha256');
  for (const name of (await readdir(path.join(root, 'skills'))).sort()) {
    try {
      digest.update(name).update(await readFile(path.join(root, 'skills', name, 'SKILL.md')));
    } catch (error) {
      if (!['ENOENT', 'ENOTDIR'].includes(error.code)) throw error;
    }
  }
  const skillsSha256 = digest.digest('hex');
  // Claude loads the real local plugin. Codex discovers the same source skills
  // natively in an isolated project, without changing the installed plugin.
  // This tests routing, not user-scope installation or plugin-cache refresh.
  if (host === 'codex') {
    await mkdir(path.join(cwd, '.agents'));
    await symlink(path.join(root, 'skills'), path.join(cwd, '.agents', 'skills'), 'dir');
  }
  const args = host === 'claude' ? [
    '--plugin-dir', root, '--setting-sources', '', '--strict-mcp-config',
    '--restricted', '--add-dir', root, path.resolve(root, '../robium-apps'),
    '--settings', '{"disableAllHooks":true}', '--tools', 'Read,Glob,Grep,Skill',
    '--allowedTools', 'Read,Glob,Grep,Skill', '--no-session-persistence',
    '--append-system-prompt', boundary, '--output-format', 'stream-json', '--verbose',
    '-p', test.prompt,
  ] : [
    'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
    '--sandbox', 'read-only', '--skip-git-repo-check', '--json',
    '-c', `developer_instructions=${JSON.stringify(boundary)}`, test.prompt,
  ];
  const result = await new Promise(resolve => {
    const child = spawn(host, args, { cwd, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '', timedOut = false;
    child.stdout.on('data', data => { stdout += data; });
    child.stderr.on('data', data => { stderr += data; });
    const timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); }, 120_000);
    child.on('error', error => { stderr += error.message; });
    child.on('close', code => { clearTimeout(timer); resolve({ code, timedOut, stdout, stderr }); });
  });
  await writeFile(path.join(output, `${test.id}.json`), JSON.stringify({
    host, cwd, skillsSha256, ...test, ...result,
  }, null, 2));
  failed ||= result.code !== 0 || result.timedOut;
  console.log(`${test.id}: ${result.timedOut ? 'TIMEOUT' : `exit ${result.code}`} — review ${test.id}.json`);
}
process.exitCode = failed ? 1 : 0;
