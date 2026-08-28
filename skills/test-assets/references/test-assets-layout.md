# The standard test-assets layout

Use one small catalog plus one manifest directory per asset. Pointer mode is
the default for large worlds, models, and datasets: Git owns metadata and
license evidence, while an ignored cache holds downloaded bytes.

## Layout

    test-assets/
      README.md
      catalog.yaml
      scripts/fetch_assets.py
      worlds/
        example-world/
          asset.yaml
          LICENSE
      cache/                 # ignored in pointer mode
      datasets/              # per-asset manifests follow the same pattern
      bags/                  # seeded project recordings, not arbitrary downloads
      goldens/               # tolerance-band outputs from verified scenarios

## Catalog schema

    schema_version: "1"
    assets:
      - id: world.example
        kind: world
        name: Example World
        storage: pointer
        manifest: worlds/example-world/asset.yaml

IDs are stable and names are human-facing. The resolver verifies that the
catalog and manifest agree on `id`, `kind`, `name`, and `storage`.

## Per-asset manifest schema

    schema_version: "1"
    id: world.example
    kind: world
    name: Example World
    revision: "1"           # local schema revision
    storage: pointer
    license:
      id: SPDX-ID
      file: LICENSE          # checked-in evidence beside asset.yaml
      url: https://upstream.example/license
    verification:
      date: "2026-08-27"
      method: Clean-cache archive fetch, SHA-256, entrypoint, and license check.
    source:
      type: git-archive
      repository: https://upstream.example/project
      revision: immutable-upstream-revision
      url: https://upstream.example/archive.tar.gz
      sha256: 64-lowercase-hex-characters
      archive: tar.gz        # tar.gz | zip
      strip_prefix: project-revision
    entrypoints:
      world: worlds/example.world

Rules:

- Pin an immutable upstream revision and the exact archive SHA-256. A branch,
  `latest`, or download URL without a checksum is not a pointer lock.
- Keep a license record next to every manifest. Compare it with the pinned
  upstream source at adoption time; restrictive assets remain pointer-only.
- Record the verification date and concrete method. A clean-cache fetch must
  validate safe extraction and every declared entrypoint.
- Do not add a fixture without an active application or test consumer.
- Vendored mode may commit bytes only under a documented size budget and with
  redistribution terms that permit it.

## Dataset slices and goldens

- Take deterministic slices, such as the first N episodes, and record N and
  the source revision. Confirm the reduced dataset still loads.
- Compare simulated goldens with explicit tolerances and seeds. Exact byte
  checks apply only to pure replay, not re-run physics.
