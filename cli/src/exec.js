import { execFile } from 'node:child_process';

// Uniform command runner: never throws, never rejects. A missing binary,
// non-zero exit, or timeout all come back as { ok: false }.
export function run(cmd, args = [], { timeout = 10_000 } = {}) {
  return new Promise((resolve) => {
    execFile(cmd, args, { timeout, encoding: 'utf8' }, (err, stdout, stderr) => {
      resolve({
        ok: !err,
        code: err ? (typeof err.code === 'number' ? err.code : 1) : 0,
        stdout: stdout ?? '',
        stderr: stderr ?? '',
      });
    });
  });
}
