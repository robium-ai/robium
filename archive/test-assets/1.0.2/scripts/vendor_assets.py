#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "huggingface_hub>=0.24"]
# ///
"""vendor_assets.py — manifest-driven test-asset fetcher/refresher.

Reads a MANIFEST.yaml (schema: the test-assets skill's
references/test-assets-layout.md), fetches each entry into place, and prints
a per-asset and total size summary. Idempotent: re-fetching an unchanged
pinned revision converges to the same bytes.

  uv run vendor_assets.py --manifest test-assets/MANIFEST.yaml
  uv run vendor_assets.py --manifest ... --only tb3_house
  uv run vendor_assets.py --manifest ... --check

Kinds: github (sparse checkout of subpath at a commit), fuel (gz fuel
download of a world/model plus optional deps), hf-dataset (snapshot of a
dataset, optionally sliced via allow_patterns). Requires: git; gz CLI for
fuel entries; network.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def sh(cmd: list[str], cwd: Path | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout.strip()


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def fetch_github(entry: dict, dest: Path) -> str:
    """Sparse-checkout entry['subpath'] at entry['revision']; returns resolved sha."""
    with tempfile.TemporaryDirectory() as td:
        sh(["git", "clone", "--filter=blob:none", "--no-checkout", "--quiet",
            entry["upstream"], td])
        sh(["git", "sparse-checkout", "set", entry["subpath"]], cwd=Path(td))
        sh(["git", "checkout", "--quiet", entry["revision"]], cwd=Path(td))
        sha = sh(["git", "rev-parse", "HEAD"], cwd=Path(td))
        src = Path(td) / entry["subpath"]
        if not src.exists():
            raise RuntimeError(f"subpath not found after checkout: {entry['subpath']}")
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / src.name)
        return sha


def fetch_fuel(entry: dict, dest: Path) -> str:
    """gz fuel download the asset (and deps) into the local cache, then copy."""
    if shutil.which("gz") is None:
        raise RuntimeError("fuel entry requires the gz CLI (install gz-sim tools)")
    uris = [entry["upstream"], *entry.get("deps", [])]
    for uri in uris:
        sh(["gz", "fuel", "download", "-u", uri])
    cache = Path.home() / ".gz" / "fuel"
    # cache layout mirrors the URI host/owner/collection/name; find by name
    name = entry["upstream"].rstrip("/").split("/")[-1]
    hits = sorted((h for h in cache.rglob(name) if h.is_dir()),
                  key=lambda p: len(str(p)))
    if not hits:
        raise RuntimeError(f"downloaded but not found in cache: {name}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(hits[0], dest)
    return str(entry.get("revision", "latest-at-fetch"))


def fetch_hf_dataset(entry: dict, dest: Path) -> str:
    from huggingface_hub import snapshot_download
    dest.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=entry["upstream"].removeprefix("https://huggingface.co/datasets/"),
        repo_type="dataset",
        revision=entry.get("revision") or None,
        allow_patterns=entry.get("allow_patterns") or None,
        local_dir=dest,
    )
    return str(entry.get("revision", "default-at-fetch"))


FETCHERS = {"github": fetch_github, "fuel": fetch_fuel, "hf-dataset": fetch_hf_dataset}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", default="test-assets/MANIFEST.yaml")
    ap.add_argument("--only", help="fetch a single entry by name")
    ap.add_argument("--check", action="store_true",
                    help="verify entries exist on disk; no fetching")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 1
    entries = yaml.safe_load(manifest_path.read_text())
    if not isinstance(entries, list) or not entries:
        print("manifest must be a non-empty list of entries", file=sys.stderr)
        return 1
    root = manifest_path.parent

    failures, total = 0, 0
    for entry in entries:
        name = entry.get("name", "<unnamed>")
        if args.only and name != args.only:
            continue
        dest = root / entry["path"]
        if args.check:
            ok = dest.is_dir() and any(dest.iterdir()) or dest.is_file()
            pinned = entry.get("revision") not in (None, "", "main", "master",
                                                  "PIN-AT-ADOPTION")
            status = "ok" if (ok and pinned) else ("MISSING" if not ok else "UNPINNED")
            print(f"  {name:30s} {status}")
            failures += 0 if status == "ok" else 1
            continue
        kind = entry.get("kind")
        if kind not in FETCHERS:
            print(f"  {name:30s} FAILED: unknown kind {kind!r}", file=sys.stderr)
            failures += 1
            continue
        try:
            resolved = FETCHERS[kind](entry, dest)
            size = dir_size(dest) if dest.is_dir() else dest.stat().st_size
            total += size
            print(f"  {name:30s} {human(size):>10s}  @ {resolved}")
        except Exception as e:  # keep going; report at end
            print(f"  {name:30s} FAILED: {e}", file=sys.stderr)
            failures += 1

    if not args.check:
        print(f"  {'TOTAL':30s} {human(total):>10s}")
    if failures:
        print(f"{failures} entr{'y' if failures == 1 else 'ies'} failed",
              file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
