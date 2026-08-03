import { readFile } from 'node:fs/promises';

const CATALOG_URL = new URL('./catalog.json', import.meta.url);

export function firstSentence(text, max = 120) {
  const cut = text.indexOf('. ');
  const s = cut !== -1 && cut < max ? text.slice(0, cut + 1) : text;
  return s.length > max ? `${s.slice(0, max - 1).trimEnd()}…` : s;
}

export async function skills({ query, log = console.log, catalogPath } = {}) {
  const raw = await readFile(catalogPath ?? CATALOG_URL, 'utf8');
  const { skills: list } = JSON.parse(raw);

  const q = query?.toLowerCase();
  const hits = q
    ? list.filter((s) => `${s.name} ${s.description}`.toLowerCase().includes(q))
    : list;

  if (hits.length === 0) {
    log(`No skills match "${query}".`);
    return 1;
  }

  const w = Math.max(...hits.map((s) => s.name.length));
  for (const s of hits) {
    log(`${s.name.padEnd(w)}  ${s.version.padEnd(7)}  ${firstSentence(s.description)}`);
  }
  log(`\n${hits.length} of ${list.length} skills. Install with: npx robium-ai install`);
  return 0;
}
