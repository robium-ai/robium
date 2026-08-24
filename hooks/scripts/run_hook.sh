#!/bin/sh
# Portable, fail-open interpreter selection for plugin hook entry points.

script_name=${1:-}
if [ -z "$script_name" ]; then
  exit 0
fi

case "$0" in
  */*) script_dir=${0%/*} ;;
  *) script_dir=. ;;
esac
script_dir=$(CDPATH= cd -- "$script_dir" 2>/dev/null && pwd) || exit 0
script_path=$script_dir/$script_name
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
