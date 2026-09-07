import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseFrontmatter, buildCatalog } from '../scripts/build-catalog.mjs';

const testDir = path.dirname(fileURLToPath(import.meta.url));
const fixtures = path.join(testDir, 'fixtures');
const repoRoot = path.resolve(testDir, '..', '..');

test('parseFrontmatter: folded scalar joins lines with spaces', () => {
  const fm = parseFrontmatter(
    '---\nname: x\ndescription: >\n  line one\n  line two\n---\nbody');
  assert.equal(fm.name, 'x');
  assert.equal(fm.description, 'line one line two');
});

test('parseFrontmatter: plain scalar', () => {
  const fm = parseFrontmatter('---\nname: y\ndescription: hello there\n---\n');
  assert.equal(fm.description, 'hello there');
});

test('parseFrontmatter: throws without a frontmatter block', () => {
  assert.throws(() => parseFrontmatter('# no frontmatter'));
});

test('buildCatalog: reads fixture skills, sorted, template-less dirs skipped', async () => {
  const catalog = await buildCatalog(fixtures);
  assert.deepEqual(catalog.skills.map((s) => s.name), ['alpha', 'beta']);
  const alpha = catalog.skills[0];
  assert.match(alpha.description, /^A folded-scalar description that spans multiple indented lines/);
  assert.equal(catalog.skills[1].description, 'Plain single-line description.');
  assert.ok(catalog.skills.every((skill) => Object.keys(skill).sort().join(',') === 'description,name'));
});

test('buildCatalog: rejects a frontmatter name that differs from its directory', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'robium-catalog-'));
  const skill = path.join(root, 'skills', 'right-name');
  await mkdir(skill, { recursive: true });
  await writeFile(path.join(skill, 'SKILL.md'), '---\nname: wrong-name\ndescription: test\n---\nbody\n');
  await assert.rejects(buildCatalog(root), /name must match its directory/);
  await rm(root, { recursive: true, force: true });
});

test('buildCatalog: rejects retired skill metadata', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'robium-catalog-'));
  const skill = path.join(root, 'skills', 'sample');
  await mkdir(skill, { recursive: true });
  await writeFile(
    path.join(skill, 'SKILL.md'),
    '---\nname: sample\ndescription: test\nversion: 1.0.0\n---\nbody\n',
  );
  await assert.rejects(buildCatalog(root), /only name and description/);
  await rm(root, { recursive: true, force: true });
});

test('committed catalog matches live skill frontmatter', async () => {
  const built = await buildCatalog(repoRoot);
  const committed = JSON.parse(await readFile(path.join(repoRoot, 'cli', 'src', 'catalog.json'), 'utf8'));
  assert.deepEqual(committed, built);
});
