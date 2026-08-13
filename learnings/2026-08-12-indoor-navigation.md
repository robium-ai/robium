- [foxglove] figured-out-from-scratch <!-- id: lrn-0812-01 -->
  symptom: The bundled Lichtblick browser viewer needs a reusable custom control panel, but the desktop-oriented `local-install` guidance writes to `~/.lichtblick-suite/extensions` and does not explain how the web build receives extensions.
  root-cause: Lichtblick's web build uses `IdbExtensionLoader("local")`; its file handler accepts `.foxe` files and installs them into browser IndexedDB, while `local-install` targets the desktop filesystem loader.
  fix: Build/package the panel with the official `create-lichtblick-extension` tool, then drag/open the `.foxe` once in the bundled web viewer; keep a custom Lichtblick build only as the later zero-install deployment option. (check: direct source inspection at Lichtblick commit `64357108ce49764732f53183d89f363d57d50502`; `.foxe` archive and compiled bundle runtime verified, live viewer exposed the expected custom-panel slot, but automated browser file-picker installation remained unavailable)
  dead-ends: Treating the generator's `local-install` command as sufficient for the embedded web viewer (it targets the desktop extension directory, not browser IndexedDB).
  anchors: foxglove#custom-panels
  source: official `create-lichtblick-extension` README/examples at `e503b8eb63b099f9c7024d3aa6605db1240332df`; Lichtblick `WebRoot.tsx`, `IdbExtensionLoader.ts`, and `useHandleFiles.tsx` at `64357108ce49764732f53183d89f363d57d50502`

- [foxglove] wrong-stale-guidance (seen 3x) <!-- id: lrn-0812-02 -->
  symptom: The current official extension example could not install/build cleanly with npm, and its generated `pretest` script printed CLI help instead of running tests: `peer eslint@"^9.38.0" from @lichtblick/eslint-plugin@2.0.8` while the example pins `eslint@10.7.0`; `lichtblick-extension pretest` is not a command in generator 1.1.0; the build also failed with `Can't resolve 'style-loader'` because the template omits direct CSS loader dependencies.
  root-cause: The example package metadata has drifted out of sync with the plugin peer range and the generator CLI's available commands.
  fix: Pin ESLint 9.38.0 for `@lichtblick/eslint-plugin` 2.0.8, use the plugin's shipped flat configs, define the extension's test command directly without the invalid `pretest` hook, and add direct `style-loader`/`css-loader` development dependencies. (check: clean `npm ci`; 18 extension tests, lint, development/production builds, `.foxe` packaging, archive-entry inspection, and compiled-bundle DOM runtime all pass)
  dead-ends: Copying the example's dependency and script block verbatim.
  anchors: foxglove#custom-panels
  source: npm resolver output and direct `lichtblick-extension` 1.1.0 CLI output on 2026-08-12

## End-of-block retro (2026-08-12, reusable Lichtblick Robot Control extension)

- [foxglove] fired ✓ · accurate ✓ (bridge placement, browser visualization, Twist teleop, and ROS-side safety boundary all held in the live stack) · complete − (web `.foxe` drag/open installation and current generator/template drift required direct upstream source inspection) · lean ✓
- [testing] fired ✓ · accurate ✓ (failure-first pure logic, DOM behavior, layout contract, packaged-bundle runtime, and live ROS data-flow checks caught real integration issues) · complete ✓ · lean ✓
