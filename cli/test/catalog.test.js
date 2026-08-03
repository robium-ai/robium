import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFrontmatter, buildCatalog } from '../scripts/build-catalog.mjs';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');

test('parseFrontmatter: folded scalar joins lines with spaces', () => {
  const fm = parseFrontmatter(
    '---\nname: x\nversion: 1.0.0\ndescription: >\n  line one\n  line two\n---\nbody');
  assert.equal(fm.name, 'x');
  assert.equal(fm.version, '1.0.0');
  assert.equal(fm.description, 'line one line two');
});

test('parseFrontmatter: plain scalar and extra keys', () => {
  const fm = parseFrontmatter('---\nname: y\nversion: 2.0.0\ndescription: hello there\ncompatibility: z\n---\n');
  assert.equal(fm.description, 'hello there');
  assert.equal(fm.compatibility, 'z');
});

test('parseFrontmatter: throws without a frontmatter block', () => {
  assert.throws(() => parseFrontmatter('# no frontmatter'));
});

test('buildCatalog: reads fixture skills, sorted, template-less dirs skipped', async () => {
  const catalog = await buildCatalog(fixtures);
  assert.deepEqual(catalog.skills.map((s) => s.name), ['alpha', 'beta']);
  const alpha = catalog.skills[0];
  assert.equal(alpha.version, '1.2.3');
  assert.match(alpha.description, /^A folded-scalar description that spans multiple indented lines/);
  assert.equal(catalog.skills[1].description, 'Plain single-line description.');
});
