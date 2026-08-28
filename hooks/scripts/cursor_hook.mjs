#!/usr/bin/env node
/** Cursor hook adapter: normalize native events and invoke capture fail-open. */
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const handlers = {
  'user-prompt-submit': ['user_prompt_submit.py', 'UserPromptSubmit'],
  'post-tool-use': ['post_tool_use.py', 'PostToolUse'],
  'session-start': ['session_start.py', 'SessionStart'],
  'session-end': ['session_end.py', 'SessionEnd'],
};

function readInput() {
  let input = '';
  process.stdin.setEncoding('utf8');
  return new Promise((resolve) => {
    process.stdin.on('data', (chunk) => { input += chunk; });
    process.stdin.on('end', () => {
      try { resolve(JSON.parse(input || '{}')); } catch { resolve({}); }
    });
    process.stdin.resume();
  });
}

function normalizedEvent(event, canonicalName) {
  const cwd = event.cwd
    || (Array.isArray(event.workspace_roots) && event.workspace_roots[0])
    || process.cwd();
  const result = {
    ...event,
    hook_event_name: canonicalName,
    cwd,
    session_id: event.session_id || event.conversation_id || '',
  };
  if (canonicalName === 'PostToolUse') {
    result.tool_name = 'Bash';
    result.tool_input = { command: event.command || '' };
    result.tool_response = { output: event.output || '' };
  }
  return result;
}

function invokePython(script, payload) {
  const candidates = [
    ['python3', []],
    ['python', []],
    ['py', ['-3']],
  ];
  for (const [command, prefix] of candidates) {
    const result = spawnSync(command, [...prefix, script], {
      input: JSON.stringify(payload),
      encoding: 'utf8',
      windowsHide: true,
      timeout: 4000,
    });
    if (!result.error || result.error.code !== 'ENOENT') return;
  }
}

const action = process.argv[2];
try {
  const selected = handlers[action];
  const event = await readInput();
  if (selected) {
    const [scriptName, canonicalName] = selected;
    invokePython(join(dirname(fileURLToPath(import.meta.url)), scriptName), normalizedEvent(event, canonicalName));
  }
} catch {
  // Learning capture must never interrupt the host session.
}

process.stdout.write(action === 'user-prompt-submit' ? '{"continue":true}\n' : '{}\n');
