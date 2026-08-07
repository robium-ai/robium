import test from 'node:test';
import assert from 'node:assert/strict';
import { findCodexRobiumPlugin, findRobiumPlugin } from '../src/plugins.js';

// Regression: claude emits { id: "robium@robium", ... }; the earlier
// `.includes('"robium"')` check never matched this shape.
test('findRobiumPlugin matches the id@marketplace shape claude emits', () => {
  const p = findRobiumPlugin('[{"id":"robium@robium","enabled":true,"version":"0.2.0"}]');
  assert.ok(p);
  assert.equal(p.enabled, true);
});

test('findRobiumPlugin: other plugins present, no robium → null', () => {
  assert.equal(findRobiumPlugin('[{"id":"github@claude-plugins-official","enabled":true}]'), null);
  assert.equal(findRobiumPlugin('[]'), null);
});

test('findRobiumPlugin: does not false-match a different plugin name', () => {
  assert.equal(findRobiumPlugin('[{"id":"robium-extras@somewhere"}]'), null);
});

test('findRobiumPlugin: non-JSON or non-array → null', () => {
  assert.equal(findRobiumPlugin('not json'), null);
  assert.equal(findRobiumPlugin('{}'), null);
});

test('findCodexRobiumPlugin matches Codex plugin list JSON', () => {
  const p = findCodexRobiumPlugin('{"installed":[{"pluginId":"robium@robium","enabled":true}]}');
  assert.ok(p);
  assert.equal(p.enabled, true);
});

test('findCodexRobiumPlugin rejects malformed and unrelated payloads', () => {
  assert.equal(findCodexRobiumPlugin('not json'), null);
  assert.equal(findCodexRobiumPlugin('{"installed":[{"pluginId":"other@robium"}]}'), null);
});
