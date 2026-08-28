import { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

// Scaffold by copying the closest shipped app (the REGISTRY.md "Bootstrap
// for" rule), never from abstract templates. Build/state artifacts are
// excluded; everything else comes across verbatim for the new app to diverge.

const EXCLUDE = new Set([
  '.venv', 'outputs', 'node_modules', '__pycache__', '.pytest_cache',
  'build', 'install', 'log', 'bags', '.DS_Store',
]);

function articleStarter(id) {
  const today = new Date().toISOString().slice(0, 10);
  return `---
title: TODO - a natural headline about the result or decision
summary: TODO - one compact sentence that adds context to the headline
collection: blog
category: article
kind: engineering-story
voice: product-lab
author: Robium team
audience: robotics-developer
level: intermediate
app: ${id}
date: ${today}
tested: ${today}
tags: []
hero:
hero_alt:
social_image:
featured: false
---

<!-- Replace this starter after the application has a real result. Write like
someone who built it: direct, specific, restrained, and without em dashes. -->

Open on the result, tension, or decision that belongs to this project.

## Why this approach fit

TODO: explain the task, constraints, alternatives, and decision.

## How the pieces connect

TODO: add a small system diagram and explain only the boundaries that matter.

## Try the tested path

TODO: include one short quick start and state the expected visible result.

## What happened in the run

TODO: state the scenario, conditions, and result in plain language.

## Where Robium changed the build

TODO: name one or two decisions, tests, or fixes that came from the skills.

## Limits

TODO: state what remains simulated, expensive, narrow, or untested.
`;
}

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

  // Application code benefits from a close reference app; editorial prose
  // does not. Replace any copied case study with a clean, ID-safe starter so a
  // new public article cannot accidentally retain the source app's claims.
  const docsDir = path.join(dst, 'docs');
  mkdirSync(docsDir, { recursive: true });
  writeFileSync(path.join(docsDir, 'case-study.md'), articleStarter(id));

  log(`Scaffolded ${id} from ${from} at ${dst}\n`);
  log('Next steps (an app is not done until these are done):');
  log('  1. Run the robium-architect agent to write docs/architecture-brief.md for the NEW problem');
  log('  2. Rewrite robium-app.yaml summary/tags/modes as the app diverges');
  log(`  3. Rename source packages/modules copied from ${from}`);
  log('  4. Make `make smoke` mean something for this app, then keep it green');
  log('  5. Add the REGISTRY.md quick-index row + card IN THE SAME COMMIT as the app');
  log('  6. Replace docs/case-study.md TODOs with verified results and real media');
  return 0;
}
