export const STANDARD_APP_VERBS = [
  ['help', 'Show commands and examples'],
  ['doctor', 'Diagnose prerequisites and conflicts'],
  ['build', 'Build application artifacts'],
  ['run', 'Run the primary application experience'],
  ['status', 'Show whether the application is running'],
  ['logs', 'Follow application logs'],
  ['stop', 'Stop the application'],
];

export function normalizeVerb(value) {
  if (typeof value === 'string' && value.length > 0) {
    return { command: value, summary: undefined };
  }
  if (value && typeof value === 'object' && typeof value.command === 'string' && value.command.length > 0) {
    return {
      command: value.command,
      summary: typeof value.summary === 'string' && value.summary.length > 0
        ? value.summary
        : undefined,
    };
  }
  return null;
}

export function getAppVerb(app, name) {
  const declared = normalizeVerb(app.verbs?.[name]);
  if (declared) return declared;
  if (name === 'run' && typeof app.runtime?.entrypoint === 'string') {
    return { command: app.runtime.entrypoint, summary: undefined };
  }
  return null;
}
