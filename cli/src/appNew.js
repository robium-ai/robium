import { cpSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

// Scaffold by copying the closest shipped app (the REGISTRY.md "Bootstrap
// for" rule), never from abstract templates. Build/state artifacts are
// excluded; everything else comes across verbatim for the new app to diverge.

const EXCLUDE = new Set([
  '.venv', 'outputs', 'node_modules', '__pycache__', '.pytest_cache',
  'build', 'install', 'log', 'bags', '.DS_Store',
]);

export function scaffoldApp({ appsDir, id, from, log = console.log }) {
  if (!id || !/^[a-z0-9][a-z0-9-]*$/.test(id)) {
    log(`Invalid app id "${id ?? ''}": use lowercase letters, digits, and dashes.`);
    return 1;
  }
  if (!from) {
    log('Missing --from <existing-app-id>: scaffolding copies the closest shipped app (see REGISTRY.md "Bootstrap for").');
    return 1;
  }
  const src = path.join(appsDir, from);
  const dst = path.join(appsDir, id);
  if (!existsSync(path.join(src, 'robium-app.yaml'))) {
    log(`Source app "${from}" not found (no ${from}/robium-app.yaml in ${appsDir}).`);
    return 1;
  }
  if (existsSync(dst)) {
    log(`Target "${id}" already exists at ${dst}.`);
    return 1;
  }

  cpSync(src, dst, {
    recursive: true,
    filter: (p) => !EXCLUDE.has(path.basename(p)),
  });

  // Reset the metadata contract for the new app; everything else is the
  // author's to rewrite as the app diverges.
  const yamlPath = path.join(dst, 'robium-app.yaml');
  let yaml = readFileSync(yamlPath, 'utf8');
  yaml = yaml
    .replace(/^id: .*$/m, `id: ${id}`)
    .replace(/^name: .*$/m, `name: ${id} (bootstrapped from ${from})`)
    .replace(/^summary: .*$/m, `summary: TODO - one-sentence outcome (bootstrapped from ${from}, rewrite me)`)
    .replace(/^version: .*$/m, 'version: 0.1.0')
    .replace(/^status: .*$/m, 'status: experimental');
  writeFileSync(yamlPath, yaml);

  log(`Scaffolded ${id} from ${from} at ${dst}\n`);
  log('Next steps (an app is not done until these are done):');
  log('  1. Run the robium-architect agent to write docs/architecture-brief.md for the NEW problem');
  log('  2. Rewrite robium-app.yaml summary/tags/scenarios as the app diverges');
  log(`  3. Rename source packages/modules copied from ${from}`);
  log('  4. Make `make smoke` mean something for this app, then keep it green');
  log('  5. Add the REGISTRY.md quick-index row + card IN THE SAME COMMIT as the app');
  return 0;
}
