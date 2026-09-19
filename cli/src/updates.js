import path from 'node:path';
import { homedir } from 'node:os';
import { existsSync } from 'node:fs';
import { run } from './exec.js';
import { validateCheckout } from './repo.js';
import { REPOSITORIES, findWorkspace, readWorkspaceConfig, saveWorkspaceConfig } from './workspace.js';

const DAY = 24 * 60 * 60 * 1000;
const UPSTREAM_REF = 'refs/robium/upstream-main';

// origin may be a user's fork. Check official main without changing their
// branches, index, worktree, or FETCH_HEAD. Never run a shell or Git reset.
export async function inspectRepository({ repo, spec, exec = run, apply = false, quiet = false }) {
  try {
    await validateCheckout(repo, spec, exec);
    const git = async (...args) => {
      const result = await exec('git', ['-C', repo, ...args], { timeout: quiet ? 4_000 : 60_000 });
      if (!result.ok) throw new Error(`Git ${args[0]} failed; check connectivity and repository state.`);
      return result.stdout.trim();
    };
    await git('fetch', '--no-tags', '--no-write-fetch-head', spec.url, `+refs/heads/main:${UPSTREAM_REF}`);
    const branch = await git('rev-parse', '--abbrev-ref', 'HEAD');
    const dirty = Boolean(await git('status', '--porcelain'));
    let inProgress = false;
    for (const marker of ['MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'sequencer']) {
      const markerPath = await git('rev-parse', '--git-path', marker);
      if (existsSync(path.resolve(repo, markerPath))) inProgress = true;
    }
    const head = await git('rev-parse', 'HEAD');
    const upstream = await git('rev-parse', UPSTREAM_REF);
    const counts = await git('rev-list', '--left-right', '--count', `HEAD...${UPSTREAM_REF}`);
    const [ahead, behind] = counts.split(/\s+/).map(Number);
    if (!Number.isInteger(ahead) || !Number.isInteger(behind)) throw new Error('Cannot compare checkout with official main.');
    const reason = inProgress ? 'Git operation in progress; finish or abort it yourself'
      : branch !== 'main' ? `on ${branch}; switch branches yourself when ready`
      : dirty ? 'uncommitted changes; commit or stash them yourself'
        : ahead ? 'local commits differ from official main; review and merge explicitly' : null;
    const result = { name: spec.name, path: repo, branch, dirty, head, upstream, ahead, behind,
      status: behind ? 'available' : 'current', reason };
    if (apply && reason) return { ...result, status: 'skipped' };
    if (apply && behind) {
      if (await git('rev-parse', 'HEAD') !== head || await git('rev-parse', '--abbrev-ref', 'HEAD') !== 'main' || await git('status', '--porcelain')) {
        return { ...result, status: 'skipped', reason: 'checkout changed during update; review before retrying' };
      }
      await git('merge', '--ff-only', UPSTREAM_REF);
      return { ...result, status: 'updated', head: upstream, behind: 0 };
    }
    return result;
  } catch (e) { return { name: spec.name, path: repo, status: 'unknown', reason: e.message }; }
}

export async function updateWorkspace({
  dir, cwd = process.cwd(), home = homedir(), exec = run, check = false,
  quiet = false, json = false, env = process.env, now = Date.now(), log = console.log,
} = {}) {
  if (quiet && !check) { log('--quiet is only supported with update --check.'); return 1; }
  try {
    if (quiet && env.ROBIUM_UPDATE_CHECKS === '0') return 0;
    const workspace = findWorkspace({ dir, cwd, home });
    if (!workspace) {
      if (!quiet) log('No workspace configured. Run npx robium-ai setup first, or pass --dir <workspace>.');
      return quiet ? 0 : 1;
    }
    const config = readWorkspaceConfig(home) ?? { root: workspace.root };
    const previous = config.checks?.[workspace.root] ?? {};
    if (quiet && previous.checkedAt && now - previous.checkedAt < DAY) return 0;
    const results = await Promise.all(REPOSITORIES.map(spec => inspectRepository({
      repo: path.join(workspace.root, spec.name), spec, exec, apply: !check, quiet,
    })));
    const available = results.filter(r => r.behind > 0);
    const unseen = available.filter(r => previous.notified?.[r.name] !== r.upstream);
    const notify = quiet && unseen.length > 0 &&
      (!previous.notifiedAt || now - previous.notifiedAt >= 7 * DAY);
    const next = { ...previous, checkedAt: now, results };
    if (notify) {
      next.notified = { ...previous.notified, ...Object.fromEntries(unseen.map(r => [r.name, r.upstream])) };
      next.notifiedAt = now;
    }
    await saveWorkspaceConfig({ ...config, checks: { ...config.checks, [workspace.root]: next } }, home);
    if (json) log(JSON.stringify({ workspace, checkedAt: now, results }, null, 2));
    else if (quiet) {
      if (notify) log(`Robium updates available for ${unseen.map(r => r.name).join(' and ')}. Working files unchanged. Run npx robium-ai update when convenient (workspace: ${workspace.root}).`);
    } else {
      log(`Workspace: ${workspace.root}`);
      for (const r of results) log(`${r.name}: ${r.status}${r.behind ? ` (${r.behind} upstream commits)` : ''}${r.reason ? ` — ${r.reason}` : ''}\n  ${r.path}`);
      if (check && available.length) log('Nothing changed. Run npx robium-ai update when ready; only clean main branches are fast-forwarded.');
    }
    return quiet ? 0 : results.some(r => ['unknown', 'skipped'].includes(r.status)) ? 1 : 0;
  } catch (e) {
    if (!quiet) log(`Cannot inspect workspace: ${e.message}`);
    return quiet ? 0 : 1;
  }
}
