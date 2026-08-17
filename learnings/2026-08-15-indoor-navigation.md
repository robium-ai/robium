# Indoor navigation learnings — 2026-08-15

- [test-assets] worked-as-documented <!-- id: lrn-0815-01 -->
  symptom: The shared catalog needed an honest redistribution and reuse policy for the selected Tugbot Warehouse world.
  fix: Followed the canonical-assets instruction to re-read the live license at adoption time; Fuel metadata identifies version 2 as CC BY-NC-ND 4.0, so the asset remains pointer-only and the app/catalog surface its non-commercial, no-derivatives restriction. (check: live Fuel metadata plus the exact version-2 zip were fetched on 2026-08-15; SHA-256 `22af262814fe01326723b4e21457869470d1d3aaa10db7abc47e3536d13adfbb` and `tugbot_warehouse.sdf` entrypoint verified.)
  anchors: test-assets#never-write-asset-facts-from-memory, test-assets#choose-sourcing-mode-deliberately
  source: https://fuel.gazebosim.org/1.0/OpenRobotics/worlds/Tugbot%20in%20Warehouse

## Shared-assets policy retro

- test-assets — fired: yes; accurate: yes for choosing pointer versus vendored storage, requiring provenance manifests, and treating derived maps as explicit promotions; complete: yes for the current repository-local policy; lean: yes.

- [none] figured-out-from-scratch <!-- id: lrn-0815-02 -->
  symptom: The website build failed with `fetch-apps: indoor-navigation/robium-app.yaml: line 58: expected "key: value", got "- world.aws-small-house"`, and the same manifest could not be parsed by the zero-dependency Robium CLI parser.
  root-cause: The shared-assets change wrote `assets.worlds` as a YAML block sequence, but the documented `robium-app.yaml` subset accepts inline arrays only.
  fix: Expressed the unchanged world IDs as `worlds: [world.aws-small-house, world.tugbot-warehouse]`. (check: both asset IDs parsed as an array through the website's vendored `parseAppYaml` implementation.)
  dead-ends: Extending only the website parser would drift it from the CLI parser and leave `robium app` unable to read the same manifest.
  anchors: robium-app.yaml parser contract, app manifest validation
