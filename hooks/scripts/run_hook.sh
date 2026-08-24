#!/bin/sh
# Portable, fail-open interpreter selection for plugin hook entry points.

script_path=${1:-}
if [ -z "$script_path" ]; then
  exit 0
fi

if [ ! -f "$script_path" ]; then
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_path"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$script_path"
fi
if command -v py >/dev/null 2>&1; then
  exec py -3 "$script_path"
fi

exit 0
