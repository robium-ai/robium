// Locate the robium plugin in `claude plugin list --json` output.
//
// Claude Code emits entries shaped { id: "robium@robium", enabled: true, ... }
// — the id is `name@marketplace`. Earlier code matched the bare token
// `"robium"`, which never appears in that JSON, so a correctly-installed plugin
// read as missing (both install's verify step and doctor). Match the plugin
// *name* (the part before `@`) to avoid false positives like `robium-x@y`.
export function findRobiumPlugin(stdout) {
  let plugins;
  try {
    plugins = JSON.parse(stdout);
  } catch {
    return null;
  }
  if (!Array.isArray(plugins)) return null;
  return plugins.find((p) => typeof p?.id === 'string' && p.id.split('@')[0] === 'robium') ?? null;
}
