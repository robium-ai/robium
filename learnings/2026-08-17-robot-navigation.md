# Robot Navigation learnings, 2026-08-17

## Production acceptance and operations block

- [live-demo] better-method-found <!-- id: lrn-0817-01 -->
  symptom: During production acceptance, `Save position` remained disabled in LOCALIZATION mode and initially looked like an AMCL or initial-pose failure.
  root-cause: The waypoint-name field was empty; the Dashboard intentionally requires a valid name before enabling the service button, but the disabled control did not explain that dependency.
  fix: Entered `home`, which enabled the button immediately, then saved and navigated to the waypoint. Future onboarding should state the name requirement or expose a short disabled-state hint. (check: the Dashboard listed `home`; Nav2 logged `Reached the goal!` and `Goal succeeded`.)
  dead-ends: changing the 3D publish type and republishing `/initialpose`; localization was already active and those steps were unrelated to the disabled button.
  anchors: live-demo#acceptance

- [cloud-run] worked-as-documented <!-- id: lrn-0817-02 -->
  symptom: The public demo still needed production evidence for isolation, fleet limits, and abandoned-session cleanup.
  fix: Crossed two live session capability IDs and received HTTP 403; allocated five services and received HTTP 429 for the sixth; marked the completed acceptance service expired and ran the real OIDC Scheduler job. (check: the Scheduler deleted the expired service and the final private-service count was zero.)
  anchors: cloud-run#operations

- [live-demo] worked-as-documented <!-- id: lrn-0817-03 -->
  symptom: The end-to-end browser workflow had not yet been completed through navigation on the production `/live/` route.
  fix: Completed mapping, map save, map load, localization, waypoint save, and waypoint navigation through embedded Lichtblick. (check: UI returned to `Not navigating`; Cloud Run logs reported `Reached the goal!` and `Goal succeeded`.)
  anchors: live-demo#acceptance

## End-of-block retro

- live-demo — fired: yes; accurate: yes for browser-first acceptance, isolated per-visitor sessions, and full viewer handoff; complete: mostly, though disabled-action onboarding could be clearer; lean: yes.
- cloud-run — fired: yes; accurate: yes for capability isolation, fleet capacity, OIDC Scheduler cleanup, and zero-resource cleanup verification; complete: yes for the current production operations pass; lean: yes.
