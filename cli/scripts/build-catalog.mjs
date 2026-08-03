// Regenerates src/catalog.json from the robium plugin (this monorepo's root).
// Run before every publish (from the cli/ dir): npm run build:catalog [-- /path/to/robium]
import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Minimal frontmatter reader for the fields the catalog needs. Handles plain
// scalars and folded scalars (`description: >` + indented lines), the two
// shapes robium actually uses. Not a general YAML parser.
export function parseFrontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) throw new Error('no frontmatter block');
  const out = {};
  let key = null;
  let buf = [];
  const flush = () => {
    if (key) out[key] = buf.join(' ').replace(/\s+/g, ' ').trim();
    key = null;
    buf = [];
  };
  for (const line of m[1].split(/\r?\n/)) {
    const kv = /^(\w[\w-]*):\s*(.*)$/.exec(line);
    if (kv) {
      flush();
      const val = kv[2].trim();
      if (val === '>' || val === '>-' || val === '|' || val === '|-') {
        key = kv[1]; // folded/literal scalar: accumulate indented lines
      } else {
        out[kv[1]] = val.replace(/^['"]|['"]$/g, '');
      }
    } else if (key && /^\s+\S/.test(line)) {
      buf.push(line.trim());
    }
  }
  flush();
  return out;
}

export async function buildCatalog(pluginDir) {
  const skillsDir = path.join(pluginDir, 'skills');
  const entries = await readdir(skillsDir, { withFileTypes: true });
  const skills = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    let text;
    try {
      text = await readFile(path.join(skillsDir, e.name, 'SKILL.md'), 'utf8');
    } catch {
      continue; // no SKILL.md (e.g. _TEMPLATE), so not an installable skill
    }
    const fm = parseFrontmatter(text);
    if (!fm.name || !fm.version || !fm.description) {
      throw new Error(`skills/${e.name}/SKILL.md missing name/version/description`);
    }
    skills.push({ name: fm.name, version: fm.version, description: fm.description });
  }
  skills.sort((a, b) => a.name.localeCompare(b.name));
  return { source: 'robium-ai/robium', skills };
}

const selfDir = path.dirname(fileURLToPath(import.meta.url));

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const pluginDir =
    process.argv[2] ??
    process.env.ROBIUM_PLUGIN_DIR ??
    path.resolve(selfDir, '..', '..');
  const catalog = await buildCatalog(pluginDir);
  const outPath = path.resolve(selfDir, '..', 'src', 'catalog.json');
  await writeFile(outPath, `${JSON.stringify(catalog, null, 2)}\n`);
  console.log(`Wrote ${catalog.skills.length} skills to ${outPath} (from ${pluginDir})`);
}
