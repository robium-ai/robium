#!/usr/bin/env node
/** Gemini CLI hook adapter: normalize host events and invoke capture fail-open. */
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
  try {
    let input = '';
    process.stdin.setEncoding('utf8');
    return new Promise((resolve) => {
      process.stdin.on('data', (chunk) => { input += chunk; });
      process.stdin.on('end', () => {
        try { resolve(JSON.parse(input || '{}')); } catch { resolve({}); }
      });
      process.stdin.resume();
    });
  } catch {
    return Promise.resolve({});
  }
}

function normalizedEvent(event, canonicalName) {
  const result = {
    ...event,
    hook_event_name: canonicalName,
    cwd: event.cwd || process.env.GEMINI_CWD || process.env.GEMINI_PROJECT_DIR || process.cwd(),
    session_id: event.session_id || process.env.GEMINI_SESSION_ID || '',
  };
  if (canonicalName === 'PostToolUse') {
    result.tool_name = event.tool_name === 'run_shell_command' ? 'Bash' : event.tool_name;
    result.tool_response = event.tool_response && typeof event.tool_response === 'object'
      ? { ...event.tool_response, output: JSON.stringify(event.tool_response) }
      : event.tool_response;
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

try {
  const selected = handlers[process.argv[2]];
  const event = await readInput();
  if (selected) {
    const [scriptName, canonicalName] = selected;
    invokePython(join(dirname(fileURLToPath(import.meta.url)), scriptName), normalizedEvent(event, canonicalName));
  }
} catch {
  // Learning capture must never interrupt the host session.
}

process.stdout.write('{}\n');
