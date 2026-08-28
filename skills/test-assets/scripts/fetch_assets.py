#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Fetch checksum-pinned pointer assets from a test-assets catalog."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

import yaml


def fail(message: str) -> ValueError:
    return ValueError(message)


def mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise fail(f"{label} must be a mapping")
    return value


def relative_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise fail(f"{label} must be a non-empty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise fail(f"{label} must be a safe relative path")
    return Path(*path.parts)


def load_catalog(path: Path) -> list[dict]:
    catalog = mapping(yaml.safe_load(path.read_text()), "catalog")
    if catalog.get("schema_version") != "1":
        raise fail("unsupported catalog schema_version")
    entries = catalog.get("assets")
    if not isinstance(entries, list) or not entries:
        raise fail("catalog assets must be a non-empty list")

    assets: list[dict] = []
    seen: set[str] = set()
    for entry_value in entries:
        entry = mapping(entry_value, "catalog asset")
        asset_id = str(entry.get("id", ""))
        if not asset_id or asset_id in seen:
            raise fail(f"missing or duplicate asset id: {asset_id!r}")
        seen.add(asset_id)
        manifest_path = path.parent / relative_path(entry.get("manifest"), "manifest")
        manifest = mapping(yaml.safe_load(manifest_path.read_text()), asset_id)
        for field in ("id", "kind", "name", "storage"):
            if manifest.get(field) != entry.get(field):
                raise fail(f"{asset_id}: catalog/manifest {field} mismatch")
        if manifest.get("storage") != "pointer":
            raise fail(f"{asset_id}: resolver accepts pointer assets only")
        if not asset_id.startswith(f"{entry.get('kind')}."):
            raise fail(f"{asset_id}: id prefix must match kind")

        license_data = mapping(manifest.get("license"), f"{asset_id}.license")
        if not license_data.get("id") or not license_data.get("url"):
            raise fail(f"{asset_id}: license id and upstream URL are required")
        license_path = manifest_path.parent / relative_path(
            license_data.get("file"), f"{asset_id}.license.file"
        )
        if not license_path.is_file():
            raise fail(f"{asset_id}: missing license evidence {license_path}")

        verification = mapping(manifest.get("verification"), f"{asset_id}.verification")
        if not verification.get("date") or not verification.get("method"):
            raise fail(f"{asset_id}: dated verification method is required")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(verification["date"])) is None:
            raise fail(f"{asset_id}: verification date must use YYYY-MM-DD")
        source = mapping(manifest.get("source"), f"{asset_id}.source")
        if not all(source.get(key) for key in ("repository", "revision", "url", "sha256", "archive")):
            raise fail(f"{asset_id}: source provenance is incomplete")
        digest = str(source["sha256"])
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise fail(f"{asset_id}: sha256 must be 64 lowercase hex characters")
        entrypoints = mapping(manifest.get("entrypoints"), f"{asset_id}.entrypoints")
        if not entrypoints:
            raise fail(f"{asset_id}: at least one entrypoint is required")
        manifest["_manifest_path"] = manifest_path
        assets.append(manifest)
    return assets


def safe_members(names: list[str]) -> None:
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise fail(f"unsafe archive member: {name}")


def fetch(asset: dict, destination: Path) -> None:
    asset_id = asset["id"]
    source = asset["source"]
    target = destination / asset_id
    with tempfile.TemporaryDirectory(prefix="robium-asset-") as temp_name:
        temp = Path(temp_name)
        archive_path = temp / "asset.archive"
        request = urllib.request.Request(source["url"], headers={"User-Agent": "robium-assets/1"})
        digest = hashlib.sha256()
        with urllib.request.urlopen(request) as response, archive_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        actual = digest.hexdigest()
        if actual != source["sha256"]:
            raise fail(f"{asset_id}: checksum mismatch: expected {source['sha256']}, got {actual}")

        extracted = temp / "extracted"
        extracted.mkdir()
        if source["archive"] == "tar.gz":
            with tarfile.open(archive_path, "r:gz") as archive:
                members = archive.getmembers()
                safe_members([member.name for member in members])
                if any(member.issym() or member.islnk() for member in members):
                    raise fail(f"{asset_id}: archive contains links")
                archive.extractall(extracted, members=members, filter="data")
        elif source["archive"] == "zip":
            with zipfile.ZipFile(archive_path) as archive:
                members = archive.infolist()
                safe_members([member.filename for member in members])
                if any(stat.S_ISLNK(member.external_attr >> 16) for member in members):
                    raise fail(f"{asset_id}: archive contains links")
                archive.extractall(extracted)
        else:
            raise fail(f"{asset_id}: unsupported archive {source['archive']!r}")

        root = extracted
        if source.get("strip_prefix"):
            root = extracted / relative_path(source["strip_prefix"], "strip_prefix")
        if not root.is_dir():
            raise fail(f"{asset_id}: strip_prefix not found")
        for label, value in asset["entrypoints"].items():
            if not (root / relative_path(value, f"entrypoint {label}")).is_file():
                raise fail(f"{asset_id}: missing entrypoint {label}: {value}")
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, target)
    print(f"{asset_id}: verified {source['sha256']} -> {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_ids", nargs="*")
    parser.add_argument("--catalog", type=Path, default=Path("test-assets/catalog.yaml"))
    parser.add_argument("--destination", type=Path, default=Path("test-assets/cache"))
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    try:
        assets = load_catalog(args.catalog)
        if args.list:
            print("\n".join(asset["id"] for asset in assets))
            return 0
        selected = set(args.asset_ids)
        unknown = selected - {asset["id"] for asset in assets}
        if unknown:
            raise fail(f"unknown asset ids: {', '.join(sorted(unknown))}")
        for asset in assets:
            if not selected or asset["id"] in selected:
                fetch(asset, args.destination)
        return 0
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
